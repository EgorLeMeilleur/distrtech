import sqlite3
from config import SQLITE_DB

def create_db():
    try:
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
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
        sample_data = [
            ('The Beatles', 'John Lennon', 'Guitar', 'Abbey Road', 'Come Together'),
            ('The Beatles', 'John Lennon', 'Piano', 'Abbey Road', 'Something'),
            ('The Beatles', 'Paul McCartney', 'Bass', 'Abbey Road', 'Something'),
            ('The Beatles', 'George Harrison', 'Guitar', 'Let It Be', 'Let It Be'),
            ('The Beatles', 'Ringo Starr', 'Drums', 'Let It Be', 'Across The Universe'),
        ]
        cursor.executemany('''
            INSERT INTO music_data (group_name, musician_name, instrument_name, album_title, song_title)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_data)
        conn.commit()
        print("Non-normalized DB created and filled successfully.")
    except Exception as e:
        print("Error creating non-normalized DB:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    create_db()