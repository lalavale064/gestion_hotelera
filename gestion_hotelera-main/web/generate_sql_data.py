
import random
import datetime
import hashlib
import uuid

# --- CONFIGURATION ---
NUM_USERS = 50
NUM_CLIENTS = 200
NUM_STAFF = 20
NUM_RESERVATIONS = 800
OUTPUT_FILE = "populate_db.sql"

# --- HELPERS ---
def random_date(start_date, end_date):
    days_between = (end_date - start_date).days
    random_days = random.randrange(days_between)
    return start_date + datetime.timedelta(days=random_days)

def get_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def escape_sql(text):
    if text is None: return "NULL"
    return "'" + str(text).replace("'", "''") + "'"

# --- DATA POOLS ---
FIRST_NAMES = ["Juan", "Maria", "Pedro", "Ana", "Luis", "Carmen", "Jose", "Laura", "Carlos", "Sofia", "Miguel", "Elena", "David", "Isabel", "Jorge", "Lucia", "Fernando", "Marta", "Roberto", "Paula"]
LAST_NAMES = ["Garcia", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Reyes"]
DOMAINS = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "hotel.com"]

ROOM_TYPES = {
    'sencilla': {'cap': 2, 'price': 1200},
    'doble': {'cap': 4, 'price': 2200},
    'suite': {'cap': 6, 'price': 4500}
}

SERVICES_LIST = [
    ('SPA01', 'Masaje Relajante', 'Masaje de 60 min', 800),
    ('SPA02', 'Facial', 'Limpieza facial profunda', 600),
    ('ROOM01', 'Desayuno Americano', 'Huevos, tocino, cafe', 250),
    ('ROOM02', 'Cena Romantica', 'Cena para 2 en habitacion', 1500),
    ('TOUR01', 'Tour Ciudad', 'Recorrido turistico', 400),
    ('BAR01', 'Botella Vino', 'Vino tinto de la casa', 500),
    ('LAV01', 'Lavanderia', 'Servicio de lavanderia por bolsa', 150)
]

STAFF_ROLES = ['recepcion', 'camarista', 'supervisor', 'gerente', 'spa', 'mantenimiento']
USER_ROLES = ['admin', 'recepcion', 'spa', 'limpieza', 'cliente']

