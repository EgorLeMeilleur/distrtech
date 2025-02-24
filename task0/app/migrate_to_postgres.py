import sqlite3
import psycopg2
from psycopg2 import sql
import sys
from config import POSTGRES, SQLITE_DB

def create_postgres_db():
    try:
        conn = psycopg2.connect(
            dbname='postgres',
            user=POSTGRES["user"],
            password=POSTGRES["password"],
            host=POSTGRES["host"],
            port=POSTGRES["port"]
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (POSTGRES["dbname"],))
        if not cursor.fetchone():
            cursor.execute(sql.SQL("CREATE DATABASE {};").format(sql.Identifier(POSTGRES["dbname"])))
            print(f"Database '{POSTGRES['dbname']}' created successfully.")
        else:
            print(f"Database '{POSTGRES['dbname']}' already exists.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error creating PostgreSQL database:", e)
        sys.exit(1)

def migrate():
    try:
        create_postgres_db()
        
        sqlite_conn = sqlite3.connect(SQLITE_DB)
        sqlite_cursor = sqlite_conn.cursor()

        pg_conn = psycopg2.connect(
            dbname=POSTGRES["dbname"],
            user=POSTGRES["user"],
            password=POSTGRES["password"],
            host=POSTGRES["host"],
            port=POSTGRES["port"]
        )
        pg_cursor = pg_conn.cursor()

        pg_cursor.execute("""
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
        pg_conn.commit()

        sqlite_cursor.execute("SELECT group_name, musician_name, instrument_name, label_name FROM music_data")
        rows = sqlite_cursor.fetchall()

        for group_name, musician_name, instrument_name, label_name in rows:
            pg_cursor.execute("SELECT id FROM labels WHERE name = %s", (label_name,))
            label = pg_cursor.fetchone()
            if label:
                label_id = label[0]
            else:
                pg_cursor.execute("INSERT INTO labels (name) VALUES (%s) RETURNING id", (label_name,))
                label_id = pg_cursor.fetchone()[0]

            pg_cursor.execute("SELECT id FROM groups WHERE name = %s AND label_id = %s", (group_name, label_id))
            group = pg_cursor.fetchone()
            if group:
                group_id = group[0]
            else:
                pg_cursor.execute("INSERT INTO groups (name, label_id) VALUES (%s, %s) RETURNING id", (group_name, label_id))
                group_id = pg_cursor.fetchone()[0]

            pg_cursor.execute("SELECT id FROM musicians WHERE name = %s AND group_id = %s", (musician_name, group_id))
            musician = pg_cursor.fetchone()
            if musician:
                musician_id = musician[0]
            else:
                pg_cursor.execute("INSERT INTO musicians (name, group_id) VALUES (%s, %s) RETURNING id", (musician_name, group_id))
                musician_id = pg_cursor.fetchone()[0]

            pg_cursor.execute("SELECT id FROM instruments WHERE name = %s", (instrument_name,))
            instrument = pg_cursor.fetchone()
            if instrument:
                instrument_id = instrument[0]
            else:
                pg_cursor.execute("INSERT INTO instruments (name) VALUES (%s) RETURNING id", (instrument_name,))
                instrument_id = pg_cursor.fetchone()[0]

            pg_cursor.execute("SELECT 1 FROM musician_instruments WHERE musician_id = %s AND instrument_id = %s", (musician_id, instrument_id))
            if not pg_cursor.fetchone():
                pg_cursor.execute("INSERT INTO musician_instruments (musician_id, instrument_id) VALUES (%s, %s)", (musician_id, instrument_id))

            pg_conn.commit()

        print("Migration from SQLite to PostgreSQL completed successfully.")
    except Exception as e:
        print("Error during migration:", e)
    finally:
        sqlite_conn.close()
        pg_cursor.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
