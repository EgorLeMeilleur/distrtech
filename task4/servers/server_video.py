import time
import socket
import backoff 
import grpc
import numpy as np
from io import BytesIO
from PIL import Image
import json
import os

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from communication.consul import register_service, discover_service, deregister_service
from communication.named_pipe import get_aggregator_pipe
from communication.socket import find_free_port, SocketCommunication, get_ip_in_network

from proto.control_pb2_grpc import VideoControlStub
from proto.control_pb2 import FilterRequest

SERVICE_NAME = 'video_server'
PIPE_NAME    = 'pipe_video'
THRESHOLD    = 106

flag_filtered = False

@backoff.on_exception(backoff.expo, Exception, max_time=60)
def resilient_register(host, port, service_id):
    register_service(SERVICE_NAME, service_id, host, port)
    print(f"Registered in Consul: {service_id}@{host}:{port}")

def handle_frame_data(data: bytes):
    global flag_filtered
    try:
        img = np.array(Image.open(BytesIO(data)))
        mean_val = img.mean()
        ts = time.time()
        print(f"Frame mean={mean_val:.2f}")

        msg = {'type': 'video', 'value': mean_val, 'ts': ts}
        pipes = get_aggregator_pipe('pipe_video')
        if pipes:
            try:
                for pipe in pipes:
                    payload = json.dumps(msg).encode("utf-8")
                    flags   = os.O_WRONLY | os.O_NONBLOCK
                    fd = os.open(pipe, flags)
                    os.write(fd, payload)
                    os.close(fd)
                    print(f"Sent to aggregator via FIFO {pipe}: {msg}")
            except Exception as e:
                print(f"Failed to write to FIFO {pipe}: {e}")
        else:
            print("Aggregator pipe not available, skipping send")

        if mean_val > THRESHOLD or flag_filtered:
            clients = discover_service('video_client')
            for addr, port in clients:
                try:
                    channel = grpc.insecure_channel(f"{addr}:{port}")
                    stub = VideoControlStub(channel)
                    if mean_val > THRESHOLD and not flag_filtered:
                        stub.ApplyFilter(FilterRequest(filter_type='blur'))
                        flag_filtered = True
                        print("Instructed client to start filter")
                    elif mean_val <= THRESHOLD and flag_filtered:
                        stub.ApplyFilter(FilterRequest(filter_type='none'))
                        flag_filtered = False
                        print("Instructed client to stop filter")
                except Exception as e:
                    print(f"gRPC call to client {addr}:{port} failed: {e}")

    except Exception:
        print("Error handling connection")

def main():
    host = get_ip_in_network()
    port = find_free_port()
    service_id = f"{SERVICE_NAME}_{port}"

    try:
        resilient_register(host, port, service_id)
    except Exception as e:
        print(f"Consul registration failed: {e}")
        return

    socket_comm = SocketCommunication(host, port)
    print(f"Listening for frames on {host}:{port}")

    try:
        while True:
            data = socket_comm.receive_data()
            if data:
                handle_frame_data(data)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        socket_comm.close_connection()
        socket_comm.close_server()
        deregister_service(service_id)
        print("Video server shut down")

if __name__ == "__main__":
    main()