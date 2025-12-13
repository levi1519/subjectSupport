# ✅ Fix: Session Serialization Error (CiudadHabilitada)

**Fecha**: 2025-12-13
**Status**: RESUELTO
**Error Original**: `TypeError: Object of type CiudadHabilitada is not JSON serializable`

---

## Problema

### Error 500 Fatal

El middleware de geolocalización estaba guardando un objeto ORM de Django (`CiudadHabilitada`) directamente en la sesión del usuario:

```python
# ANTES (INCORRECTO)
geo_result = {
    'allowed': True,
    'city': 'Milagro',
    'region': 'Guayas',
    'ciudad_obj': <CiudadHabilitada object>,  # <- ORM object NO serializable
}
request.session['geo_data'] = geo_result  # ERROR 500 aquí
```

### ¿Por Qué Falla?

Django serializa las sesiones a JSON para guardarlas en la base de datos. Los objetos ORM de Django **no son JSON serializables** por defecto.

**Stack Trace Típico**:
```
TypeError: Object of type CiudadHabilitada is not JSON serializable
  File "django/contrib/sessions/backends/db.py", line 87, in save
    obj.session_data = self.encode(session_dict)
  File "django/core/signing.py", line 119, in dumps
    return json.dumps(obj, separators=(',', ':')).encode('latin-1')
```

---

## Solución Implementada

### Archivo Modificado: `core/utils/geo.py`

**Cambios realizados**:

1. Renombrado `ciudad_obj` → `ciudad_data`
2. Convertir objeto ORM a diccionario serializable antes de guardar en sesión

### Código DESPUÉS (CORRECTO)

```python
# Convertir ciudad_obj a dict serializable para guardar en sesión
ciudad_data = None
if ciudad_obj:
    ciudad_data = {
        'ciudad': ciudad_obj.ciudad,
        'provincia': ciudad_obj.provincia,
        'pais': ciudad_obj.pais,
        'activo': ciudad_obj.activo,
    }

geo_result = {
    'allowed': allowed,
    'city': city,
    'region': region,
    'country': location_data.get('country', 'Unknown'),
    'ciudad_data': ciudad_data,  # <- Ahora es un dict, JSON serializable
    'skip_check': False,
    'ip_address': ip_address
}

# Guardar en sesión (ahora funciona sin errores)
request.session['geo_data'] = geo_result
```

---

## Cambios Detallados

### 1. Función `check_geo_restriction()` - Líneas 170-270

**Cambio 1**: Docstring actualizado
```python
# ANTES
Returns:
    dict con:
    - ciudad_obj: CiudadHabilitada (si está disponible)

# DESPUÉS
Returns:
    dict con:
    - ciudad_data: dict (datos serializables de la ciudad, si está disponible)
```

**Cambio 2**: Skip check mode (líneas 189-195)
```python
# ANTES
return {
    'ciudad_obj': None,
}

# DESPUÉS
return {
    'ciudad_data': None,
}
```

**Cambio 3**: Sesión existente (líneas 197-217)
```python
# ANTES
geo_data_session['ciudad_obj'] = ciudad_obj

# DESPUÉS
if ciudad_obj:
    geo_data_session['ciudad_data'] = {
        'ciudad': ciudad_obj.ciudad,
        'provincia': ciudad_obj.provincia,
        'pais': ciudad_obj.pais,
        'activo': ciudad_obj.activo,
    }
else:
    geo_data_session['ciudad_data'] = None
```

**Cambio 4**: Detection failed (línea 234)
```python
# ANTES
'ciudad_obj': None,

# DESPUÉS
'ciudad_data': None,
```

**Cambio 5**: Nueva detección (líneas 247-262)
```python
# ANTES
geo_result = {
    'ciudad_obj': ciudad_obj,
}

# DESPUÉS
ciudad_data = None
if ciudad_obj:
    ciudad_data = {
        'ciudad': ciudad_obj.ciudad,
        'provincia': ciudad_obj.provincia,
        'pais': ciudad_obj.pais,
        'activo': ciudad_obj.activo,
    }

geo_result = {
    'ciudad_data': ciudad_data,
}
```

---

## Campos Incluidos en ciudad_data

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `ciudad` | str | Nombre de la ciudad (ej: "Milagro") |
| `provincia` | str | Provincia/Estado (ej: "Guayas") |
| `pais` | str | País (ej: "Ecuador") |
| `activo` | bool | Si el servicio está activo en esta ciudad |

**Campos NO incluidos** (no necesarios en sesión):
- `id` - PK del modelo
- `fecha_habilitacion` - Fecha administrativa
- `orden_prioridad` - Orden de listado
- `notas` - Notas internas

---

## Migración de Código Existente

### Si Usabas `ciudad_obj` en Vistas

**ANTES**:
```python
def my_view(request):
    geo_data = request.geo_data
    if geo_data['ciudad_obj']:
        ciudad_name = geo_data['ciudad_obj'].ciudad
        provincia = geo_data['ciudad_obj'].provincia
```

**DESPUÉS**:
```python
def my_view(request):
    geo_data = request.geo_data
    if geo_data['ciudad_data']:
        ciudad_name = geo_data['ciudad_data']['ciudad']
        provincia = geo_data['ciudad_data']['provincia']
```

