-- Script para reparar los acentos rotos (Mojibake) en la base de datos
USE gestion_hotelera;

-- Reparar tabla CLIENTS
UPDATE clients 
SET full_name = CONVERT(CAST(CONVERT(full_name USING latin1) AS BINARY) USING utf8mb4)
WHERE full_name REGEXP '[ÃÂ]';

UPDATE clients 
SET address = CONVERT(CAST(CONVERT(address USING latin1) AS BINARY) USING utf8mb4)
WHERE address REGEXP '[ÃÂ]' AND address IS NOT NULL;

-- Reparar tabla STAFF
UPDATE staff 
SET full_name = CONVERT(CAST(CONVERT(full_name USING latin1) AS BINARY) USING utf8mb4)
WHERE full_name REGEXP '[ÃÂ]';

UPDATE staff 
SET area = CONVERT(CAST(CONVERT(area USING latin1) AS BINARY) USING utf8mb4)
WHERE area REGEXP '[ÃÂ]' AND area IS NOT NULL;

-- Reparar tabla RESERVATIONS
UPDATE reservations 
SET guest_name = CONVERT(CAST(CONVERT(guest_name USING latin1) AS BINARY) USING utf8mb4)
WHERE guest_name REGEXP '[ÃÂ]';

-- Reparar tabla SERVICES
UPDATE services 
SET name = CONVERT(CAST(CONVERT(name USING latin1) AS BINARY) USING utf8mb4)
WHERE name REGEXP '[ÃÂ]';

UPDATE services 
SET description = CONVERT(CAST(CONVERT(description USING latin1) AS BINARY) USING utf8mb4)
WHERE description REGEXP '[ÃÂ]' AND description IS NOT NULL;

SELECT 'Reparacion completada' as status;
