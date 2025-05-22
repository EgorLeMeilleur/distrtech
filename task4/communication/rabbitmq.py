import pika
import time
from services.config import RABBIT_ADDR, RABBIT_PORT, RABBIT_USER, RABBIT_PASS
    
class QueueCommunication:
    def __init__(self, queue_name):
        self.host = RABBIT_ADDR
        self.port = RABBIT_PORT
        self.user = RABBIT_USER
        self.password = RABBIT_PASS
        self.queue_name = queue_name
        self.queue_name = queue_name
        self.exchange = 'key_exchange'
        self.routing_key = 'key_key'
    
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