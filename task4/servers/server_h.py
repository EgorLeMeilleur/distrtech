import json
import socket
import time
import grpc
import backoff

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from communication.consul import register_service, discover_service, deregister_service
from communication.rabbitmq import QueueCommunication
from communication.named_pipe import send_pipe
from communication.socket import find_free_port

from proto.control_pb2_grpc import HumidityControlStub
from proto.control_pb2 import Range

SERVICE_NAME = 'hum_server'
RABBIT_QUEUE = 'hum_requests'
PIPE_NAME = 'pipe_hum'
GRPC_METHOD = 'SetRange'

def handle_message(body: bytes, flag_ok: bool) -> bool:
    try:
        data = json.loads(body.decode())
        t = data['value']
        ts = data['ts']
        print(f"Received hum={t:.2f} at ts={ts}")

        if t > 33:
            try:
                send_pipe(PIPE_NAME, {'type': 'hum', 'value': 1.5 * t + 4, 'ts': ts})
                print(f"Wrote to pipe '{PIPE_NAME}'")
            except Exception as e:
                print(f"Failed to write to pipe: {e}")

            if flag_ok:
                flag_ok = False
                try:
                    clients = discover_service('hum_client')
                    print(f"Discovered hum_client: {clients}")
                    for addr, port in clients:
                        try:
                            channel = grpc.insecure_channel(f"{addr}:{port}")
                            stub = HumidityControlStub(channel)
                            resp = stub.SetRange(Range(min=72, max=80))
                            print(f"gRPC SetRange(72,80) -> {resp.message}")
                        except Exception as e:
                            print(f"gRPC call failed: {e}")
                except Exception as e:
                    print(f"Consul discovery failed: {e}")

        else:
            try:
                send_pipe(PIPE_NAME, {'type': 'hum', 'value': 2 * t + 5, 'ts': ts})
                print(f"Wrote to pipe '{PIPE_NAME}'")
            except Exception as e:
                print(f"Failed to write to pipe: {e}")

            if not flag_ok:
                flag_ok = True
                try:
                    clients = discover_service('hum_client')
                    print(f"Discovered hum_client: {clients}")
                    for addr, port in clients:
                        try:
                            channel = grpc.insecure_channel(f"{addr}:{port}")
                            stub = HumidityControlStub(channel)
                            resp = stub.SetRange(Range(min=50, max=75))
                            print(f"gRPC SetRange(50,75) -> {resp.message}")
                        except Exception as e:
                            print(f"gRPC call failed: {e}")
                except Exception as e:
                    print(f"Consul discovery failed: {e}")

    except Exception:
        print("Error processing message")

    return flag_ok


@backoff.on_exception(backoff.expo, Exception, max_time=600)
def resilient_register(host: str, port: int, service_id: str):
    register_service(SERVICE_NAME, service_id, host, port)
    print(f"Registered in Consul: {service_id}@{host}:{port}")


@backoff.on_exception(backoff.expo, Exception, max_time=600)
def resilient_rabbit_connect() -> QueueCommunication:
    qc = QueueCommunication(RABBIT_QUEUE)
    print(f"Connected to RabbitMQ queue '{RABBIT_QUEUE}'")
    return qc


def main():
    host = socket.gethostbyname(socket.gethostname())
    port = find_free_port()
    service_id = f"{SERVICE_NAME}_{port}"

    try:
        resilient_register(host, port, service_id)
    except Exception as e:
        print(f"Consul registration failed: {e}")
        return

    try:
        queue = resilient_rabbit_connect()
    except Exception as e:
        print(f"RabbitMQ connection failed: {e}")
        deregister_service(service_id)
        return

    flag_ok = True
    print(f"Serving, waiting messages on '{RABBIT_QUEUE}'")
    try:
        while True:
            try:
                body = queue.receive_data()
                if body:
                    flag_ok = handle_message(body, flag_ok)
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error in processing loop: {e}")
                time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        try:
            deregister_service(service_id)
            print(f"Deregistered {service_id}")
        except Exception as e:
            print(f"Failed to deregister: {e}")


if __name__ == "__main__":
    main()
