import pymysql
import os

# Configuration
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3307))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "gestion_hotelera")

def restore_users():
    print(f"Connecting to {DB_HOST}:{DB_PORT}...")
    conn = None
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                               database=DB_NAME, port=DB_PORT,
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
                               autocommit=True)
        
        with conn.cursor() as cur:
            # Users to restore
            # Using SHA2(password, 256) equivalent in Python or raw SQL
            # Since we are using pymysql, we can use the SQL function SHA2 directly in the query.
            
            users_to_insert = [
                ('admin@hotel.com', 'admin', 'admin'),
                ('recepcion@hotel.com', 'recepcion', 'recepcion'),
                ('spa@hotel.com', 'spa', 'spa'),
                ('cliente@hotel.com', 'cliente', 'cliente')
            ]
            
            print("Restoring default users...")
            for email, password, role in users_to_insert:
                # Check if exists
                cur.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    print(f"User {email} already exists. Skipping.")
                else:
                    # Insert
                    sql = "INSERT INTO users (email, password_hash, user_role) VALUES (%s, SHA2(%s, 256), %s)"
                    cur.execute(sql, (email, password, role))
                    print(f"Restored user: {email} (Role: {role})")
            
            # Also restore the client link for cliente@hotel.com if needed
            # The SQL had: INSERT INTO clients (user_id, full_name, email) VALUES (4, 'Cliente Prueba', 'cliente@hotel.com');
            # We need to find the user_id for cliente@hotel.com first
            
            cur.execute("SELECT user_id FROM users WHERE email = 'cliente@hotel.com'")
            client_user = cur.fetchone()
            if client_user:
                user_id = client_user['user_id']
                # Check if client exists
                cur.execute("SELECT client_id FROM clients WHERE email = 'cliente@hotel.com'")
                if not cur.fetchone():
                    cur.execute("INSERT INTO clients (user_id, full_name, email) VALUES (%s, %s, %s)", 
                                (user_id, 'Cliente Prueba', 'cliente@hotel.com'))
                    print(f"Restored client profile for cliente@hotel.com")
                else:
                    print("Client profile for cliente@hotel.com already exists.")

    except Exception as e:
        print(f"Fatal Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    restore_users()
