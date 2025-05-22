import socket

def send_socket(addr: str, port: int, payload: bytes):
    length = len(payload).to_bytes(4, byteorder="big")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((addr, port))
        s.sendall(length + payload)

def recv_socket(conn: socket.socket, buffer_size: int = 4096) -> bytes:
    raw_len = conn.recv(4)
    if not raw_len:
        return b""
    msg_len = int.from_bytes(raw_len, byteorder="big")
    data = b""
    while len(data) < msg_len:
        chunk = conn.recv(buffer_size)
        if not chunk:
            break
        data += chunk
    return data