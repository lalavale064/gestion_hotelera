/* =========================================================
   BASE DE DATOS: GESTIÓN HOTELERA 
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
  checkin_date DATETIME NOT NULL,
  checkout_date DATETIME NOT NULL,
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
   CORRECCIONES (para los demás roles)
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

-- Nota: Los datos de clientes, habitaciones, staff, servicios, reservas e invoices
-- se cargan desde el archivo hotel_data_inserts.sql

