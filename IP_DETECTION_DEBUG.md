# 🔍 Diagnóstico de Detección de IP - Debug Logging

**Fecha**: 2025-12-11
**Objetivo**: Diagnosticar por qué la geolocalización retorna 'Unknown' en Render

---

## Problema Detectado

En Render, la geolocalización está retornando `'Unknown'` como ciudad, sugiriendo que:

1. La IP detectada no es la correcta (probablemente IP interna de Render)
2. Los headers de proxy no se están capturando correctamente

---

## Cambios Realizados

### 1. Archivo Modificado: `core/middleware.py`

**Líneas añadidas**: 50-64

Se agregó logging detallado en el método `__call__` del middleware para capturar:

1. **IP detectada** - La IP que el sistema está usando para geolocalización
2. **HTTP_X_FORWARDED_FOR** - Header que contiene la IP real del cliente detrás de proxies
3. **REMOTE_ADDR** - IP del servidor que hace la request (puede ser proxy de Render)

```python
# LOG: Detectar IP y headers para diagnóstico
x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
remote_addr = request.META.get('REMOTE_ADDR')

# Determinar IP que se usará (misma lógica que get_client_ip en geo.py)
if x_forwarded_for:
    ip = x_forwarded_for.split(',')[0].strip()
else:
    ip = remote_addr

logger.info(
    f"Middleware IP Detectada: {ip}. "
    f"Headers: X-Forwarded-For: {x_forwarded_for}, "
    f"REMOTE_ADDR: {remote_addr}"
)
```

### 2. Archivo Modificado: `core/utils/geo.py`

**Líneas modificadas**: 64-111

Se agregó logging detallado en la función `get_location_from_ip()` para capturar:

1. **IP enviada a la API** - Confirmar qué IP se está geolocalizando
2. **Status HTTP** - Código de respuesta de la API (200, 401, 429, etc.)
3. **Respuesta cruda** - JSON completo retornado por ipgeolocation.io
4. **Stack traces completos** - En caso de excepciones (`exc_info=True`)

```python
# LOG 1: Confirmar IP que se está usando
logger.info(f"Geo API called with IP: {ip_address}")

# LOG 2: Status HTTP de la respuesta
logger.info(f"API Status for IP {ip_address}: {response.status_code}")

# LOG 3: Respuesta cruda de la API
logger.info(f"Raw API Response for IP {ip_address}: {data}")

# LOG 4: Stack traces completos en excepciones
except Exception as e:
    logger.error(f"Error: {str(e)}", exc_info=True)
```

---

## Cómo Verificar en Producción (Render)

### Paso 1: Deploy del Cambio

```bash
git add core/middleware.py core/utils/geo.py IP_DETECTION_DEBUG.md
git commit -m "debug: Add comprehensive logging for IP detection and geolocation API"
git push origin main
```

Render hará auto-deploy.

### Paso 2: Acceder a los Logs de Render

1. Ir a: https://dashboard.render.com
2. Seleccionar tu Web Service: `subjectsupport`
3. Click en la pestaña **"Logs"**
4. Activar **"Auto-scroll"** para ver logs en tiempo real

### Paso 3: Generar Tráfico

Desde un navegador (fuera de Milagro si es posible):

```
https://tu-app.onrender.com/
```

### Paso 4: Buscar en los Logs

Ahora verás una secuencia completa de logs. Buscar:

1. **Middleware IP Detection**:
   ```
   INFO: Middleware IP Detectada: 190.15.128.1. Headers: X-Forwarded-For: 190.15.128.1, REMOTE_ADDR: 10.0.0.5
   ```

2. **API Call**:
   ```
   INFO: Geo API called with IP: 190.15.128.1
   ```

3. **API Status**:
   ```
   INFO: API Status for IP 190.15.128.1: 200
   ```

4. **Raw API Response**:
   ```
   INFO: Raw API Response for IP 190.15.128.1: {'ip': '190.15.128.1', 'city': 'Guayaquil', 'state_prov': 'Guayas', ...}
   ```

**Ejemplo completo cuando funciona**:

```
INFO: Middleware IP Detectada: 190.15.128.1. Headers: X-Forwarded-For: 190.15.128.1, REMOTE_ADDR: 10.0.0.5
INFO: Checking geo restriction for IP: 190.15.128.1
INFO: Geo API called with IP: 190.15.128.1
INFO: API Status for IP 190.15.128.1: 200
INFO: Raw API Response for IP 190.15.128.1: {'ip': '190.15.128.1', 'city': 'Guayaquil', 'state_prov': 'Guayas', 'country_name': 'Ecuador', ...}
INFO: Geo data obtained for IP 190.15.128.1: Guayaquil, Guayas
```

**Ejemplo cuando falla (IP privada)**:

