# 🌍 Guía Completa de Geolocalización y Restricción Geográfica

## 📋 Índice

1. [Visión General](#visión-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Configuración Inicial](#configuración-inicial)
4. [Uso y Administración](#uso-y-administración)
5. [Testing y Debugging](#testing-y-debugging)
6. [Preguntas Frecuentes](#preguntas-frecuentes)
7. [Troubleshooting](#troubleshooting)

---

## Visión General

### ¿Qué hace este sistema?

El sistema de geolocalización de SubjectSupport permite:

1. **Detectar automáticamente** la ubicación (ciudad) de cada visitante por su IP
2. **Restringir el acceso** solo a usuarios de ciudades donde el servicio está disponible
3. **Gestionar la expansión** gradual a nuevas ciudades desde el Django Admin
4. **Capturar demanda** de ciudades no habilitadas mediante formulario de notificación

### Caso de Uso MVP

**Objetivo**: Lanzar SOLO en Milagro, Guayas, Ecuador inicialmente.

**Flujo**:
- Usuario de **Milagro** → ✅ Acceso completo al sistema
- Usuario de **Quito** → ❌ Redirigido a página "Servicio no disponible"
- Admin habilita **Guayaquil** → ✅ Usuarios de Guayaquil ahora tienen acceso

---

## Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                    Usuario Accede al Sitio                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           GeoRestrictionMiddleware (middleware.py)           │
│  - Intercepta todas las requests                             │
│  - Obtiene IP del usuario                                    │
│  - Consulta API de geolocalización                           │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐         ┌──────────────────┐
│ IP → Ciudad  │         │  CiudadHabilitada │
│  (ipapi.co)  │         │      (DB Model)   │
└──────┬───────┘         └────────┬─────────┘
       │                          │
       └──────────┬───────────────┘
                  │
                  ▼
        ┌─────────────────────┐
        │ ¿Ciudad habilitada? │
        └─────────┬───────────┘
                  │
     ┌────────────┴────────────┐
     │                         │
     ▼                         ▼
┌─────────┐             ┌──────────────┐
│  SÍ ✅  │             │  NO ❌        │
│ Permite │             │ Redirige a   │
│ acceso  │             │ /servicio-no │
│         │             │ -disponible/ │
└─────────┘             └──────────────┘
```

### Archivos Clave

| Archivo | Propósito |
|---------|-----------|
| `core/models.py` | Modelos `CiudadHabilitada` y `NotificacionExpansion` |
| `core/utils/geo.py` | Funciones de geolocalización y verificación |
| `core/middleware.py` | Middleware que intercepta requests |
| `core/views.py` | Views para página no disponible y notificaciones |
| `core/forms.py` | Form para solicitar notificación |
| `templates/core/servicio_no_disponible.html` | Template para usuarios bloqueados |
| `core/fixtures/ciudades_iniciales.json` | Fixture con Milagro habilitado |

---

## Configuración Inicial

### Paso 1: Instalar Dependencias

La geolocalización usa la librería `requests` (ya debe estar instalada):

```bash
pip install requests python-dotenv  # Si no están ya instalados
```

### Paso 1.5: Configurar API Key de ipgeolocation.io

1. **Obtener API Key gratuita**:
   - Ir a: https://ipgeolocation.io/
   - Click en "Sign Up" (registro gratuito)
   - Verificar email
   - Ir a Dashboard → API Keys
   - Copiar tu API Key

2. **Añadir a .env**:
   ```bash
   # En el archivo .env
   IPGEOLOCATION_API_KEY=tu-api-key-aqui
   ```

**Plan Gratuito**: 50,000 requests/mes (suficiente para MVP)

### Paso 2: Aplicar Migraciones

```bash
# Crear migraciones para los nuevos modelos
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate
```

### Paso 3: Cargar Fixture Inicial

```bash
# Cargar Milagro como ciudad habilitada
python manage.py loaddata core/fixtures/ciudades_iniciales.json
```

Esto creará:
- **Ciudad**: Milagro
- **Provincia**: Guayas
- **País**: Ecuador
- **Activo**: True
- **Prioridad**: 1

### Paso 4: Configurar .env

El archivo `.env` debe incluir:

```bash
# Geolocalización
# True = Bypass (desarrollo/testing)
# False = Activar restricción (producción)
SKIP_GEO_CHECK=True
```

**Importante**:
- `SKIP_GEO_CHECK=True` → Para desarrollo local (permite acceso desde cualquier ubicación)
- `SKIP_GEO_CHECK=False` → Para producción (activa restricción geográfica)

### Paso 5: Verificar Configuración

```bash
# Ejecutar script de prueba
python test_geolocation.py
```

Deberías ver:
```
✅ Fixture inicial CARGADO correctamente
✅ Servicio DISPONIBLE en: Milagro, Guayas
```

---

## Uso y Administración

### Gestionar Ciudades desde Django Admin

1. **Acceder al Admin**:
   ```
   http://localhost:8000/admin/
   ```

2. **Ir a "Ciudades Habilitadas"**:
   - Click en "Core" → "Ciudades Habilitadas"

3. **Añadir Nueva Ciudad**:
   - Click en "Añadir Ciudad Habilitada"
   - Rellenar:
     - **Ciudad**: Ej: Guayaquil
     - **Provincia**: Ej: Guayas
     - **País**: Ecuador (default)
     - **Activo**: ✓ (checkbox marcado)
     - **Orden prioridad**: 10 (menor = mayor prioridad)
   - Guardar

4. **Activar/Desactivar Ciudad**:
   - En la lista, usar el checkbox "Activo"
   - O seleccionar ciudades y usar acciones "Activar" / "Desactivar"

### Ver Solicitudes de Notificación

1. **Acceder a "Notificaciones de Expansión"**:
   - Admin → Core → Notificaciones de Expansión

2. **Información Disponible**:
   - Email del usuario
   - Ciudad deseada
   - Ciudad detectada por IP
   - Estado de notificación (enviada/pendiente)

3. **Marcar como Notificado**:
   - Seleccionar notificaciones
   - Acción: "Marcar como notificado"

---

## Testing y Debugging

### Modo Desarrollo (SKIP_GEO_CHECK=True)

En `.env`:
```bash
SKIP_GEO_CHECK=True
```

**Comportamiento**:
- ✅ Bypass completo de restricción geográfica
- ✅ Cualquier IP puede acceder
- ✅ Útil para desarrollo local
- ⚠️ **NUNCA usar en producción**

### Modo Producción (SKIP_GEO_CHECK=False)

En `.env`:
```bash
SKIP_GEO_CHECK=False
```

**Comportamiento**:
- ✓ Restricción geográfica activa
- ✓ Solo ciudades habilitadas pueden acceder
- ✓ Usuarios bloqueados ven página de notificación

### Simular Diferentes IPs (Testing)

Para testing, puedes usar la función `set_test_ip()` desde Django shell:

```python
# En Django shell
from core.utils.geo import set_test_ip
from django.test import RequestFactory

request = RequestFactory().get('/')
request.session = {}

# Simular IP de Ecuador
set_test_ip(request, '190.15.128.1')

# Simular IP de USA
set_test_ip(request, '8.8.8.8')
```

### Ver Logs de Geolocalización

Los logs se generan automáticamente:

```python
# En logs verás:
INFO: Geo data obtained for IP 190.15.128.1: Guayaquil, Guayas
INFO: Service available in Milagro, Guayas
WARNING: Access blocked for user from Quito, Pichincha
```

### Script de Prueba

```bash
python test_geolocation.py
```

Verifica:
1. Ciudades habilitadas en BD
2. Disponibilidad de servicio por ciudad
3. Fixture inicial cargado
4. Configuración SKIP_GEO_CHECK

---

## Preguntas Frecuentes

### ¿Cuántas ciudades puedo habilitar?

Ilimitadas. El sistema está diseñado para escalar.

### ¿Cómo funciona la detección por IP?

Usa la API gratuita de **ipgeolocation.io**:
- **Límite**: 50,000 requests/mes gratis
- **Datos**: Ciudad, estado/provincia, país, latitud, longitud, zona horaria, ISP
- **Caché**: Resultados se cachean en sesión (1 hora)
- **Migración**: Anteriormente usábamos ipapi.co (1,000 req/día) → migrado a ipgeolocation.io para mayor cuota

### ¿Qué pasa si no se puede detectar la ubicación?

Por defecto, **permite el acceso** (fail-safe).

Puedes cambiar esto en `core/utils/geo.py:147`:
```python
# Cambiar de True a False para ser más restrictivo
'allowed': True,  # ← Cambiar a False
```

### ¿El sistema funciona con VPNs?

Sí, detecta la ubicación del servidor VPN, no la real del usuario.

### ¿Cómo desactivo temporalmente la restricción?

En `.env`:
```bash
SKIP_GEO_CHECK=True
```

Reinicia el servidor.

### ¿Las rutas del admin están bloqueadas?

NO. El middleware excluye:
- `/admin/`
- `/servicio-no-disponible/`
- `/notificarme/`
- `/static/`
- `/media/`

Ver `core/middleware.py:23` para la lista completa.

---

## Troubleshooting

### Problema: "Servicio no disponible" incluso con SKIP_GEO_CHECK=True

**Solución**:
1. Verificar `.env`:
   ```bash
   cat .env | grep SKIP_GEO_CHECK
   # Debe mostrar: SKIP_GEO_CHECK=True
   ```
2. Reiniciar servidor:
   ```bash
   python manage.py runserver
   ```
3. Verificar en Django shell:
   ```python
   from django.conf import settings
   print(settings.SKIP_GEO_CHECK)  # Debe ser True
   ```

### Problema: No se detecta la ciudad correctamente

**Posibles causas**:
1. **API Key no configurada**:
   - Verificar que `IPGEOLOCATION_API_KEY` está en `.env`
   - Solución: Añadir API key válida de ipgeolocation.io
2. **IP local (127.0.0.1)**:
   - En desarrollo, se usa IP local que no se puede geolocalizar
   - Solución: Usar `set_test_ip()` para simular
3. **Límite de API alcanzado**:
   - ipgeolocation.io tiene límite de 50,000 req/mes
   - Solución: Verificar cuota en dashboard de ipgeolocation.io
4. **Sin conexión a internet**:
   - La API requiere internet
   - Solución: Usar SKIP_GEO_CHECK=True para desarrollo offline

### Problema: Ciudades no aparecen en Admin

**Solución**:
```bash
# Verificar migraciones
python manage.py showmigrations core

# Si no están aplicadas:
python manage.py migrate

# Cargar fixture
python manage.py loaddata core/fixtures/ciudades_iniciales.json
```

### Problema: Error "requests module not found"

**Solución**:
```bash
pip install requests
```

### Problema: Cache de geolocalización desactualizado

**Solución**:
```python
# Django shell
from django.core.cache import cache
cache.clear()  # Limpia todo el caché
```

O reinicia el servidor.

---

## Expansión a Nuevas Ciudades

### Proceso Recomendado

1. **Analizar Demanda**:
   - Admin → Notificaciones de Expansión
   - Identificar ciudades con más solicitudes

2. **Habilitar Ciudad**:
   - Admin → Ciudades Habilitadas → Añadir
   - Rellenar datos, marcar como Activo

3. **Notificar Usuarios** (Manual):
   - Filtrar notificaciones por ciudad
   - Enviar email de lanzamiento
   - Marcar como "Notificado"

4. **Monitorear**:
   - Logs de accesos
   - Nuevas registraciones
   - Feedback de usuarios

---

## API de Geolocalización - Alternativas

### Opción 1: ipgeolocation.io (Actual) ✅

✅ **Ventajas**:
- Gratuita (50,000 req/mes)
- Fácil de usar (HTTP REST)
- Datos completos (ciudad, provincia, país, timezone, ISP)
- Buena precisión

❌ **Desventajas**:
- Requiere API key
- Requiere internet

### Opción 2: ipapi.co (Anterior - Deprecado)

⚠️ **Migrado a ipgeolocation.io**:
- Límite muy bajo (1,000 req/día)
- No suficiente para producción

### Opción 3: MaxMind GeoLite2

✅ **Ventajas**:
- Base de datos local (sin límites)
- Más rápido (sin latency de red)
- Funciona offline

❌ **Desventajas**:
- Requiere instalación de `geoip2`
- BD debe actualizarse mensualmente
- Más complejo de configurar

**Implementación** (si quieres cambiar):
```bash
pip install geoip2
```

En `core/utils/geo.py`, reemplazar `get_location_from_ip()` con GeoIP2.

---

## Métricas y Analytics

### Datos que puedes analizar:

1. **Solicitudes de expansión**:
   - Qué ciudades tienen más demanda
   - Provincias con mayor interés

2. **Ciudades bloqueadas** (en logs):
   - De dónde provienen los visitantes
   - Cuántos usuarios rechazados por ubicación

3. **Conversión por ciudad**:
   - Registros vs visitantes por ciudad
   - Ciudades con mejor engagement

### Query útil:

```python
# Django shell
from core.models import NotificacionExpansion
from django.db.models import Count

# Top ciudades solicitadas
top_cities = NotificacionExpansion.objects.values('ciudad_deseada').annotate(
    count=Count('id')
).order_by('-count')[:10]

for city in top_cities:
    print(f"{city['ciudad_deseada']}: {city['count']} solicitudes")
```

---

## Roadmap Futuro

### Features Planificados

- [ ] Notificaciones automáticas por email cuando se habilita ciudad
- [ ] Dashboard de analytics de expansión
- [ ] Sistema de pre-registro para nuevas ciudades
- [ ] Geo-targeting de ads por ciudad
- [ ] Detección de provincia fallback si ciudad no disponible
- [ ] Multi-idioma según país detectado

---

**Última actualización**: 2025-12-04
**Versión del sistema**: 1.0.0
**Mantenedor**: SubjectSupport Team
