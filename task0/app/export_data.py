import psycopg2
import json
import subprocess
import argparse
from config import POSTGRES, EXPORT_JSON, EXPORT_EXCEL, CSHARP_EXPORT_EXEC

def export_data(label_name=None):
    try:
        pg_conn = psycopg2.connect(
            user=POSTGRES["user"],
            password=POSTGRES["password"],
            host=POSTGRES["host"],
            port=POSTGRES["port"],
            dbname=POSTGRES["dbname"]
        )
        pg_cursor = pg_conn.cursor()
        
        if label_name == "":
            query = """
                SELECT
                    g.name AS group_name,
                    m.name AS musician_name,
                    i.name AS instrument_name,
                    l.name AS label_name
                FROM
                    groups g
                    JOIN labels l ON g.label_id = l.id
                    JOIN musicians m ON g.id = m.group_id
                    JOIN musician_instruments mi ON m.id = mi.musician_id
                    JOIN instruments i ON mi.instrument_id = i.id
            """
            pg_cursor.execute(query)
        else:
            query = """
                SELECT
                    g.name AS group_name
                FROM
                    groups g
                JOIN labels l ON g.label_id = l.id
                WHERE
                    l.name = %s
            """
            pg_cursor.execute(query, (label_name,))
    
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
    parser = argparse.ArgumentParser(description="Export groups from a specific label.")
    parser.add_argument("label_name", type=str, help="The name of the label to filter groups by.")
    args = parser.parse_args()
    export_data(args.label_name)
