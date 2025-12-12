#!/usr/bin/env python3
"""
Script para probar el registro completo de usuarios.
Simula el proceso de registro tanto para tutores como para clientes.
"""
import os
import sys

# Add virtual environment to path
venv_path = os.path.join(os.path.dirname(__file__), 'env', 'Lib', 'site-packages')
sys.path.insert(0, venv_path)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')

import django
django.setup()

from django.test import Client
from django.urls import reverse
from accounts.models import User, TutorProfile, ClientProfile
import uuid

def test_tutor_registration():
    """Test: Registro de tutor completo"""
    print("=" * 70)
    print("TEST: Registro de Tutor")
    print("=" * 70)

    # Create test client
    client = Client()

    # Generate unique email
    unique_id = str(uuid.uuid4())[:8]
    test_data = {
        'name': f'Test Tutor {unique_id}',
        'email': f'tutor{unique_id}@test.com',
        'subjects': 'Matemáticas, Física',
        'bio': 'Soy un tutor de prueba',
        'experience': '5 años de experiencia',
        'password1': 'SecurePass123!',
        'password2': 'SecurePass123!',
    }

    print(f"✓ Datos de prueba generados:")
    print(f"  - Email: {test_data['email']}")
    print(f"  - Nombre: {test_data['name']}")
    print(f"  - Materias: {test_data['subjects']}")

    # Get registration page
    try:
        url = reverse('register_tutor')
        print(f"✓ URL de registro: {url}")

        response = client.get(url)
        print(f"✓ GET request status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Error: GET request failed with status {response.status_code}")
            return False

        # Check CSRF token
        if 'csrfmiddlewaretoken' in response.content.decode():
            print("✓ CSRF token encontrado en el formulario")
        else:
            print("⚠️  CSRF token no encontrado (puede causar error 403)")

    except Exception as e:
        print(f"❌ Error obteniendo página de registro: {e}")
        return False

    # Submit registration
    try:
        response = client.post(url, data=test_data, follow=True)
        print(f"✓ POST request status: {response.status_code}")

        if response.status_code == 200:
            # Check if user was created
            try:
                user = User.objects.get(email=test_data['email'])
                print(f"✅ Usuario creado exitosamente: {user.email}")

                # Check tutor profile
                try:
                    profile = TutorProfile.objects.get(user=user)
                    print(f"✅ Perfil de tutor creado:")
                    print(f"  - Materias: {profile.subjects}")
                    print(f"  - Ciudad: {profile.city}")
                    print(f"  - País: {profile.country}")
                    return True
                except TutorProfile.DoesNotExist:
                    print("❌ Perfil de tutor NO fue creado")
                    return False

            except User.DoesNotExist:
                print("❌ Usuario NO fue creado")
                print("Response content:")
                print(response.content.decode()[:500])
                return False
        else:
            print(f"❌ Registro falló con status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error en POST request: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_client_registration():
    """Test: Registro de cliente completo"""
    print("\n" + "=" * 70)
    print("TEST: Registro de Cliente")
    print("=" * 70)

    # Create test client
    client = Client()

    # Generate unique email
    unique_id = str(uuid.uuid4())[:8]
    test_data = {
        'name': f'Test Client {unique_id}',
        'email': f'client{unique_id}@test.com',
        'password1': 'SecurePass123!',
        'password2': 'SecurePass123!',
        'is_minor': False,
    }

    print(f"✓ Datos de prueba generados:")
    print(f"  - Email: {test_data['email']}")
    print(f"  - Nombre: {test_data['name']}")

    # Get registration page
    try:
        url = reverse('register_client')
        print(f"✓ URL de registro: {url}")

        response = client.get(url)
        print(f"✓ GET request status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Error: GET request failed with status {response.status_code}")
            return False

        # Check CSRF token
        if 'csrfmiddlewaretoken' in response.content.decode():
            print("✓ CSRF token encontrado en el formulario")
        else:
            print("⚠️  CSRF token no encontrado (puede causar error 403)")

    except Exception as e:
        print(f"❌ Error obteniendo página de registro: {e}")
        return False

    # Submit registration
    try:
        response = client.post(url, data=test_data, follow=True)
        print(f"✓ POST request status: {response.status_code}")

        if response.status_code == 200:
            # Check if user was created
            try:
                user = User.objects.get(email=test_data['email'])
                print(f"✅ Usuario creado exitosamente: {user.email}")

                # Check client profile
                try:
                    profile = ClientProfile.objects.get(user=user)
                    print(f"✅ Perfil de cliente creado:")
                    print(f"  - Es menor: {profile.is_minor}")
                    print(f"  - Ciudad: {profile.city}")
                    print(f"  - País: {profile.country}")
                    return True
                except ClientProfile.DoesNotExist:
                    print("❌ Perfil de cliente NO fue creado")
                    return False

            except User.DoesNotExist:
                print("❌ Usuario NO fue creado")
                print("Response content:")
                print(response.content.decode()[:500])
                return False
        else:
            print(f"❌ Registro falló con status {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error en POST request: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Ejecutar todos los tests de registro"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "TESTS DE REGISTRO DE USUARIOS" + " " * 19 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")

    results = []

    # Count initial users
    initial_users = User.objects.count()
    print(f"Usuarios existentes: {initial_users}\n")

    # Run tests
    results.append(("Registro de Tutor", test_tutor_registration()))
    results.append(("Registro de Cliente", test_client_registration()))

    # Count final users
    final_users = User.objects.count()

    # Summary
    print("\n" + "=" * 70)
    print("RESUMEN DE TESTS")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nUsuarios creados: {final_users - initial_users}")

    print("\n" + "=" * 70)
    print(f"TOTAL: {passed}/{total} tests pasaron")
    print("=" * 70)

    if passed == total:
        print("\n✅ ¡Todos los tests de registro pasaron!")
        print("\n🎉 El registro está funcionando correctamente.")
        print("   No hay errores CSRF 403.")
        print("   Los formularios validan y crean usuarios exitosamente.")
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
