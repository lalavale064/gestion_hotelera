# Hotel Management System - Docker Setup

Este proyecto utiliza Docker para facilitar el despliegue.

## Requisitos Previos

- Docker Desktop instalado
- Docker Compose instalado

## Instrucciones de Uso

### 1. Construir y Levantar los Contenedores

```bash
docker-compose up --build
```

Este comando:
- Construye la imagen de la aplicación Flask
- Descarga la imagen de MySQL 8.0
- Crea los contenedores
- Inicializa la base de datos con el esquema y los datos
- Levanta la aplicación

### 2. Acceder a la Aplicación

Una vez que los contenedores estén corriendo, accede a:

```
http://localhost:5001/login.html
```

### 3. Credenciales de Acceso

- **Admin**: `admin@hotel.com` / `admin`
- **Recepción**: `recepcion@hotel.com` / `recepcion`
- **Spa**: `spa@hotel.com` / `spa`
- **Cliente**: `cliente@hotel.com` / `cliente`

### 4. Detener los Contenedores

```bash
docker-compose down
```

### 5. Detener y Eliminar Volúmenes (Reiniciar BD)

```bash
docker-compose down -v
```

## Configuración

### Variables de Entorno

Las variables de entorno se configuran en `docker-compose.yml`:

- `DB_HOST`: Nombre del servicio de base de datos (db)
- `DB_PORT`: Puerto de MySQL (3306 interno)
- `DB_USER`: Usuario de la base de datos
- `DB_PASS`: Contraseña de la base de datos
- `DB_NAME`: Nombre de la base de datos

### Puertos

- **Aplicación Web**: `5001` (host) → `5001` (contenedor)
- **MySQL**: `3307` (host) → `3306` (contenedor)

## Desarrollo

Para desarrollo con hot-reload, el código en `./web` está montado como volumen. Los cambios se reflejarán automáticamente.

## Solución de Problemas

### La base de datos no se inicializa

```bash
docker-compose down -v
docker-compose up --build
```

### Ver logs

```bash
# Logs de todos los servicios
docker-compose logs -f

# Logs solo de la aplicación
docker-compose logs -f web

# Logs solo de la base de datos
docker-compose logs -f db
```

### Acceder al contenedor

```bash
# Acceder a la aplicación
docker exec -it hotel_web bash

# Acceder a MySQL
docker exec -it hotel_db mysql -u hotel_user -p
```
