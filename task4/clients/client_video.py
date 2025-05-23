import time
import socket
import threading
import backoff
import grpc
import cv2
from concurrent import futures

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from communication.consul import register_service, discover_service, deregister_service
from communication.socket import find_free_port, SocketCommunication, get_ip_in_network

from proto.control_pb2_grpc import VideoControlServicer, add_VideoControlServicer_to_server
from proto.control_pb2 import Empty

STREAM_URL   = 'https://stream.mu-u.ru:8443/amka/cam7/playlist.m3u8'
SERVICE_NAME = 'video_client'

filter_active = False

class VideoService(VideoControlServicer):
    def ApplyFilter(self, request, context):
        global filter_active
        if request.filter_type != 'none':
            filter_active = True
            print(f"gRPC: start filter '{request.filter_type}'")
        else:
            filter_active = False
            print("gRPC: stop filter")
        return Empty(message="OK")

@backoff.on_exception(backoff.expo, Exception, max_time=60)
def resilient_register(host, port, service_id):
    register_service(SERVICE_NAME, service_id, host, port)
    print(f"Registered in Consul: {service_id}@{host}:{port}")

def grpc_server_loop(host, port):
    server = grpc.server(futures.ThreadPoolExecutor())
    add_VideoControlServicer_to_server(VideoService(), server)
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    print(f"gRPC server listening on {host}:{port}")
    server.wait_for_termination()

def main():
    host = get_ip_in_network()
    grpc_port = find_free_port()
    service_id = f"{SERVICE_NAME}_{grpc_port}"

    try:
        resilient_register(host, grpc_port, service_id)
    except Exception as e:
        print(f"Consul registration failed: {e}")
        return

    threading.Thread(
        target=grpc_server_loop,
        args=(host, grpc_port),
        daemon=True
    ).start()

    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        print("Cannot open video stream")
        deregister_service(service_id)
        return


    try:
        while True:
            ret, frame = cap.read()

            servers = discover_service('video_server')
            if not servers:
                print("No video_server instances found, retrying...")
                time.sleep(2)
                continue

            if not ret:
                print("Empty frame, retry in 1s")
                time.sleep(1)
                continue


            if filter_active:
                frame = cv2.GaussianBlur(frame, (15, 15), 0)

            _, buf = cv2.imencode('.jpg', frame)
            data = buf.tobytes()

            for addr, port in servers:
                try:
                    sock = SocketCommunication(addr, port)
                    sock.send_data(data)
                    print(f"Sent frame to {addr}:{port}")
                except Exception as e:
                    print(f"Connection to {addr}:{port} failed: {e}")
                finally:
                    sock.close_connection()

            time.sleep(3)

    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        cap.release()
        try:
            deregister_service(service_id)
            print("Video client shut down")
        except Exception as e:
            print(f"Failed to deregister: {e}")

if __name__ == "__main__":
    main()