```
INFO: Middleware IP Detectada: 10.0.0.5. Headers: X-Forwarded-For: None, REMOTE_ADDR: 10.0.0.5
INFO: Checking geo restriction for IP: 10.0.0.5
INFO: Geo API called with IP: 10.0.0.5
INFO: API Status for IP 10.0.0.5: 200
INFO: Raw API Response for IP 10.0.0.5: {'ip': '10.0.0.5', 'city': '', 'state_prov': '', 'country_name': '', ...}
WARNING: Could not detect location for IP 10.0.0.5, allowing access by default
```

---

## Interpretación de los Logs

### ✅ Caso Correcto

```
Middleware IP Detectada: 190.15.128.1
Headers: X-Forwarded-For: 190.15.128.1, REMOTE_ADDR: 10.0.0.5
```

**Interpretación**:
- ✅ `X-Forwarded-For` contiene la IP pública del usuario
- ✅ Se está usando la IP correcta para geolocalización
- ✅ El sistema debería funcionar correctamente

### ❌ Caso Problemático 1: X-Forwarded-For es None

```
Middleware IP Detectada: 10.0.0.5
Headers: X-Forwarded-For: None, REMOTE_ADDR: 10.0.0.5
```

**Interpretación**:
- ❌ Render no está pasando el header `X-Forwarded-For`
- ❌ Se está usando la IP interna de Render (10.x.x.x)
- ❌ La geolocalización falla (IPs privadas no se pueden geolocalizar)

**Solución**: Render debería pasar automáticamente este header, verificar configuración.

### ❌ Caso Problemático 2: IP Local

```
Middleware IP Detectada: 127.0.0.1
Headers: X-Forwarded-For: None, REMOTE_ADDR: 127.0.0.1
```

**Interpretación**:
- ❌ Request viene de localhost (solo en desarrollo)
- ❌ No se puede geolocalizar

**Solución**: Normal en desarrollo local, usar `SKIP_GEO_CHECK=True`

---

## Posibles Problemas y Soluciones

### Problema 1: X-Forwarded-For es None en Render

**Causa**: Render puede usar un header diferente.

**Solución**: Modificar `core/utils/geo.py` función `get_client_ip()`:

```python
def get_client_ip(request):
    # Intentar múltiples headers de proxy
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    x_real_ip = request.META.get('HTTP_X_REAL_IP')  # Header alternativo
    forwarded = request.META.get('HTTP_FORWARDED')  # RFC 7239

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    elif x_real_ip:
        ip = x_real_ip.strip()
    elif forwarded:
        # Parsear "for=192.0.2.60;proto=http;by=203.0.113.43"
        ip = forwarded.split('for=')[1].split(';')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    # Logs adicionales...
    return ip
```

### Problema 2: Múltiples IPs en X-Forwarded-For

**Formato**: `X-Forwarded-For: client, proxy1, proxy2`

**Solución actual**: Ya implementada - tomamos la primera IP:

```python
ip = x_forwarded_for.split(',')[0].strip()
```

### Problema 3: IPs Privadas (10.x.x.x, 172.x.x.x, 192.168.x.x)

Si los logs muestran IP privada, significa que Render no está configurando proxies correctamente.

**Solución**:

1. Verificar que `SECURE_PROXY_SSL_HEADER` está configurado en settings.py:

