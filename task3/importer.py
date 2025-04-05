import argparse
import json
import socket
import pika
import psycopg2
from psycopg2 import sql
import os
import base64
import secrets
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Загрузка конфигурации
with open("config.json", "r") as f:
    config = json.load(f)

# Генерация RSA-ключей, если отсутствуют
def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    with open(config["encryption"]["rsa_private_key_file"], "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
    with open(config["encryption"]["rsa_public_key_file"], "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    return private_key, public_key

if not (os.path.exists(config["encryption"]["rsa_private_key_file"]) and os.path.exists(config["encryption"]["rsa_public_key_file"])):
    private_key, public_key = generate_rsa_keys()
else:
    with open(config["encryption"]["rsa_private_key_file"], "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

# Функция симметричного дешифрования AES-256 (режим CBC с PKCS7)
def aes_decrypt(iv, ciphertext, key):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    pad_len = padded[-1]
    return padded[:-pad_len]

# Функция вставки строки в нормализованную БД PostgreSQL
def insert_normalized_data(group_name, musician_name, instrument_name, label_name):
    pg_conf = config["db"]["postgres"]
    conn = psycopg2.connect(
        dbname=pg_conf["dbname"],
        user=pg_conf["user"],
        password=pg_conf["password"],
        host=pg_conf["host"],
        port=pg_conf["port"]
    )
    cursor = conn.cursor()
    # Создаём таблицы, если они ещё не существуют (однократно)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS groups (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            label_id INTEGER REFERENCES labels(id)
        );
        CREATE TABLE IF NOT EXISTS musicians (
            id SERIAL PRIMARY KEY,
            name TEXT,
            group_id INTEGER REFERENCES groups(id)
        );
        CREATE TABLE IF NOT EXISTS instruments (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS musician_instruments (
            musician_id INTEGER REFERENCES musicians(id),
            instrument_id INTEGER REFERENCES instruments(id),
            PRIMARY KEY (musician_id, instrument_id)
        );
    """)
    conn.commit()
    
    # Логика миграции (аналогичная вашему скрипту)
    cursor.execute("SELECT id FROM labels WHERE name = %s", (label_name,))
    label = cursor.fetchone()
    if label:
        label_id = label[0]
    else:
        cursor.execute("INSERT INTO labels (name) VALUES (%s) RETURNING id", (label_name,))
        label_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM groups WHERE name = %s AND label_id = %s", (group_name, label_id))
    group = cursor.fetchone()
    if group:
        group_id = group[0]
    else:
        cursor.execute("INSERT INTO groups (name, label_id) VALUES (%s, %s) RETURNING id", (group_name, label_id))
        group_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM musicians WHERE name = %s AND group_id = %s", (musician_name, group_id))
    musician = cursor.fetchone()
    if musician:
        musician_id = musician[0]
    else:
        cursor.execute("INSERT INTO musicians (name, group_id) VALUES (%s, %s) RETURNING id", (musician_name, group_id))
        musician_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM instruments WHERE name = %s", (instrument_name,))
    instrument = cursor.fetchone()
    if instrument:
        instrument_id = instrument[0]
    else:
        cursor.execute("INSERT INTO instruments (name) VALUES (%s) RETURNING id", (instrument_name,))
        instrument_id = cursor.fetchone()[0]

    cursor.execute("SELECT 1 FROM musician_instruments WHERE musician_id = %s AND instrument_id = %s", (musician_id, instrument_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO musician_instruments (musician_id, instrument_id) VALUES (%s, %s)", (musician_id, instrument_id))
    conn.commit()
    cursor.close()
    conn.close()

# Обработка входящего зашифрованного сообщения
def process_message(message):
    msg = json.loads(message)
    iv = base64.b64decode(msg["iv"])
    encrypted_data = base64.b64decode(msg["data"])
    encrypted_sym_key = base64.b64decode(msg["key"])
    
    # Расшифровка симметричного ключа RSA
    sym_key = private_key.decrypt(
        encrypted_sym_key,
        asym_padding.OAEP(
            mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    decrypted = aes_decrypt(iv, encrypted_data, sym_key)
    data_dict = json.loads(decrypted.decode("utf-8"))
    
    print("Получены данные:", data_dict)
    insert_normalized_data(data_dict["group_name"],
                           data_dict["musician_name"],
                           data_dict["instrument_name"],
                           data_dict["label_name"])

# Обработка сообщений через RabbitMQ
def rabbitmq_listener():
    rabbit_conf = config["transport"]["rabbitmq"]
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_conf["host"]))
    channel = connection.channel()
    channel.queue_declare(queue=rabbit_conf["queue"])
    
    def callback(ch, method, properties, body):
        process_message(body.decode("utf-8"))
    
    channel.basic_consume(queue=rabbit_conf["queue"], on_message_callback=callback, auto_ack=True)
    print("Ожидание сообщений из RabbitMQ...")
    channel.start_consuming()

# Обработка сообщений через сокеты
def socket_listener():
    socket_conf = config["transport"]["socket"]
    host = socket_conf["host"]
    port = socket_conf["port"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"Сокет-сервер запущен на {host}:{port}")
        while True:
            conn, addr = s.accept()
            with conn:
                print("Подключение от", addr)
                # Принимаем длину сообщения (4 байта, big-endian)
                length_data = conn.recv(4)
                if not length_data:
                    continue
                msg_length = int.from_bytes(length_data, byteorder="big")
                chunks = []
                bytes_recd = 0
                while bytes_recd < msg_length:
                    chunk = conn.recv(min(msg_length - bytes_recd, 2048))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    bytes_recd += len(chunk)
                message = b"".join(chunks).decode("utf-8")
                process_message(message)

def main():
    parser = argparse.ArgumentParser(description="Импортёр данных (нормализованная БД)")
    parser.add_argument("--transport", choices=["rabbitmq", "socket"], required=True,
                        help="Выберите транспорт для приёма данных: rabbitmq или socket")
    args = parser.parse_args()

    if args.transport == "rabbitmq":
        rabbitmq_listener()
    elif args.transport == "socket":
        socket_listener()

if __name__ == "__main__":
    main()
