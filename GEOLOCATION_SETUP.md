# 🚀 Setup Rápido - Sistema de Geolocalización

## Instalación en 5 Pasos

### 1. Aplicar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Cargar Fixture Inicial (Milagro habilitado)

```bash
python manage.py loaddata core/fixtures/ciudades_iniciales.json
```

### 3. Configurar .env

Asegúrate de tener en tu archivo `.env`:

```bash
# Para desarrollo/testing (permite acceso desde cualquier ubicación)
SKIP_GEO_CHECK=True

# Para producción (activa restricción geográfica)
# SKIP_GEO_CHECK=False
```

### 4. Verificar Instalación

```bash
python test_geolocation.py
```

Deberías ver:
```
✅ Fixture inicial CARGADO correctamente
✅ Servicio DISPONIBLE en: Milagro, Guayas
```

### 5. Iniciar Servidor

```bash
python manage.py runserver
```

---

## ✅ Verificación Funcional

### Test 1: Modo Desarrollo (SKIP_GEO_CHECK=True)

1. Inicia servidor
2. Visita `http://localhost:8000`
3. **Resultado esperado**: Acceso normal a la landing page

### Test 2: Modo Producción (SKIP_GEO_CHECK=False)

1. En `.env`, cambiar a `SKIP_GEO_CHECK=False`
2. Reiniciar servidor
3. Visita `http://localhost:8000`
4. **Resultado esperado**:
   - Si tu IP local: Posiblemente acceso normal
   - Si IP no identificable: Redirige a `/servicio-no-disponible/`

### Test 3: Admin - Gestionar Ciudades

1. Accede al admin: `http://localhost:8000/admin/`
2. Ve a "Core" → "Ciudades Habilitadas"
3. **Deberías ver**: Milagro, Guayas marcado como activo

---

## 🌍 Habilitar Nueva Ciudad

### Desde Django Admin

1. **Login** en `/admin/`
2. **Navega** a "Ciudades Habilitadas"
3. **Click** en "Añadir Ciudad Habilitada"
4. **Rellena**:
   - **Ciudad**: Guayaquil
   - **Provincia**: Guayas
   - **País**: Ecuador
   - **Activo**: ✓ (marcado)
   - **Orden prioridad**: 10
5. **Guardar**

### Desde Django Shell (Programáticamente)

```python
python manage.py shell

>>> from core.models import CiudadHabilitada
>>> CiudadHabilitada.objects.create(
...     ciudad='Guayaquil',
...     provincia='Guayas',
...     pais='Ecuador',
...     activo=True,
...     orden_prioridad=10
... )
```

---

## 📊 Ver Solicitudes de Notificación

Cuando un usuario fuera de zona visita, puede dejar su email. Para ver:

1. **Admin** → "Notificaciones de Expansión"
2. **Lista muestra**:
   - Email del usuario
   - Ciudad deseada
   - Ciudad detectada (por IP)
   - Si ya fue notificado

---

## 🔧 Comandos Útiles

```bash
# Aplicar migraciones
python manage.py makemigrations && python manage.py migrate

# Cargar fixture inicial
python manage.py loaddata core/fixtures/ciudades_iniciales.json

# Ver ciudades habilitadas
python manage.py shell -c "from core.models import CiudadHabilitada; print(list(CiudadHabilitada.objects.values()))"

# Test de geolocalización
python test_geolocation.py

# Limpiar caché de geolocalización
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

---

## 🚨 Troubleshooting Rápido

### Problema: "No module named 'requests'"

```bash
pip install requests
```

### Problema: "No se detecta la ciudad"

**En desarrollo local**: Normal. La IP 127.0.0.1 no se puede geolocalizar.

**Solución**: Usar `SKIP_GEO_CHECK=True` en `.env`

### Problema: "Servicio no disponible" siempre

1. Verificar `.env`:
   ```bash
   cat .env | grep SKIP_GEO_CHECK
   # Debe ser: SKIP_GEO_CHECK=True (para desarrollo)
   ```

2. Reiniciar servidor

3. Verificar en shell:
   ```bash
   python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.SKIP_GEO_CHECK)  # Debe ser True
   ```

### Problema: No aparecen ciudades en Admin

```bash
# Verificar migraciones
python manage.py showmigrations core

# Aplicar si faltan
python manage.py migrate core

# Cargar fixture
python manage.py loaddata core/fixtures/ciudades_iniciales.json
```

---

## 📖 Documentación Completa

Para más detalles, ver: **GEOLOCATION_GUIDE.md**

---

## 🎯 Próximos Pasos

1. ✅ Sistema instalado y funcionando
2. ⏳ Configurar para producción:
   - Generar nuevo SECRET_KEY
   - `SKIP_GEO_CHECK=False` en Render
   - Configurar variables de entorno en Render
3. ⏳ Habilitar ciudades adicionales según demanda
4. ⏳ Monitorear solicitudes de notificación
5. ⏳ Implementar envío automático de emails (futuro)

---

**¡Sistema listo para usar!** 🎉
