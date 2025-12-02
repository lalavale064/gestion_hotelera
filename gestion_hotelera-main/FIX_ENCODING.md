# Solución al Problema de Acentos (Encoding UTF-8)

## Problema
Los caracteres con acentos aparecen incorrectamente: "Hernández" se muestra como "HernÃ¡ndez"

## Causa
El problema se debe a:
1. La base de datos MySQL no estaba configurada para UTF-8
2. Los datos existentes pueden estar corruptos por doble encoding


## Archivos Modificados

- `docker-compose.yml` - Agregada configuración UTF-8 para MySQL
- `web/app.py` - Ya tiene `app.config['JSON_AS_ASCII'] = False`
- `fix_encoding.py` - Script de diagnóstico y corrección

## Notas Técnicas

La configuración agregada a `docker-compose.yml`:
- `MYSQL_CHARSET: utf8mb4` - Charset de 4 bytes para soportar todos los caracteres
- `MYSQL_COLLATION: utf8mb4_unicode_ci` - Collation recomendada
- `command: --character-set-server=utf8mb4` - Fuerza UTF-8 al iniciar MySQL

## Contacto de Soporte

Si después de seguir estos pasos el problema persiste, comparte:
1. El output de ejecutar el script (Opción 5)
2. Una captura de pantalla del error
