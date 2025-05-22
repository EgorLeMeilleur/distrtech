import grpc
from concurrent import futures

def send_grpc(host: str, port: int, stub_class, request_obj):
    """
    host: хост клиента/сервера,
    port: порт gRPC,
    stub_class: класс Stub, например TempControlStub,
    request_obj: protobuf-сообщение (например Range(min=..., max=...))
    """
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = stub_class(channel)
    return stub.__class__.__name__  # вызов нужного метода делается вне этой абстракции

def serve_grpc(servicer, add_servicer_fn, port: int):
    """
    servicer: экземпляр класса-реализации,
    add_servicer_fn: функция add_*_to_server,
    порт: на каком слушать соединения
    """
    server = grpc_com.server(futures.ThreadPoolExecutor(max_workers=4))
    add_servicer_fn(servicer, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    return server