import argparse
import yaml
import json
from communication import SocketCommunication, QueueCommunication
from db_utils import create_sqlite_db, get_data_from_sqlite
from crypto import generate_aes_key, encrypt_with_aes, encrypt_with_rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

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
        comm = SocketCommunication(socket_config["host"], socket_config["port"])

    elif args.mode == 'queue':
        queue_config = config["connection"]["queue"]
        comm = QueueCommunication(queue_config)

    rsa_public_key = comm.receive_data()
    pem_public_key = json.loads(rsa_public_key)["public_key"]
    rsa_key = serialization.load_pem_public_key(
        pem_public_key.encode('utf-8'), 
        backend=default_backend()
    )

    aes_key = generate_aes_key()
    encrypted_aes_key = encrypt_with_rsa(rsa_key, aes_key)
        
    comm.send_data(encrypted_aes_key)
    
    for row in data:
        json_data = json.dumps(row).encode('utf-8')
        encrypted_data = encrypt_with_aes(aes_key, json_data)
        comm.send_data(encrypted_data)

if __name__ == "__main__":
    main()