#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar y corregir problemas de encoding en la base de datos
Ejecutar después de configurar el docker-compose.yml con UTF-8
"""

import pymysql
import os

# Configuración de conexión
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3307))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "")
DB_NAME = os.environ.get("DB_NAME", "gestion_hotelera")

def get_connection():
    """Crear conexión a la base de datos con UTF-8"""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        charset='utf8mb4',
        use_unicode=True,
        autocommit=False
    )

def check_database_charset():
    """Verificar la configuración de charset de la base de datos"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("=" * 60)
            print("VERIFICACIÓN DE CONFIGURACIÓN DE BASE DE DATOS")
            print("=" * 60)
            
            # Verificar charset de la base de datos
            cur.execute(f"SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME = '{DB_NAME}'")
            result = cur.fetchone()
            print(f"\nBase de datos '{DB_NAME}':")
            print(f"  Charset: {result[0]}")
            print(f"  Collation: {result[1]}")
            
            # Verificar charset de las tablas
            cur.execute(f"SELECT TABLE_NAME, TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{DB_NAME}'")
            tables = cur.fetchall()
            print(f"\nTablas:")
            for table, collation in tables:
                print(f"  {table}: {collation}")
            
            # Verificar charset de las columnas de texto
            cur.execute(f"""
                SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = '{DB_NAME}' 
                AND CHARACTER_SET_NAME IS NOT NULL
            """)
            columns = cur.fetchall()
            print(f"\nColumnas de texto:")
            for table, column, charset, collation in columns:
                status = "✓" if charset == 'utf8mb4' else "✗"
                print(f"  {status} {table}.{column}: {charset}/{collation}")
            
    finally:
        conn.close()

def check_data_corruption():
    """Verificar si hay datos con problemas de encoding"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("\n" + "=" * 60)
            print("VERIFICACIÓN DE DATOS EXISTENTES")
            print("=" * 60)
            
            # Verificar clientes
            cur.execute("SELECT client_id, full_name FROM clients LIMIT 10")
            clients = cur.fetchall()
            print("\nPrimeros 10 clientes:")
            for client_id, name in clients:
                # Detectar caracteres problemáticos
                has_problem = 'Ã' in name or 'Â' in name or 'Ã±' in name
                status = "⚠️" if has_problem else "✓"
                print(f"  {status} [{client_id}] {name}")
            
            # Verificar staff
            cur.execute("SELECT staff_id, full_name FROM staff LIMIT 10")
            staff = cur.fetchall()
            print("\nPrimeros 10 empleados:")
            for staff_id, name in staff:
                has_problem = 'Ã' in name or 'Â' in name or 'Ã±' in name
                status = "⚠️" if has_problem else "✓"
                print(f"  {status} [{staff_id}] {name}")
                
    finally:
        conn.close()

def fix_database_charset():
    """Convertir todas las tablas y columnas a UTF-8"""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("\n" + "=" * 60)
            print("CORRIGIENDO CHARSET DE BASE DE DATOS")
            print("=" * 60)
            
            # Convertir la base de datos
            print(f"\n1. Convirtiendo base de datos a utf8mb4...")
            cur.execute(f"ALTER DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("   ✓ Base de datos convertida")
            
            # Obtener todas las tablas
            cur.execute(f"SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{DB_NAME}'")
            tables = [row[0] for row in cur.fetchall()]
            
            # Convertir cada tabla
            print(f"\n2. Convirtiendo {len(tables)} tablas...")
            for table in tables:
                print(f"   Convirtiendo tabla '{table}'...", end=" ")
                cur.execute(f"ALTER TABLE `{table}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print("✓")
            
            conn.commit()
            print("\n✓ Conversión completada exitosamente")
            
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error durante la conversión: {e}")
    finally:
        conn.close()

def fix_corrupted_data():
    """
    Intenta corregir datos corruptos por doble encoding
    ADVERTENCIA: Este proceso es delicado y puede causar más problemas si no se usa correctamente
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("\n" + "=" * 60)
            print("CORRIGIENDO DATOS CORRUPTOS")
            print("=" * 60)
            print("\n⚠️  ADVERTENCIA: Este proceso intentará decodificar datos con doble encoding")
            print("Si los datos ya están correctos, esto los corromperá.")
            
            response = input("\n¿Estás seguro de continuar? (escribe 'SI' para confirmar): ")
            if response != 'SI':
                print("Operación cancelada")
                return
            
            # Corregir clientes
            cur.execute("SELECT client_id, full_name FROM clients")
            clients = cur.fetchall()
            
            fixed_count = 0
            for client_id, name in clients:
                try:
                    # Intentar decodificar doble encoding UTF-8 -> Latin1 -> UTF-8
                    if 'Ã' in name or 'Â' in name:
                        # Convertir a bytes asumiendo que son UTF-8
                        name_bytes = name.encode('latin1')
                        # Decodificar como UTF-8
                        fixed_name = name_bytes.decode('utf8')
                        
                        cur.execute("UPDATE clients SET full_name = %s WHERE client_id = %s", 
                                  (fixed_name, client_id))
                        print(f"  ✓ [{client_id}] '{name}' -> '{fixed_name}'")
                        fixed_count += 1
                except Exception as e:
                    print(f"  ✗ [{client_id}] Error: {e}")
            
            # Corregir staff
            cur.execute("SELECT staff_id, full_name FROM staff")
            staff = cur.fetchall()
            
            for staff_id, name in staff:
                try:
                    if 'Ã' in name or 'Â' in name:
                        name_bytes = name.encode('latin1')
                        fixed_name = name_bytes.decode('utf8')
                        
                        cur.execute("UPDATE staff SET full_name = %s WHERE staff_id = %s", 
                                  (fixed_name, staff_id))
                        print(f"  ✓ [Staff {staff_id}] '{name}' -> '{fixed_name}'")
                        fixed_count += 1
                except Exception as e:
                    print(f"  ✗ [Staff {staff_id}] Error: {e}")
            
            conn.commit()
            print(f"\n✓ Se corrigieron {fixed_count} registros")
            
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error durante la corrección: {e}")
    finally:
        conn.close()

def main():
    """Menú principal"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║   Script de Corrección de Encoding para MySQL/UTF-8      ║
║                   Gestión Hotelera                         ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    while True:
        print("\nOpciones:")
        print("  1. Verificar configuración de charset")
        print("  2. Verificar datos corruptos")
        print("  3. Corregir charset de base de datos y tablas")
        print("  4. Corregir datos corruptos (CUIDADO)")
        print("  5. Ejecutar verificación completa (1+2)")
        print("  0. Salir")
        
        choice = input("\nSelecciona una opción: ")
        
        if choice == '1':
            check_database_charset()
        elif choice == '2':
            check_data_corruption()
        elif choice == '3':
            fix_database_charset()
        elif choice == '4':
            fix_corrupted_data()
        elif choice == '5':
            check_database_charset()
            check_data_corruption()
        elif choice == '0':
            print("\n¡Hasta luego!")
            break
        else:
            print("Opción no válida")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperación interrumpida por el usuario")
    except Exception as e:
        print(f"\n✗ Error fatal: {e}")
