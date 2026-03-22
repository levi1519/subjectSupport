#!/usr/bin/env python
"""
Script de prueba para verificar que todos los fixes están funcionando correctamente.
Ejecutar con: python test_fixes.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')
django.setup()

from django.conf import settings
from accounts.forms import TutorRegistrationForm, ClientRegistrationForm
from accounts.models import User

def test_environment_variables():
    """Test 1: Verificar que las variables de entorno se cargan correctamente"""
    print("=" * 70)
    print("TEST 1: Verificando Variables de Entorno")
    print("=" * 70)

    print(f"✓ DEBUG: {settings.DEBUG}")
    print(f"✓ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"✓ SECRET_KEY: {settings.SECRET_KEY[:20]}...")

    if settings.DEBUG:
        print("✅ DEBUG está activado - Modo desarrollo")
    else:
        print("⚠️  DEBUG está desactivado - Modo producción")

    if 'localhost' in settings.ALLOWED_HOSTS or '127.0.0.1' in settings.ALLOWED_HOSTS:
        print("✅ ALLOWED_HOSTS incluye localhost")
    else:
        print("⚠️  ALLOWED_HOSTS NO incluye localhost - puede causar problemas en local")

    print()

def test_tutor_form_fields():
    """Test 2: Verificar que los campos city/country son opcionales en TutorRegistrationForm"""
    print("=" * 70)
    print("TEST 2: Verificando Campos Opcionales en TutorRegistrationForm")
    print("=" * 70)

    # Simular datos de formulario SIN city/country
    form_data = {
        'name': 'Test Tutor',
        'email': 'testtutor@example.com',
        'subjects': 'Matemáticas, Física',
        'password1': 'testpass123',
        'password2': 'testpass123',
        # NO incluir city/country
    }

    form = TutorRegistrationForm(data=form_data)

    city_field = form.fields.get('city')
    country_field = form.fields.get('country')

    if city_field:
        print(f"✓ Campo 'city' existe")
        print(f"  - required: {city_field.required}")
        if not city_field.required:
            print("  ✅ Campo 'city' es OPCIONAL")
        else:
            print("  ❌ Campo 'city' es REQUERIDO - PROBLEMA!")

    if country_field:
        print(f"✓ Campo 'country' existe")
        print(f"  - required: {country_field.required}")
        if not country_field.required:
            print("  ✅ Campo 'country' es OPCIONAL")
        else:
            print("  ❌ Campo 'country' es REQUERIDO - PROBLEMA!")

    print()

def test_client_form_fields():
    """Test 3: Verificar que los campos city/country son opcionales en ClientRegistrationForm"""
    print("=" * 70)
    print("TEST 3: Verificando Campos Opcionales en ClientRegistrationForm")
    print("=" * 70)

    # Simular datos de formulario SIN city/country
    form_data = {
        'name': 'Test Client',
        'email': 'testclient@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123',
        'is_minor': False,
        # NO incluir city/country
    }

    form = ClientRegistrationForm(data=form_data)

    city_field = form.fields.get('city')
    country_field = form.fields.get('country')

    if city_field:
        print(f"✓ Campo 'city' existe")
        print(f"  - required: {city_field.required}")
        if not city_field.required:
            print("  ✅ Campo 'city' es OPCIONAL")
        else:
            print("  ❌ Campo 'city' es REQUERIDO - PROBLEMA!")

    if country_field:
        print(f"✓ Campo 'country' existe")
        print(f"  - required: {country_field.required}")
        if not country_field.required:
            print("  ✅ Campo 'country' es OPCIONAL")
        else:
            print("  ❌ Campo 'country' es REQUERIDO - PROBLEMA!")

    print()

def test_form_validation():
    """Test 4: Verificar que los formularios validan sin city/country"""
    print("=" * 70)
    print("TEST 4: Validación de Formularios sin City/Country")
    print("=" * 70)

    # Test TutorRegistrationForm
    print("→ TutorRegistrationForm:")
    tutor_data = {
        'name': 'Test Tutor',
        'email': f'testtutor{os.getpid()}@example.com',  # Email único
        'subjects': 'Matemáticas',
        'password1': 'ComplexPass123!',
        'password2': 'ComplexPass123!',
    }

    tutor_form = TutorRegistrationForm(data=tutor_data)
    if tutor_form.is_valid():
        print("  ✅ Formulario de tutor es VÁLIDO sin city/country")
    else:
        print("  ❌ Formulario de tutor es INVÁLIDO")
        print(f"  Errores: {tutor_form.errors}")

    # Test ClientRegistrationForm
    print("\n→ ClientRegistrationForm:")
    client_data = {
        'name': 'Test Client',
        'email': f'testclient{os.getpid()}@example.com',  # Email único
        'password1': 'ComplexPass123!',
        'password2': 'ComplexPass123!',
        'is_minor': False,
    }

    client_form = ClientRegistrationForm(data=client_data)
    if client_form.is_valid():
        print("  ✅ Formulario de cliente es VÁLIDO sin city/country")
    else:
        print("  ❌ Formulario de cliente es INVÁLIDO")
        print(f"  Errores: {client_form.errors}")

    print()

def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "TESTS DE VERIFICACIÓN DE FIXES" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")

    try:
        test_environment_variables()
        test_tutor_form_fields()
        test_client_form_fields()
        test_form_validation()

        print("=" * 70)
        print("✅ TODOS LOS TESTS COMPLETADOS")
        print("=" * 70)
        print("\nSi todos los tests pasaron correctamente, puedes proceder a:")
        print("1. Ejecutar el servidor: python manage.py runserver")
        print("2. Probar el registro de tutores: http://localhost:8000/accounts/register/tutor/")
        print("3. Probar el registro de estudiantes: http://localhost:8000/accounts/register/client/")
        print()

    except Exception as e:
        print(f"\n❌ ERROR durante los tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_all_tests()
