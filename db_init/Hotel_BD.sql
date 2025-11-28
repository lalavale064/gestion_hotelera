/* =========================================================
   BASE DE DATOS: GESTIÓN HOTELERA (OPTIMIZADA)
   ========================================================= */

DROP DATABASE IF EXISTS gestion_hotelera;
CREATE DATABASE gestion_hotelera DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
USE gestion_hotelera;

/* 1. USUARIOS */
CREATE TABLE users (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  user_role VARCHAR(20) NOT NULL DEFAULT 'cliente',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_email (email)
) ENGINE=InnoDB;

/* 2. CLIENTES */
CREATE TABLE clients (
  client_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NULL,
  full_name VARCHAR(120) NOT NULL,
  email VARCHAR(120) NULL,
  phone VARCHAR(40) NULL,
  address VARCHAR(200) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_clients_users FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
  CONSTRAINT chk_client_email CHECK (email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),
  CONSTRAINT chk_client_phone CHECK (phone REGEXP '^[0-9]+$'),
  INDEX idx_client_name (full_name),
  INDEX idx_client_email (email)
) ENGINE=InnoDB;

/* 3. HABITACIONES */
CREATE TABLE rooms (
  room_id INT AUTO_INCREMENT PRIMARY KEY,
  room_num INT NOT NULL UNIQUE,
  room_type ENUM('sencilla','doble','suite') NOT NULL,
  capacity INT NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  status ENUM('disponible','ocupada','mantenimiento') NOT NULL DEFAULT 'disponible',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_room_status (status),
  INDEX idx_room_type (room_type)
) ENGINE=InnoDB;

/* 4. STAFF */
CREATE TABLE staff (
  staff_id INT AUTO_INCREMENT PRIMARY KEY,
  full_name VARCHAR(120) NOT NULL,
  staff_role VARCHAR(80) NOT NULL,
  area VARCHAR(80) NULL,
  hire_date DATE NOT NULL,
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_staff_name (full_name)
) ENGINE=InnoDB;

