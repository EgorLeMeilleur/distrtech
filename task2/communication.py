import socket
import pika

class SocketCommunication:
    def __init__(self, host, port):
        self.host = host
        self.port = port
    
    def send_data(self, data):
        """Отправка данных через сокеты"""
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((self.host, self.port))
        client.sendall(data)
        client.close()
    
    def receive_data(self, buffer_size=4096):
        """Приём данных через сокеты"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(1)
        conn, addr = server.accept()
        data = conn.recv(buffer_size)
        conn.close()
        server.close()
        return data

class QueueCommunication:
    def __init__(self, config):
        self.host = config["host"]
        self.port = config["port"]
        self.user = config["user"]
        self.password = config["password"]
        self.queue_name = config["queue_name"]
        self.exchange = config["exchange"]
        self.routing_key = config["routing_key"]
    
    def send_data(self, data):
        """Отправка данных через очередь сообщений"""
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
    
    def receive_data(self):
        """Приём данных из очереди сообщений"""
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
        
        method_frame, header_frame, body = channel.basic_get(queue=self.queue_name)
        
        if method_frame:
            channel.basic_ack(method_frame.delivery_tag)
            connection.close()
            return body
        else:
            connection.close()
            return None
