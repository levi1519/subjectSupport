#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Cargar fixture de ciudades habilitadas SOLO si la tabla está vacía
python manage.py shell << EOF
from core.models import CiudadHabilitada
if not CiudadHabilitada.objects.exists():
    print('Loading ciudades_iniciales fixture...')
    from django.core.management import call_command
    call_command('loaddata', 'core/fixtures/ciudades_iniciales.json')
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
