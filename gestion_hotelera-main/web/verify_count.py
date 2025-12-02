import pymysql
import os

# Configuration
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3307))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "gestion_hotelera")

TABLES = ['users', 'clients', 'rooms', 'staff', 'services', 'reservations', 'reservation_services', 'invoices']

def verify_counts():
    print(f"Connecting to {DB_HOST}:{DB_PORT}...")
    conn = None
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                               database=DB_NAME, port=DB_PORT,
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        
        with conn.cursor() as cur:
            print("Current Row Counts:")
            total_rows = 0
            for table in TABLES:
                try:
                    cur.execute(f"SELECT COUNT(*) as c FROM {table}")
                    count = cur.fetchone()['c']
                    print(f"{table}: {count}")
                    total_rows += count
                except Exception as e:
                    print(f"{table}: Error ({e})")
            
            print(f"Total Rows across checked tables: {total_rows}")

    except Exception as e:
        print(f"Fatal Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verify_counts()
