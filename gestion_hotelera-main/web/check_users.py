import pymysql
import os

# Configuration
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3307))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "gestion_hotelera")

EMAILS = ['admin@hotel.com', 'recepcion@hotel.com', 'spa@hotel.com']

def check_users():
    print(f"Connecting to {DB_HOST}:{DB_PORT}...")
    conn = None
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                               database=DB_NAME, port=DB_PORT,
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        
        with conn.cursor() as cur:
            for email in EMAILS:
                cur.execute("SELECT user_id, email, user_role FROM users WHERE email = %s", (email,))
                user = cur.fetchone()
                if user:
                    print(f"Found: {user}")
                else:
                    print(f"MISSING: {email}")

    except Exception as e:
        print(f"Fatal Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_users()
