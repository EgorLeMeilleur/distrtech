import socket
import select

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class SocketCommunication:
    def __init__(self, host, port):
        self.host = host
        self.port = port
    
    def send_data(self, data):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))
        message_length = len(data)
        header = message_length.to_bytes(4, byteorder='big')
        message = header + data
        client.sendall(message)
        client.close()

    def receive_data(self, buffer_size=40, timeout=10):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(1)
        server.settimeout(timeout)

        try:
            ready, _, _ = select.select([server], [], [], timeout)
            if not ready:
                print("Socket timeout: no incoming connection.")
                server.close()
                return None

            conn, addr = server.accept()
            conn.settimeout(timeout)

            raw_len = conn.recv(4)
            message_length = int.from_bytes(raw_len, byteorder='big')

            data = b""
            while len(data) < message_length:
                chunk = conn.recv(buffer_size)
                if not chunk:
                    print('crash')
                    break
                data += chunk

            # data = conn.recv(buffer_size)

            conn.close()
            server.close()
            return data if data else None

        except socket.timeout:
            print("Socket timeout: connection not received in time.")
            server.close()
            return None

        except Exception as e:
            print(f"Socket error: {e}")
            server.close()
            return None