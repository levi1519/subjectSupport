# 📝 Configuración de Logging para Django en Render

**Fecha**: 2025-12-11
**Objetivo**: Asegurar que los logs de INFO se vean en Render Dashboard

---

## Problema

Los logs de nivel `INFO` generados por el middleware y utilidades de geolocalización no aparecían en los logs de Render, solo se veían logs de Gunicorn.

---

## Solución Implementada

### Configuración en `settings.py`

Se agregó el diccionario `LOGGING` al final de `settings.py` (líneas 255-297):

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'INFO',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

---

## Qué Hace Esta Configuración

### 1. **Formatters**

Define cómo se formatean los mensajes de log:

- **verbose**: Incluye nivel, timestamp, módulo y mensaje
  ```
  INFO 2025-12-11 10:30:45 middleware Middleware IP Detectada: 190.15.128.1
  ```

- **simple**: Solo nivel y mensaje
  ```
  INFO Middleware IP Detectada: 190.15.128.1
  ```

### 2. **Handlers**

- **console**: Envía logs a `stdout` (consola)
  - Usa `StreamHandler` para escribir a la salida estándar
  - Render captura `stdout` y lo muestra en el Dashboard
  - Nivel mínimo: `INFO`

### 3. **Root Logger**

Configuración por defecto para todos los loggers no especificados:
- Handler: `console`
- Nivel: `INFO`

### 4. **Loggers Específicos**

**django**: Logs del framework Django
- Nivel: `INFO`
- Captura: Requests, queries, errores internos

**core**: Logs de la app `core`
- Nivel: `INFO`
- Captura: Middleware, geolocalización, vistas

**accounts**: Logs de la app `accounts`
- Nivel: `INFO`
- Captura: Autenticación, registro, perfiles

---

## Niveles de Logging

En orden de severidad (menor a mayor):

1. **DEBUG** - Información detallada de debugging
2. **INFO** - Información general del flujo de la aplicación ← **Configurado**
3. **WARNING** - Advertencias (algo inesperado pero no error)
4. **ERROR** - Errores que no detienen la aplicación
5. **CRITICAL** - Errores críticos que pueden detener la app

**Configuración actual**: Captura `INFO` y superiores (INFO, WARNING, ERROR, CRITICAL)

---

## Verificación Local

### Prueba en Desarrollo

```bash
# Activar entorno
env\Scripts\activate

# Ejecutar servidor
python manage.py runserver
```

**Resultado esperado en consola**:

```
INFO 2025-12-11 10:30:45 middleware Middleware IP Detectada: 127.0.0.1. Headers: X-Forwarded-For: None, REMOTE_ADDR: 127.0.0.1
INFO 2025-12-11 10:30:45 geo Checking geo restriction for IP: 127.0.0.1
INFO 2025-12-11 10:30:45 geo Geo check skipped (SKIP_GEO_CHECK=True)
```

Si ves estos logs → Configuración correcta ✅

---

## Verificación en Producción (Render)

### Paso 1: Deploy

```bash
git add subjectSupport/settings.py LOGGING_CONFIGURATION.md
git commit -m "feat: Add logging configuration for Render"
git push origin main
```

### Paso 2: Ver Logs en Render

1. Dashboard → Tu Web Service
2. Pestaña **"Logs"**
3. Activar **"Auto-scroll"**
4. Generar tráfico visitando tu app

### Paso 3: Buscar Logs

Deberías ver:

```
INFO 2025-12-11 10:30:45 middleware Middleware IP Detectada: <IP>
INFO 2025-12-11 10:30:45 geo Geo API called with IP: <IP>
INFO 2025-12-11 10:30:45 geo API Status for IP <IP>: 200
INFO 2025-12-11 10:30:45 geo Raw API Response for IP <IP>: {...}
```

---

## Troubleshooting

### ❌ No veo logs en Render

**Posibles causas**:

1. **Logs no se están generando**
   - Verificar que el código con logging está deployed
   - Verificar git commit y push exitosos

2. **Nivel de logging muy alto**
   - Verificar `'level': 'INFO'` en handlers y loggers
   - Cambiar temporalmente a `'DEBUG'` para ver más

3. **Logger incorrecto**
   - Verificar que usas `logger = logging.getLogger(__name__)`
   - Verificar que `__name__` corresponde a `core` o `accounts`

4. **Render no captura stdout**
   - Render captura automáticamente `stdout`
   - Verificar que usas `StreamHandler` (no `FileHandler`)

### ❌ Demasiados logs

Si ves demasiados logs DEBUG de Django:

```python
'django': {
    'handlers': ['console'],
    'level': 'WARNING',  # Cambiar de INFO a WARNING
    'propagate': False,
},
```