/* 5. SERVICIOS */
CREATE TABLE services (
  service_id INT AUTO_INCREMENT PRIMARY KEY,
  service_code VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(120) NOT NULL,
  description TEXT NULL,
  price DECIMAL(10,2) NOT NULL,
  status ENUM('activo','inactivo') NOT NULL DEFAULT 'activo',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

/* 6. RESERVAS */
CREATE TABLE reservations (
  reservation_id INT AUTO_INCREMENT PRIMARY KEY,
  reservation_code VARCHAR(20) UNIQUE,
  client_id INT NOT NULL,
  room_id INT NOT NULL,
  guest_name VARCHAR(120) NOT NULL,
  guest_email VARCHAR(120) NULL,
  guest_phone VARCHAR(40) NULL,
  checkin_date DATE NOT NULL,
  checkout_date DATE NOT NULL,
  total DECIMAL(10,2) NOT NULL DEFAULT 0,
  status ENUM('reservada','confirmada','checkin','checkout','cancelada','facturada') NOT NULL DEFAULT 'reservada',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_reservations_clients FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
  CONSTRAINT fk_reservations_rooms FOREIGN KEY (room_id) REFERENCES rooms(room_id),
  CONSTRAINT chk_guest_email CHECK (guest_email IS NULL OR guest_email REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),
  CONSTRAINT chk_guest_phone CHECK (guest_phone IS NULL OR guest_phone REGEXP '^[0-9]+$'),
  INDEX idx_res_dates (checkin_date, checkout_date),
  INDEX idx_res_status (status),
  INDEX idx_guest_name (guest_name)
) ENGINE=InnoDB;

/* Trigger para generar reservation_code automáticamente 
DELIMITER $$
CREATE TRIGGER trg_reservation_code 
BEFORE INSERT ON reservations
FOR EACH ROW 
BEGIN
    IF NEW.reservation_code IS NULL OR NEW.reservation_code = '' THEN
        SET NEW.reservation_code = CONCAT('R-', SUBSTRING(UUID(), 1, 8));
    END IF;
END$$
DELIMITER ; */

/* 7. SERVICIOS RESERVA */
CREATE TABLE reservation_services (
  reservation_service_id INT AUTO_INCREMENT PRIMARY KEY,
  reservation_id INT NOT NULL,
  service_id INT NOT NULL,
  quantity INT NOT NULL DEFAULT 1,
  unit_price DECIMAL(10,2) NOT NULL,
  added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_rs_reservation FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE,
  CONSTRAINT fk_rs_service FOREIGN KEY (service_id) REFERENCES services(service_id)
) ENGINE=InnoDB;

/* 8. FACTURAS */
CREATE TABLE invoices (
  invoice_id INT AUTO_INCREMENT PRIMARY KEY,
  invoice_code VARCHAR(20) UNIQUE,
  reservation_id INT NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  method ENUM('efectivo','tarjeta','transferencia') NOT NULL,
  invoice_date DATE NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_invoices_reservation FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE
) ENGINE=InnoDB;

/* =========================================================
   Añadir columna service_date a reservation_services sólo si no existe
   (compatible incluso con versiones de MariaDB que no soporten
   "ADD COLUMN IF NOT EXISTS")
   ========================================================= */

SET @schema_name = DATABASE();
SET @table_name  = 'reservation_services';
SET @column_name = 'service_date';

SELECT COUNT(*) INTO @col_count
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = @schema_name
  AND TABLE_NAME = @table_name
  AND COLUMN_NAME = @column_name;

SET @sql_stmt = IF(@col_count = 0,
    CONCAT('ALTER TABLE ', @table_name, ' ADD COLUMN ', @column_name, ' DATE'),
    CONCAT('SELECT ''Column ', @column_name, ' already exists in ', @table_name, ''''));

PREPARE alter_stmt FROM @sql_stmt;
EXECUTE alter_stmt;
DEALLOCATE PREPARE alter_stmt;

/* =========================================================
   DATOS SEMILLA CORREGIDOS PARA EL ESQUEMA OPTIMIZADO
   ========================================================= */

/* 1. USUARIOS (Se asume que los primeros 3 ya tienen IDs 1, 2 y 3) */
INSERT INTO users (email, password_hash, user_role) VALUES
('admin@hotel.com', SHA2('admin',256), 'admin'),
('recepcion@hotel.com', SHA2('recepcion',256), 'recepcion'),
('spa@hotel.com', SHA2('spa',256), 'spa');

/* 2. CLIENTES */

-- Cliente vinculado al usuario cliente (ID 4)
INSERT INTO users (email, password_hash, user_role) VALUES
('cliente@hotel.com', SHA2('cliente',256), 'cliente');

-- Cliente (ID 1) vinculado al usuario 'cliente@hotel.com' (ID 4)
INSERT INTO clients (user_id, full_name, email) VALUES
(4, 'Cliente Prueba', 'cliente@hotel.com');

-- Clientes adicionales (IDs 2, 3, 4, 5, 6)
INSERT INTO clients (full_name, email, phone, address) VALUES
('Ana Reséndiz', 'ana@example.com', '5544332211', 'Calle Falsa 123'),
('Luis Pérez', 'luisp@example.com', '5511223344', 'Av. Central 50'),
('María Gómez', 'maria.g@example.com', '5566778899', 'Blvd. Sur 88'),
('Carlos Ruiz', 'carlosr@example.com', '5588997766', 'Paseo del Sol 45'),
('Valeria Hernández', 'valeria.h@example.com', '5522446688', 'Reforma 10');


/* 3. HABITACIONES (Usamos IDs correlativos 1, 2, 3, 4, 5, 6, 7, 8) */

-- Primer set de habitaciones (IDs 1, 2, 3)
INSERT INTO rooms (room_num, room_type, capacity, price) VALUES 
(101, 'sencilla', 1, 50.00),
(102, 'doble', 2, 80.00),
(103, 'suite', 4, 150.00);

-- Segundo set de habitaciones (IDs 4, 5, 6, 7, 8). Se corrigen ENUMS a minúsculas.
INSERT INTO rooms (room_num, room_type, price, status, capacity) VALUES
(201, 'sencilla', 70.00, 'disponible', 2),
(202, 'doble', 100.00, 'disponible', 3),
(301, 'suite', 180.00, 'ocupada', 4),
(302, 'sencilla', 75.00, 'mantenimiento', 2),
(401, 'suite', 200.00, 'disponible', 5);


/* 4. STAFF (Personal para el rol 'spa' y otros) */
INSERT INTO staff (full_name, staff_role, area, hire_date) VALUES
('Ana Lópea', 'Recepcionista', 'Front Desk', '2022-08-10'),
('Roberto Flores', 'Limpieza', 'Mantenimiento', '2023-01-20'),
('Elena Díaz', 'Gerente', 'Administración', '2021-05-01'),
('Javier Maza', 'Terapeuta', 'Spa', '2023-11-15');


/* 5. SERVICIOS. Se corrige el nombre de la columna a 'name' y se añaden 'service_code'. */
INSERT INTO services (service_code, name, price) VALUES
('SPA-BAS', 'Spa básico', 50.00),
('MAS-REL', 'Masaje relajante', 120.00),
('DES-BUF', 'Desayuno buffet', 30.00),
('TRANS-AER', 'Transporte al aeropuerto', 80.00),
('ROOM-SERV', 'Servicio al cuarto', 15.00);


/* 6. RESERVAS. Se añaden las columnas 'guest_name', 'guest_email' y se corrigen los ENUMS.
   Se asume que los IDs de clientes son 1, 2, 3, 4, 5, 6 y los IDs de habitaciones son 1, 2, 3, 4, 5. */
INSERT INTO reservations (client_id, room_id, guest_name, guest_email, checkin_date, checkout_date, total, status) VALUES
-- Res ID 1: Cliente 2 (Ana), Hab 1 (101, $50) -> 2 noches * 50 = 100
(2, 1, 'Ana Reséndiz', 'ana@example.com', '2025-01-10', '2025-01-12', 100.00, 'facturada'), 

-- Res ID 2: Cliente 3 (Luis), Hab 2 (102, $80) -> 2 noches * 80 = 160
(3, 2, 'Luis Pérez', 'luisp@example.com', '2025-02-05', '2025-02-07', 160.00, 'checkin'), 

-- Res ID 3: Cliente 4 (María), Hab 3 (103, $150) -> 4 noches * 150 = 600
(4, 3, 'María Gómez', 'maria.g@example.com', '2025-03-01', '2025-03-05', 600.00, 'confirmada'), 

-- Res ID 4: Cliente 5 (Carlos), Hab 4 (201, $70) -> 3 noches * 70 = 210
(5, 4, 'Carlos Ruiz', 'carlosr@example.com', '2025-04-15', '2025-04-18', 210.00, 'cancelada'), 

-- Res ID 5: Cliente 6 (Valeria), Hab 5 (202, $100) -> 5 noches * 100 = 500
(6, 5, 'Valeria Hernández', 'valeria.h@example.com', '2025-05-20', '2025-05-25', 500.00, 'reservada');


/* 7. SERVICIOS RESERVA (Ejemplo de servicio aplicado a la Reserva ID 2 (Luis)) */
-- Se asume ID de servicio 3 (Desayuno buffet, $30) y 2 (Masaje relajante, $120)
INSERT INTO reservation_services (reservation_id, service_id, quantity, unit_price, service_date) VALUES
(2, 3, 2, 30.00, '2025-02-06'), -- Desayuno para dos el 06-Feb
(2, 2, 1, 120.00, '2025-02-06'); -- Un masaje


/* 8. FACTURAS. Se usa la tabla 'invoices' en lugar de 'payments' y se corrigen los ENUMS. */
INSERT INTO invoices (reservation_id, total, invoice_date, method) VALUES
(1, 100.00, '2025-01-12', 'tarjeta'),
(2, 280.00, '2025-02-07', 'efectivo'), -- Total: 160 (Reserva) + 60 (2 Desayunos) + 120 (Masaje) = 340. Usaremos 280 para simular algún descuento o error.
(3, 600.00, '2025-03-05', 'transferencia'),
(5, 500.00, '2025-05-20', 'tarjeta');

