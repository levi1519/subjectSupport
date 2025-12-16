#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Poblar ServiceArea (GeoDjango) SOLO si la tabla está vacía
python manage.py shell << EOF
try:
    from core.models import ServiceArea
    if not ServiceArea.objects.exists():
        print('Populating ServiceArea with Milagro polygon...')
        from django.core.management import call_command
        call_command('populate_service_areas')
        print('ServiceArea populated successfully')
    else:
        print('ServiceArea table is not empty, skipping population')
except ImportError:
    print('GIS not available, skipping ServiceArea population')
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
