# 🔍 Resumen de Logging para Debug de Geolocalización

**Fecha**: 2025-12-11
**Estado**: IMPLEMENTADO

---

## Cambios Implementados

### 1. Logging en Middleware (`core/middleware.py`)

**Líneas**: 50-64

Captura información de IP y headers antes de llamar a geolocalización:

```python
logger.info(
    f"Middleware IP Detectada: {ip}. "
    f"Headers: X-Forwarded-For: {x_forwarded_for}, "
    f"REMOTE_ADDR: {remote_addr}"
)
```

**Qué se registra**:
- IP que se usará para geolocalización
- Header `X-Forwarded-For` (IP real del cliente)
- Header `REMOTE_ADDR` (puede ser proxy interno)

---

### 2. Logging en Geolocalización (`core/utils/geo.py`)

**Líneas**: 64-111

Captura toda la interacción con la API de geolocalización:

```python
# LOG 1: IP enviada a la API
logger.info(f"Geo API called with IP: {ip_address}")

# LOG 2: Status HTTP
logger.info(f"API Status for IP {ip_address}: {response.status_code}")

# LOG 3: Respuesta cruda completa
logger.info(f"Raw API Response for IP {ip_address}: {data}")

# LOG 4: Stack traces en excepciones
except Exception as e:
    logger.error(f"Error: {str(e)}", exc_info=True)
```

**Qué se registra**:
- IP exacta enviada a ipgeolocation.io
- Código HTTP de respuesta (200, 401, 429, etc.)
- JSON completo retornado por la API
- Stack traces completos si hay errores

---

## Cómo Usar

### 1. Deploy

```bash
git add core/middleware.py core/utils/geo.py
git commit -m "debug: Add comprehensive logging for geolocation debugging"
git push origin main
```

### 2. Ver Logs en Render

1. Dashboard → Tu Web Service → **Logs**
2. Activar **Auto-scroll**
3. Generar tráfico visitando tu app
4. Buscar las líneas de log

### 3. Interpretar Logs

Buscar esta secuencia:

```
[1] Middleware IP Detectada: <IP>
[2] Geo API called with IP: <IP>
[3] API Status for IP <IP>: <CODE>
[4] Raw API Response for IP <IP>: {...}
```

---

## Diagnósticos Comunes

### ✅ Todo Funciona

```
INFO: Middleware IP Detectada: 190.15.128.1
INFO: Geo API called with IP: 190.15.128.1
INFO: API Status for IP 190.15.128.1: 200
INFO: Raw API Response: {'city': 'Guayaquil', 'state_prov': 'Guayas', ...}
```

**Acción**: Ninguna, el sistema funciona correctamente.

---

### ❌ Problema: X-Forwarded-For es None

```
INFO: Middleware IP Detectada: 10.0.0.5
INFO: Headers: X-Forwarded-For: None, REMOTE_ADDR: 10.0.0.5
INFO: Raw API Response: {'city': '', 'state_prov': '', ...}
```

**Causa**: Render no está pasando el header de proxy.

**Solución**: Modificar `core/utils/geo.py` función `get_client_ip()` para usar headers alternativos:

```python
def get_client_ip(request):
    # Intentar múltiples headers
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    x_real_ip = request.META.get('HTTP_X_REAL_IP')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    elif x_real_ip:
        ip = x_real_ip.strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip
```

---

### ❌ Problema: API Status 401

```
INFO: API Status for IP 190.15.128.1: 401
ERROR: IP API returned status 401
```

**Causa**: API key no configurada o inválida.

**Solución**:
1. Verificar que `IPGEOLOCATION_API_KEY` está en Render Environment
2. Verificar que el valor es correcto: `fea21382d3f544cdb92199e1751fcd6a`

---

### ❌ Problema: API Status 429

```
INFO: API Status for IP 190.15.128.1: 429
ERROR: IP API returned status 429
```

**Causa**: Límite de 50,000 requests/mes alcanzado.

**Soluciones**:
1. Verificar cuota en https://app.ipgeolocation.io/
2. Aumentar caché TTL a 24 horas
3. Upgrade a plan pagado ($15/mes)
4. Migrar a MaxMind GeoLite2 (local)

---

### ⚠️ Problema: city y state_prov vacíos

```
INFO: Raw API Response: {'ip': '10.0.0.5', 'city': '', 'state_prov': '', ...}
```

**Causa**: IP privada (10.x.x.x, 172.x.x.x, 192.168.x.x) no se puede geolocalizar.

**Diagnóstico**: Problema con detección de IP real del cliente.

**Solución**: Ver "Problema: X-Forwarded-For es None" arriba.

---

## Limpieza Post-Debug (Opcional)

Una vez resuelto el problema, puedes:

### Opción 1: Mantener Logging (Recomendado)

Cambiar nivel de `INFO` a `DEBUG`:

```python
# En core/middleware.py y core/utils/geo.py
logger.debug(...)  # En lugar de logger.info(...)
```

Ventaja: Se puede activar cuando sea necesario sin modificar código.

### Opción 2: Reducir Verbosidad

Mantener solo logs críticos:

```python
# Eliminar:
# - logger.info(f"Geo API called with IP...")
# - logger.info(f"API Status...")
# - logger.info(f"Raw API Response...")

# Mantener:
# - logger.info(f"Middleware IP Detectada...")
# - logger.info(f"Geo data obtained...")
# - logger.error(..., exc_info=True)
```

### Opción 3: Remover Todo el Logging

Revertir cambios:

```bash
git revert <commit-hash>
git push origin main
```

---

## Testing Local

Para probar localmente antes de deploy:

```bash
# Activar entorno
env\Scripts\activate

# Iniciar servidor con logging visible
python manage.py runserver

# En otro terminal, hacer request
curl http://localhost:8000/

# Ver logs en la consola del runserver
```

Los logs aparecerán en la consola mostrando toda la información de debug.

---

## Archivos Modificados

| Archivo | Líneas | Cambios |
|---------|--------|---------|
| `core/middleware.py` | 50-64 | Logging de IP y headers |
| `core/utils/geo.py` | 64-111 | Logging de API calls y responses |
| `IP_DETECTION_DEBUG.md` | Todo | Documentación completa de debug |
| `GEO_DEBUG_SUMMARY.md` | Todo | Este resumen |

---

## Próximos Pasos

1. ✅ Código con logging implementado
2. ⏳ Deploy a Render
3. ⏳ Revisar logs en Render Dashboard
4. ⏳ Identificar problema específico
5. ⏳ Aplicar solución correspondiente
6. ⏳ Verificar que funciona
7. ⏳ (Opcional) Reducir verbosidad de logs

---

**Documentación completa**: Ver [IP_DETECTION_DEBUG.md](./IP_DETECTION_DEBUG.md)

**Última actualización**: 2025-12-11
