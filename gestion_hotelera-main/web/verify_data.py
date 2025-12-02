
import pymysql
import os

# Configuration (matching app.py)
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3307))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "gestion_hotelera")

def verify_data():
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                               database=DB_NAME, port=DB_PORT,
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        
        with conn.cursor() as cur:
            tables = ['users', 'clients', 'rooms', 'staff', 'services', 'reservations', 'reservation_services', 'invoices']
            print("--- DATA COUNTS ---")
            for t in tables:
                cur.execute(f"SELECT COUNT(*) as c FROM {t}")
                print(f"{t.upper()}: {cur.fetchone()['c']}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    verify_data()
