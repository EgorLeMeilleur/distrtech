import argparse
import json
import sqlite3
import socket
import pika
import base64
import secrets
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Загрузка конфигурации
with open("config.json", "r") as f:
    config = json.load(f)

# Чтение открытого RSA-ключа (сгенерированного импортёром)
with open(config["encryption"]["rsa_public_key_file"], "rb") as key_file:
    public_key = serialization.load_pem_public_key(key_file.read(), backend=default_backend())

# Функция симметричного шифрования AES-256 (режим CBC с PKCS7)
def aes_encrypt(plaintext, key):
    iv = secrets.token_bytes(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    pad_len = 16 - len(plaintext) % 16
    padding_bytes = bytes([pad_len] * pad_len)
    padded = plaintext + padding_bytes
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return iv, ciphertext

# Чтение данных из SQLite (ненормализованная БД)
def fetch_data():
    conn = sqlite3.connect(config["db"]["sqlite_file"])
    cursor = conn.cursor()
    cursor.execute("SELECT group_name, musician_name, instrument_name, label_name FROM music_data")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Отправка данных через RabbitMQ
def send_via_rabbitmq(message):
    rabbit_conf = config["transport"]["rabbitmq"]
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_conf["host"]))
    channel = connection.channel()
    channel.queue_declare(queue=rabbit_conf["queue"])
    channel.basic_publish(exchange="",
                          routing_key=rabbit_conf["queue"],
                          body=message)
    connection.close()

# Отправка данных через сокеты
def send_via_socket(message):
    socket_conf = config["transport"]["socket"]
    with socket.create_connection((socket_conf["host"], socket_conf["port"])) as s:
        msg_bytes = message.encode("utf-8")
        # Передаём длину сообщения (4 байта, big-endian)
        s.send(len(msg_bytes).to_bytes(4, byteorder="big"))
        s.sendall(msg_bytes)

def main():
    parser = argparse.ArgumentParser(description="Экспортер данных")
    parser.add_argument("--transport", choices=["rabbitmq", "socket"], required=True,
                        help="Выберите транспорт: rabbitmq или socket")
    args = parser.parse_args()

    rows = fetch_data()
    for row in rows:
        # Формируем словарь с данными
        data_dict = {
            "group_name": row[0],
            "musician_name": row[1],
            "instrument_name": row[2],
            "label_name": row[3]
        }
        data_bytes = json.dumps(data_dict).encode("utf-8")
        
        # Генерация случайного симметричного ключа (AES-256)
        sym_key = secrets.token_bytes(32)
        iv, ciphertext = aes_encrypt(data_bytes, sym_key)
        
        # Шифрование симметричного ключа с использованием RSA открытого ключа
        encrypted_sym_key = public_key.encrypt(
            sym_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Формируем итоговое сообщение (кодировка base64 для бинарных данных)
        message_dict = {
            "iv": base64.b64encode(iv).decode("utf-8"),
            "data": base64.b64encode(ciphertext).decode("utf-8"),
            "key": base64.b64encode(encrypted_sym_key).decode("utf-8")
        }
        message = json.dumps(message_dict)
        
        if args.transport == "rabbitmq":
            send_via_rabbitmq(message)
        elif args.transport == "socket":
            send_via_socket(message)
        
        print("Отправлена строка:", data_dict)

if __name__ == "__main__":
    main()
