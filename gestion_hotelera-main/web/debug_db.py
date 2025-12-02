
import pymysql
import os

# Configuration (matching app.py)
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3307))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "gestion_hotelera")

def check_users():
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                               database=DB_NAME, port=DB_PORT,
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
        
        with conn.cursor() as cur:
            print("--- USERS ---")
            cur.execute("SELECT user_id, email, user_role FROM users")
            users = cur.fetchall()
            for u in users:
                print(u)
                
            print("\n--- CLIENTS ---")
            cur.execute("SELECT client_id, user_id, full_name, email FROM clients")
            clients = cur.fetchall()
            for c in clients:
                print(c)
                
            print("\n--- ANALYSIS ---")
            for u in users:
                if u['user_role'] == 'cliente':
                    linked_client = next((c for c in clients if c['user_id'] == u['user_id']), None)
                    if linked_client:
                        print(f"User {u['email']} (ID: {u['user_id']}) is linked to Client ID: {linked_client['client_id']}")
                    else:
                        print(f"WARNING: User {u['email']} (ID: {u['user_id']}) has role 'cliente' but NO linked client record!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    check_users()
