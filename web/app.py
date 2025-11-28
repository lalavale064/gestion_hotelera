# app.py - CÓDIGO CORREGIDO Y COMPLETO
from flask import Flask, request, render_template, jsonify, redirect, abort
import os, hashlib, re 
import pymysql
from pymysql.cursors import DictCursor
from datetime import date, datetime

# --- CONFIGURACIÓN ---
app = Flask(__name__, template_folder="templates", static_folder="static")

# Variables de entorno o configuración local de XAMPP (AJUSTAR AQUÍ)
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1") 
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "") 
DB_NAME = os.environ.get("DB_NAME", "gestion_hotelera")

# Tipos de roles soportados
ROLES = ['admin', 'cliente', 'spa', 'recepcion']

def get_conn():
    conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS,
                           database=DB_NAME, port=DB_PORT, cursorclass=DictCursor,
                           autocommit=True,
                           charset='utf8mb4',     # Mantenemos este parámetro
                           use_unicode=True)      # Y este

    # 🚨 PASO CRÍTICO: Forzar el juego de caracteres después de la conexión
    with conn.cursor() as cur:
        cur.execute("SET NAMES 'utf8mb4'")
        
    return conn

def sha256_hex(s):
    # Función para generar el hash de la contraseña (debe coincidir con MySQL SHA2(s, 256))
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def validate_email(email):
    if not email: return True # Permitir vacíos si es opcional, pero si se envía debe ser válido
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)

def validate_phone(phone):
    if not phone: return True
    return re.match(r'^[0-9]+$', phone)

