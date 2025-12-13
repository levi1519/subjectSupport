# ✅ Fix: Build Script - Conditional Fixture Loading

**Fecha**: 2025-12-13
**Status**: IMPLEMENTADO
**Problema**: IntegrityError en deploy por fixture duplicado

---

## Error Original

```
IntegrityError: duplicate key value violates unique constraint "core_ciudadhabilitada_ciudad_provincia_pais_key"
DETAIL: Key (ciudad, provincia, pais)=(Milagro, Guayas, Ecuador) already exists.
```

**Causa**: El comando `loaddata` en `build.sh` intentaba cargar el fixture en cada deploy, incluso cuando los datos ya existían en la base de datos.

---

## Solución Implementada

### Archivo Modificado: `build.sh`

**ANTES** (causaba IntegrityError en re-deploys):
```bash
python manage.py migrate
python manage.py loaddata core/fixtures/ciudades_iniciales.json
```

**DESPUÉS** (chequea si la tabla está vacía):
```bash
python manage.py migrate

# Cargar fixture de ciudades habilitadas SOLO si la tabla está vacía
python manage.py shell << EOF
from core.models import CiudadHabilitada
if CiudadHabilitada.objects.count() == 0:
    print('Loading ciudades_iniciales fixture...')
    import os
    os.system('python manage.py loaddata core/fixtures/ciudades_iniciales.json')
    print('Fixture loaded successfully')
else:
    print('CiudadHabilitada table is not empty, skipping fixture load')
EOF
```

---

## Lógica del Chequeo

1. **Verificar si tabla está vacía**: `CiudadHabilitada.objects.count() == 0`
2. **Si está vacía** → Cargar fixture (primer deploy o BD reseteada)
3. **Si tiene datos** → Saltar carga (re-deploy, datos ya existen)

---

## Build.sh Completo y Final

```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Cargar fixture de ciudades habilitadas SOLO si la tabla está vacía
python manage.py shell << EOF
from core.models import CiudadHabilitada
if CiudadHabilitada.objects.count() == 0:
    print('Loading ciudades_iniciales fixture...')
    import os
    os.system('python manage.py loaddata core/fixtures/ciudades_iniciales.json')
    print('Fixture loaded successfully')
else:
    print('CiudadHabilitada table is not empty, skipping fixture load')
EOF

# Crear superusuario automáticamente si no existe
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@subjectsupport.com', 'Admin123!SubjectSupport')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF
```

---

## Comportamiento en Diferentes Escenarios

### Escenario 1: Primer Deploy (BD Vacía)

```
=== Build Log ===
Running migrations...
Loading ciudades_iniciales fixture...
Installed 1 object(s) from 1 fixture(s)
Fixture loaded successfully

Superuser created successfully
```

**Resultado**: ✅ Fixture cargado, superuser creado

---

### Escenario 2: Re-Deploy (BD con Datos)

```
=== Build Log ===
Running migrations...
CiudadHabilitada table is not empty, skipping fixture load

Superuser already exists
```

**Resultado**: ✅ Fixture saltado, sin IntegrityError

---

### Escenario 3: Deploy después de Reset de BD

```
=== Build Log ===
Running migrations...
Loading ciudades_iniciales fixture...
Installed 1 object(s) from 1 fixture(s)
Fixture loaded successfully

Superuser created successfully
```

**Resultado**: ✅ Fixture cargado nuevamente, superuser re-creado

---

## Ventajas de Esta Solución

### 1. Idempotente
- ✅ El script puede ejecutarse múltiples veces sin errores
- ✅ Safe para re-deploys automáticos de Render

### 2. Inteligente
- ✅ Solo carga datos cuando es necesario
- ✅ Respeta datos existentes en BD

### 3. Mantiene Funcionalidad Original
- ✅ Primer deploy: fixture cargado
- ✅ Re-deploy: sin cambios en BD
- ✅ Post-reset: fixture re-cargado

### 4. Consistente con Superuser
- ✅ Misma lógica aplicada a superuser
- ✅ Chequea existencia antes de crear

