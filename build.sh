#!/usr/bin/env bash
set -o errexit
# Encontrar GDAL dinámicamente en Nix store
export GDAL_LIBRARY_PATH=$(find /nix/store -name "libgdal.so" 2>/dev/null | head -1)
export GEOS_LIBRARY_PATH=$(find /nix/store -name "libgeos_c.so" 2>/dev/null | head -1)
echo "GDAL: $GDAL_LIBRARY_PATH"
echo "GEOS: $GEOS_LIBRARY_PATH"



pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Poblar ServiceArea (GeoDjango) SOLO si la tabla está vacía
python manage.py shell << EOF
try:
    from apps.academicTutoring.models import ServiceArea
    if not ServiceArea.objects.exists():
        from django.core.management import call_command
        call_command('populate_service_areas')
        print('ServiceArea populated')
    else:
        print('ServiceArea already exists')
except Exception as e:
    print(f'GIS skipped: {e}')
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
