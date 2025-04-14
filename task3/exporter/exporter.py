import time
import logging
from grpc_client import GRPCDataImporterClient
from db_work import initialize_sqlite_db, get_music_data
import os
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'exporter_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    sqlite_db = config['exporter']['sqlite_db_path']

    initialize_sqlite_db(sqlite_db)
    
    data = get_music_data(sqlite_db)
    print(f"Найдено {len(data)} записей для экспорта")
    
    grpc_config = config['importer']
    client = GRPCDataImporterClient(
        grpc_config['host'],
        grpc_config['port'],
        config['security']['ca_cert']
    )

    group_names, musician_names, instrument_names, label_names = [], [], [], []

    
    for record in data:
        group_name, musician_name, instrument_name, label_name = record
        group_names.append(group_name)
        musician_names.append(musician_name)
        instrument_names.append(instrument_name)
        label_names.append(label_name)

    success, message = client.import_music_data(group_name, musician_name, instrument_name, label_name)
    if success:
        print("Процесс экспорта завершен")
    else:
        print(f"Ошибка при экспорте")

    client.close()

if __name__ == "__main__":
    main()