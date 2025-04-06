import sqlite3
import psycopg2
from psycopg2 import sql

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

def get_data_from_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT group_name, musician_name, instrument_name, label_name FROM music_data")
    data = cursor.fetchall()
    conn.close()
    return data

def insert_normalized_data(config, group_name, musician_name, instrument_name, label_name):
    pg_conf = config["db"]["postgres"]

    conn = psycopg2.connect(
        dbname='postgres',
        user=pg_conf["user"],
        password=pg_conf["password"],
        host=pg_conf["host"],
        port=pg_conf["port"]
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (pg_conf["dbname"],))
    if not cursor.fetchone():
        cursor.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(pg_conf["dbname"])))
    
    cursor.close()
    conn.close()

    conn = psycopg2.connect(
        dbname=pg_conf["dbname"],
        user=pg_conf["user"],
        password=pg_conf["password"],
        host=pg_conf["host"],
        port=pg_conf["port"]
    )
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS labels (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS groups (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE,
            label_id INTEGER REFERENCES labels(id)
        );
        CREATE TABLE IF NOT EXISTS musicians (
            id SERIAL PRIMARY KEY,
            name TEXT,
            group_id INTEGER REFERENCES groups(id)
        );
        CREATE TABLE IF NOT EXISTS instruments (
            id SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        CREATE TABLE IF NOT EXISTS musician_instruments (
            musician_id INTEGER REFERENCES musicians(id),
            instrument_id INTEGER REFERENCES instruments(id),
            PRIMARY KEY (musician_id, instrument_id)
        );
    """)
    conn.commit()
    
    cursor.execute("SELECT id FROM labels WHERE name = %s", (label_name,))
    label = cursor.fetchone()
    if label:
        label_id = label[0]
    else:
        cursor.execute("INSERT INTO labels (name) VALUES (%s) RETURNING id", (label_name,))
        label_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM groups WHERE name = %s AND label_id = %s", (group_name, label_id))
    group = cursor.fetchone()
    if group:
        group_id = group[0]
    else:
        cursor.execute("INSERT INTO groups (name, label_id) VALUES (%s, %s) RETURNING id", (group_name, label_id))
        group_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM musicians WHERE name = %s AND group_id = %s", (musician_name, group_id))
    musician = cursor.fetchone()
    if musician:
        musician_id = musician[0]
    else:
        cursor.execute("INSERT INTO musicians (name, group_id) VALUES (%s, %s) RETURNING id", (musician_name, group_id))
        musician_id = cursor.fetchone()[0]

    cursor.execute("SELECT id FROM instruments WHERE name = %s", (instrument_name,))
    instrument = cursor.fetchone()
    if instrument:
        instrument_id = instrument[0]
    else:
        cursor.execute("INSERT INTO instruments (name) VALUES (%s) RETURNING id", (instrument_name,))
        instrument_id = cursor.fetchone()[0]

    cursor.execute("SELECT 1 FROM musician_instruments WHERE musician_id = %s AND instrument_id = %s", (musician_id, instrument_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO musician_instruments (musician_id, instrument_id) VALUES (%s, %s)", (musician_id, instrument_id))
    conn.commit()
    cursor.close()
    conn.close()