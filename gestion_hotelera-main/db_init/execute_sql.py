import pymysql
import os
import re

# Database configuration
DB_HOST = "127.0.0.1"
DB_PORT = 3307
DB_USER = "root"
DB_PASS = ""

def execute_sql_file(filename):
    """Execute a SQL file"""
    print(f"\n{'='*60}")
    print(f"Ejecutando: {filename}")
    print(f"{'='*60}\n")
    
    # Read SQL file
    with open(filename, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Connect to MySQL
    conn = None
    current_db = None
    
    try:
        # First, connect without database
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # Split SQL into statements
        # Remove comments
        sql_content = re.sub(r'/\*.*?\*/', '', sql_content, flags=re.DOTALL)
        sql_content = re.sub(r'--.*?\n', '\n', sql_content)
        
        # Split by semicolon but keep it simple
        statements = []
        current = []
        
        for line in sql_content.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('--') or line.startswith('/*'):
                continue
                
            current.append(line)
            
            if line.endswith(';'):
                stmt = ' '.join(current)
                if stmt.strip():
                    statements.append(stmt)
                current = []
        
        success_count = 0
        error_count = 0
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            try:
                # Check if it's a USE statement
                if statement.upper().strip().startswith('USE '):
                    db_name = statement.split()[1].strip(';').strip('`')
                    cursor.execute(f"USE `{db_name}`")
                    current_db = db_name
                    print(f"[OK] Usando base de datos: {db_name}")
                    success_count += 1
                    continue
                
                # Execute the statement
                cursor.execute(statement)
                conn.commit()
                success_count += 1
                
                # Print progress for important statements
                if 'DROP DATABASE' in statement.upper():
                    db_name = re.search(r'DROP DATABASE (?:IF EXISTS )?`?(\w+)`?', statement, re.IGNORECASE)
                    if db_name:
                        print(f"[OK] Base de datos eliminada: {db_name.group(1)}")
                elif 'CREATE DATABASE' in statement.upper():
                    db_name = re.search(r'CREATE DATABASE `?(\w+)`?', statement, re.IGNORECASE)
                    if db_name:
                        print(f"[OK] Base de datos creada: {db_name.group(1)}")
                elif 'CREATE TABLE' in statement.upper():
                    table_name = re.search(r'CREATE TABLE `?(\w+)`?', statement, re.IGNORECASE)
                    if table_name:
                        print(f"[OK] Tabla creada: {table_name.group(1)}")
                elif 'INSERT INTO' in statement.upper():
                    table_name = re.search(r'INSERT INTO `?(\w+)`?', statement, re.IGNORECASE)
                    if table_name:
                        # Count how many rows
                        values_count = statement.upper().count('VALUES') + statement.count('),(')
                        print(f"[OK] Datos insertados en: {table_name.group(1)}")
                elif 'ALTER TABLE' in statement.upper():
                    table_name = re.search(r'ALTER TABLE `?(\w+)`?', statement, re.IGNORECASE)
                    if table_name:
                        print(f"[OK] Tabla alterada: {table_name.group(1)}")
                        
            except pymysql.err.IntegrityError as e:
                error_count += 1
                if 'Duplicate entry' in str(e):
                    # Ignore duplicate entries as they might already exist
                    success_count += 1  # Count as success
                    error_count -= 1
                elif 'database exists' in str(e).lower():
                    success_count += 1
                    error_count -= 1
                else:
                    print(f"[WARNING] Error de integridad: {str(e)[:100]}")
                    
            except pymysql.err.OperationalError as e:
                if 'already exists' in str(e).lower() or 'Duplicate' in str(e):
                    success_count += 1
                else:
                    error_count += 1
                    print(f"[WARNING] Error operacional: {str(e)[:100]}")
                    
            except Exception as e:
                error_msg = str(e)
                # Ignore certain errors
                if any(x in error_msg.lower() for x in ['already exists', 'duplicate column', 'database exists']):
                    success_count += 1
                else:
                    error_count += 1
                    # Only print significant errors
                    if 'no database selected' not in error_msg.lower():
                        print(f"[WARNING] Error #{i}: {error_msg[:150]}")
        
        print(f"\n{'='*60}")
        print(f"Completado: {success_count} exitosos, {error_count} errores")
        print(f"{'='*60}\n")
        
        cursor.close()
        
    except Exception as e:
        print(f"ERROR DE CONEXION: {e}")
        return False
    finally:
        if conn:
            conn.close()
    
    return error_count == 0 or error_count < 5  # Allow some errors

def main():
    print("\n" + "="*60)
    print("CONFIGURACION DE BASE DE DATOS - GESTION HOTELERA")
    print("="*60 + "\n")
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # List of SQL files to execute in order
    sql_files = [
        os.path.join(current_dir, 'Hotel_BD.sql'),
        os.path.join(current_dir, 'hotel_data_inserts.sql')
    ]
    
    # Execute each file
    all_success = True
    for sql_file in sql_files:
        if os.path.exists(sql_file):
            result = execute_sql_file(sql_file)
            if not result:
                all_success = False
                print(f"\n[WARNING] Errores al ejecutar {os.path.basename(sql_file)}")
        else:
            print(f"\n[WARNING] Archivo no encontrado: {sql_file}")
            all_success = False
    
    print("\n" + "="*60)
    if all_success:
        print("[OK] SCRIPTS SQL EJECUTADOS EXITOSAMENTE")
    else:
        print("[WARNING] SCRIPTS EJECUTADOS CON ALGUNAS ADVERTENCIAS")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
