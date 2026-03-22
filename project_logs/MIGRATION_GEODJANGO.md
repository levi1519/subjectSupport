# Migración a GeoDjango - Guía Completa

## Resumen de la Migración

Este documento describe la migración arquitectónica del sistema de restricción geográfica de SubjectSupport, pasando de un sistema basado en comparación de strings a una solución robusta y estandarizada con GeoDjango + PostGIS.

### Estado Anterior (Sistema Obsoleto)
- **Problema**: Restricción basada en comparación de cadenas de texto (`if city == 'Milagro'`)
- **Fragilidad**: La API de geolocalización a veces retorna "Guayaquil" en lugar de "Milagro" para IPs del área
- **Solución temporal**: "Blindaje" forzado que sobrescribía la ciudad si la provincia era "Guayas"
- **Limitaciones**: Impreciso, difícil de escalar, no permite definir áreas de cobertura precisas

### Estado Nuevo (GeoDjango + PostGIS)
- **Solución**: Consultas espaciales con polígonos geográficos
- **Precisión**: 100% basada en coordenadas GPS (latitud/longitud) del usuario
- **Tecnología**: PostGIS para consultas espaciales `area__contains=user_point`
- **Escalabilidad**: Fácil agregar nuevas ciudades dibujando polígonos en el admin de Django
- **Estándar**: Usa `django.contrib.gis`, la solución oficial de Django para GIS

---

## Archivos Modificados

### 1. Configuración (`subjectSupport/settings.py`)
```python
# NUEVO: django.contrib.gis en INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'django.contrib.gis',  # GeoDjango
    ...
]

# NUEVO: Backend PostGIS para producción
if DEBUG:
    # Desarrollo: SQLite normal (GDAL no requerido localmente)
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', ...}}
else:
    # Producción: PostGIS
    db_config['ENGINE'] = 'django.contrib.gis.db.backends.postgis'
    DATABASES = {'default': db_config}
```

### 2. Nuevo Modelo (`core/models.py`)
```python
class ServiceArea(gis_models.Model):
    """Polígono geográfico que define área de cobertura del servicio."""
    city_name = models.CharField(max_length=100, unique=True)
    area = gis_models.PolygonField(srid=4326)  # Geometría PostGIS
    activo = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 3. Nueva Lógica Geo (`core/utils/geo.py`)
**Antes** (comparación de strings):
```python
if city.lower() == 'milagro':
    return True
```

**Ahora** (consulta espacial):
```python
def is_point_in_service_area(latitude, longitude):
    user_point = Point(longitude, latitude, srid=4326)
    service_area = ServiceArea.objects.filter(
        activo=True,
        area__contains=user_point  # Consulta espacial PostGIS
    ).first()
    return (True, service_area) if service_area else (False, None)
```

### 4. Middleware Actualizado (`core/middleware.py`)
```python
# ANTES:
if ciudad_data:  # ciudad_data era un dict con ciudad hardcoded
    access_granted = True

# AHORA:
service_area = geo_result.get('service_area')  # Resultado de consulta PostGIS
if service_area:  # Usuario dentro del polígono
    access_granted = True
```

### 5. Vista de Routing Actualizada (`core/views.py`)
```python
class GeoRootRouterView(View):
    def get(self, request):
        service_area = geo_data.get('service_area')

        # NUEVA LÓGICA: Basada en geometría, no en strings
        if service_area:
            return redirect('student_landing')  # Dentro del polígono
        elif country == 'Ecuador':
            return redirect('tutor_landing')  # Ecuador pero fuera del polígono
        else:
            return redirect('servicio_no_disponible')  # Fuera de Ecuador
```

---

## Pasos de Despliegue en Producción

### Pre-requisitos
1. **PostgreSQL con PostGIS**: Verificar que la extensión PostGIS esté instalada
   ```sql
   -- Conectar a la base de datos de producción
   \c your_database_name

   -- Verificar si PostGIS está instalado
   SELECT PostGIS_version();

   -- Si no está instalado, instalarlo (requiere permisos de superuser)
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

2. **En Render.com**: PostGIS viene preinstalado en los planes PostgreSQL, solo necesitas habilitarlo:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```

### Paso 1: Habilitar PostGIS en la Base de Datos

Conectarse a la base de datos de producción y ejecutar:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Verificar instalación:
```sql
SELECT PostGIS_version();
-- Debe retornar algo como: 3.3 USE_GEOS=1 USE_PROJ=1...
```

### Paso 2: Desplegar Código

```bash
# 1. Asegurarse de estar en la rama feature/geodjango-migration
git checkout feature/geodjango-migration

# 2. Verificar que todos los cambios estén commiteados
git status

# 3. Push a la rama (Render desplegará automáticamente)
git push origin feature/geodjango-migration
```

### Paso 3: Ejecutar Migraciones

Una vez desplegado el código en Render:

```bash
# En el shell de Render, ejecutar:
python manage.py migrate

