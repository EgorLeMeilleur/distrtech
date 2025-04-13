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
    logging.info(f"Found {len(data)} records to export")
    
    grpc_config = config['importer']
    client = GRPCDataImporterClient(
        grpc_config['host'],
        grpc_config['port'],
        config['security']['ca_cert']
    )
    
    for record in data:
        group_name, musician_name, instrument_name, label_name = record
        success, message = client.import_music_data(group_name, musician_name, instrument_name, label_name)
        if success:
            logging.info(f"Exported: {group_name} - {musician_name} - {instrument_name} - {label_name}")
            logging.info(f"Response: {message}")
        else:
            logging.error(f"Failed to export: {group_name} - {musician_name}")
        time.sleep(0.1)

    logging.info("Export process completed")
    client.close()

if __name__ == "__main__":
    main()