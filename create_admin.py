#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

if not User.objects.filter(email='admin@edulatam.com').exists():
    User.objects.create_superuser('admin@edulatam.com', 'Admin EduLatam', 'EduLatam2025!')
    print("✅ Admin creado: admin@edulatam.com / EduLatam2025!")
else:
    print("ℹ️ Admin ya existe")