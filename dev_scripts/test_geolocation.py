#!/usr/bin/env python3
"""
Script de prueba para el sistema de geolocalización.
Simula diferentes IPs y verifica que la restricción geográfica funcione correctamente.
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

from core.utils.geo import (
    get_location_from_ip,
    is_service_available_in_city,
    get_available_cities
)
from core.models import CiudadHabilitada


def test_ip_geolocation():
    """Test 1: Probar detección de ubicación por IP"""
    print("=" * 70)
    print("TEST 1: Detección de Ubicación por IP")
    print("=" * 70)

    # IPs de prueba (públicas de diferentes ubicaciones)
    test_ips = [
        ('8.8.8.8', 'Google DNS - Mountain View, CA'),
        ('1.1.1.1', 'Cloudflare DNS - Los Angeles, CA'),
        ('190.15.128.1', 'Ecuador - ISP local'),
    ]

    for ip, description in test_ips:
        print(f"\n→ Probando IP: {ip} ({description})")
        location = get_location_from_ip(ip)

        if location:
            print(f"  ✓ Ciudad: {location.get('city', 'N/A')}")
            print(f"  ✓ Región: {location.get('region', 'N/A')}")
            print(f"  ✓ País: {location.get('country', 'N/A')}")
        else:
            print(f"  ❌ No se pudo obtener información de ubicación")

    print("\n")


def test_ciudad_habilitada():
    """Test 2: Verificar ciudades habilitadas en BD"""
    print("=" * 70)
    print("TEST 2: Ciudades Habilitadas en Base de Datos")
    print("=" * 70)

    ciudades = get_available_cities()

    if ciudades:
        print(f"\n✓ Encontradas {ciudades.count()} ciudad(es) habilitada(s):\n")
        for ciudad in ciudades:
            status = "✓ Activo" if ciudad.activo else "✗ Inactivo"
            print(f"  - {ciudad.ciudad}, {ciudad.provincia} ({status})")
            print(f"    Prioridad: {ciudad.orden_prioridad}")
    else:
        print("\n⚠️  No hay ciudades habilitadas en la base de datos")
        print("    Ejecuta: python manage.py loaddata core/fixtures/ciudades_iniciales.json")

    print("\n")


def test_service_availability():
    """Test 3: Verificar disponibilidad de servicio por ciudad"""
    print("=" * 70)
    print("TEST 3: Verificación de Disponibilidad de Servicio")
    print("=" * 70)

    test_cities = [
        ('Milagro', 'Guayas'),
        ('Guayaquil', 'Guayas'),
        ('Quito', 'Pichincha'),
        ('Cuenca', 'Azuay'),
    ]

    for ciudad, provincia in test_cities:
        print(f"\n→ Verificando: {ciudad}, {provincia}")
        available, ciudad_obj = is_service_available_in_city(ciudad, provincia)

        if available:
            print(f"  ✅ Servicio DISPONIBLE")
            print(f"     Ciudad registrada: {ciudad_obj}")
        else:
            print(f"  ❌ Servicio NO disponible")

    print("\n")


def test_fixture_load():
    """Test 4: Verificar si el fixture inicial está cargado"""
    print("=" * 70)
    print("TEST 4: Verificación de Fixture Inicial")
    print("=" * 70)

    milagro = CiudadHabilitada.objects.filter(
        ciudad__iexact='Milagro',
        provincia__iexact='Guayas'
    ).first()

    if milagro:
        print("\n✅ Fixture inicial CARGADO correctamente")
        print(f"   Ciudad: {milagro.ciudad}, {milagro.provincia}")
        print(f"   Activo: {milagro.activo}")
        print(f"   Prioridad: {milagro.orden_prioridad}")
        print(f"   Notas: {milagro.notas}")
    else:
        print("\n❌ Fixture inicial NO está cargado")
        print("\nPara cargar el fixture:")
        print("   python manage.py loaddata core/fixtures/ciudades_iniciales.json")

    print("\n")


def test_skip_geo_check():
    """Test 5: Verificar configuración SKIP_GEO_CHECK"""
    print("=" * 70)
    print("TEST 5: Configuración SKIP_GEO_CHECK")
    print("=" * 70)

    from django.conf import settings

    skip_check = settings.SKIP_GEO_CHECK

    print(f"\n✓ SKIP_GEO_CHECK = {skip_check}")

    if skip_check:
        print("  ⚠️  Restricción geográfica DESACTIVADA (modo desarrollo)")
        print("     Todos los usuarios pueden acceder sin importar su ubicación")
    else:
        print("  ✓ Restricción geográfica ACTIVADA (modo producción)")
        print("     Solo usuarios de ciudades habilitadas pueden acceder")

    print("\n")


def run_all_tests():
    """Ejecutar todos los tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "TESTS DE GEOLOCALIZACIÓN" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print("\n")

    try:
        test_fixture_load()
        test_ciudad_habilitada()
        test_service_availability()
        test_skip_geo_check()

        # Test IP geolocation solo si hay conexión
        print("⚠️  Test de detección por IP requiere conexión a internet...")
        print("    Omitiendo por ahora. Ejecuta manualmente si lo necesitas.\n")
        # test_ip_geolocation()

        print("=" * 70)
        print("✅ TESTS COMPLETADOS")
        print("=" * 70)

        print("\n📋 Próximos pasos:")
        print("   1. Cargar fixture: python manage.py loaddata core/fixtures/ciudades_iniciales.json")
        print("   2. Crear migraciones: python manage.py makemigrations")
        print("   3. Aplicar migraciones: python manage.py migrate")
        print("   4. Iniciar servidor: python manage.py runserver")
        print("   5. Probar en navegador: http://localhost:8000")
        print("\n")

    except Exception as e:
        print(f"\n❌ ERROR durante los tests: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    try:
        run_all_tests()
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrumpidos por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
