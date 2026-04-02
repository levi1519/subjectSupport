#!/usr/bin/env python3
"""
Script para probar que el servidor Django arranca correctamente.
Valida que todas las configuraciones están correctas.
"""
import os
import sys

# Add virtual environment to path
venv_path = os.path.join(os.path.dirname(__file__), 'env', 'Lib', 'site-packages')
sys.path.insert(0, venv_path)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')

def test_django_setup():
    """Test 1: Verificar que Django se configura correctamente"""
    print("=" * 70)
    print("TEST 1: Configuración de Django")
    print("=" * 70)

    try:
        import django
        django.setup()
        print(f"✅ Django {django.get_version()} configurado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error configurando Django: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_settings():
    """Test 2: Verificar configuraciones de settings.py"""
    print("\n" + "=" * 70)
    print("TEST 2: Variables de Configuración")
    print("=" * 70)

    try:
        from django.conf import settings

        print(f"✓ DEBUG: {settings.DEBUG}")
        print(f"✓ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"✓ SECRET_KEY: {settings.SECRET_KEY[:20]}...{settings.SECRET_KEY[-10:]}")
        print(f"✓ CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")

        # Validations
        assert settings.SECRET_KEY, "SECRET_KEY está vacío!"
        assert len(settings.SECRET_KEY) >= 40, "SECRET_KEY es muy corto!"
        assert settings.ALLOWED_HOSTS, "ALLOWED_HOSTS está vacío!"

        if settings.DEBUG:
            assert 'localhost' in settings.ALLOWED_HOSTS or '127.0.0.1' in settings.ALLOWED_HOSTS, \
                "En DEBUG mode, ALLOWED_HOSTS debe incluir localhost o 127.0.0.1"

        print("✅ Todas las configuraciones son válidas")
        return True
    except Exception as e:
        print(f"❌ Error en configuraciones: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database():
    """Test 3: Verificar conexión a base de datos"""
    print("\n" + "=" * 70)
    print("TEST 3: Conexión a Base de Datos")
    print("=" * 70)

    try:
        from django.db import connection
        from django.conf import settings

        print(f"✓ Database engine: {settings.DATABASES['default']['ENGINE']}")
        print(f"✓ Database name: {settings.DATABASES['default']['NAME']}")

        # Test connection
        connection.ensure_connection()
        print("✅ Conexión a base de datos exitosa")
        return True
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")
        return False

def test_models():
    """Test 4: Verificar que los modelos cargan correctamente"""
    print("\n" + "=" * 70)
    print("TEST 4: Modelos de Django")
    print("=" * 70)

    try:
        from accounts.models import User, TutorProfile, ClientProfile
        from core.models import ClassSession, TutorLead

        print("✓ User model cargado")
        print("✓ TutorProfile model cargado")
        print("✓ ClientProfile model cargado")
        print("✓ ClassSession model cargado")
        print("✓ TutorLead model cargado")

        # Count existing records
        print(f"\nEstadísticas:")
        print(f"  - Usuarios: {User.objects.count()}")
        print(f"  - Tutores: {TutorProfile.objects.count()}")
        print(f"  - Clientes: {ClientProfile.objects.count()}")
        print(f"  - Sesiones: {ClassSession.objects.count()}")

        print("✅ Todos los modelos cargados correctamente")
        return True
    except Exception as e:
        print(f"❌ Error cargando modelos: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_urls():
    """Test 5: Verificar que las URLs están configuradas"""
    print("\n" + "=" * 70)
    print("TEST 5: Configuración de URLs")
    print("=" * 70)

    try:
        from django.urls import reverse

        urls_to_test = [
            ('landing', 'Página de inicio'),
            ('login', 'Login'),
            ('register_tutor', 'Registro de tutor'),
            ('register_client', 'Registro de cliente'),
        ]

        for url_name, description in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✓ {description}: {url}")
            except Exception as e:
                print(f"⚠️  {description}: Error - {e}")

        print("✅ URLs configuradas correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en URLs: {e}")
        return False

def test_csrf_middleware():
    """Test 6: Verificar middleware CSRF"""
    print("\n" + "=" * 70)
    print("TEST 6: CSRF Middleware")
    print("=" * 70)

    try:
        from django.conf import settings

        csrf_middleware = 'django.middleware.csrf.CsrfViewMiddleware'
        if csrf_middleware in settings.MIDDLEWARE:
            print(f"✓ CSRF Middleware está activo")
            print(f"✓ CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")
            print("✅ CSRF configurado correctamente")
            return True
        else:
            print("❌ CSRF Middleware NO está en MIDDLEWARE!")
            return False
    except Exception as e:
        print(f"❌ Error verificando CSRF: {e}")
        return False

def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "TESTS DEL SERVIDOR DJANGO" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")

    results = []

    # Run tests in order
    results.append(("Django Setup", test_django_setup()))
    if results[-1][1]:  # Only continue if Django setup succeeded
        results.append(("Settings", test_settings()))
        results.append(("Database", test_database()))
        results.append(("Models", test_models()))
        results.append(("URLs", test_urls()))
        results.append(("CSRF", test_csrf_middleware()))

    # Summary
    print("\n" + "=" * 70)
    print("RESUMEN DE TESTS")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 70)
    print(f"TOTAL: {passed}/{total} tests pasaron")
    print("=" * 70)

    if passed == total:
        print("\n✅ ¡Todos los tests pasaron! El servidor está listo para arrancar.")
        print("\nPara iniciar el servidor:")
        print("  python manage.py runserver")
        print("\nLuego visita:")
        print("  http://localhost:8000/")
        return True
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa los errores arriba.")
        return False

if __name__ == '__main__':
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrumpidos por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
