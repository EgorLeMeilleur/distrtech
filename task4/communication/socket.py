import socket
import select

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class SocketCommunication:
    def __init__(self, host: str, port: int, buffer_size: int = 4096, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.timeout = timeout
        self.server = None
        self.conn = None

    def open_server(self):
        if self.server:
            return
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(1)
        self.server.settimeout(self.timeout)

    def accept_connection(self):
        if not self.server:
            self.open_server()
        try:
            ready, _, _ = select.select([self.server], [], [], self.timeout)
            if not ready:
                return False
            self.conn, _ = self.server.accept()
            self.conn.settimeout(self.timeout)
            return True
        except Exception:
            self.close_connection()
            return False

    def receive_data(self):
        if not self.conn:
            if not self.accept_connection():
                return None
        try:
            raw_len = self.conn.recv(4)
            if not raw_len:
                raise ConnectionError("Empty header")
            msg_len = int.from_bytes(raw_len, byteorder='big')
            data = b''
            while len(data) < msg_len:
                chunk = self.conn.recv(self.buffer_size)
                if not chunk:
                    raise ConnectionError("Connection lost during data recv")
                data += chunk
            return data
        except Exception:
            self.close_connection()
            return None

    def send_data(self, data):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(self.timeout)
        client.connect((self.host, self.port))
        header = len(data).to_bytes(4, byteorder='big')
        client.sendall(header + data)
        client.close()

    def close_connection(self):
        if self.conn:
            try: self.conn.close()
            except: pass
            self.conn = None

    def close_server(self):
        if self.server:
            try: self.server.close()
            except: pass
            self.server = None