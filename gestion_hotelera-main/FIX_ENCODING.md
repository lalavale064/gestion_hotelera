# Solución al Problema de Acentos (Encoding UTF-8)

## Problema
Los caracteres con acentos aparecen incorrectamente: "Hernández" se muestra como "HernÃ¡ndez"

## Causa
El problema se debe a:
1. La base de datos MySQL no estaba configurada para UTF-8
2. Los datos existentes pueden estar corruptos por doble encoding

## Solución (3 Pasos)

### Paso 1: Detener los Contenedores

```bash
cd /Users/valeresendiz/Downloads/gestion_hotelera-main
docker-compose down
```

### Paso 2: Reiniciar con la Nueva Configuración

Ya actualicé el `docker-compose.yml` con la configuración UTF-8. Ahora reinicia:

```bash
docker-compose up -d
```

### Paso 3: Ejecutar el Script de Corrección

Este script te ayudará a diagnosticar y corregir los problemas:

```bash
# Instalar pymysql si no lo tienes
pip3 install pymysql

# Ejecutar el script
python3 fix_encoding.py
```

**Opciones del script:**

1. **Opción 5** primero (Verificación completa):
   - Te mostrará la configuración actual
   - Te mostrará qué datos tienen problemas

2. **Opción 3** (Corregir charset):
   - Convierte todas las tablas a UTF-8
   - Es seguro de ejecutar

3. **Opción 4** (Corregir datos corruptos):
   - ⚠️ **SOLO si tienes datos con "Ã" o "Â"**
   - Intenta decodificar el doble encoding
   - **ADVERTENCIA**: Haz backup primero si tienes datos importantes

## Verificación

Después de ejecutar los pasos:

1. Abre la aplicación en: http://localhost:3310
2. Crea un nuevo cliente con acentos: "José Hernández"
3. Verifica que se muestre correctamente

## Si los Datos Antiguos siguen Mal

Si después de todo esto los datos ANTIGUOS siguen mal:

**Opción A - Recomendasda**: Recrear los datos de prueba
```bash
# Detener contenedores
docker-compose down

# Borrar el volumen de datos (¡PIERDE TODOS LOS DATOS!)
docker volume rm gestion_hotelera-main_db_data

# Volver a crear todo
docker-compose up -d
```

**Opción B**: Usar el script con la opción 4 para corregir datos existentes

## Archivos Modificados

- ✅ `docker-compose.yml` - Agregada configuración UTF-8 para MySQL
- ✅ `web/app.py` - Ya tiene `app.config['JSON_AS_ASCII'] = False`
- ✅ `fix_encoding.py` - Script de diagnóstico y corrección

## Notas Técnicas

La configuración agregada a `docker-compose.yml`:
- `MYSQL_CHARSET: utf8mb4` - Charset de 4 bytes para soportar todos los caracteres
- `MYSQL_COLLATION: utf8mb4_unicode_ci` - Collation recomendada
- `command: --character-set-server=utf8mb4` - Fuerza UTF-8 al iniciar MySQL

## Contacto de Soporte

Si después de seguir estos pasos el problema persiste, comparte:
1. El output de ejecutar el script (Opción 5)
2. Una captura de pantalla del error
