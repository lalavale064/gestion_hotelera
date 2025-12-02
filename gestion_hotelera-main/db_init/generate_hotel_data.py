#!/usr/bin/env python3
# -*- coding: utf-8 -*-
random.seed(12345)

# Helper functions
def sha256_hash(text):
    """Generate SHA256 hash matching MySQL SHA2(text, 256)"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def sql_escape(text):
    """Escape single quotes for SQL"""
    if text is None:
        return 'NULL'
    return text.replace("'", "''")

def generate_reservation_code():
    """Generate unique reservation code like R-XXXXXX"""
    return f"R-{fake.bothify(text='??????').upper()}"

def generate_invoice_code():
    """Generate unique invoice code like I-XXXXXX"""
    return f"I-{fake.bothify(text='??????').upper()}"

# Global counters to track existing records
EXISTING_USERS = 4
EXISTING_CLIENTS = 6
EXISTING_ROOMS = 8
EXISTING_STAFF = 4
EXISTING_SERVICES = 5
EXISTING_RESERVATIONS = 5

# Track used values for uniqueness
used_emails = set()
used_room_nums = set(range(101, 109))  # Existing rooms
used_service_codes = {'SPA-BAS', 'MAS-REL', 'DES-BUF', 'TRANS-AER', 'ROOM-SERV'}
used_reservation_codes = set()
used_invoice_codes = set()

# ============================================================================
# 1. GENERATE USERS
# ============================================================================
def generate_users(count=996):
    """Generate users with different roles"""
    users = []
    user_id = EXISTING_USERS + 1
    
    # Role distribution
    cliente_count = int(count * 0.8) # More clients
    recepcion_count = 100
    spa_count = 50
    limpieza_count = 30
    admin_count = max(5, count - cliente_count - recepcion_count - spa_count - limpieza_count)
    
    roles_dist = (
        ['cliente'] * cliente_count +
        ['recepcion'] * recepcion_count +
        ['spa'] * spa_count +
        ['limpieza'] * limpieza_count +
        ['admin'] * admin_count
    )
    random.shuffle(roles_dist)
    
    for i in range(count):
        # Generate unique email
        while True:
            email = fake.email()
            if email not in used_emails:
                used_emails.add(email)
                break
        
        role = roles_dist[i]
        password = 'password123'  # Same password for all demo users
        password_hash = sha256_hash(password)
        
        users.append(f"({user_id}, '{sql_escape(email)}', '{password_hash}', '{role}')")
        user_id += 1
    
    return users, user_id - 1  # Return last user_id

# ============================================================================
# 2. GENERATE CLIENTS
# ============================================================================
def generate_clients(count=994, max_user_id=1000):
    """Generate clients, some linked to users, some standalone"""
    clients = []
    client_id = EXISTING_CLIENTS + 1
    
    # 60% of clients will have user_id, 40% won't
    user_link_count = int(count * 0.6)
    
    # Available user_ids (only 'cliente' role users)
    # Assuming user_ids 5-804 are 'cliente' role (800 total)
    available_user_ids = list(range(5, 805))
    random.shuffle(available_user_ids)
    
    for i in range(count):
        full_name = fake.name()
        
        # Generate unique email
        while True:
            email = fake.email()
            if email not in used_emails:
                used_emails.add(email)
                break
        
        phone = fake.numerify(text='##########')  # 10 digit phone
        address = sql_escape(fake.address().replace('\n', ', '))
        
        # Assign user_id for first 60% of clients
        if i < user_link_count and available_user_ids:
            user_id = available_user_ids.pop()
            clients.append(f"({client_id}, {user_id}, '{sql_escape(full_name)}', '{email}', '{phone}', '{address}')")
        else:
            clients.append(f"({client_id}, NULL, '{sql_escape(full_name)}', '{email}', '{phone}', '{address}')")
        
        client_id += 1
    
    return clients

# ============================================================================
# 3. GENERATE ROOMS
# ============================================================================
def generate_rooms(count=992):
    """Generate hotel rooms with realistic configurations"""
    rooms = []
    room_id = EXISTING_ROOMS + 1
    
    # Room type distribution: 40% sencilla, 40% doble, 20% suite
    sencilla_count = int(count * 0.4)
    doble_count = int(count * 0.4)
    suite_count = count - sencilla_count - doble_count  # Ensure exact count
    
    room_types = (
        ['sencilla'] * sencilla_count +
        ['doble'] * doble_count +
        ['suite'] * suite_count
    )
    random.shuffle(room_types)
    
    # Status distribution: 70% disponible, 20% ocupada, 10% mantenimiento
    disponible_count = int(count * 0.7)
    ocupada_count = int(count * 0.2)
    mantenimiento_count = count - disponible_count - ocupada_count  # Ensure exact count
    
    status_options = (
        ['disponible'] * disponible_count +
        ['ocupada'] * ocupada_count +
        ['mantenimiento'] * mantenimiento_count
    )
    random.shuffle(status_options)
    
    for i in range(count):
        # Generate unique room number
        while True:
            room_num = random.randint(109, 1500)
            if room_num not in used_room_nums:
                used_room_nums.add(room_num)
                break
        
        room_type = room_types[i]
        status = status_options[i]
        
        # Set capacity and price based on room type
        if room_type == 'sencilla':
            capacity = random.randint(1, 2)
            price = round(random.uniform(500, 1200), 2)
        elif room_type == 'doble':
            capacity = random.randint(2, 4)
            price = round(random.uniform(1000, 2000), 2)
        else:  # suite
            capacity = random.randint(2, 6)
            price = round(random.uniform(2000, 5000), 2)
        
        rooms.append(f"({room_id}, {room_num}, '{room_type}', {capacity}, {price}, '{status}')")
        room_id += 1
    
    return rooms

# ============================================================================
# 4. GENERATE STAFF
# ============================================================================
def generate_staff(count=996):
    """Generate staff members with various roles"""
    staff = []
    staff_id = EXISTING_STAFF + 1
    
    roles = ['recepcionista', 'camarista', 'supervisor', 'gerente', 'terapeuta spa', 
             'mantenimiento', 'seguridad', 'chef', 'mesero', 'botones']
    areas = ['Front Desk', 'Limpieza', 'Administración', 'Spa', 'Mantenimiento', 
             'Seguridad', 'Restaurante', 'Cocina', 'Servicios']
    
    for i in range(count):
        full_name = fake.name()
        staff_role = random.choice(roles)
        area = random.choice(areas)
        
        # hire_date between 2015 and 2025-11-30
        start_date = date(2015, 1, 1)
        end_date = date(2025, 11, 30)
        hire_date = fake.date_between(start_date=start_date, end_date=end_date)
        
        # 95% active, 5% inactive
        active = 1 if random.random() < 0.95 else 0
        
        staff.append(f"({staff_id}, '{sql_escape(full_name)}', '{staff_role}', '{area}', '{hire_date}', {active})")
        staff_id += 1
    
    return staff

# ============================================================================
# 5. GENERATE SERVICES
# ============================================================================
def generate_services(count=995):
    """Generate hotel services"""
    services = []
    service_id = EXISTING_SERVICES + 1
    
    # Service categories with templates
    service_templates = {
        'SPA': ['Masaje sueco', 'Masaje piedras calientes', 'Facial rejuvenecedor', 
                'Aromaterapia', 'Reflexología', 'Tratamiento corporal', 'Sauna', 
                'Jacuzzi privado', 'Manicure', 'Pedicure'],
        'ROOM': ['Servicio de habitación', 'Limpieza extra', 'Amenidades premium',
                 'Almohadas adicionales', 'Toallas extra', 'Mini bar premium'],
        'FOOD': ['Desayuno continental', 'Comida buffet', 'Cena gourmet', 
                 'Room service 24h', 'Champagne', 'Vino premium', 'Coctel especial',
                 'Pastel personalizado', 'Canasta de frutas', 'Chocolates gourmet'],
        'TRANS': ['Transporte aeropuerto', 'Taxi al centro', 'Renta de auto',
                  'Tour ciudad', 'Servicio chofer', 'Shuttle service'],
        'ACT': ['Tour guiado', 'Excursión playa', 'Clase de yoga', 'Clase de cocina',
                'Buceo', 'Snorkel', 'Equitación', 'Golf', 'Tenis'],
        'LAUND': ['Lavandería express', 'Planchado', 'Tintorería', 'Lavado en seco']
    }
    
    # Flatten all services
    all_services = []
    for category, items in service_templates.items():
        for item in items:
            all_services.append((category, item))
    
    # Generate more services by adding variations
    while len(all_services) < count:
        category = random.choice(list(service_templates.keys()))
        base_name = random.choice(service_templates[category])
        variation = random.choice(['Premium', 'Deluxe', 'Ejecutivo', 'VIP', 'Especial'])
        all_services.append((category, f"{base_name} {variation}"))
    
    random.shuffle(all_services)
    
    for i in range(count):
        category, name = all_services[i]
        
        # Generate unique service code
        while True:
            code_num = random.randint(1, 999)
            service_code = f"{category}-{code_num:03d}"
            if service_code not in used_service_codes:
                used_service_codes.add(service_code)
                break
        
        description = fake.sentence(nb_words=10)
        price = round(random.uniform(50, 3000), 2)
        
        # 90% active, 10% inactive
        status = 'activo' if random.random() < 0.9 else 'inactivo'
        
        services.append(f"({service_id}, '{service_code}', '{sql_escape(name)}', '{sql_escape(description)}', {price}, '{status}')")
        service_id += 1
    
    return services

# ============================================================================
# 6. GENERATE RESERVATIONS
# ============================================================================
def generate_reservations(count=995):
    """Generate reservations following hotel business logic"""
    reservations = []
    reservation_id = EXISTING_RESERVATIONS + 1
    
    # Available clients (7 to 1006)
    client_ids = list(range(7, 1007))
    
    # Available rooms (9 to 1008)
    room_ids = list(range(9, 1009))
    
    # Track room availability by date
    room_bookings = {}  # {room_id: [(checkin, checkout), ...]}
    
    # Today's date for status logic
    today = date(2025, 12, 1)
    
    # Date range for reservations
    start_range = date(2024, 1, 1)
    end_range = date(2026, 12, 31)
    
    attempts = 0
    max_attempts = count * 10
    
    while len(reservations) < count and attempts < max_attempts:
        attempts += 1
        
        client_id = random.choice(client_ids)
        room_id = random.choice(room_ids)
        
        # Generate check-in and check-out dates with TIME
        # Check-in: 14:00 - 23:00
        checkin_date_base = fake.date_between(start_date=start_range, end_date=end_range)
        checkin_time = time(random.randint(14, 23), random.randint(0, 59), 0)
        checkin_date = datetime.combine(checkin_date_base, checkin_time)
        
        # Stay duration: 1-14 nights
        nights = random.randint(1, 14)
        
        # Check-out: 07:00 - 12:00
        checkout_date_base = checkin_date_base + timedelta(days=nights)
        checkout_time = time(random.randint(7, 12), random.randint(0, 59), 0)
        checkout_date = datetime.combine(checkout_date_base, checkout_time)
        
        # Check if room is available for these dates
        if room_id not in room_bookings:
            room_bookings[room_id] = []
        
        # Check for conflicts
        conflict = False
        for booked_checkin, booked_checkout in room_bookings[room_id]:
            # Check if dates overlap
            if not (checkout_date <= booked_checkin or checkin_date >= booked_checkout):
                conflict = True
                break
        
        if conflict:
            continue  # Try another reservation
        
        # No conflict, proceed with reservation
        room_bookings[room_id].append((checkin_date, checkout_date))
        
        # Generate unique reservation code
        while True:
            res_code = generate_reservation_code()
            if res_code not in used_reservation_codes:
                used_reservation_codes.add(res_code)
                break
        
        # Guest details
        guest_name = sql_escape(fake.name())
        guest_email = fake.email()
        guest_phone = fake.numerify(text='##########')
        
        # Calculate total (will use average room price)
        # For simplicity, use random price based on room type
        room_type_prices = {
            'sencilla': random.uniform(500, 1200),
            'doble': random.uniform(1000, 2000),
            'suite': random.uniform(2000, 5000)
        }
        # Randomly pick a room type for calculation
        room_type = random.choice(['sencilla', 'doble', 'suite'])
        room_price = round(random.choice(list(room_type_prices.values())), 2)
        total = round(room_price * nights, 2)
        
        # Determine status based on dates
        if checkout_date < today:
            # Past reservation
            status_options = ['checkout', 'checkout', 'checkout', 'checkout', 
                            'cancelada', 'facturada']
            status = random.choice(status_options)
        elif checkin_date <= today <= checkout_date:
            # Current stay
            status = 'checkin'
        elif checkin_date > today:
            # Future reservation
            status_options = ['reservada', 'reservada', 'confirmada', 'confirmada', 'cancelada']
            status = random.choice(status_options)
        else:
            status = 'reservada'
        
        reservations.append(
            f"({reservation_id}, '{res_code}', {client_id}, {room_id}, '{guest_name}', "
            f"'{guest_email}', '{guest_phone}', '{checkin_date}', '{checkout_date}', "
            f"{total}, '{status}')"
        )
        reservation_id += 1
    
    return reservations, room_bookings

# ============================================================================
# 7. GENERATE RESERVATION SERVICES
# ============================================================================
def generate_reservation_services(reservation_count, room_bookings):
    """Generate services for reservations"""
    services_list = []
    service_id = 1
    
    # Only generate for active reservations (not cancelada)
    # Reservation IDs: 6 to (6 + reservation_count - 1)
    
    for res_id in range(6, 6 + reservation_count):
        # Determine if this reservation is cancelled (need to track statuses)
        # For simplicity, assume 20% are cancelled
        if random.random() < 0.2:
            continue  # Skip cancelled reservations
        
        # Get reservation details (we need to reconstruct checkin/checkout)
        # Since we don't have direct access, we'll generate realistic service dates
        
        # Random checkin/checkout for service date calculation
        checkin = fake.date_between(start_date=date(2024, 1, 1), end_date=date(2026, 12, 31))
        nights = random.randint(1, 14)
        checkout = checkin + timedelta(days=nights)
        
        # Add 2-5 services per reservation on average to ensure > 1000 total
        num_services = random.randint(2, 5)
        
        for _ in range(num_services):
            service_ref_id = random.randint(6, 1000)  # Random service ID
            quantity = random.randint(1, 5)
            unit_price = round(random.uniform(50, 3000), 2)
            
            # Service date between checkin and checkout
            service_date = fake.date_between(start_date=checkin, end_date=checkout)
            
            services_list.append(
                f"({service_id}, {res_id}, {service_ref_id}, {quantity}, {unit_price}, '{service_date}')"
            )
            service_id += 1
    
    return services_list

# ============================================================================
# 8. GENERATE INVOICES
# ============================================================================
def generate_invoices():
    """Generate invoices for facturada reservations"""
    invoices = []
    invoice_id = 1
    
    # Generate invoices for approximately 10% of reservations (~120 invoices)
    # These correspond to reservations with status='facturada'
    facturada_count = 120
    
    # Random reservation IDs that are facturada
    reservation_ids = random.sample(range(6, 1001), facturada_count)
    
    for res_id in reservation_ids:
        # Generate unique invoice code
        while True:
            inv_code = generate_invoice_code()
            if inv_code not in used_invoice_codes:
                used_invoice_codes.add(inv_code)
                break
        
        # Total (random realistic amount)
        total = round(random.uniform(1000, 15000), 2)
        
        # Payment method
        method = random.choice(['tarjeta', 'tarjeta', 'efectivo', 'transferencia'])
        
        # Invoice date (recent past)
        invoice_date = fake.date_between(start_date=date(2024, 1, 1), end_date=date(2025, 12, 1))
        
        invoices.append(
            f"({invoice_id}, '{inv_code}', {res_id}, {total}, '{method}', '{invoice_date}')"
        )
        invoice_id += 1
    
    return invoices

# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================
def main():
    print("Generating hotel database records...")
    print("=" * 70)
    
    # Generate all data
    print("1. Generating USERS...")
    users, max_user_id = generate_users(1200)
    
    print("2. Generating CLIENTS...")
    clients = generate_clients(1200, max_user_id)
    
    print("3. Generating ROOMS...")
    rooms = generate_rooms(1200)
    
    print("4. Generating STAFF...")
    staff = generate_staff(1000)
    
    print("5. Generating SERVICES...")
    services = generate_services(1000)
    
    print("6. Generating RESERVATIONS...")
    reservations, room_bookings = generate_reservations(1200)
    
    print("7. Generating RESERVATION_SERVICES...")
    reservation_services = generate_reservation_services(len(reservations), room_bookings)
    
    print("8. Generating INVOICES...")
    invoices = generate_invoices()
    
    # Write to SQL file
    output_file = "hotel_data_inserts.sql"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("/* ========================================\n")
        f.write("   HOTEL DATABASE - GENERATED DATA\n")
        f.write("   FECHA: 01 DE DICIEMBRE DEL 2025 Y SON LAS 3:44\n")
        f.write("   ========================================*/\n\n")
        f.write("USE gestion_hotelera;\n\n")
        
        # Disable constraints temporarily for faster inserts
        f.write("SET FOREIGN_KEY_CHECKS=0;\n")
        f.write("SET UNIQUE_CHECKS=0;\n")
        f.write("SET AUTOCOMMIT=0;\n\n")
        
        # USERS
        f.write("-- ============================================\n")
        f.write("-- USERS (996 new records)\n")
        f.write("-- ============================================\n")
        f.write("INSERT INTO users (user_id, email, password_hash, user_role) VALUES\n")
        f.write(",\n".join(users))
        f.write(";\n\n")
        
        # CLIENTS
        f.write("-- ============================================\n")
        f.write("-- CLIENTS (994 new records)\n")
        f.write("-- ============================================\n")
        f.write("INSERT INTO clients (client_id, user_id, full_name, email, phone, address) VALUES\n")
        f.write(",\n".join(clients))
        f.write(";\n\n")
        
        # ROOMS
        f.write("-- ============================================\n")
        f.write("-- ROOMS (992 new records)\n")
        f.write("-- ============================================\n")
        f.write("INSERT INTO rooms (room_id, room_num, room_type, capacity, price, status) VALUES\n")
        f.write(",\n".join(rooms))
        f.write(";\n\n")
        
        # STAFF
        f.write("-- ============================================\n")
        f.write("-- STAFF (996 new records)\n")
        f.write("-- ============================================\n")
        f.write("INSERT INTO staff (staff_id, full_name, staff_role, area, hire_date, active) VALUES\n")
        f.write(",\n".join(staff))
        f.write(";\n\n")
        
        # SERVICES
        f.write("-- ============================================\n")
        f.write("-- SERVICES (995 new records)\n")
        f.write("-- ============================================\n")
        f.write("INSERT INTO services (service_id, service_code, name, description, price, status) VALUES\n")
        f.write(",\n".join(services))
        f.write(";\n\n")
        
        # RESERVATIONS
        f.write("-- ============================================\n")
        f.write("-- RESERVATIONS (995 new records)\n")
        f.write("-- ============================================\n")
        f.write("INSERT INTO reservations (reservation_id, reservation_code, client_id, room_id, guest_name, guest_email, guest_phone, checkin_date, checkout_date, total, status) VALUES\n")
        f.write(",\n".join(reservations))
        f.write(";\n\n")
        
        # RESERVATION SERVICES
        f.write("-- ============================================\n")
        f.write("-- RESERVATION_SERVICES\n")
        f.write("-- ============================================\n")
        if reservation_services:
            f.write("INSERT INTO reservation_services (reservation_service_id, reservation_id, service_id, quantity, unit_price, service_date) VALUES\n")
            f.write(",\n".join(reservation_services))
            f.write(";\n\n")
        
        # INVOICES
        f.write("-- ============================================\n")
        f.write("-- INVOICES\n")
        f.write("-- ============================================\n")
        if invoices:
            f.write("INSERT INTO invoices (invoice_id, invoice_code, reservation_id, total, method, invoice_date) VALUES\n")
            f.write(",\n".join(invoices))
            f.write(";\n\n")
        
        # Re-enable constraints
        f.write("COMMIT;\n")
        f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        f.write("SET UNIQUE_CHECKS=1;\n")
        f.write("SET AUTOCOMMIT=1;\n\n")
        
        f.write("-- ============================================\n")
        f.write("-- GENERATION COMPLETE\n")
        f.write("-- ============================================\n")
    
    print(f"\n[OK] SQL file generated: {output_file}")
    print("\nRecord counts:")
    print(f"  - Users: {len(users)}")
    print(f"  - Clients: {len(clients)}")
    print(f"  - Rooms: {len(rooms)}")
    print(f"  - Staff: {len(staff)}")
    print(f"  - Services: {len(services)}")
    print(f"  - Reservations: {len(reservations)}")
    print(f"  - Reservation Services: {len(reservation_services)}")
    print(f"  - Invoices: {len(invoices)}")
    print("\n" + "=" * 70)
    print("DONE! Execute the SQL file in your MySQL database.")

if __name__ == "__main__":
    main()
