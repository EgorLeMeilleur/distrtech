# migrate_to_postgres.py
import sqlite3
import psycopg2

# Функция для получения или вставки записи и возврата её id
def get_or_create(cursor, table, field, value):
    cursor.execute(f"SELECT id FROM {table} WHERE {field} = %s", (value,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute(f"INSERT INTO {table} ({field}) VALUES (%s) RETURNING id", (value,))
        return cursor.fetchone()[0]

# Подключаемся к ненормализованной БД (SQLite)
sqlite_conn = sqlite3.connect('music_non_normalized.db')
sqlite_cursor = sqlite_conn.cursor()

# Подключаемся к PostgreSQL (здесь параметры подключения замените на свои)
pg_conn = psycopg2.connect(
    dbname="your_postgres_db",
    user="your_username",
    password="your_password",
    host="localhost",
    port="5432"
)
pg_cursor = pg_conn.cursor()

# Создание схемы нормализованной БД в PostgreSQL
pg_cursor.execute("""
    CREATE TABLE IF NOT EXISTS groups (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE
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
    
    CREATE TABLE IF NOT EXISTS albums (
        id SERIAL PRIMARY KEY,
        title TEXT,
        group_id INTEGER REFERENCES groups(id)
    );
    
    CREATE TABLE IF NOT EXISTS songs (
        id SERIAL PRIMARY KEY,
        title TEXT,
        album_id INTEGER REFERENCES albums(id)
    );
""")
pg_conn.commit()

# Извлекаем данные из SQLite
sqlite_cursor.execute("SELECT group_name, musician_name, instrument_name, album_title, song_title FROM music_data")
rows = sqlite_cursor.fetchall()

for group_name, musician_name, instrument_name, album_title, song_title in rows:
    # Вставляем/получаем группу
    pg_cursor.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
    group = pg_cursor.fetchone()
    if group:
        group_id = group[0]
    else:
        pg_cursor.execute("INSERT INTO groups (name) VALUES (%s) RETURNING id", (group_name,))
        group_id = pg_cursor.fetchone()[0]
    
    # Вставляем музыканта (предполагается, что музыкант принадлежит группе)
    pg_cursor.execute("SELECT id FROM musicians WHERE name = %s AND group_id = %s", (musician_name, group_id))
    musician = pg_cursor.fetchone()
    if musician:
        musician_id = musician[0]
    else:
        pg_cursor.execute("INSERT INTO musicians (name, group_id) VALUES (%s, %s) RETURNING id", (musician_name, group_id))
        musician_id = pg_cursor.fetchone()[0]
    
    # Вставляем инструмент
    pg_cursor.execute("SELECT id FROM instruments WHERE name = %s", (instrument_name,))
    instrument = pg_cursor.fetchone()
    if instrument:
        instrument_id = instrument[0]
    else:
        pg_cursor.execute("INSERT INTO instruments (name) VALUES (%s) RETURNING id", (instrument_name,))
        instrument_id = pg_cursor.fetchone()[0]
    
    # Вставляем связь музыкант-инструмент (если такой записи ещё нет)
    pg_cursor.execute("SELECT 1 FROM musician_instruments WHERE musician_id = %s AND instrument_id = %s", (musician_id, instrument_id))
    if not pg_cursor.fetchone():
        pg_cursor.execute("INSERT INTO musician_instruments (musician_id, instrument_id) VALUES (%s, %s)", (musician_id, instrument_id))
    
    # Вставляем альбом (принадлежит группе)
    pg_cursor.execute("SELECT id FROM albums WHERE title = %s AND group_id = %s", (album_title, group_id))
    album = pg_cursor.fetchone()
    if album:
        album_id = album[0]
    else:
        pg_cursor.execute("INSERT INTO albums (title, group_id) VALUES (%s, %s) RETURNING id", (album_title, group_id))
        album_id = pg_cursor.fetchone()[0]
    
    # Вставляем песню (относим к альбому)
    pg_cursor.execute("SELECT id FROM songs WHERE title = %s AND album_id = %s", (song_title, album_id))
    song = pg_cursor.fetchone()
    if not song:
        pg_cursor.execute("INSERT INTO songs (title, album_id) VALUES (%s, %s)", (song_title, album_id))

    pg_conn.commit()

sqlite_conn.close()
pg_conn.commit()
pg_cursor.close()
pg_conn.close()
print("Миграция данных из SQLite в PostgreSQL завершена.")