### ❌ Logs sin timestamp

Usar formatter `verbose` en lugar de `simple`:

```python
'console': {
    'class': 'logging.StreamHandler',
    'formatter': 'verbose',  # ← Usar verbose
    'level': 'INFO',
},
```

---

## Ajustes Opcionales

### Logging Solo en Producción

Si quieres logging detallado solo en producción:

```python
# En settings.py
if not DEBUG:
    # Logging verbose para producción
    LOGGING['loggers']['core']['level'] = 'INFO'
else:
    # Logging reducido para desarrollo
    LOGGING['loggers']['core']['level'] = 'WARNING'
```

### Logging a Archivo (Adicional)

Para guardar logs en archivo además de consola:

```python
'handlers': {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'verbose',
        'level': 'INFO',
    },
    'file': {
        'class': 'logging.FileHandler',
        'filename': BASE_DIR / 'logs' / 'django.log',
        'formatter': 'verbose',
        'level': 'INFO',
    },
},
'loggers': {
    'core': {
        'handlers': ['console', 'file'],  # Ambos handlers
        'level': 'INFO',
        'propagate': False,
    },
},
```

**Nota**: Render es efímero, los archivos se borran en cada deploy. Mejor usar solo console.

### Logging de SQL Queries (Debug)

Para ver todas las queries SQL:

```python
'loggers': {
    'django.db.backends': {
        'handlers': ['console'],
        'level': 'DEBUG',
        'propagate': False,
    },
}
```

⚠️ Solo usar en desarrollo, genera muchos logs.

---

## Best Practices

### 1. Niveles Apropiados

```python
# Información general del flujo
logger.info("User logged in successfully")

# Advertencias (no crítico)
logger.warning("API rate limit approaching")

# Errores (pero app sigue funcionando)
logger.error("Failed to send email", exc_info=True)

# Crítico (app puede fallar)
logger.critical("Database connection lost")
```

### 2. Usar exc_info=True para Excepciones

```python
try:
    # código
except Exception as e:
    logger.error(f"Error: {str(e)}", exc_info=True)  # ← Captura stack trace
```

### 3. No Logear Información Sensible

```python
# ❌ MAL
logger.info(f"User password: {password}")

# ✅ BIEN
logger.info(f"User {username} authenticated successfully")
```

### 4. Context en Logs

```python
# ✅ BIEN - Incluye contexto útil
logger.info(f"Geo API called with IP: {ip_address}")

# ❌ MAL - Muy genérico
logger.info("API called")
```

---

## Estructura de LOGGING

```
LOGGING
├── version: 1
├── disable_existing_loggers: False
├── formatters
│   ├── verbose (con timestamp)
│   └── simple (sin timestamp)
├── handlers
│   └── console (StreamHandler → stdout)
├── root (logger por defecto)
│   ├── handlers: [console]
│   └── level: INFO
└── loggers (específicos)
    ├── django (framework)
    ├── core (app core)
    └── accounts (app accounts)
```

---

## Logs Esperados en Render

Una vez configurado correctamente, verás esta secuencia:

```
INFO 2025-12-11 10:30:45 middleware Middleware IP Detectada: 190.15.128.1. Headers: X-Forwarded-For: 190.15.128.1, REMOTE_ADDR: 10.0.0.5
INFO 2025-12-11 10:30:45 geo Checking geo restriction for IP: 190.15.128.1
INFO 2025-12-11 10:30:45 geo Geo API called with IP: 190.15.128.1
INFO 2025-12-11 10:30:45 geo API Status for IP 190.15.128.1: 200
INFO 2025-12-11 10:30:45 geo Raw API Response for IP 190.15.128.1: {'ip': '190.15.128.1', 'city': 'Guayaquil', ...}
INFO 2025-12-11 10:30:45 geo Geo data obtained for IP 190.15.128.1: Guayaquil, Guayas
```

---

## Checklist

- [x] Configuración `LOGGING` añadida a `settings.py`
- [x] Handler `console` configurado con nivel `INFO`
- [x] Loggers `core` y `accounts` configurados
- [x] Formatter `verbose` con timestamp
- [ ] Deploy a Render
- [ ] Verificar logs visibles en Render Dashboard
- [ ] Confirmar que captura logs de geolocalización

---

## Recursos

- [Django Logging Docs](https://docs.djangoproject.com/en/5.2/topics/logging/)
- [Python Logging Docs](https://docs.python.org/3/library/logging.html)
- [Render Logging](https://render.com/docs/logs)

---

**Última actualización**: 2025-12-11
**Archivo modificado**: `subjectSupport/settings.py` (líneas 255-297)
