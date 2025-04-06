import argparse
import os
import time
import yaml
import json
from communication import SocketCommunication, QueueCommunication
from db_utils import create_sqlite_db, get_data_from_sqlite
from crypto import generate_aes_key, encrypt_with_aes, load_rsa_public_key, encrypt_with_rsa

def main():
    parser = argparse.ArgumentParser(description='Программа экспорта данных')
    parser.add_argument('--mode', choices=['socket', 'queue'], default='socket', help='Режим передачи данных')
    parser.add_argument('--config', default='config.yaml', help='Путь к конфигурационному файлу')
    args = parser.parse_args()
    
    config_file = args.config

    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    
    # Создаём и заполняем SQLite базу данных
    create_sqlite_db(config["db"]["sqlite"]["path"])
    
    # Генерируем ключ AES
    aes_key = generate_aes_key()
    
    # Загружаем публичный ключ RSA (который должен быть предварительно получен от импортера)
    public_key_file = config["connection"]["encryption"]["rsa_public_key_file"]
    if not os.path.exists(public_key_file):
        print(f"Ошибка: Файл с публичным ключом RSA не найден: {public_key_file}")
        print("Убедитесь, что импортер уже запущен и сгенерировал ключи.")
        return
    
    public_key = load_rsa_public_key(public_key_file)
    
    # Шифруем AES ключ с помощью RSA
    encrypted_aes_key = encrypt_with_rsa(public_key, aes_key)
    
    # Данные из SQLite
    data = get_data_from_sqlite(config["db"]["sqlite"]["path"])
    
    if args.mode == 'socket':
        # Используем сокеты для передачи данных
        socket_config = config["connection"]["socket"]
        comm = SocketCommunication(socket_config["host"], socket_config["port"])
        
        # Сначала отправляем зашифрованный AES ключ
        comm.send_data(encrypted_aes_key)
        time.sleep(1)  # Небольшая задержка
        
        # Затем отправляем данные, зашифрованные с помощью AES
        for row in data:
            json_data = json.dumps(row).encode('utf-8')
            encrypted_data = encrypt_with_aes(aes_key, json_data)
            comm.send_data(encrypted_data)
            time.sleep(0.5)  # Задержка между отправками
        
    elif args.mode == 'queue':
        # Используем очередь сообщений для передачи данных
        queue_config = config["connection"]["queue"]
        comm = QueueCommunication(queue_config)
        
        # Сначала отправляем зашифрованный AES ключ
        comm.send_data(encrypted_aes_key)
        
        # Затем отправляем данные, зашифрованные с помощью AES
        for row in data:
            json_data = json.dumps(row).encode('utf-8')
            encrypted_data = encrypt_with_aes(aes_key, json_data)
            comm.send_data(encrypted_data)
            time.sleep(0.5)  # Задержка между отправками

if __name__ == "__main__":
    main()