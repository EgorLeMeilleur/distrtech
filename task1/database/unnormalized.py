# create_non_normalized_db.py
import sqlite3

# Подключаемся к базе (файл music_non_normalized.db)
conn = sqlite3.connect('music_non_normalized.db')
cursor = conn.cursor()

# Создаём таблицу, в которой все данные хранятся в одной структуре
cursor.execute('''
    CREATE TABLE IF NOT EXISTS music_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT,
        musician_name TEXT,
        instrument_name TEXT,
        album_title TEXT,
        song_title TEXT
    )
''')

# Пример вставки данных (для группы "The Beatles")
sample_data = [
    ('The Beatles', 'John Lennon', 'Guitar', 'Abbey Road', 'Come Together'),
    ('The Beatles', 'John Lennon', 'Piano', 'Abbey Road', 'Something'),
    ('The Beatles', 'Paul McCartney', 'Bass', 'Abbey Road', 'Something'),
    ('The Beatles', 'George Harrison', 'Guitar', 'Let It Be', 'Let It Be'),
    ('The Beatles', 'Ringo Starr', 'Drums', 'Let It Be', 'Across The Universe'),
    # Добавьте другие строки по необходимости
]

cursor.executemany('''
    INSERT INTO music_data (group_name, musician_name, instrument_name, album_title, song_title)
    VALUES (?, ?, ?, ?, ?)
''', sample_data)

conn.commit()
conn.close()
print("Ненормализованная БД создана и заполнена данными.")
