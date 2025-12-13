#!/usr/bin/env python
"""
Test para verificar el fallback de provincia.
Simula el caso donde API retorna "Guayaquil" pero usuario esta en Milagro.
Ejecutar: python test_provincia_fallback.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')
django.setup()

from core.models import CiudadHabilitada
from core.utils.geo import is_service_available_in_city

print("=" * 70)
print("TEST DE PROVINCIA FALLBACK")
print("=" * 70)
print()

# Verificar ciudades en BD
print("1. Ciudades activas en la base de datos:")
ciudades_activas = CiudadHabilitada.objects.filter(activo=True)
for ciudad in ciudades_activas:
    print(f"   - {ciudad.ciudad}, {ciudad.provincia}, {ciudad.pais}")
print()

# Test cases
test_cases = [
    # (ciudad_api, provincia_api, descripcion)
    ("Milagro", "Guayas", "Match exacto (ciudad + provincia)"),
    ("Guayaquil", "Guayas", "Fallback por provincia (API retorna Guayaquil en vez de Milagro)"),
    ("Duran", "Guayas", "Fallback por provincia (otra ciudad de Guayas)"),
    ("Cuenca", "Azuay", "No match (provincia diferente)"),
    ("Milagro", None, "Match solo por ciudad (sin provincia)"),
]

print("2. Probando diferentes escenarios:")
print()

for ciudad, provincia, descripcion in test_cases:
    print(f"   Test: {descripcion}")
    print(f"   Buscando: ciudad='{ciudad}', provincia='{provincia}'")

    disponible, ciudad_obj = is_service_available_in_city(ciudad, provincia)

    if disponible:
        print(f"   [OK] SUCCESS - Acceso permitido")
        print(f"        Matched: {ciudad_obj.ciudad}, {ciudad_obj.provincia}")
    else:
        print(f"   [BLOCKED] Acceso bloqueado")

    print()

print("=" * 70)
print("RESULTADO ESPERADO")
print("=" * 70)
print()
print("1. Match exacto (Milagro, Guayas): [OK]")
print("2. Fallback (Guayaquil, Guayas): [OK] - CLAVE para solucionar el problema")
print("3. Fallback (Duran, Guayas): [OK]")
print("4. No match (Cuenca, Azuay): [BLOCKED]")
print("5. Match solo ciudad (Milagro, None): [OK]")
print()
print("Si el test 2 muestra [OK], el fallback esta funcionando y usuarios")
print("de Milagro cuyas IPs aparezcan como 'Guayaquil' podran acceder.")
print()
print("=" * 70)
