import pymysql
import os
import random

# Database configuration
DB_HOST = "127.0.0.1"
DB_PORT = 3307
DB_USER = "root"
DB_PASS = ""
DB_NAME = "gestion_hotelera"

def restore_data():
    print("\n" + "="*60)
    print("RESTAURANDO DATOS DE RESERVAS Y FACTURAS")
    print("="*60 + "\n")
    
    conn = None
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT,
            charset='utf8mb4',
            autocommit=True
        )
        cursor = conn.cursor()
        
        # Path to SQL file
        sql_file_path = os.path.join(os.path.dirname(__file__), 'hotel_data_inserts.sql')
        print(f"Leyendo archivo: {sql_file_path}")
        
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        def extract_insert(table_name):
            start_marker = f"INSERT INTO {table_name}"
            start_idx = content.find(start_marker)
            if start_idx == -1:
                return None
            
            # Find the next semicolon
            end_idx = content.find(";", start_idx)
            if end_idx == -1:
                return None
                
            return content[start_idx:end_idx+1]

        reservations_sql = extract_insert("reservations")
        invoices_sql = extract_insert("invoices")
        
        if not reservations_sql:
            print("ERROR: No se encontró la sentencia INSERT para 'reservations'")
            return

        # 1. RESTORE RESERVATIONS
        print("\n[1/3] Restaurando reservas...")
        # Use INSERT IGNORE to skip existing duplicates
        reservations_sql = reservations_sql.replace("INSERT INTO", "INSERT IGNORE INTO")
        
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        cursor.execute(reservations_sql)
        print(f"      - Reservas insertadas/ignoradas. Filas afectadas: {cursor.rowcount}")
        
        # 2. RESTORE INVOICES
        if invoices_sql:
            print("\n[2/3] Restaurando facturas...")
            invoices_sql = invoices_sql.replace("INSERT INTO", "INSERT IGNORE INTO")
            cursor.execute(invoices_sql)
            print(f"      - Facturas insertadas/ignoradas. Filas afectadas: {cursor.rowcount}")
        else:
            print("\n[2/3] No se encontraron facturas para restaurar.")

        cursor.execute("SET FOREIGN_KEY_CHECKS=1")
        
        # 3. UPDATE RESERVATIONS TO POINT TO VALID ROOMS
        print("\n[3/3] Redistribuyendo reservas en las 1500 habitaciones...")
        
        # Get all current room IDs
        cursor.execute("SELECT room_id FROM rooms")
        all_room_ids = [row[0] for row in cursor.fetchall()]
        
        if not all_room_ids:
            print("ERROR: No hay habitaciones en la base de datos.")
            return

        # Get all reservation IDs
        cursor.execute("SELECT reservation_id FROM reservations")
        reservation_ids = [row[0] for row in cursor.fetchall()]
        
        # Update reservations with random rooms
        updates = []
        for res_id in reservation_ids:
            room_id = random.choice(all_room_ids)
            updates.append((room_id, res_id))
        
        # Update in batches
        batch_size = 100
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            cursor.executemany(
                "UPDATE reservations SET room_id = %s WHERE reservation_id = %s",
                batch
            )
            
        print(f"      - {len(updates)} reservas actualizadas con habitaciones válidas.")

        # FINAL SUMMARY
        print("\n" + "="*60)
        print("RESUMEN FINAL DE LA BASE DE DATOS")
        print("="*60)
        
        cursor.execute("SELECT COUNT(*) FROM rooms")
        print(f"  - Habitaciones: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM services")
        print(f"  - Servicios:    {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM reservations")
        print(f"  - Reservas:     {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM invoices")
        print(f"  - Facturas:     {cursor.fetchone()[0]}")

    except Exception as e:
        print(f"\nERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    restore_data()