# Esto creará la tabla core_servicearea con el campo PolygonField
```

### Paso 4: Poblar Áreas de Servicio

```bash
# Ejecutar el management command para crear el polígono de Milagro:
python manage.py populate_service_areas
```

Este comando creará un `ServiceArea` para Milagro con un polígono rectangular aproximado.

### Paso 5: Refinar Polígono (Opcional pero Recomendado)

1. Acceder al admin de Django: `https://subjectsupport.onrender.com/admin/`
2. Ir a **Core → Service Areas**
3. Editar el área de "Milagro"
4. Usar el **mapa interactivo** para ajustar el polígono con mayor precisión
5. Dibujar los límites reales del Cantón Milagro
6. Guardar

### Paso 6: Verificación

1. **Probar desde Milagro**:
   - Acceder a `https://subjectsupport.onrender.com/` desde una IP de Milagro
   - Debe redirigir a `/estudiantes/`

2. **Probar desde otra ciudad de Ecuador**:
   - Debe redirigir a `/tutores/`

3. **Verificar logs**:
   ```
   Checking if point (-2.134, -79.594) is in service area
   ✓ MATCH: Point (-2.134, -79.594) is inside Milagro service area
   ```

---

## Comandos Útiles

### Verificar Estado de PostGIS
```bash
python manage.py shell

from django.contrib.gis.geos import Point
from core.models import ServiceArea

# Verificar que ServiceArea funciona
areas = ServiceArea.objects.all()
print(f"Service Areas: {areas.count()}")

# Probar consulta espacial
milagro_point = Point(-79.594, -2.134, srid=4326)  # Centro de Milagro
area = ServiceArea.objects.filter(area__contains=milagro_point).first()
print(f"Point is in: {area.city_name if area else 'No area'}")
```

### Poblar/Actualizar Áreas de Servicio
```bash
# Ejecutar el comando de población
python manage.py populate_service_areas

# Ver todas las áreas activas
python manage.py shell -c "from core.models import ServiceArea; [print(f'{a.city_name}: {a.activo}') for a in ServiceArea.objects.all()]"
```

### Limpiar Datos de Sesión (si hay problemas)
```bash
# En producción, limpiar cache de sesiones:
python manage.py clearsessions
```

---

## Rollback (Si es necesario)

Si hay problemas con la migración, se puede hacer rollback:

```bash
# 1. Revertir migraciones
python manage.py migrate core 0003_notificacionexpansion_alter_tutorlead_options_and_more

# 2. Revertir código
git checkout main
git push origin main

# 3. (Opcional) Desinstalar extensión PostGIS
# CUIDADO: Solo si NO hay otros proyectos usándola
# CREATE EXTENSION postgis;  -- en la BD
```

---

## Mantenimiento Futuro

### Agregar Nueva Ciudad

1. Ir al admin: `/admin/core/servicearea/add/`
2. Completar:
   - **City name**: Nombre de la ciudad (ej: "Guayaquil")
   - **Activo**: Marcar checkbox
   - **Descripción**: Descripción opcional
3. **Dibujar polígono** en el mapa interactivo
4. Guardar

La nueva ciudad estará inmediatamente disponible, sin necesidad de código.

### Editar Área Existente

1. Ir a `/admin/core/servicearea/`
2. Click en la ciudad a editar
3. Ajustar polígono en el mapa
4. Guardar

### Desactivar Temporalmente una Ciudad

1. Ir a `/admin/core/servicearea/`
2. Desmarcar **Activo** en la ciudad
3. Guardar

Los usuarios de esa ciudad perderán acceso inmediatamente.

---

## Notas Técnicas

### SRID 4326 (WGS84)
- Sistema de coordenadas estándar GPS
- Formato: `Point(longitude, latitude, srid=4326)`
- **IMPORTANTE**: Orden es (LON, LAT), no (LAT, LON)

### Rendimiento
- Las consultas espaciales PostGIS usan índices GiST automáticamente
- Rendimiento: ~1-2ms por consulta
- Cache en sesión evita consultas repetidas

### Modelo Legado `CiudadHabilitada`
- Marcado como DEPRECADO
- Se mantiene para compatibilidad temporal
- NO usar en nueva lógica
- Puede eliminarse en futuras versiones

---

## Recursos

- **Documentación GeoDjango**: https://docs.djangoproject.com/en/5.2/ref/contrib/gis/
- **PostGIS**: https://postgis.net/documentation/
- **Render PostgreSQL**: https://render.com/docs/databases
- **ipgeolocation.io API**: https://ipgeolocation.io/documentation/ip-geolocation-api.html

---

## Autor y Fecha

**Migración completada**: 2025-12-15
**Rama**: `feature/geodjango-migration`
**Versión Django**: 5.2.8
**Versión PostgreSQL**: 15+ con PostGIS 3.3+
