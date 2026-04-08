import os
import psycopg2

HOST = "localhost"
PORT = 5432
DBNAME = "commerce"
USER = "postgres"
PASSWORD = "1234"
DATA_DIR = os.path.expanduser("~/repositorios/pipeline-commerce/data/interim/")

def table_exists(cur, table):
    cur.execute("""
    SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'public' AND table_name = %s
    )
    """, (table,))
    return cur.fetchone()[0]

def main():
    conn = psycopg2.connect(dbname=DBNAME, user=USER, password=PASSWORD, host=HOST, port=PORT)
    try:
        with conn:
            with conn.cursor() as cur:
                print("Connected to PostgreSQL database.")
                for fname in os.listdir(DATA_DIR):
                    print(f"Processing file: {fname}")
                    if not fname.lower().endswith(".csv"):
                        continue
                    table = os.path.splitext(fname)[0]  # uses filename (without .csv) as table name
                    path = os.path.join(DATA_DIR, fname)
                    if not table_exists(cur, table):
                        print(f"Skipping {fname}: table '{table}' does not exist in database.")
                        continue
                    print(f"Loading {fname} -> table {table} ...")
                    with open(path, "r", encoding="utf-8") as f:
                        cur.copy_expert(f"COPY {table} FROM STDIN WITH CSV HEADER DELIMITER ';'", f)
                    print("Done.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()