import socket
import pika
import select
import time

class SocketCommunication:
    def __init__(self, host, port):
        self.host = host
        self.port = port
    
    def send_data(self, data):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))
        client.sendall(data)
        client.close()

def receive_data(self, buffer_size=4096, timeout=10):
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

        data = conn.recv(buffer_size)
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


class QueueCommunication:
    def __init__(self, config, host):
        self.host = host
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.queue_name = config["queue_name"]
        self.exchange = config["exchange"]
        self.routing_key = config["routing_key"]
    
    def send_data(self, data):
        credentials = pika.PlainCredentials(self.user, self.password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials
        ))
        channel = connection.channel()
        
        channel.exchange_declare(exchange=self.exchange, exchange_type='direct')
        channel.queue_declare(queue=self.queue_name)
        channel.queue_bind(queue=self.queue_name, exchange=self.exchange, routing_key=self.routing_key)
        
        channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.routing_key,
            body=data
        )
        
        connection.close()

    def receive_data(self, timeout=10):
        credentials = pika.PlainCredentials(self.user, self.password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            credentials=credentials
        ))
        channel = connection.channel()

        channel.exchange_declare(exchange=self.exchange, exchange_type='direct')
        channel.queue_declare(queue=self.queue_name)
        channel.queue_bind(queue=self.queue_name, exchange=self.exchange, routing_key=self.routing_key)

        start_time = time.time()
        body = None

        while time.time() - start_time < timeout:
            method_frame, header_frame, body = channel.basic_get(queue=self.queue_name)
            if method_frame:
                channel.basic_ack(method_frame.delivery_tag)
                break
            time.sleep(0.5)

        connection.close()
        return body

