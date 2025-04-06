import argparse
import os
import time
import yaml
import json
from communication import SocketCommunication, QueueCommunication
from db_utils import insert_normalized_data
from crypto import generate_rsa_keys, load_rsa_private_key, decrypt_with_rsa, decrypt_with_aes, save_rsa_keys

def main():
    parser = argparse.ArgumentParser(description='Программа импорта данных')
    parser.add_argument('--mode', choices=['socket', 'queue'], default='socket', help='Режим передачи данных')
    parser.add_argument('--config', default='config.yaml', help='Путь к конфигурационному файлу')
    args = parser.parse_args()
    
    config_file = args.config

    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    
    # Генерируем пару ключей RSA
    private_key_file = config["connection"]["encryption"]["rsa_private_key_file"]
    public_key_file = config["connection"]["encryption"]["rsa_public_key_file"]
    
    if not os.path.exists(private_key_file) or not os.path.exists(public_key_file):
        private_key, public_key = generate_rsa_keys()
        save_rsa_keys(private_key, public_key, private_key_file, public_key_file)
        print(f"Сгенерированы новые ключи RSA: {public_key_file}, {private_key_file}")
    else:
        private_key = load_rsa_private_key(private_key_file)
        print(f"Загружены существующие ключи RSA: {public_key_file}, {private_key_file}")
    
    if args.mode == 'socket':
        # Используем сокеты для приёма данных
        socket_config = config["connection"]["socket"]
        comm = SocketCommunication(socket_config["host"], socket_config["port"])
        
        # Сначала получаем зашифрованный AES ключ
        encrypted_aes_key = comm.receive_data()
        aes_key = decrypt_with_rsa(private_key, encrypted_aes_key)
        
        # Затем получаем и обрабатываем данные
        while True:
            try:
                encrypted_data = comm.receive_data()
                json_data = decrypt_with_aes(aes_key, encrypted_data)
                data = json.loads(json_data.decode('utf-8'))
                
                # Вставляем данные в нормализованную БД
                insert_normalized_data(config, data[0], data[1], data[2], data[3])
                print(f"Данные импортированы: {data}")
            except Exception as e:
                print(f"Ошибка при приёме или обработке данных: {e}")
                break
    
    elif args.mode == 'queue':
        # Используем очередь сообщений для приёма данных
        queue_config = config["connection"]["queue"]
        comm = QueueCommunication(queue_config)
        
        # Сначала получаем зашифрованный AES ключ
        encrypted_aes_key = comm.receive_data()
        if encrypted_aes_key:
            aes_key = decrypt_with_rsa(private_key, encrypted_aes_key)
            
            # Затем получаем и обрабатываем данные
            while True:
                encrypted_data = comm.receive_data()
                if not encrypted_data:
                    time.sleep(1)  # Если нет данных, ждём и пробуем снова
                    continue
                
                json_data = decrypt_with_aes(aes_key, encrypted_data)
                data = json.loads(json_data.decode('utf-8'))
                
                # Вставляем данные в нормализованную БД
                insert_normalized_data(config, data[0], data[1], data[2], data[3])
                print(f"Данные импортированы: {data}")

if __name__ == "__main__":
    main()