# --- GENERATOR ---
def generate():
    sql_statements = []
    sql_statements.append("USE gestion_hotelera;")
    sql_statements.append("SET FOREIGN_KEY_CHECKS = 0;") # Disable FK checks for bulk insert safety
    
    print("Generating Users...")
    users = []
    # Keep track of emails to ensure uniqueness
    existing_emails = set(['admin@hotel.com', 'recepcion@hotel.com', 'spa@hotel.com', 'cliente@hotel.com'])
    
    for i in range(NUM_USERS):
        while True:
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            email = f"{fname.lower()}.{lname.lower()}{random.randint(1,999)}@{random.choice(DOMAINS)}"
            if email not in existing_emails:
                existing_emails.add(email)
                break
        
        role = random.choice(USER_ROLES)
        password_hash = get_hash('1234') # Default password
        created_at = random_date(datetime.date(2023, 1, 1), datetime.date(2024, 1, 1))
        
        # user_id will be auto-increment in DB, but we need to reference it. 
        # Since we are generating SQL, we can't know the ID. 
        # Strategy: We will INSERT and assume IDs start after existing ones, or just use NULL for ID and let DB handle it.
        # But for Clients linked to Users, we need the ID.
        # SOLUTION: We will assume we are appending. But to be safe in SQL script, we can't easily link without variables.
        # However, for this request, I will generate INSERTs with specific IDs starting from a high number to avoid collision, 
        # OR I will just generate the data and let the user know that 'user_id' linking might be loose if they run it on existing DB.
        # BETTER: Use variables in SQL? No, too complex.
        # SIMPLEST: Start IDs from 1000.
        
        user_id = 1000 + i
        users.append({'id': user_id, 'email': email, 'role': role, 'name': f"{fname} {lname}"})
        
        sql_statements.append(f"INSERT INTO users (user_id, email, password_hash, user_role, created_at) VALUES ({user_id}, '{email}', '{password_hash}', '{role}', '{created_at}');")

    print("Generating Clients...")
    clients = []
    for i in range(NUM_CLIENTS):
        client_id = 1000 + i
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        full_name = f"{fname} {lname}"
        
        # Link to a user if available and role is cliente
        linked_user_id = "NULL"
        
        # Try to find a user to link
        if i < len(users) and users[i]['role'] == 'cliente':
             linked_user_id = users[i]['id']
             email = users[i]['email']
        else:
             email = f"{fname.lower()}.{lname.lower()}{random.randint(1000,9999)}@{random.choice(DOMAINS)}"

        phone = f"{random.randint(5500000000, 5599999999)}"
        address = f"Calle {random.randint(1, 100)}, Col. Centro"
        created_at = random_date(datetime.date(2023, 1, 1), datetime.date(2024, 1, 1))
        
        clients.append({'id': client_id, 'name': full_name, 'email': email})
        sql_statements.append(f"INSERT INTO clients (client_id, user_id, full_name, email, phone, address, created_at) VALUES ({client_id}, {linked_user_id}, '{full_name}', '{email}', '{phone}', '{address}', '{created_at}');")

    print("Generating Rooms...")
    rooms = []
    room_id_counter = 1000
    for floor in range(1, 6): # 5 floors
        for num in range(1, 11): # 10 rooms per floor
            room_num = floor * 100 + num
            r_type = random.choice(list(ROOM_TYPES.keys()))
            capacity = ROOM_TYPES[r_type]['cap']
            price = ROOM_TYPES[r_type]['price']
            status = random.choice(['disponible', 'disponible', 'disponible', 'ocupada', 'mantenimiento']) # Weighted
            
            rooms.append({'id': room_id_counter, 'num': room_num, 'price': price, 'type': r_type})
            sql_statements.append(f"INSERT INTO rooms (room_id, room_num, room_type, capacity, price, status, created_at) VALUES ({room_id_counter}, {room_num}, '{r_type}', {capacity}, {price}, '{status}', NOW());")
            room_id_counter += 1

    print("Generating Staff...")
    for i in range(NUM_STAFF):
        staff_id = 1000 + i
        fname = random.choice(FIRST_NAMES)
        lname = random.choice(LAST_NAMES)
        role = random.choice(STAFF_ROLES)
        area = "General"
        if role == 'recepcion': area = "Front Desk"
        elif role == 'spa': area = "Wellness"
        elif role == 'mantenimiento': area = "Facilities"
        
        hire_date = random_date(datetime.date(2020, 1, 1), datetime.date(2024, 1, 1))
        active = 1 if random.random() > 0.1 else 0
        
        sql_statements.append(f"INSERT INTO staff (staff_id, full_name, staff_role, area, hire_date, active, created_at) VALUES ({staff_id}, '{fname} {lname}', '{role}', '{area}', '{hire_date}', {active}, NOW());")

    print("Generating Services...")
    services = []
    for i, s in enumerate(SERVICES_LIST):
        sid = 1000 + i
        services.append({'id': sid, 'price': s[3]})
        sql_statements.append(f"INSERT INTO services (service_id, service_code, name, description, price, status, created_at) VALUES ({sid}, '{s[0]}', '{s[1]}', '{s[2]}', {s[3]}, 'activo', NOW());")

    print("Generating Reservations...")
    # Logic to avoid overlaps: Dictionary mapping room_id -> list of (start, end)
    room_occupancy = {r['id']: [] for r in rooms}
    
    today = datetime.date.today()
    
    for i in range(NUM_RESERVATIONS):
        res_id = 1000 + i
        client = random.choice(clients)
        room = random.choice(rooms)
        
        # Find a valid date slot
        attempts = 0
        while attempts < 50:
            start_date = random_date(datetime.date(2024, 1, 1), datetime.date(2025, 6, 1))
            duration = random.randint(1, 7)
            end_date = start_date + datetime.timedelta(days=duration)
            
            # Check overlap
            overlap = False
            for booked_start, booked_end in room_occupancy[room['id']]:
                if not (end_date <= booked_start or start_date >= booked_end):
                    overlap = True
                    break
            
            if not overlap:
                room_occupancy[room['id']].append((start_date, end_date))
                break
            attempts += 1
            
        if attempts >= 50: continue # Skip if can't find slot
        
        # Determine status
        if end_date < today:
            status = 'checkout'
            # Randomly facturada
            if random.random() > 0.2: status = 'facturada'
        elif start_date <= today <= end_date:
            status = 'checkin'
        else:
            status = 'confirmada'
            if random.random() > 0.8: status = 'reservada'
            
        if random.random() < 0.05: status = 'cancelada'

        total_room = room['price'] * duration
        res_code = f"R-{uuid.uuid4().hex[:8].upper()}"
        
        sql_statements.append(f"INSERT INTO reservations (reservation_id, reservation_code, client_id, room_id, guest_name, guest_email, guest_phone, checkin_date, checkout_date, total, status, created_at) VALUES ({res_id}, '{res_code}', {client['id']}, {room['id']}, '{client['name']}', '{client['email']}', '55{random.randint(10000000,99999999)}', '{start_date}', '{end_date}', {total_room}, '{status}', NOW());")
        
        # Services
        total_services = 0
        if status not in ['cancelada', 'reservada']:
            num_srv = random.randint(0, 5)
            for _ in range(num_srv):
                srv = random.choice(services)
                qty = random.randint(1, 3)
                srv_date = random_date(start_date, end_date)
                srv_price = srv['price']
                line_total = srv_price * qty
                total_services += line_total
                
                sql_statements.append(f"INSERT INTO reservation_services (reservation_id, service_id, quantity, unit_price, added_at, service_date) VALUES ({res_id}, {srv['id']}, {qty}, {srv_price}, '{srv_date} 10:00:00', '{srv_date}');")

        # Invoice
        if status == 'facturada':
            inv_code = f"I-{uuid.uuid4().hex[:8].upper()}"
            final_total = total_room + total_services
            method = random.choice(['efectivo', 'tarjeta', 'transferencia'])
            inv_date = end_date
            
            sql_statements.append(f"INSERT INTO invoices (invoice_code, reservation_id, total, method, invoice_date, created_at) VALUES ('{inv_code}', {res_id}, {final_total}, '{method}', '{inv_date}', NOW());")

    sql_statements.append("SET FOREIGN_KEY_CHECKS = 1;")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))
    
    print(f"Done! Generated {len(sql_statements)} statements in {OUTPUT_FILE}")

if __name__ == "__main__":
    generate()
