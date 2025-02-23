import psycopg2
import json
import subprocess
from config import POSTGRES, EXPORT_JSON, EXPORT_EXCEL, CSHARP_EXPORT_EXEC

def export_data():
    try:
        pg_conn = psycopg2.connect(
            user=POSTGRES["user"],
            password=POSTGRES["password"],
            host=POSTGRES["host"],
            port=POSTGRES["port"],
            dbname=POSTGRES["dbname"]
        )
        pg_cursor = pg_conn.cursor()

        query = """
            SELECT s.title as song, a.title as album, g.name as group_name
            FROM songs s
            JOIN albums a ON s.album_id = a.id
            JOIN groups g ON a.group_id = g.id
            ORDER BY g.name, a.title, s.title;
        """
        pg_cursor.execute(query)
        rows = pg_cursor.fetchall()
        columns = [desc[0] for desc in pg_cursor.description]

        data = [dict(zip(columns, row)) for row in rows]
        pg_cursor.close()
        pg_conn.close()

        with open(EXPORT_JSON, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("Data extracted and written to", EXPORT_JSON)

        subprocess.run([CSHARP_EXPORT_EXEC, EXPORT_JSON, EXPORT_EXCEL], check=True)
        print("Data exported to Excel successfully.")
    except Exception as e:
        print("Error during export:", e)

if __name__ == "__main__":
    export_data()