# --- FUNCIONES DE SEGURIDAD (TODO: IMPLEMENTAR VERIFICACIÓN REAL) ---
def require_role(allowed_roles):
    """
    Decorador para la verificación de roles. 
    Para esta demo, lee el rol enviado en el header 'X-User-Role' del Frontend (INSEGURO, SOLO PARA PRUEBAS).
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            user_role = request.headers.get('X-User-Role')
            
            # El administrador tiene pase libre
            if user_role == 'admin':
                return f(*args, **kwargs)

            if user_role not in allowed_roles:
                return jsonify({"error": "Acceso no autorizado. Rol requerido: " + ', '.join(allowed_roles)}), 403
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# --- RUTAS DE PÁGINAS ESTÁTICAS ---
@app.route("/")
def root():
    return redirect("/login.html")

@app.route("/login.html")
def login_page():
    return render_template("login.html")

@app.route("/cliente.html")
def cliente_page():
    return render_template("cliente.html")

@app.route("/administrador.html")
def admin_page():
    return render_template("administrador.html")

# NUEVA VISTA PARA EMPLEADOS (SPA, RECEPCIÓN)
@app.route("/empleado.html")
def empleado_page():
    return render_template("empleado.html")

# --- AUTH ---
@app.route("/api/login", methods=["POST"])
def api_login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # 1. Verificar credenciales en la tabla users
            cur.execute("SELECT user_id, user_role FROM users WHERE email=%s AND password_hash=SHA2(%s, 256)", (email, password))
            user = cur.fetchone()

            if user:
                role = user['user_role']
                response = {'message': 'Login exitoso', 'role': role}
                
                # 2. Si es cliente, buscar su client_id
                if role == 'cliente':
                    cur.execute("SELECT client_id FROM clients WHERE user_id=%s", (user['user_id'],))
                    client = cur.fetchone()
                    if client:
                        response['client_id'] = client['client_id']
                
                return jsonify(response)
            else:
                return jsonify({'error': 'Credenciales inválidas.'}), 401
    except Exception as e:
        print(f"Error durante el login: {e}")
        return jsonify({'error': 'Error interno del servidor.'}), 500
    finally:
        if conn: conn.close()


# --- UTILIDADES DE PAGINACIÓN ---
def get_paginated_query(cursor, table_name, search_fields, search_query, page, per_page, extra_where="", extra_params=None, order_by="id DESC"):
    """
    Construye y ejecuta una consulta paginada con búsqueda.
    Retorna un diccionario con data y metadatos de paginación.
    """
    if extra_params is None:
        extra_params = []
    
    offset = (page - 1) * per_page
    params = []
    where_clauses = []

    # 1. Filtro de búsqueda (Search)
    if search_query:
        search_terms = []
        for field in search_fields:
            search_terms.append(f"{field} LIKE %s")
            params.append(f"%{search_query}%")
        if search_terms:
            where_clauses.append(f"({' OR '.join(search_terms)})")
    
    # 2. Filtros extra
    if extra_where:
        where_clauses.append(extra_where)
        params.extend(extra_params)

    where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    # 3. Contar total de registros (para la paginación)
    count_sql = f"SELECT COUNT(*) as total FROM {table_name} {where_str}"
    cursor.execute(count_sql, tuple(params))
    total_records = cursor.fetchone()['total']
    total_pages = (total_records + per_page - 1) // per_page

    # 4. Obtener datos paginados
    data_sql = f"SELECT * FROM {table_name} {where_str} ORDER BY {order_by} LIMIT %s OFFSET %s"
    params.append(per_page)
    params.append(offset)
    
    cursor.execute(data_sql, tuple(params))
    results = cursor.fetchall()

    return {
        "data": results,
        "total": total_records,
        "page": page,
        "per_page": per_page,
        "pages": total_pages
    }

# ====================================================================
#                          ENDPOINTS CRUD
# ====================================================================

# --- CLIENTES (Gestión de Clientes) ---
@app.route("/api/clients", methods=["GET"])
@require_role(['admin', 'recepcion'])
def api_get_clients():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search = request.args.get('q', '')

    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            result = get_paginated_query(
                cur, 
                table_name="clients", 
                search_fields=["full_name", "email", "phone", "address"], 
                search_query=search, 
                page=page, 
                per_page=per_page,
                order_by="client_id DESC"
            )
            return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/clients", methods=["POST"])
@require_role(['admin', 'recepcion'])
def api_create_client():
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Validaciones
            if data.get('email') and not validate_email(data['email']):
                return jsonify({"error": "Formato de email inválido"}), 400
            if data.get('phone') and not validate_phone(data['phone']):
                return jsonify({"error": "El teléfono debe contener solo números"}), 400

            cur.execute("INSERT INTO clients (full_name, email, phone, address) VALUES (%s, %s, %s, %s)",
                        (data['full_name'], data.get('email'), data.get('phone'), data.get('address')))
            return jsonify({"message": "Cliente creado exitosamente", "id": cur.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/clients/<int:client_id>", methods=["PUT"])
@require_role(['admin', 'recepcion'])
def api_update_client(client_id):
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Validaciones
            if data.get('email') and not validate_email(data['email']):
                return jsonify({"error": "Formato de email inválido"}), 400
            if data.get('phone') and not validate_phone(data['phone']):
                return jsonify({"error": "El teléfono debe contener solo números"}), 400

            cur.execute("UPDATE clients SET full_name=%s, email=%s, phone=%s, address=%s WHERE client_id=%s",
                        (data['full_name'], data.get('email'), data.get('phone'), data.get('address'), client_id))
            if cur.rowcount == 0:
                return jsonify({"error": "Cliente no encontrado"}), 404
            return jsonify({"message": "Cliente actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/clients/<int:client_id>", methods=["DELETE"])
@require_role(['admin']) # Solo ADMIN puede eliminar
def api_delete_client(client_id):
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Eliminación en cascada manual (por si la BD no tiene ON DELETE CASCADE configurado)
            # 1. Obtener IDs de reservas del cliente
            cur.execute("SELECT reservation_id FROM reservations WHERE client_id = %s", (client_id,))
            res_ids = [r['reservation_id'] for r in cur.fetchall()]
            
            if res_ids:
                format_strings = ','.join(['%s'] * len(res_ids))
                # 2. Eliminar facturas asociadas
                cur.execute(f"DELETE FROM invoices WHERE reservation_id IN ({format_strings})", tuple(res_ids))
                # 3. Eliminar servicios de reserva asociados
                cur.execute(f"DELETE FROM reservation_services WHERE reservation_id IN ({format_strings})", tuple(res_ids))
                # 4. Eliminar reservas
                cur.execute(f"DELETE FROM reservations WHERE reservation_id IN ({format_strings})", tuple(res_ids))

            # 5. Eliminar cliente
            cur.execute("DELETE FROM clients WHERE client_id=%s", (client_id,))
            
            if cur.rowcount == 0 and not res_ids: # Si no borró nada y no había reservas
                return jsonify({"error": "Cliente no encontrado"}), 404
            
            return jsonify({"message": "Cliente y sus reservas eliminados"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# --- HABITACIONES (Gestión de Habitaciones) ---
@app.route("/api/rooms", methods=["GET"])
def api_get_rooms():
    # Acceso de lectura para todos (Cliente, Admin, Empleado)
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search = request.args.get('q', '')
    status_filter = request.args.get('status') # Nuevo filtro
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            extra_where = ""
            extra_params = []
            
            if status_filter:
                extra_where = "status = %s"
                extra_params.append(status_filter)

            result = get_paginated_query(
                cur, 
                table_name="rooms", 
                search_fields=["room_num", "room_type", "status"], 
                search_query=search, 
                page=page, 
                per_page=per_page,
                extra_where=extra_where,
                extra_params=extra_params,
                order_by="room_num ASC"
            )
            return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/rooms", methods=["POST"])
@require_role(['admin'])
def api_create_room():
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO rooms (room_num, room_type, capacity, price) VALUES (%s, %s, %s, %s)",
                        (data['room_num'], data['room_type'], data['capacity'], data['price']))
            return jsonify({"message": "Habitación creada", "room_id": cur.lastrowid}), 201
    except pymysql.err.IntegrityError:
        return jsonify({"error": "El número de habitación ya existe."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/rooms/<int:room_id>", methods=["PUT"])
@require_role(['admin', 'recepcion'])
def api_update_room(room_id):
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("UPDATE rooms SET room_num=%s, room_type=%s, capacity=%s, price=%s, status=%s WHERE room_id=%s",
                        (data['room_num'], data['room_type'], data['capacity'], data['price'], data['status'], room_id))
            if cur.rowcount == 0:
                return jsonify({"error": "Habitación no encontrada"}), 404
            return jsonify({"message": "Habitación actualizada"}), 200
    except pymysql.err.IntegrityError:
        return jsonify({"error": "El número de habitación ya existe."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/rooms/<int:room_id>", methods=["DELETE"])
@require_role(['admin'])
def api_delete_room(room_id):
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM rooms WHERE room_id=%s", (room_id,))
            if cur.rowcount == 0:
                return jsonify({"error": "Habitación no encontrada"}), 404
            return jsonify({"message": "Habitación eliminada"}), 200
    except Exception as e:
        return jsonify({"error": "No se puede eliminar la habitación. Hay reservas asociadas."}), 400
    finally:
        if conn: conn.close()

# --- EMPLEADOS (Gestión de Staff) ---
@app.route("/api/staff", methods=["GET"])
@require_role(['admin', 'recepcion'])
def api_get_staff():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search = request.args.get('q', '')

    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            result = get_paginated_query(
                cur, 
                table_name="staff", 
                search_fields=["full_name", "staff_role", "area"], 
                search_query=search, 
                page=page, 
                per_page=per_page,
                order_by="staff_id DESC"
            )
            return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/staff", methods=["POST"])
@require_role(['admin'])
def api_create_staff():
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO staff (full_name, staff_role, area, hire_date, active) VALUES (%s, %s, %s, %s, %s)",
                        (data['full_name'], data['staff_role'], data.get('area'), data['hire_date'], data.get('active', 1)))
            return jsonify({"message": "Empleado creado", "staff_id": cur.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/staff/<int:staff_id>", methods=["PUT"])
@require_role(['admin'])
def api_update_staff(staff_id):
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("UPDATE staff SET full_name=%s, staff_role=%s, area=%s, hire_date=%s, active=%s WHERE staff_id=%s",
                        (data['full_name'], data['staff_role'], data.get('area'), data['hire_date'], data.get('active', 1), staff_id))
            if cur.rowcount == 0:
                return jsonify({"error": "Empleado no encontrado"}), 404
            return jsonify({"message": "Empleado actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# RUTA NUEVA: Eliminar empleado
@app.route("/api/staff/<int:staff_id>", methods=["DELETE"])
@require_role(['admin'])
def api_delete_staff(staff_id):
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM staff WHERE staff_id=%s", (staff_id,))
            if cur.rowcount == 0:
                return jsonify({"error": "Empleado no encontrado"}), 404
            return jsonify({"message": "Empleado eliminado"}), 200
    except Exception as e:
        return jsonify({"error": "No se puede eliminar el empleado. Tiene datos asociados (ej: turnos, roles de usuario)."}), 400
    finally:
        if conn: conn.close()
        
# --- SERVICIOS (Administración de Servicios) ---
@app.route("/api/services", methods=["GET"])
@require_role(['admin', 'spa', 'recepcion', 'cliente']) # Acceso de lectura amplio
def api_get_services():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search = request.args.get('q', '')
    status = request.args.get('status', '')

    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            extra_where = ""
            extra_params = []
            
            if status:
                extra_where = "status = %s"
                extra_params.append(status)

            result = get_paginated_query(
                cur, 
                table_name="services", 
                search_fields=["service_code", "name", "description"], 
                search_query=search, 
                page=page, 
                per_page=per_page,
                extra_where=extra_where,
                extra_params=extra_params,
                order_by="service_id ASC"
            )
            return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/services", methods=["POST"])
@require_role(['admin'])
def api_create_service():
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("INSERT INTO services (service_code, name, description, price) VALUES (%s, %s, %s, %s)",
                        (data['service_code'], data['name'], data.get('description'), data['price']))
            return jsonify({"message": "Servicio creado", "service_id": cur.lastrowid}), 201
    except pymysql.err.IntegrityError:
        return jsonify({"error": "El código de servicio ya existe."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# RUTA NUEVA: Actualizar servicio (PUT, que faltaba)
@app.route("/api/services/<int:service_id>", methods=["PUT"])
@require_role(['admin'])
def api_update_service(service_id):
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("UPDATE services SET service_code=%s, name=%s, description=%s, price=%s, status=%s WHERE service_id=%s",
                        (data['service_code'], data['name'], data.get('description'), data['price'], data.get('status', 'activo'), service_id))
            if cur.rowcount == 0:
                return jsonify({"error": "Servicio no encontrado"}), 404
            return jsonify({"message": "Servicio actualizado"}), 200
    except pymysql.err.IntegrityError:
        return jsonify({"error": "El código de servicio ya existe."}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# RUTA NUEVA: Eliminar servicio
@app.route("/api/services/<int:service_id>", methods=["DELETE"])
@require_role(['admin'])
def api_delete_service(service_id):
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM services WHERE service_id=%s", (service_id,))
            if cur.rowcount == 0:
                return jsonify({"error": "Servicio no encontrado"}), 404
            return jsonify({"message": "Servicio eliminado"}), 200
    except Exception as e:
        return jsonify({"error": "No se puede eliminar el servicio. Hay registros de consumo asociados."}), 400
    finally:
        if conn: conn.close()

# --- RESERVAS (Creación, Consulta, Modificación) ---

@app.route("/api/reservations", methods=["GET"])
@require_role(['admin', 'recepcion', 'spa', 'cliente'])
def api_get_reservations():
    client_id = request.args.get('client_id')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search = request.args.get('q', '')

    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Construcción manual de la consulta paginada debido a los JOINs
            offset = (page - 1) * per_page
            params = []
            where_clauses = []

            # Filtro por cliente
            if client_id:
                where_clauses.append("r.client_id = %s")
                params.append(client_id)
            
            # Filtro por estado
            status_filter = request.args.get('status')
            if status_filter:
                where_clauses.append("r.status = %s")
                params.append(status_filter)
            
            # Filtro de búsqueda
            if search:
                where_clauses.append("(r.reservation_code LIKE %s OR r.guest_name LIKE %s OR c.full_name LIKE %s)")
                params.append(f"%{search}%")
                params.append(f"%{search}%")
                params.append(f"%{search}%")

            where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # 1. Count
            count_sql = f"""
                SELECT COUNT(*) as total 
                FROM reservations r
                JOIN clients c ON r.client_id = c.client_id
                {where_str}
            """
            # Nota: params se usa dos veces, así que hacemos una copia o lo pasamos igual si no se modifica
            cur.execute(count_sql, tuple(params))
            total_records = cur.fetchone()['total']
            total_pages = (total_records + per_page - 1) // per_page

            # 2. Data
            sql = f"""
                SELECT 
                    r.reservation_id, r.reservation_code, r.room_id, ro.room_num, r.guest_name, r.guest_email, 
                    r.checkin_date, r.checkout_date, r.total, r.status,
                    c.full_name AS client_name
                FROM reservations r
                JOIN rooms ro ON r.room_id = ro.room_id
                JOIN clients c ON r.client_id = c.client_id
                {where_str}
                ORDER BY r.reservation_id DESC
                LIMIT %s OFFSET %s
                """
            params.append(per_page)
            params.append(offset)

            cur.execute(sql, tuple(params))
            results = cur.fetchall()

            return jsonify({
                "data": results,
                "total": total_records,
                "page": page,
                "per_page": per_page,
                "pages": total_pages
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/reservations", methods=["POST"])
@require_role(['admin', 'recepcion', 'cliente'])
def api_create_reservation():
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # 1. Obtener el precio de la habitación para calcular el total inicial
            cur.execute("SELECT price FROM rooms WHERE room_id = %s", (data['room_id'],))
            room = cur.fetchone()
            if not room:
                return jsonify({"error": "Habitación no válida."}), 400
            
            # Cálculo simple
            price = room['price']
            # Se asegura de manejar la resta de fechas para calcular los días
            checkin = datetime.strptime(data['checkin_date'], '%Y-%m-%d')
            checkout = datetime.strptime(data['checkout_date'], '%Y-%m-%d')
            num_days = max(1, (checkout - checkin).days)
            total = price * num_days

            # Obtener nombre del huésped si no se proporciona
            guest_name = data.get('guest_name')
            guest_email = data.get('guest_email')
            guest_phone = data.get('guest_phone')

            # Validaciones de huésped
            if guest_email and not validate_email(guest_email):
                return jsonify({"error": "Formato de email de huésped inválido"}), 400
            if guest_phone and not validate_phone(guest_phone):
                return jsonify({"error": "El teléfono de huésped debe contener solo números"}), 400

            if not guest_name:
                cur.execute("SELECT full_name FROM clients WHERE client_id = %s", (data['client_id'],))
                client = cur.fetchone()
                if client:
                    guest_name = client['full_name']
                else:
                    return jsonify({"error": "Cliente no encontrado."}), 400

            cur.execute("""
                INSERT INTO reservations (client_id, room_id, guest_name, guest_email, guest_phone, checkin_date, checkout_date, total, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'reservada')
                """, (data['client_id'], data['room_id'], guest_name, data.get('guest_email'), data.get('guest_phone'), 
                      data['checkin_date'], data['checkout_date'], total))
            
            return jsonify({"message": "Reserva creada exitosamente", "reservation_id": cur.lastrowid, "total_estimado": total}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/reservations/<int:res_id>", methods=["PUT"])
@require_role(['admin', 'recepcion', 'cliente'])
def api_update_reservation(res_id):
    data = request.json
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            status_to_update = data.get('status')
            
            # Nota: 'facturada' se actualiza desde la ruta de facturación, pero la mantenemos aquí también.
            if status_to_update in ['confirmada', 'checkin', 'checkout', 'cancelada', 'facturada']: 
                cur.execute("UPDATE reservations SET status=%s WHERE reservation_id=%s",
                            (status_to_update, res_id))
                
                # Actualizar estado de la habitación
                if status_to_update == 'checkin':
                    # Obtener room_id de la reserva
                    cur.execute("SELECT room_id FROM reservations WHERE reservation_id=%s", (res_id,))
                    res = cur.fetchone()
                    if res:
                        cur.execute("UPDATE rooms SET status='ocupada' WHERE room_id=%s", (res['room_id'],))
                elif status_to_update == 'checkout':
                    cur.execute("SELECT room_id FROM reservations WHERE reservation_id=%s", (res_id,))
                    res = cur.fetchone()
                    if res:
                        cur.execute("UPDATE rooms SET status='disponible' WHERE room_id=%s", (res['room_id'],))

            else:
                 return jsonify({"error": "Estado de reserva no válido."}), 400
            
            if cur.rowcount == 0:
                return jsonify({"error": "Reserva no encontrada"}), 404
            return jsonify({"message": "Reserva actualizada"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/reservations/<int:res_id>", methods=["DELETE"])
@require_role(['admin'])
def api_delete_reservation(res_id):
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Primero eliminamos servicios asociados para evitar error de FK (si no hay cascade)
            cur.execute("DELETE FROM reservation_services WHERE reservation_id=%s", (res_id,))
            # Eliminamos facturas asociadas? Mejor no, o sí. Asumamos que sí para limpiar.
            cur.execute("DELETE FROM invoices WHERE reservation_id=%s", (res_id,))
            
            cur.execute("DELETE FROM reservations WHERE reservation_id=%s", (res_id,))
            if cur.rowcount == 0:
                return jsonify({"error": "Reserva no encontrada"}), 404
            return jsonify({"message": "Reserva eliminada"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# POST para agregar servicio a reserva (Recepción/Spa)
@app.route("/api/reservations/<int:res_id>/services", methods=["POST"])
@require_role(['admin', 'recepcion', 'spa', 'cliente'])
def api_add_reservation_service(res_id):
    data = request.json
    service_id = data.get('service_id')
    quantity = data.get('quantity', 1)
    service_date_str = data.get('service_date') # YYYY-MM-DD
    
    if not service_date_str:
         return jsonify({"error": "La fecha del servicio es obligatoria."}), 400

    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # 1. Validar Reserva y Fechas
            cur.execute("SELECT client_id, checkin_date, checkout_date, status FROM reservations WHERE reservation_id = %s", (res_id,))
            res = cur.fetchone()
            if not res:
                return jsonify({"error": "Reserva no encontrada."}), 404
            
            # Si es cliente, validar que la reserva le pertenezca
            user_role = request.headers.get('X-User-Role')
            if user_role == 'cliente':
                client_id = int(request.headers.get('X-Client-Id', 0))
                if res['client_id'] != client_id:
                    return jsonify({"error": "No tienes permiso para agregar servicios a esta reserva."}), 403
            
            # Validar estado (solo activas)
            if res['status'] not in ['reservada', 'confirmada', 'checkin']:
                 return jsonify({"error": "Solo se pueden agregar servicios a reservas activas."}), 400

            # Validar fecha
            service_date = datetime.strptime(service_date_str, '%Y-%m-%d').date()
            if not (res['checkin_date'] <= service_date <= res['checkout_date']):
                return jsonify({"error": f"La fecha del servicio debe estar entre {res['checkin_date']} y {res['checkout_date']}."}), 400

            # 2. Obtener precio actual del servicio
            cur.execute("SELECT price FROM services WHERE service_id = %s", (service_id,))
            service = cur.fetchone()
            if not service:
                return jsonify({"error": "Servicio no válido."}), 400
            
            unit_price = service['price']
            total_service_cost = unit_price * int(quantity)

            # 3. Insertar el servicio consumido
            cur.execute("""
                INSERT INTO reservation_services (reservation_id, service_id, quantity, unit_price, service_date) 
                VALUES (%s, %s, %s, %s, %s)
                """, (res_id, service_id, quantity, unit_price, service_date))
            
            # 4. Actualizar el total de la reserva
            cur.execute("UPDATE reservations SET total = total + %s WHERE reservation_id = %s", (total_service_cost, res_id))
            
            return jsonify({"message": "Servicio añadido a la reserva y total actualizado", "id": cur.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# NUEVO: Obtener LISTADO de reservas de servicios (para la tabla de gestión)
@app.route("/api/reservation_services", methods=["GET"])
@require_role(['admin', 'recepcion', 'spa'])
def api_get_reservation_services():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    search = request.args.get('q', '')

    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            offset = (page - 1) * per_page
            params = []
            where_clauses = []

            if search:
                where_clauses.append("(c.full_name LIKE %s OR s.name LIKE %s OR ro.room_num LIKE %s)")
                params.append(f"%{search}%")
                params.append(f"%{search}%")
                params.append(f"%{search}%")
            
            where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            # Count
            count_sql = f"""
                SELECT COUNT(*) as total 
                FROM reservation_services rs
                JOIN reservations r ON rs.reservation_id = r.reservation_id
                JOIN clients c ON r.client_id = c.client_id
                JOIN rooms ro ON r.room_id = ro.room_id
                JOIN services s ON rs.service_id = s.service_id
                {where_str}
            """
            cur.execute(count_sql, tuple(params))
            total_records = cur.fetchone()['total']
            total_pages = (total_records + per_page - 1) // per_page

            # Data
            sql = f"""
                SELECT 
                    rs.reservation_service_id, rs.service_date, rs.quantity, rs.unit_price, 
                    (rs.quantity * rs.unit_price) as line_total,
                    s.name as service_name,
                    c.full_name as client_name,
                    ro.room_num,
                    r.reservation_code
                FROM reservation_services rs
                JOIN reservations r ON rs.reservation_id = r.reservation_id
                JOIN clients c ON r.client_id = c.client_id
                JOIN rooms ro ON r.room_id = ro.room_id
                JOIN services s ON rs.service_id = s.service_id
                {where_str}
                ORDER BY rs.service_date DESC, rs.reservation_service_id DESC
                LIMIT %s OFFSET %s
            """
            params.append(per_page)
            params.append(offset)
            
            cur.execute(sql, tuple(params))
            results = cur.fetchall()

            return jsonify({
                "data": results,
                "total": total_records,
                "page": page,
                "per_page": per_page,
                "pages": total_pages
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# NUEVO: Obtener reservas activas de un cliente (para el combo de servicios)
@app.route("/api/clients/<int:client_id>/active_reservations", methods=["GET"])
@require_role(['admin', 'recepcion', 'spa'])
def api_get_client_active_reservations(client_id):
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.reservation_id, r.reservation_code, r.checkin_date, r.checkout_date, ro.room_num 
                FROM reservations r
                JOIN rooms ro ON r.room_id = ro.room_id
                WHERE r.client_id = %s AND r.status IN ('reservada', 'confirmada', 'checkin')
                ORDER BY r.checkin_date DESC
            """, (client_id,))
            return jsonify(cur.fetchall())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# --- NUEVA RUTA PARA RESERVAS ELEGIBLES PARA FACTURACIÓN ---
