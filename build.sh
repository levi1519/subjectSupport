#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py loaddata core/fixtures/ciudades_iniciales.json

#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py loaddata core/fixtures/ciudades_iniciales.json

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