```python
# En settings.py (producción)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

2. Añadir configuración de trusted proxies (Django 4.2+):

```python
# settings.py
ALLOWED_HOSTS = ['.onrender.com']
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
```

---

## Verificación Adicional

### Test Manual de Geolocalización

Una vez que tengas la IP de los logs, puedes testearla manualmente:

```bash
# Reemplazar <IP-DEL-LOG> con la IP que viste en los logs
curl "https://api.ipgeolocation.io/ipgeo?apiKey=fea21382d3f544cdb92199e1751fcd6a&ip=<IP-DEL-LOG>"
```

**Ejemplo**:

```bash
curl "https://api.ipgeolocation.io/ipgeo?apiKey=fea21382d3f544cdb92199e1751fcd6a&ip=190.15.128.1"
```

**Respuesta esperada**:

```json
{
  "city": "Guayaquil",
  "state_prov": "Guayas",
  "country_name": "Ecuador",
  ...
}
```

Si la API retorna `'Unknown'` incluso con la IP correcta, entonces el problema es:
- La IP no se puede geolocalizar (privada, VPN, etc.)
- Límite de API alcanzado
- API key inválida

---

## Checklist de Diagnóstico

Sigue estos pasos en orden:

- [ ] **Step 1**: Deploy del código con logging
- [ ] **Step 2**: Acceder a Render Logs
- [ ] **Step 3**: Generar tráfico a la app
- [ ] **Step 4**: Capturar línea "Middleware IP Detectada"
- [ ] **Step 5**: Verificar si `X-Forwarded-For` tiene valor
- [ ] **Step 6**: Verificar si la IP es pública (no 10.x, 172.x, 192.168.x)
- [ ] **Step 7**: Test manual de esa IP con curl
- [ ] **Step 8**: Si API retorna datos correctos pero app no → revisar código
- [ ] **Step 9**: Si API retorna Unknown → problema con IP detection

---

## Logs Completos Esperados

### ✅ Secuencia Exitosa (Usuario de Ecuador)

```
INFO: Middleware IP Detectada: 190.15.128.1. Headers: X-Forwarded-For: 190.15.128.1, REMOTE_ADDR: 10.0.0.5
INFO: Checking geo restriction for IP: 190.15.128.1
INFO: Geo API called with IP: 190.15.128.1
INFO: API Status for IP 190.15.128.1: 200
INFO: Raw API Response for IP 190.15.128.1: {'ip': '190.15.128.1', 'city': 'Guayaquil', 'state_prov': 'Guayas', 'country_name': 'Ecuador', 'country_code2': 'EC', 'latitude': '-2.1700', 'longitude': '-79.9224', ...}
INFO: Geo data obtained for IP 190.15.128.1: Guayaquil, Guayas
INFO: Service available in Milagro, Guayas
```

### ❌ Usuario Bloqueado (Fuera de Ecuador)

```
INFO: Middleware IP Detectada: 8.8.8.8. Headers: X-Forwarded-For: 8.8.8.8, REMOTE_ADDR: 10.0.0.5
INFO: Checking geo restriction for IP: 8.8.8.8
INFO: Geo API called with IP: 8.8.8.8
INFO: API Status for IP 8.8.8.8: 200
INFO: Raw API Response for IP 8.8.8.8: {'ip': '8.8.8.8', 'city': 'Mountain View', 'state_prov': 'California', 'country_name': 'United States', ...}
INFO: Geo data obtained for IP 8.8.8.8: Mountain View, California
INFO: Service NOT available in Mountain View, California
INFO: Access blocked for user from Mountain View, California (IP: 8.8.8.8)
```

### ⚠️ Error: IP Privada (Problema con X-Forwarded-For)

```
INFO: Middleware IP Detectada: 10.0.0.5. Headers: X-Forwarded-For: None, REMOTE_ADDR: 10.0.0.5
INFO: Checking geo restriction for IP: 10.0.0.5
INFO: Geo API called with IP: 10.0.0.5
INFO: API Status for IP 10.0.0.5: 200
INFO: Raw API Response for IP 10.0.0.5: {'ip': '10.0.0.5', 'city': '', 'state_prov': '', 'country_name': '', ...}
WARNING: Could not detect location for IP 10.0.0.5, allowing access by default
```

**Diagnóstico**: Render no está pasando el header `X-Forwarded-For` → Ver sección "Problema 1" arriba.

### ❌ Error: API Key Inválida

```
INFO: Middleware IP Detectada: 190.15.128.1. Headers: X-Forwarded-For: 190.15.128.1, REMOTE_ADDR: 10.0.0.5
INFO: Checking geo restriction for IP: 190.15.128.1
INFO: Geo API called with IP: 190.15.128.1
INFO: API Status for IP 190.15.128.1: 401
ERROR: IP API returned status 401 for 190.15.128.1
WARNING: Could not detect location for IP 190.15.128.1, allowing access by default
```

**Diagnóstico**: Variable `IPGEOLOCATION_API_KEY` no configurada o inválida en Render.

### ❌ Error: Límite de API Alcanzado

```
INFO: Middleware IP Detectada: 190.15.128.1. Headers: X-Forwarded-For: 190.15.128.1, REMOTE_ADDR: 10.0.0.5
INFO: Checking geo restriction for IP: 190.15.128.1
INFO: Geo API called with IP: 190.15.128.1
INFO: API Status for IP 190.15.128.1: 429
ERROR: IP API returned status 429 for 190.15.128.1
WARNING: Could not detect location for IP 190.15.128.1, allowing access by default
```

**Diagnóstico**: Se alcanzó el límite de 50,000 requests/mes. Verificar cuota en dashboard de ipgeolocation.io.

---

## Próximos Pasos

1. **Deploy y revisar logs** - Ver qué IP se está detectando
2. **Si X-Forwarded-For es None** - Implementar headers alternativos
3. **Si IP es privada** - Configurar trusted proxies en Django
4. **Si IP es correcta pero geo falla** - Verificar API key y cuota

---

## Limpieza del Logging (Opcional)

Una vez resuelto el problema, puedes:

1. **Mantener el logging** (recomendado) - Útil para monitoreo
2. **Reducir verbosidad** - Cambiar `logger.info` a `logger.debug`
3. **Remover logging** - Eliminar las líneas 50-64 de middleware.py

Recomendación: **Mantener el logging** con `logger.debug` para poder activarlo cuando sea necesario.

---

**Actualizado**: 2025-12-11
**Archivo modificado**: `core/middleware.py`
**Líneas añadidas**: 50-64
