import argparse
import yaml
import json
from communication import SocketCommunication, QueueCommunication
from db_utils import insert_normalized_data
from crypto import generate_rsa_keys, decrypt_with_rsa, decrypt_with_aes
from cryptography.hazmat.primitives import serialization
import time
def main():
    parser = argparse.ArgumentParser(description='Программа импорта данных')
    parser.add_argument('--mode', choices=['socket', 'queue'], default='socket', help='Режим передачи данных')
    parser.add_argument('--config', default='config.yaml', help='Путь к конфигурационному файлу')
    args = parser.parse_args()
    
    config_file = args.config

    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)

    private_key, public_key = generate_rsa_keys()

    if args.mode == 'socket':
        socket_config = config["connection"]["socket"]
        comm_data = SocketCommunication(socket_config["host_data"], socket_config["port"])
        comm_key = SocketCommunication(socket_config["host_key"], socket_config["port"])

    elif args.mode == 'queue':
        queue_config = config["connection"]["queue"]
        comm_data = QueueCommunication(queue_config, queue_config["host_data"])
        comm_key = QueueCommunication(queue_config, queue_config["host_key"])

    pem_public_key = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')

    send_public_key = json.dumps({"public_key": pem_public_key}).encode('utf-8')
    comm_key.send_data(send_public_key)
    print(f"Отправлен публичный ключ RSA")
    encrypted_aes_key = comm_data.receive_data(timeout=10)
    print(f"Получен AES ключ")
    aes_key = decrypt_with_rsa(private_key, encrypted_aes_key)
    
    while True:
        print("Ожидание данных...")
        encrypted_data = comm_data.receive_data(timeout=10)
        if not encrypted_data:
            print("Нет данных или соединение прервано. Завершение импорта.")
            break

        try:
            json_data = decrypt_with_aes(aes_key, encrypted_data)
            data = json.loads(json_data.decode('utf-8'))
            insert_normalized_data(config, data[0], data[1], data[2], data[3])
            print(f"Данные импортированы: {data}")
        except Exception as e:
            print(f"Ошибка при обработке данных: {e}")
            break


if __name__ == "__main__":
    main()