@app.route("/api/reservations/eligible_for_invoice", methods=["GET"])
@require_role(['admin', 'recepcion'])
def api_get_eligible_reservations():
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Filtra las reservas que están en estado 'checkout' y por lo tanto listas para facturar.
            # Se incluye el campo r.total para el "Total Estimado"
            sql = """
                SELECT 
                    r.reservation_id, r.reservation_code, r.checkin_date, r.checkout_date, r.total, r.status,
                    c.client_id, c.full_name AS client_name, 
                    ro.room_id, ro.room_num, ro.room_type, ro.price as room_price
                FROM reservations r
                JOIN clients c ON r.client_id = c.client_id
                JOIN rooms ro ON r.room_id = ro.room_id
                WHERE r.status = 'checkout'
                ORDER BY r.checkin_date DESC
            """
            cur.execute(sql)
            return jsonify(cur.fetchall())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# --- FACTURACIÓN (Invoices): UNIFICADO Y CORREGIDO ---
@app.route("/api/invoices", methods=["GET", "POST"])
@app.route("/api/invoices/<int:invoice_id>", methods=["GET", "PUT", "DELETE"])
@require_role(['admin', 'recepcion'])
def manage_invoices(invoice_id=None):
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # GET: Obtener todas las facturas (Paginado)
            if request.method == 'GET' and invoice_id is None:
                page = int(request.args.get('page', 1))
                per_page = int(request.args.get('per_page', 10))
                search = request.args.get('q', '')

                # Construcción manual para JOINs si quisiéramos buscar por nombre de cliente, 
                # pero invoices no tiene client_id directo (está en reservations).
                # Haremos un JOIN simple.
                
                offset = (page - 1) * per_page
                params = []
                where_clauses = []

                if search:
                    # Buscamos por ID de factura o ID de reserva (convertidos a string)
                    where_clauses.append("(invoice_id LIKE %s OR reservation_id LIKE %s)")
                    params.append(f"%{search}%")
                    params.append(f"%{search}%")
                
                where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                # Count
                cur.execute(f"SELECT COUNT(*) as total FROM invoices {where_str}", tuple(params))
                total_records = cur.fetchone()['total']
                total_pages = (total_records + per_page - 1) // per_page

                # Data
                sql = f"SELECT * FROM invoices {where_str} ORDER BY invoice_date DESC LIMIT %s OFFSET %s"
                params.append(per_page)
                params.append(offset)
                
                cur.execute(sql, tuple(params))
                results = cur.fetchall()

                return jsonify({
                    "data": results,
                    "total": total_records,
                    "page": page,
                    "per_page": per_page,
                    "pages": total_pages
                })
            
            # POST: Crear nueva factura (para reservas en estado 'checkout')
            if request.method == 'POST':
                data = request.json
                res_id = data.get('reservation_id')
                
                # 1. VERIFICAR ESTADO Y PREVENCIÓN DE DOBLE FACTURACIÓN
                cur.execute("SELECT status FROM reservations WHERE reservation_id = %s", (res_id,))
                reservation = cur.fetchone()

                if not reservation:
                    return jsonify({"error": f"Reserva {res_id} no encontrada."}), 404

                if reservation['status'] == 'facturada':
                    return jsonify({"error": f"La Reserva {res_id} ya ha sido Facturada."}), 400

                if reservation['status'] != 'checkout':
                    return jsonify({"error": f"Solo se puede Facturar una reserva en estado 'checkout'. Estado actual: {reservation['status'].upper()}."}), 400

                # 2. CREAR LA FACTURA
                cur.execute("""
                    INSERT INTO invoices (reservation_id, total, method, invoice_date) 
                    VALUES (%s, %s, %s, CURRENT_DATE())
                """, (res_id, data['total'], data['method']))
                invoice_id = cur.lastrowid
                
                # 3. ACTUALIZAR EL ESTADO DE LA RESERVA
                cur.execute("UPDATE reservations SET status = 'facturada' WHERE reservation_id = %s", (res_id,))

                return jsonify({"message": "Factura generada y reserva actualizada", "invoice_id": invoice_id}), 201

            # PUT: Actualizar factura (CORRECCIÓN DEL ERROR 1292)
            if request.method == 'PUT' and invoice_id is not None:
                data = request.json
                
                # *** CORRECCIÓN DEL ERROR 1292: Manejo de fecha vacía ***
                invoice_date_str = data.get('invoice_date')
                
                # Si la cadena es vacía o None, usamos la fecha actual para evitar el error.
                if invoice_date_str == '' or invoice_date_str is None:
                    invoice_date = date.today().strftime('%Y-%m-%d')
                else:
                    invoice_date = invoice_date_str

                cur.execute("""
                    UPDATE invoices 
                    SET total = %s, method = %s, invoice_date = %s, reservation_id = %s
                    WHERE invoice_id = %s
                """, (data['total'], data['method'], invoice_date, data['reservation_id'], invoice_id))
                
                if cur.rowcount == 0:
                    return jsonify({"error": "Factura no encontrada"}), 404
                return jsonify({"message": "Factura actualizada"}), 200

            # DELETE: Eliminar factura
            if request.method == 'DELETE' and invoice_id is not None:
                # Opcional: Podrías querer cambiar el estado de la reserva asociada si se elimina la factura
                cur.execute("DELETE FROM invoices WHERE invoice_id = %s", (invoice_id,))
                
                if cur.rowcount == 0:
                    return jsonify({"error": "Factura no encontrada"}), 404
                return jsonify({"message": "Factura eliminada"}), 200
            
            # GET: Obtener una sola factura (si es necesario)
            if request.method == 'GET' and invoice_id is not None:
                cur.execute("SELECT * FROM invoices WHERE invoice_id = %s", (invoice_id,))
                invoice = cur.fetchone()
                if not invoice:
                    return jsonify({"error": "Factura no encontrada"}), 404
                return jsonify(invoice)

    except Exception as e:
        print(f"Error en manage_invoices: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()



# --- DASHBOARD METRICS ---
@app.route("/api/dashboard", methods=["GET"])
@require_role(['admin', 'recepcion'])
def api_dashboard():
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # 1. Reservas Activas (reservada, confirmada, checkin)
            cur.execute("SELECT COUNT(*) as count FROM reservations WHERE status IN ('reservada', 'confirmada', 'checkin')")
            active_reservations = cur.fetchone()['count']

            # 2. Total Ingresos (suma de facturas)
            cur.execute("SELECT SUM(total) as total FROM invoices")
            res_income = cur.fetchone()
            total_income = res_income['total'] if res_income['total'] else 0

            # 3. Total Clientes
            cur.execute("SELECT COUNT(*) as count FROM clients")
            total_clients = cur.fetchone()['count']

            # 4. Habitaciones (Total, Mantenimiento, Ocupadas, Disponibles)
            cur.execute("SELECT COUNT(*) as count FROM rooms")
            total_rooms = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM rooms WHERE status='mantenimiento'")
            maintenance_rooms = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM rooms WHERE status='ocupada'")
            occupied_rooms = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM rooms WHERE status='disponible'")
            available_rooms = cur.fetchone()['count']

            # 5. Ocupación %
            occupancy_rate = 0
            if total_rooms > 0:
                occupancy_rate = round((occupied_rooms / total_rooms) * 100, 1)

            return jsonify({
                "active_reservations": active_reservations,
                "total_income": total_income,
                "total_clients": total_clients,
                "occupancy_rate": occupancy_rate,
                "total_rooms": total_rooms,
                "maintenance_rooms": maintenance_rooms,
                "occupied_rooms": occupied_rooms,
                "available_rooms": available_rooms
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# NUEVO: Actualizar reserva de servicio (PUT)
@app.route("/api/reservation_services/<int:rs_id>", methods=["PUT"])
@require_role(['admin', 'recepcion', 'spa'])
def api_update_reservation_service(rs_id):
    data = request.json
    new_quantity = data.get('quantity')
    new_date = data.get('service_date')
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Obtener datos actuales
            cur.execute("SELECT reservation_id, quantity, unit_price FROM reservation_services WHERE reservation_service_id = %s", (rs_id,))
            current = cur.fetchone()
            if not current:
                return jsonify({"error": "Servicio de reserva no encontrado"}), 404
            
            res_id = current['reservation_id']
            unit_price = current['unit_price']
            old_quantity = current['quantity']
            
            # Calcular diferencia
            old_total = old_quantity * unit_price
            new_total = int(new_quantity) * unit_price
            diff = new_total - old_total
            
            # Actualizar servicio
            cur.execute("""
                UPDATE reservation_services 
                SET quantity = %s, service_date = %s 
                WHERE reservation_service_id = %s
            """, (new_quantity, new_date, rs_id))
            
            # Actualizar total reserva
            cur.execute("UPDATE reservations SET total = total + %s WHERE reservation_id = %s", (diff, res_id))
            
            return jsonify({"message": "Servicio actualizado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# NUEVO: Eliminar reserva de servicio (DELETE)
@app.route("/api/reservation_services/<int:rs_id>", methods=["DELETE"])
@require_role(['admin', 'recepcion', 'spa'])
def api_delete_reservation_service(rs_id):
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            # Obtener datos para restar total
            cur.execute("SELECT reservation_id, quantity, unit_price FROM reservation_services WHERE reservation_service_id = %s", (rs_id,))
            current = cur.fetchone()
            if not current:
                return jsonify({"error": "Servicio de reserva no encontrado"}), 404
            
            res_id = current['reservation_id']
            line_total = current['quantity'] * current['unit_price']
            
            # Eliminar
            cur.execute("DELETE FROM reservation_services WHERE reservation_service_id = %s", (rs_id,))
            
            # Actualizar total reserva
            cur.execute("UPDATE reservations SET total = total - %s WHERE reservation_id = %s", (line_total, res_id))
            
            return jsonify({"message": "Servicio eliminado de la reserva"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# --- ENDPOINTS ROL: CLIENTE ---
@app.route("/api/my_reservations", methods=["GET"])
@require_role(['cliente'])
def api_my_reservations():
    client_id = request.headers.get('X-Client-Id')
    if not client_id:
        return jsonify({"error": "Client ID missing"}), 400
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.reservation_id, r.reservation_code, r.checkin_date, r.checkout_date, 
                       r.total, r.status, ro.room_num, ro.room_type
                FROM reservations r
                JOIN rooms ro ON r.room_id = ro.room_id
                WHERE r.client_id = %s
                ORDER BY r.checkin_date DESC
            """, (client_id,))
            reservations = cur.fetchall()
            return jsonify(reservations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/my_reservation_services", methods=["GET"])
@require_role(['cliente'])
def api_my_reservation_services():
    client_id = request.headers.get('X-Client-Id')
    if not client_id:
        return jsonify({"error": "Client ID missing"}), 400
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rs.service_date, s.name as service_name, rs.quantity, rs.unit_price, 
                       (rs.quantity * rs.unit_price) as line_total, r.reservation_code
                FROM reservation_services rs
                JOIN reservations r ON rs.reservation_id = r.reservation_id
                JOIN services s ON rs.service_id = s.service_id
                WHERE r.client_id = %s
                ORDER BY rs.service_date DESC
            """, (client_id,))
            services = cur.fetchall()
            return jsonify(services)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route("/api/reservations/<int:res_id>/cancel", methods=["PUT"])
@require_role(['cliente', 'recepcion'])
def api_cancel_reservation(res_id):
    # Cliente solo puede cancelar si estado es 'reservada'
    # Recepcion puede cancelar en cualquier momento (aunque idealmente antes de checkout)
    role = request.headers.get('X-User-Role')
    
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT status, client_id FROM reservations WHERE reservation_id = %s", (res_id,))
            res = cur.fetchone()
            if not res:
                return jsonify({"error": "Reserva no encontrada"}), 404
            
            if role == 'cliente':
                # Verificar que la reserva pertenezca al cliente (seguridad adicional)
                client_id = request.headers.get('X-Client-Id')
                if str(res['client_id']) != str(client_id):
                     return jsonify({"error": "No autorizado"}), 403
                
                if res['status'] != 'reservada':
                    return jsonify({"error": "Solo se pueden cancelar reservas en estado 'reservada'."}), 400

            cur.execute("UPDATE reservations SET status = 'cancelada' WHERE reservation_id = %s", (res_id,))
            return jsonify({"message": "Reserva cancelada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# --- ENDPOINTS ROL: RECEPCION ---
@app.route("/api/reservations/daily_ops", methods=["GET"])
@require_role(['recepcion', 'admin'])
def api_daily_ops():
    # Reservas con checkin o checkout HOY (o rango cercano)
    today = date.today()
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.reservation_id, r.reservation_code, r.checkin_date, r.checkout_date, 
                       r.status, c.full_name as client_name, ro.room_num
                FROM reservations r
                JOIN clients c ON r.client_id = c.client_id
                JOIN rooms ro ON r.room_id = ro.room_id
                WHERE r.checkin_date = %s OR r.checkout_date = %s
                ORDER BY r.checkin_date ASC
            """, (today, today))
            ops = cur.fetchall()
            return jsonify(ops)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

# --- ENDPOINTS ROL: SPA ---
@app.route("/api/reservations/in_house", methods=["GET"])
@require_role(['spa', 'recepcion', 'admin'])
def api_in_house_guests():
    # Huéspedes activos (Check-in)
    search = request.args.get('q', '')
    conn = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            sql = """
                SELECT r.reservation_id, r.reservation_code, r.guest_name, ro.room_num,
                       r.checkin_date, r.checkout_date
                FROM reservations r
                JOIN rooms ro ON r.room_id = ro.room_id
                WHERE r.status IN ('checkin', 'ocupada')
            """
            params = []
            
            if search:
                sql += " AND (r.guest_name LIKE %s OR ro.room_num LIKE %s OR r.reservation_code LIKE %s)"
                params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
            
            sql += " ORDER BY ro.room_num ASC"
            
            cur.execute(sql, tuple(params))
            guests = cur.fetchall()
            return jsonify(guests)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
