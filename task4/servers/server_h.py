from flask import Flask, request
import threading, os
import grpc
from common import register_service, discover_service, health_app
import humid_control_pb2_grpc, humid_control_pb2

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze_humid():
    h = request.json['humid']
    if h <= 72:
        result = 1.5 * h + 2
        with open('pipe_humid', 'w') as p:
            p.write(str(result))
    else:
        clients = discover_service('humidity_client')
        if clients:
            addr, port = clients[0]
            channel = grpc.insecure_channel(f"{addr}:{5002}")
            stub = humid_control_pb2_grpc.HumidControlStub(channel)
            stub.SetRange(humid_control_pb2.Range(min=72, max=80))
    return '', 200

if __name__ == '__main__':
    register_service('humidity_server', 'humidity_server_1', 6002)
    threading.Thread(target=health_app, args=(6002,), daemon=True).start()
    if not os.path.exists('pipe_humid'):
        os.mkfifo('pipe_humid')
    app.run(host='0.0.0.0', port=6002)