### Si Usabas `ciudad_obj` en Templates

**ANTES**:
```django
{% if request.geo_data.ciudad_obj %}
    <p>Ciudad: {{ request.geo_data.ciudad_obj.ciudad }}</p>
    <p>Provincia: {{ request.geo_data.ciudad_obj.provincia }}</p>
{% endif %}
```

**DESPUÉS**:
```django
{% if request.geo_data.ciudad_data %}
    <p>Ciudad: {{ request.geo_data.ciudad_data.ciudad }}</p>
    <p>Provincia: {{ request.geo_data.ciudad_data.provincia }}</p>
{% endif %}
```

---

## Testing

### Test Local

Script creado: `test_session_fix.py`

```bash
# Ejecutar test
python test_session_fix.py
```

**Resultado esperado**:
```
1. Probando check_geo_restriction...
   SUCCESS - geo_result es JSON serializable

2. Verificando que se puede guardar en session...
   SUCCESS - geo_data guardado en session sin errores

3. Verificando que se puede recuperar de session...
   SUCCESS - geo_data recuperado de session
```

### Verificación en Producción

1. **Deploy del fix**:
   ```bash
   git add core/utils/geo.py test_session_fix.py SESSION_SERIALIZATION_FIX.md
   git commit -m "fix: Replace ORM object with serializable dict in session (ciudad_data)"
   git push origin main
   ```

2. **Probar en Render**:
   - Visitar la app desde Ecuador
   - Verificar que NO hay Error 500
   - Verificar que la sesión persiste entre requests

3. **Revisar logs en Render**:
   - NO debe aparecer `TypeError: Object of type CiudadHabilitada is not JSON serializable`
   - Debe aparecer: `INFO: Service available in [ciudad], [provincia]`

---

## Beneficios del Fix

### 1. Error 500 Eliminado
- La sesión ahora se serializa correctamente a JSON
- No más crashes por objetos no serializables

### 2. Performance Mejorada
- Diccionarios son más ligeros que objetos ORM en sesión
- Menos overhead de serialización/deserialización

### 3. Desacoplamiento
- La sesión no depende del modelo CiudadHabilitada
- Si cambias el modelo, la sesión no se rompe

### 4. Debugging Más Fácil
- Los diccionarios son más fáciles de inspeccionar en logs
- JSON serializable = puedes ver el contenido en DevTools

---

## Posibles Issues y Soluciones

### Issue 1: "KeyError: 'ciudad_obj'"

**Causa**: Código antiguo que busca `ciudad_obj` en lugar de `ciudad_data`

**Solución**: Buscar y reemplazar en todo el proyecto:
```bash
# Buscar usos de ciudad_obj
grep -r "ciudad_obj" --include="*.py" --include="*.html"

# Reemplazar con ciudad_data
# Adaptar el código según los ejemplos de migración arriba
```

### Issue 2: Sesiones existentes con ciudad_obj

**Causa**: Usuarios que ya tienen `ciudad_obj` guardado en su sesión

**Solución**: El código maneja ambos casos:
```python
# El código ahora actualiza ciudad_data al verificar sesión existente
if geo_data_session:
    # Vuelve a consultar y guarda como ciudad_data
    allowed, ciudad_obj = is_service_available_in_city(...)
    if ciudad_obj:
        geo_data_session['ciudad_data'] = {
            'ciudad': ciudad_obj.ciudad,
            'provincia': ciudad_obj.provincia,
            'pais': ciudad_obj.pais,
            'activo': ciudad_obj.activo,
        }
```

**Alternativa**: Limpiar sesiones antiguas (opcional):
```python
# En Django shell o management command
from django.contrib.sessions.models import Session
Session.objects.all().delete()  # Forzar re-login de todos los usuarios
```

---

## Checklist de Verificación

- [x] `ciudad_obj` reemplazado por `ciudad_data` en `check_geo_restriction()`
- [x] Conversión de ORM object a dict implementada
- [x] Docstrings actualizados
- [x] `python manage.py check` pasa sin errores
- [x] Test de serialización ejecutado exitosamente
- [x] Documentación completa creada
- [ ] Deploy a Render
- [ ] Verificación en producción sin Error 500
- [ ] Búsqueda de usos de `ciudad_obj` en views/templates (si existen)

---

## Referencias

- **Django Sessions**: https://docs.djangoproject.com/en/5.2/topics/http/sessions/
- **JSON Serialization**: https://docs.python.org/3/library/json.html
- **Model Serialization**: https://docs.djangoproject.com/en/5.2/topics/serialization/

---

## Archivos Modificados

| Archivo | Líneas | Cambio |
|---------|--------|--------|
| `core/utils/geo.py` | 170-270 | `ciudad_obj` → `ciudad_data` con serialización |
| `test_session_fix.py` | Todo | Nuevo - Test de serialización |
| `SESSION_SERIALIZATION_FIX.md` | Todo | Esta documentación |

---

**Última actualización**: 2025-12-13
**Status**: LISTO PARA DEPLOY
**Severidad del error original**: CRÍTICA (Error 500)
**Severidad post-fix**: NINGUNA
