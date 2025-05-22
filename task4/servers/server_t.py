from flask import Flask, request
import threading
import grpc
from concurrent import futures
from common import register_service, discover_service, health_app
import temp_control_pb2_grpc, temp_control_pb2

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze_temp():
    data = request.json
    t = data['temp']
    if t <= 33:
        # линейное уравнение
        result = 2 * t + 5
        # отправка в общий сервер по именованному каналу
        with open('pipe_temp', 'w') as p:
            p.write(str(result))
    else:
        # gRPC: попросить клиент генерировать 33-40
        clients = discover_service('temp_client')
        if clients:
            addr, port = clients[0]
            channel = grpc.insecure_channel(f"{addr}:{5001}")
            stub = temp_control_pb2_grpc.TempControlStub(channel)
            stub.SetRange(temp_control_pb2.Range(min=33, max=40))
    return '', 200

if __name__ == '__main__':
    register_service('temp_server', 'temp_server_1', 6001)
    threading.Thread(target=health_app, args=(6001,), daemon=True).start()
    # named pipe
    if not os.path.exists('pipe_temp'):
        os.mkfifo('pipe_temp')
    app.run(host='0.0.0.0', port=6001)