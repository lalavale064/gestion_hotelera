
import pymysql
import os

# Configuration (matching app.py)
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3307))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "gestion_hotelera")
SQL_FILE = "populate_db.sql"

def load_data():
    print(f"Connecting to {DB_HOST}:{DB_PORT}...")
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                               database=DB_NAME, port=DB_PORT,
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
                               autocommit=True)
        
        print(f"Reading {SQL_FILE}...")
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        # Split by semicolon to get individual statements, but be careful with data containing semicolons.
        # The generator puts each statement on a new line and ends with ;
        # So we can iterate line by line or split.
        # Given the generator format, splitting by ";\n" is safer or just iterating lines.
        # Actually, the generator outputs one statement per line ending in ;
        
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        print(f"Found {len(statements)} statements. Executing...")
        
        with conn.cursor() as cur:
            # Disable FK checks globally for this session
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            count = 0
            for sql in statements:
                try:
                    cur.execute(sql)
                    count += 1
                    if count % 500 == 0:
                        print(f"Executed {count} statements...")
                except Exception as e:
                    print(f"Error executing: {sql[:50]}... -> {e}")
            
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
            
        print(f"Successfully executed {count} statements.")

    except Exception as e:
        print(f"Fatal Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    load_data()
