import grpc
from concurrent import futures

def send_grpc(host: str, port: int, stub_class, request_obj):
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = stub_class(channel)
    return stub.__class__.__name__

def serve_grpc(servicer, add_servicer_fn, port: int):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    add_servicer_fn(servicer, server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    return server