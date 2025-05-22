import json
import time
import socket
import random
import threading
from datetime import datetime
import grpc
from concurrent import futures
import backoff 

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from communication.consul import register_service, deregister_service
from communication.rabbitmq import QueueCommunication
from communication.socket import find_free_port

from proto.control_pb2_grpc import HumidityControlServicer, add_HumidityControlServicer_to_server
from proto.control_pb2 import Empty

SERVICE_NAME = 'hum_client'
QUEUE_NAME = 'hum_requests'
GRPC_WORKERS = 2

min_hum = 50.0
max_hum = 75.0

class HumClientService(HumidityControlServicer):
    def SetRange(self, request, context):
        global min_hum, max_hum
        min_hum = request.min
        max_hum = request.max
        print(f"gRPC SetRange received: min={min_hum}, max={max_hum}")
        return Empty()

@backoff.on_exception(backoff.expo, Exception, max_time=600)
def resilient_register(host, port, service_id):
    register_service(SERVICE_NAME, service_id, host, port)
    print(f"Registered service in Consul: {SERVICE_NAME}/{service_id}@{host}:{port}")

@backoff.on_exception(backoff.expo, Exception, max_time=600)
def resilient_rabbit_connect():
    queue = QueueCommunication(QUEUE_NAME)
    print(f"Connected to RabbitMQ queue '{QUEUE_NAME}'")
    return queue

def grpc_server_loop(host, port):
    while True:
        try:
            server = grpc.server(futures.ThreadPoolExecutor(max_workers=GRPC_WORKERS))
            add_HumidityControlServicer_to_server(HumidityControlServicer(), server)
            server.add_insecure_port(f'{host}:{port}')
            server.start()
            print(f"gRPC server started on {host}:{port}")
            server.wait_for_termination()
        except Exception as e:
            print(f"gRPC server crashed: {e}, restarting in 5s")
            time.sleep(5)

def main():
    host = socket.gethostbyname(socket.gethostname())
    grpc_port = find_free_port()
    service_id = f'{SERVICE_NAME}_{grpc_port}'

    try:
        resilient_register(host, grpc_port, service_id)
    except Exception as e:
        print(f"Не удалось зарегистрироваться в Consul: {e}")
        return

    grpc_thread = threading.Thread(target=grpc_server_loop, args=(host, grpc_port), daemon=True)
    grpc_thread.start()

    try:
        queue = resilient_rabbit_connect()
    except Exception as e:
        print(f"Не удалось подключиться к RabbitMQ: {e}")
        deregister_service(service_id)
        return
    try:
        while True:
            value = round(random.uniform(min_hum, max_hum), 2)
            ts = datetime.utcnow().isoformat()
            msg = {'value': value, 'ts': ts}
            try:
                queue.send_data(json.dumps(msg).encode('utf-8'))
                print(f"Sent hum={value:.2f} at ts={ts}")
            except Exception as e:
                print(f"Failed to send to RabbitMQ: {e}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        try:
            deregister_service(service_id)
            print(f"Deregistered service {service_id}")
        except Exception as e:
            print(f"Failed to deregister: {e}")

if __name__ == '__main__':
    main()
