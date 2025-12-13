#!/usr/bin/env python
"""
Test para verificar case sensitivity en búsqueda de ciudades habilitadas.
Ejecutar: python test_case_sensitivity.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')
django.setup()

from core.models import CiudadHabilitada
from core.utils.geo import is_service_available_in_city

print("=" * 70)
print("TEST DE CASE SENSITIVITY - BUSQUEDA DE CIUDADES")
print("=" * 70)
print()

# Primero, mostrar ciudades activas en BD
print("1. Ciudades activas en la base de datos:")
ciudades_activas = CiudadHabilitada.objects.filter(activo=True)
for ciudad in ciudades_activas:
    print(f"   - {ciudad.ciudad}, {ciudad.provincia}, {ciudad.pais}")
print()

# Test cases con diferentes variaciones de mayúsculas/minúsculas
test_cases = [
    ("Milagro", "Guayas"),
    ("milagro", "guayas"),
    ("MILAGRO", "GUAYAS"),
    ("MiLaGrO", "GuAyAs"),
    ("Milagro", "guayas"),
    ("milagro", "Guayas"),
]

print("2. Probando variaciones de case sensitivity:")
print()

for ciudad, provincia in test_cases:
    print(f"   Buscando: ciudad='{ciudad}', provincia='{provincia}'")
    disponible, ciudad_obj = is_service_available_in_city(ciudad, provincia)

    if disponible:
        print(f"   [OK] SUCCESS - Match encontrado: {ciudad_obj.ciudad}, {ciudad_obj.provincia}")
    else:
        print(f"   [FAIL] No match encontrado")
    print()

print("=" * 70)
print("RESULTADO")
print("=" * 70)
print()
print("Si todos los test cases muestran 'SUCCESS', el case sensitivity")
print("esta funcionando correctamente y 'Milagro'/'milagro'/'MILAGRO'")
print("son tratados como iguales.")
print()
print("=" * 70)
