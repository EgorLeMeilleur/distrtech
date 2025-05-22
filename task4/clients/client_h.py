import grpc
import time
import random
import requests
import threading
from common import register_service, discover_service, health_app
import humid_control_pb2_grpc, humid_control_pb2

def run_humidity_client():
    register_service('humidity_client', 'humidity_client_1', 5002)
    threading.Thread(target=health_app, args=(5002,), daemon=True).start()

    gen_min, gen_max = 50, 75
    while True:
        val = random.uniform(gen_min, gen_max)
        addrs = discover_service('humidity_server')
        if addrs:
            addr, port = addrs[0]
            url = f"http://{addr}:{port}/analyze"
            try:
                requests.post(url, json={'humid': val})
            except:
                pass
        time.sleep(1)

if __name__ == '__main__':
    run_humidity_client()