#!/usr/bin/env python
"""
Test para verificar qué valores exactos retorna la API de geolocalización.
Ejecutar: python test_api_response.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')
django.setup()

from core.utils.geo import get_location_from_ip

print("=" * 70)
print("TEST DE API RESPONSE - VERIFICAR VALORES EXACTOS")
print("=" * 70)
print()

# IPs de Ecuador para testing
test_ips = [
    "190.15.128.1",   # IP ejemplo de Ecuador
    "181.39.135.1",   # Otro ejemplo
    "200.125.171.1",  # Otro ejemplo
]

print("Probando IPs de Ecuador para ver formato exacto de respuesta:")
print()

for ip in test_ips:
    print(f"IP: {ip}")
    print("-" * 70)

    location_data = get_location_from_ip(ip)

    if location_data:
        print(f"  city: '{location_data.get('city', 'N/A')}'")
        print(f"  region: '{location_data.get('region', 'N/A')}'")
        print(f"  country: '{location_data.get('country', 'N/A')}'")
        print(f"  Full response keys: {list(location_data.keys())}")
    else:
        print("  [ERROR] No se pudo obtener ubicacion")

    print()

print("=" * 70)
print("DIAGNOSTICO")
print("=" * 70)
print()
print("Revisa los valores de 'city' y 'region' arriba.")
print("Si estos NO coinciden EXACTAMENTE con 'Milagro' y 'Guayas',")
print("entonces la API esta retornando otros valores.")
print()
print("Posibles problemas:")
print("1. API retorna nombre diferente de ciudad (ej: 'Milagro Canton')")
print("2. API retorna provincia con otro nombre (ej: 'Provincia de Guayas')")
print("3. API retorna valores en ingles (ej: 'Guayas Province')")
print()
print("=" * 70)
