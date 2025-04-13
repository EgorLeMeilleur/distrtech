import sqlite3
import logging
import os

def initialize_sqlite_db(db_path):
    if not os.path.exists(db_path):
        logging.info(f"Creating SQLite database at {db_path}")
        create_sqlite_db(db_path)
    else:
        logging.info(f"SQLite database already exists at {db_path}")

def create_sqlite_db(db_path):
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

def get_music_data(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT group_name, musician_name, instrument_name, label_name FROM music_data")
    data = cursor.fetchall()
    conn.close()
    return data
