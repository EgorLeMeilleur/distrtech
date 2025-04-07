import argparse
import yaml
import json
from communication import SocketCommunication, QueueCommunication
from db_utils import create_sqlite_db, get_data_from_sqlite
from crypto import generate_aes_key, encrypt_with_aes, encrypt_with_rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import time

def main():
    parser = argparse.ArgumentParser(description='Программа экспорта данных')
    parser.add_argument('--mode', choices=['socket', 'queue'], default='socket', help='Режим передачи данных')
    parser.add_argument('--config', default='config.yaml', help='Путь к конфигурационному файлу')
    args = parser.parse_args()
    
    config_file = args.config

    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    
    create_sqlite_db(config["db"]["sqlite"]["path"])
    data = get_data_from_sqlite(config["db"]["sqlite"]["path"])
    
    if args.mode == 'socket':
        socket_config = config["connection"]["socket"]
        comm_data = SocketCommunication(socket_config["host_data"], socket_config["port"])
        
        rsa_public_key = comm_data.receive_data(timeout=10)
        if not rsa_public_key:
            print("Нет данных или соединение прервано. Завершение импорта.")
            return
        
        print("Получен публичный ключ RSA")
        pem_public_key = json.loads(rsa_public_key)["public_key"]
        rsa_key = serialization.load_pem_public_key(pem_public_key.encode('utf-8'), backend=default_backend())

        aes_key = generate_aes_key()
        encrypted_aes_key = encrypt_with_rsa(rsa_key, aes_key)

    elif args.mode == 'queue':
        queue_config = config["connection"]["queue"]
        comm_data = QueueCommunication(queue_config, queue_config["host_data"], queue_config["queue_data"], queue_config["exchange_data"], queue_config["routing_data"])
        comm_key = QueueCommunication(queue_config, queue_config["host_key"], queue_config["queue_key"], queue_config["exchange_key"], queue_config["routing_key"])

        rsa_public_key = comm_key.receive_data(timeout=10)
        if not rsa_public_key:
            print("Нет данных или соединение прервано. Завершение импорта.")
            return
        
        print("Получен публичный ключ RSA")
        pem_public_key = json.loads(rsa_public_key)["public_key"]
        rsa_key = serialization.load_pem_public_key(pem_public_key.encode('utf-8'), backend=default_backend())

        aes_key = generate_aes_key()
        encrypted_aes_key = encrypt_with_rsa(rsa_key, aes_key)
        
    comm_data.send_data(encrypted_aes_key)
    print("Отправлен ключ AES")
    time.sleep(0.2)
    
    for row in data:
        if not row:
            print("Пустые данные. Завершение экспорта.")
            break
        try:
            json_data = json.dumps(row).encode('utf-8')
            encrypted_data = encrypt_with_aes(aes_key, json_data)
            comm_data.send_data(encrypted_data)
            print("Отправлены данные:", json_data)
            time.sleep(0.2)
        except Exception as e:
            print(f"Ошибка при отправке данных: {e}")
            break

if __name__ == "__main__":
    main()