import pymysql

# Database configuration
DB_HOST = "127.0.0.1"
DB_PORT = 3307
DB_USER = "root"
DB_PASS = ""
DB_NAME = "gestion_hotelera"

def verify_database():
    """Verify what was loaded into the database"""
    print("\n" + "="*60)
    print("VERIFICACION DE DATOS EN LA BASE DE DATOS")
    print("="*60 + "\n")
    
    conn = None
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=DB_PORT,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # Get all tables
        tables = [
            ('users', 'Usuarios'),
            ('clients', 'Clientes'),
            ('rooms', 'Habitaciones'),
            ('staff', 'Personal'),
            ('services', 'Servicios'),
            ('reservations', 'Reservas'),
            ('reservation_services', 'Servicios de Reserva'),
            ('invoices', 'Facturas')
        ]
        
        print(f"{'Tabla':<25} {'Total Registros':>20}")
        print("="*60)
        
        total_records = 0
        for table_name, display_name in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            result = cursor.fetchone()
            count = result[0]
            total_records += count
            print(f"{display_name:<25} {count:>20,}")
        
        print("="*60)
        print(f"{'TOTAL':<25} {total_records:>20,}")
        print("="*60 + "\n")
        
        # Show sample data from each table
        print("\n" + "="*60)
        print("MUESTRA DE DATOS (Primeros 3 registros de cada tabla)")
        print("="*60 + "\n")
        
        for table_name, display_name in tables:
            print(f"\n--- {display_name} ({table_name}) ---")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            rows = cursor.fetchall()
            
            if rows:
                # Get column names
                cursor.execute(f"DESCRIBE {table_name}")
                columns = [col[0] for col in cursor.fetchall()]
                
                print(f"Total: {len(rows)} registros mostrados")
                for row in rows:
                    print(f"  - {', '.join([f'{col}={val}' for col, val in zip(columns[:4], row[:4])])}")
            else:
                print("  (Sin datos)")
        
        cursor.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return True

if __name__ == "__main__":
    verify_database()
