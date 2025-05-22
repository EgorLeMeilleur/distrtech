import os
import pika
import json
from services.config import RABBIT_ADDR, RABBIT_PORT

# RABBIT_URL = 

def create_queue(queue_name: str):
    conn = pika.BlockingConnection(pika.URLParameters(RABBIT_URL))
    ch = conn.channel()
    ch.queue_declare(queue=queue_name, durable=True)
    conn.close()

def send_rabbit(queue_name: str, message: dict):
    conn = pika.BlockingConnection(pika.URLParameters(RABBIT_URL))
    ch = conn.channel()
    ch.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(message).encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    conn.close()

def recv_rabbit(queue_name: str, callback):
    conn = pika.BlockingConnection(pika.URLParameters(RABBIT_URL))
    ch = conn.channel()
    ch.basic_qos(prefetch_count=1)
    ch.queue_declare(queue=queue_name, durable=True)

    def _on_message(ch, method, properties, body):
        data = json.loads(body.decode("utf-8"))
        callback(data)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_consume(queue=queue_name, on_message_callback=_on_message)
    ch.start_consuming()