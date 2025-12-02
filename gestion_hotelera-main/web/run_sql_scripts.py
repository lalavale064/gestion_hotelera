import pymysql
import os
import sys

# Configuration (matching app.py)
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3307))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "gestion_hotelera")

SQL_FILES = [
    "../hotel_data_inserts.sql",
    "../fix_encoding.sql"
]

LOG_FILE = "execution_log.txt"

def log(msg):
    try:
        print(msg)
    except Exception:
        pass # Ignore console print errors
    
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(str(msg) + "\n")
    except Exception:
        pass

def truncate_tables(conn):
    tables = ['reservation_services', 'invoices', 'reservations', 'clients', 'rooms', 'staff', 'services', 'users']
    log("Truncating tables...")
    with conn.cursor() as cur:
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {table}")
                log(f"Truncated {table}")
            except Exception as e:
                log(f"Error truncating {table}: {e}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")

def run_scripts():
    # Clear log file
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("Starting execution...\n")

    log(f"Connecting to {DB_HOST}:{DB_PORT}...")
    conn = None
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                               database=DB_NAME, port=DB_PORT,
                               charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
                               autocommit=True)
        
        truncate_tables(conn)
        
        with conn.cursor() as cur:
            # Disable FK checks globally for this session
            cur.execute("SET FOREIGN_KEY_CHECKS = 0")
            cur.execute("SET UNIQUE_CHECKS = 0")
            
            for sql_file in SQL_FILES:
                if not os.path.exists(sql_file):
                    log(f"Error: File {sql_file} not found.")
                    continue
                    
                log(f"Reading {sql_file}...")
                with open(sql_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Split by semicolon
                statements = [s.strip() for s in sql_content.split(';') if s.strip()]
                
                log(f"Found {len(statements)} statements in {sql_file}. Executing...")
                
                count = 0
                total_rows_affected = 0
                for i, sql in enumerate(statements):
                    try:
                        # Skip empty statements
                        if not sql:
                            continue
                            
                        log(f"Executing statement #{i+1}: {sql[:50]}...")
                        cur.execute(sql)
                        rows = cur.rowcount
                        total_rows_affected += rows
                        count += 1
                        log(f"Executed statement #{i+1}. Rows affected: {rows}")
                    except Exception as e:
                        log(f"Error executing statement #{i+1} in {sql_file}:")
                        log(f"Error: {repr(e)}")
                
                log(f"Successfully executed {count} statements from {sql_file} (out of {len(statements)}).")
                log(f"Total rows affected in {sql_file}: {total_rows_affected}")
            
            # Test Insert
            try:
                log("Attempting test insert...")
                cur.execute("INSERT INTO users (email, password_hash, user_role) VALUES ('test_debug@example.com', 'hash', 'cliente')")
                log(f"Test insert affected rows: {cur.rowcount}")
            except Exception as e:
                log(f"Test insert failed: {e}")

            conn.commit() # Commit transaction explicitly as SQL file might disable autocommit
            cur.execute("SET FOREIGN_KEY_CHECKS = 1")
            cur.execute("SET UNIQUE_CHECKS = 1")
            
    except Exception as e:
        log(f"Fatal Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_scripts()
