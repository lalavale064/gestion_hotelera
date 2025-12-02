import pymysql
from datetime import datetime, timedelta
import random

# Database configuration
DB_HOST = "127.0.0.1"
DB_PORT = 3307
DB_USER = "root"
DB_PASS = ""
DB_NAME = "gestion_hotelera"

def update_database():
    """Update database according to requirements"""
    print("\n" + "="*60)
    print("ACTUALIZANDO BASE DE DATOS")
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
            autocommit=False
        )
        
        cursor = conn.cursor()
        
        # 1. DELETE GENERATED SERVICES (Keep only the original 5)
        print("[1/3] Eliminando servicios generados (dejando solo los 5 originales)...")
        cursor.execute("DELETE FROM reservation_services WHERE service_id > 5")
        deleted_rs = cursor.rowcount
        
        cursor.execute("DELETE FROM services WHERE service_id > 5")
        deleted_services = cursor.rowcount
        print(f"      - {deleted_services} servicios eliminados")
        print(f"      - {deleted_rs} servicios de reserva eliminados")
        
        # 2. GENERATE 1500 ROOMS
        print("\n[2/3] Generando 1500 habitaciones...")
        
        # First, delete old generated rooms (keeping original 8)
        cursor.execute("SELECT MAX(room_id) FROM rooms WHERE room_id <= 8")
        result = cursor.fetchone()
        max_original_id = result[0] if result[0] else 8
        
        cursor.execute("DELETE FROM reservation_services")
        cursor.execute("DELETE FROM invoices")
        cursor.execute("DELETE FROM reservations WHERE room_id > %s", (max_original_id,))
        cursor.execute("DELETE FROM rooms WHERE room_id > %s", (max_original_id,))
        
        # Generate 1500 rooms
        room_types = ['sencilla', 'doble', 'suite']
        statuses = ['disponible', 'ocupada', 'mantenimiento']
        status_weights = [0.7, 0.2, 0.1]  # 70% disponible, 20% ocupada, 10% mantenimiento
        
        # Get existing room numbers
        cursor.execute("SELECT room_num FROM rooms")
        existing_rooms = {row[0] for row in cursor.fetchall()}
        
        rooms_to_insert = []
        room_num = 101
        
        count = 0
        while count < 1500:
            # Skip if room number already exists
            if room_num in existing_rooms:
                room_num += 1
                continue
                
            room_type = random.choice(room_types)
            
            # Set capacity based on room type
            if room_type == 'sencilla':
                capacity = random.choice([1, 2])
                base_price = random.uniform(50, 100)
            elif room_type == 'doble':
                capacity = random.choice([2, 3, 4])
                base_price = random.uniform(80, 150)
            else:  # suite
                capacity = random.choice([4, 5, 6])
                base_price = random.uniform(150, 300)
            
            price = round(base_price, 2)
            status = random.choices(statuses, weights=status_weights)[0]
            
            rooms_to_insert.append((room_num, room_type, capacity, price, status))
            count += 1
            room_num += 1
            
            # Skip to next floor every 50 rooms logic adjusted
            # We just increment room_num linearly but maybe we want floors?
            # Let's keep it simple: just increment room_num, but if it ends in 99, jump to next 100
            if str(room_num).endswith('99'):
                room_num = (room_num // 100 + 1) * 100 + 1
        
        # Insert rooms in batches
        batch_size = 100
        for i in range(0, len(rooms_to_insert), batch_size):
            batch = rooms_to_insert[i:i + batch_size]
            cursor.executemany(
                "INSERT INTO rooms (room_num, room_type, capacity, price, status) VALUES (%s, %s, %s, %s, %s)",
                batch
            )
        
        print(f"      - 1500 habitaciones creadas")
        
        # 3. UPDATE RESERVATIONS TO USE NEW ROOMS
        print("\n[3/3] Actualizando reservas para usar nuevas habitaciones...")
        
        # Get all room IDs
        cursor.execute("SELECT room_id FROM rooms")
        all_room_ids = [row[0] for row in cursor.fetchall()]
        
        # Get all reservations
        cursor.execute("SELECT reservation_id FROM reservations")
        reservation_ids = [row[0] for row in cursor.fetchall()]
        
        # Update reservations with random rooms
        updates = []
        for res_id in reservation_ids:
            room_id = random.choice(all_room_ids)
            updates.append((room_id, res_id))
        
        # Update in batches
        for i in range(0, len(updates), batch_size):
            batch = updates[i:i + batch_size]
            cursor.executemany(
                "UPDATE reservations SET room_id = %s WHERE reservation_id = %s",
                batch
            )
        
        print(f"      - {len(updates)} reservas actualizadas")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "="*60)
        print("[OK] BASE DE DATOS ACTUALIZADA EXITOSAMENTE")
        print("="*60)
        
        # Print summary
        print("\nRESUMEN:")
        cursor.execute("SELECT COUNT(*) FROM rooms")
        total_rooms = cursor.fetchone()[0]
        print(f"  - Habitaciones: {total_rooms}")
        
        cursor.execute("SELECT COUNT(*) FROM services")
        total_services = cursor.fetchone()[0]
        print(f"  - Servicios: {total_services}")
        
        cursor.execute("SELECT COUNT(*) FROM reservations")
        total_reservations = cursor.fetchone()[0]
        print(f"  - Reservas: {total_reservations}")
        
        cursor.close()
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    update_database()
