import grpc
import time
from concurrent import futures
from common import register_service, discover_service
import requests

# gRPC stub подбора диапазона (генерация сигналов)
import temp_control_pb2_grpc, temp_control_pb2


def run_temp_client():
    # регистрация в Consul
    register_service('temp_client', 'temp_client_1', 5001)

    # HTTP health check
    threading.Thread(target=health_app, args=(5001,), daemon=True).start()

    # основной цикл генерации
    gen_min, gen_max = 10, 35
    while True:
        val = random.uniform(gen_min, gen_max)
        # найти анализатор температуры
        addrs = discover_service('temp_server')
        if addrs:
            addr, port = addrs[0]
            url = f"http://{addr}:{port}/analyze"
            try:
                requests.post(url, json={'temp': val})
            except:
                pass
        time.sleep(1)

if __name__ == '__main__':
    run_temp_client()