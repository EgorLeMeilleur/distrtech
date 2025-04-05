import sqlite3
import json

def create_db():

    with open("config.json", "r") as f:
        config = json.load(f)

    try:
        conn = sqlite3.connect(config["db"]["sqlite_file"])
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
        print("Non-normalized DB created and filled successfully.")
    except Exception as e:
        print("Error creating non-normalized DB:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    create_db()
