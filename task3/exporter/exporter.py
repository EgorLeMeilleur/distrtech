import sqlite3
import grpc
import yaml
import time
import logging
import os
from concurrent import futures
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'protos'))

import data_transfer_pb2
import data_transfer_pb2_grpc

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataExporterService:
    def __init__(self, config_path):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        self.sqlite_db = self.config['exporter']['sqlite_db_path']
        
        self.initialize_sqlite_db()
    
    def initialize_sqlite_db(self):
        if not os.path.exists(self.sqlite_db):
            logging.info(f"Creating SQLite database at {self.sqlite_db}")
            self.create_sqlite_db(self.sqlite_db)
        else:
            logging.info(f"SQLite database already exists at {self.sqlite_db}")
    
    def create_sqlite_db(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(''' 
            CREATE TABLE IF NOT EXISTS music_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT,
                musician_name TEXT,
                instrument_name TEXT,
                label_name TEXT,
                UNIQUE(group_name, musician_name, instrument_name, label_name)
            )
        ''')

        sample_data = [
            ('The Beatles', 'John Lennon', 'Guitar', 'universal'),
            ('The Beatles', 'John Lennon', 'Piano', 'universal'),
            ('The Beatles', 'Paul McCartney', 'Bass', 'universal'),
            ('The Beatles', 'George Harrison', 'Guitar', 'universal'),
            ('The Beatles', 'Ringo Starr', 'Drums', 'universal'),
            
            ('Queen', 'Freddie Mercury', 'Vocals', 'sony'),
            ('Queen', 'Brian May', 'Guitar', 'sony'),
            ('Queen', 'Roger Taylor', 'Drums', 'sony'),
            ('Queen', 'John Deacon', 'Bass', 'sony'),
            
            ('Led Zeppelin', 'Robert Plant', 'Vocals', 'warner'),
            ('Led Zeppelin', 'Jimmy Page', 'Guitar', 'warner'),
            ('Led Zeppelin', 'John Paul Jones', 'Bass', 'warner'),
            ('Led Zeppelin', 'John Bonham', 'Drums', 'warner')
        ]

        cursor.executemany('''
            INSERT OR IGNORE INTO music_data (group_name, musician_name, instrument_name, label_name)
            VALUES (?, ?, ?, ?)
        ''', sample_data)

        conn.commit()
        conn.close()
        logging.info("SQLite database created and populated with sample data")
    
    def get_data_from_sqlite(self):
        """Retrieve all data from SQLite database"""
        conn = sqlite3.connect(self.sqlite_db)
        cursor = conn.cursor()
        cursor.execute("SELECT group_name, musician_name, instrument_name, label_name FROM music_data")
        data = cursor.fetchall()
        conn.close()
        return data
    
    def start_exporting(self):
        data_to_export = self.get_data_from_sqlite()
        logging.info(f"Found {len(data_to_export)} records to export")
        
        importer_address = f"{self.config['importer']['host']}:{self.config['importer']['port']}"
        credentials = grpc.ssl_channel_credentials(
            root_certificates=open(self.config['security']['ca_cert'], 'rb').read()
        )
        
        with grpc.secure_channel(importer_address, credentials) as channel:
            stub = data_transfer_pb2_grpc.DataImporterStub(channel)
            
            for record in data_to_export:
                group_name, musician_name, instrument_name, label_name = record
                
                request = data_transfer_pb2.MusicDataRequest(
                    group_name=group_name,
                    musician_name=musician_name,
                    instrument_name=instrument_name,
                    label_name=label_name
                )
                
                try:
                    response = stub.ImportMusicData(request)
                    logging.info(f"Exported: {group_name} - {musician_name} - {instrument_name} - {label_name}")
                    logging.info(f"Response: {response.message}")
                    time.sleep(0.1)
                except Exception as e:
                    logging.error(f"Error exporting data: {e}")
                    logging.error(f"Details: {str(e)}")

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'exporter_config.yaml')
    logging.info(f"Starting Data Exporter Service with config: {config_path}")
    
    exporter = DataExporterService(config_path)
    exporter.start_exporting()
    
    logging.info("Export process completed")

if __name__ == "__main__":
    main()