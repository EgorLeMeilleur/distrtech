from grpc_client import GRPCDataImporterClient
from db_work import initialize_sqlite_db, get_music_data
import os
import yaml

def prepare_message(transaction):
        return {
            'group_name': transaction[0],
            'musician_name': transaction[1],
            'instrument_name': transaction[2],
            'label_name': transaction[3],
        }

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'exporter_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    sqlite_db = config['exporter']['sqlite_db_path']

    initialize_sqlite_db(sqlite_db)
    
    data = get_music_data(sqlite_db)
    print(f"Найдено {len(data)} записей для экспорта.")
    
    grpc_config = config['importer']
    client = GRPCDataImporterClient(
        grpc_config['host'],
        grpc_config['port'],
        config['security']['ca_cert']
    )

    transactions = []
    
    for record in data:
        message = prepare_message(record)
        transactions.append(message)

    success, message = client.import_music_data(transactions)
    print(message)
    if success:
        print("Процесс экспорта завершен.")
    else:
        print(f"Ошибка при экспорте.")

    client.close()

if __name__ == "__main__":
    main()