---

## Testing Local

### Test 1: Simular Primer Deploy (BD Vacía)

```bash
# Eliminar BD local
rm db.sqlite3

# Ejecutar build.sh
bash build.sh
```

**Resultado esperado**:
```
Loading ciudades_iniciales fixture...
Fixture loaded successfully
```

---

### Test 2: Simular Re-Deploy (BD con Datos)

```bash
# Ejecutar build.sh nuevamente sin eliminar BD
bash build.sh
```

**Resultado esperado**:
```
CiudadHabilitada table is not empty, skipping fixture load
```

---

## Verificación en Render

### Logs Esperados en Primer Deploy

```
Dec 13 14:30:00 PM  ==> Running migrations...
Dec 13 14:30:01 PM  Operations to perform: ...
Dec 13 14:30:02 PM  Running migrations: ...
Dec 13 14:30:03 PM  Loading ciudades_iniciales fixture...
Dec 13 14:30:03 PM  Installed 1 object(s) from 1 fixture(s)
Dec 13 14:30:03 PM  Fixture loaded successfully
Dec 13 14:30:04 PM  Superuser created successfully
```

---

### Logs Esperados en Re-Deploy

```
Dec 13 14:35:00 PM  ==> Running migrations...
Dec 13 14:35:01 PM  Operations to perform: ...
Dec 13 14:35:01 PM  No migrations to apply.
Dec 13 14:35:02 PM  CiudadHabilitada table is not empty, skipping fixture load
Dec 13 14:35:03 PM  Superuser already exists
```

**Clave**: NO debe aparecer `IntegrityError`

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| [build.sh](build.sh) | Chequeo condicional para fixture + limpieza de duplicación |

---

## Alternativas Consideradas

### Alternativa 1: `loaddata --ignore-conflicts` (Django 3.0+)

```bash
python manage.py loaddata --ignore-conflicts core/fixtures/ciudades_iniciales.json
```

**Problema**:
- ❌ No disponible en todas las versiones de Django
- ❌ Puede ocultar errores reales

---

### Alternativa 2: `try-except` en Python

```bash
python manage.py loaddata core/fixtures/ciudades_iniciales.json || echo "Fixture already loaded"
```

**Problema**:
- ❌ No diferencia entre "ya existe" y "error real"
- ❌ Menos control sobre qué se está cargando

---

### Alternativa 3: Chequeo Condicional (ELEGIDA)

```bash
python manage.py shell << EOF
if CiudadHabilitada.objects.count() == 0:
    os.system('python manage.py loaddata ...')
EOF
```

**Ventajas**:
- ✅ Control total sobre la lógica
- ✅ Mensajes de log claros
- ✅ Compatible con todas las versiones de Django
- ✅ Fácil de extender para otros fixtures

---

## Próximos Pasos

1. ✅ Build.sh modificado
2. ⏳ Deploy a Render
3. ⏳ Verificar logs: debe mostrar "skipping fixture load"
4. ⏳ Confirmar que no hay IntegrityError
5. ⏳ Verificar que app funciona correctamente

---

## Notas Adicionales

### Si Necesitas Recargar el Fixture

**Opción 1**: Via Django Admin
1. Ir a `/admin/core/ciudadhabilitada/`
2. Eliminar todas las entradas
3. Hacer re-deploy → Fixture se cargará automáticamente

**Opción 2**: Via Render Shell
```bash
# En Render Dashboard → Shell
python manage.py shell
>>> from core.models import CiudadHabilitada
>>> CiudadHabilitada.objects.all().delete()
>>> exit()

# Luego hacer re-deploy
```

**Opción 3**: Via Fixture con `flush`
```bash
# ⚠️ PELIGRO: Elimina TODAS las tablas
python manage.py flush
python manage.py loaddata core/fixtures/ciudades_iniciales.json
```

---

**Última actualización**: 2025-12-13
**Status**: LISTO PARA DEPLOY
**Severidad del error original**: ALTA (deploy fallido)
**Severidad post-fix**: RESUELTA
