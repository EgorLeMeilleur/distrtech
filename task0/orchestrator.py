import argparse
import subprocess
import sys

def run_create_db():
    try:
        subprocess.run(["python", "app/create_non_normalized_db.py"], check=True)
    except subprocess.CalledProcessError as e:
        print("Error running create_non_normalized_db.py:", e)

def run_migrate():
    try:
        subprocess.run(["python", "app/migrate_to_postgres.py"], check=True)
    except subprocess.CalledProcessError as e:
        print("Error running migrate_to_postgres.py:", e)

def run_export(label_name=None):
    if label_name is None:
        label_name = ""
    try:
        subprocess.run(["python", "app/export_data.py", label_name], check=True)
    except subprocess.CalledProcessError as e:
        print("Error running export_data.py:", e)
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run database workflow steps.")
    parser.add_argument("--create", action="store_true", help="Run non-normalized DB creation")
    parser.add_argument("--migrate", action="store_true", help="Run migration to PostgreSQL")
    parser.add_argument("--export", action="store_true", help="Run export from normalized DB to Excel")
    parser.add_argument("--all", action="store_true", help="Run all steps in sequence")
    parser.add_argument("--label_name", type=str, help="Label name to filter export by")
    
    args = parser.parse_args()

    if args.all:
        run_create_db()
        run_migrate()
        if args.label_name:
            run_export(args.label_name)
        else:
            run_export()
    else:
        if args.create:
            run_create_db()
        if args.migrate:
            run_migrate()
        if args.export:
            if args.label_name:
                run_export(args.label_name)
            else:
                run_export()
        if not (args.create or args.migrate or args.export):
            print("No valid arguments provided. Use --help for options.")
            sys.exit(1)
