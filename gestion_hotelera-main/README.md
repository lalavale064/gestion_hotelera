# Sistema de Gestión Hotelera

Sistema completo de gestión hotelera desarrollado con Flask y MySQL, que incluye módulos de administración, recepción, servicios (spa) y portal de clientes.

## Tabla de Contenidos

- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Ejecución](#-instalación-y-ejecución)
  - [Opción 1: Docker (Recomendado)](#opción-1-docker-recomendado)
  - [Opción 2: Instalación Local](#opción-2-instalación-local)
- [Credenciales de Acceso](#-credenciales-de-acceso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Funcionalidades](#-funcionalidades)
- [Solución de Problemas](#-solución-de-problemas)

##  Características

- **Panel de Administración**: Gestión completa de habitaciones, clientes, personal, servicios, reservas y facturación
- **Módulo de Recepción**: Check-in/Check-out, gestión de reservas diarias
- **Módulo de Servicios (Spa)**: Carga de servicios a habitaciones, catálogo de servicios
- **Portal de Clientes**: Reservas en línea, consulta de consumos, cancelaciones
- **Reportes**: Generación de reportes de ocupación y exportación a CSV
- **Autenticación**: Sistema de login con roles diferenciados
- **Protección de Rutas**: Control de acceso basado en roles

## Tecnologías

- **Backend**: Flask (Python 3.9)
- **Base de Datos**: MySQL 8.0
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Containerización**: Docker & Docker Compose
- **ORM**: PyMySQL

##  Requisitos Previos

### Para Docker (Recomendado)
- [Docker Desktop](https://www.docker.com/products/docker-desktop) instalado
- Docker Compose (incluido en Docker Desktop)

### Para Instalación Local
- Python 3.9 o superior
- MySQL 8.0 o MariaDB 10.5+
- pip (gestor de paquetes de Python)

## Instalación y Ejecución

### Opción 1: Docker (Recomendado)

Esta es la forma más rápida y sencilla de ejecutar el proyecto.

#### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd gestion_hotelera-main
```

#### 2. Levantar los contenedores

```bash
docker-compose up --build
```

Este comando:
- Construye la imagen de la aplicación Flask
- Descarga MySQL 8.0
- Inicializa la base de datos con el esquema y 10,000+ registros de prueba
- Levanta ambos servicios

#### 3. Acceder a la aplicación

Abre tu navegador y ve a:

```
http://localhost:5002/login.html
```

#### 4. Detener los contenedores

```bash
# Presiona Ctrl+C en la terminal donde está corriendo
# Luego ejecuta:
docker-compose down
```

#### 5. Reiniciar desde cero (opcional)

Si necesitas reiniciar la base de datos:

```bash
docker-compose down -v
docker-compose up --build
```

---

### Opción 2: Instalación Local

#### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd gestion_hotelera-main
```

#### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 4. Configurar MySQL

Asegúrate de tener MySQL corriendo en el puerto 3307 (o ajusta las variables de entorno).

#### 5. Inicializar la base de datos

```bash
cd web
python run_sql_scripts.py
```

Este script:
- Crea el esquema de la base de datos
- Carga 10,000+ registros de prueba
- Restaura los usuarios por defecto

#### 6. Ejecutar la aplicación

```bash
python app.py
```

#### 7. Acceder a la aplicación

```
http://localhost:5001/login.html
```

---

## Credenciales de Acceso

El sistema incluye usuarios de prueba para cada rol:

| Rol | Email | Contraseña |
|-----|-------|------------|
| **Administrador** | admin@hotel.com | admin |
| **Recepción** | recepcion@hotel.com | recepcion |
| **Spa/Servicios** | spa@hotel.com | spa |
| **Cliente** | cliente@hotel.com | cliente |

##  Estructura del Proyecto

```
gestion_hotelera-main/
├── web/                          # Aplicación Flask
│   ├── app.py                    # Aplicación principal
│   ├── templates/                # Plantillas HTML
│   │   ├── login.html
│   │   ├── administrador.html
│   │   ├── empleado.html
│   │   └── cliente.html
│   └── static/                   # Archivos estáticos (si los hay)
├── db_init/                      # Scripts de inicialización de BD
│   └── Hotel_BD.sql              # Esquema de la base de datos
├── hotel_data_inserts.sql        # Datos de prueba (10,000+ registros)
├── fix_encoding.sql              # Corrección de encoding
├── Dockerfile                    # Configuración Docker para Flask
├── docker-compose.yml            # Orquestación de servicios
├── requirements.txt              # Dependencias de Python
└── README.md                     # Este archivo
```

##  Funcionalidades

### Panel de Administración
-  Gestión de habitaciones (CRUD)
- Gestión de clientes (CRUD)
- Gestión de personal (CRUD)
- Gestión de servicios (CRUD)
- Gestión de reservas (CRUD)
- Facturación
- Reportes de ocupación
- Exportación a CSV (sin acentos para compatibilidad)
- Dashboard con métricas

### Módulo de Recepción
- Operaciones diarias (Check-in/Check-out)
- Visualización de estado de habitaciones
- Gestión de reservas

### Módulo de Servicios (Spa)
- Visualización de huéspedes activos
- Carga de servicios a habitaciones
- Catálogo de servicios
- Historial de servicios

### Portal de Clientes
- Búsqueda de disponibilidad
- Creación de reservas
- Consulta de reservas
- Solicitud de servicios
- Cancelación de reservas
- Visualización de consumos

##  Solución de Problemas

### Error: Puerto ya en uso

Si ves errores como `port is already allocated`:

**Para Docker:**
```bash
# Cambia los puertos en docker-compose.yml
# Línea de Flask: "5002:5001" -> "5003:5001"
# Línea de MySQL: "3308:3306" -> "3309:3306"
```

**Para instalación local:**
```bash
# Detén otros servicios que usen los puertos 5001 o 3307
# O cambia las variables de entorno en app.py
```

### Error: Base de datos no se conecta

**Docker:**
```bash
# Espera a que MySQL esté listo (puede tardar 30-60 segundos)
docker-compose logs -f db
```

**Local:**
```bash
# Verifica que MySQL esté corriendo
# Verifica las credenciales en web/app.py
```

### Error: No aparecen los datos

```bash
# Docker: Reinicia los volúmenes
docker-compose down -v
docker-compose up --build

# Local: Re-ejecuta el script de población
cd web
python run_sql_scripts.py
```

### Ver logs de Docker

```bash
# Todos los servicios
docker-compose logs -f

# Solo Flask
docker-compose logs -f web

# Solo MySQL
docker-compose logs -f db
```

## Notas Adicionales

- La base de datos incluye más de 10,000 registros de prueba para demostración
- Los CSV exportados tienen los acentos removidos para evitar problemas de encoding
- El sistema usa autenticación basada en `localStorage` (solo para demostración)
- Las contraseñas se almacenan con hash SHA256

## Contribuciones

Este es un proyecto académico. Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

**¿Problemas?** Abre un issue en GitHub con:
- Sistema operativo
- Versión de Docker/Python
- Logs completos del error
- Pasos para reproducir el problema
# gestion_hotelera
Programa de gestión hotelera con sql
