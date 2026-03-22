#!/usr/bin/env python
"""
Script de prueba para verificar que la sesión puede serializar geo_data correctamente.
Ejecutar: python test_session_fix.py
"""

import os
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')
django.setup()

from core.models import CiudadHabilitada
from django.test import RequestFactory
from core.utils.geo import check_geo_restriction

print("=" * 70)
print("TEST DE SERIALIZACION DE SESSION - FIX CIUDAD_OBJ")
print("=" * 70)
print()

# Crear request factory
factory = RequestFactory()
request = factory.get('/')

# Agregar session mock
from django.contrib.sessions.middleware import SessionMiddleware
middleware = SessionMiddleware(lambda x: None)
middleware.process_request(request)
request.session.save()

print("1. Probando check_geo_restriction con SKIP_GEO_CHECK=True...")
from django.conf import settings
settings.SKIP_GEO_CHECK = True

geo_result = check_geo_restriction(request)
print(f"   allowed: {geo_result['allowed']}")
print(f"   city: {geo_result['city']}")
print(f"   ciudad_data: {geo_result.get('ciudad_data')}")
print()

print("2. Intentando serializar geo_result a JSON...")
try:
    json_str = json.dumps(geo_result)
    print("   SUCCESS - geo_result es JSON serializable")
    print(f"   JSON length: {len(json_str)} caracteres")
except TypeError as e:
    print(f"   ERROR - No se puede serializar: {e}")
print()

print("3. Verificando que se puede guardar en session...")
try:
    request.session['geo_data'] = geo_result
    request.session.save()
    print("   SUCCESS - geo_data guardado en session sin errores")
except Exception as e:
    print(f"   ERROR - Fallo al guardar en session: {e}")
print()

print("4. Verificando que se puede recuperar de session...")
try:
    retrieved = request.session.get('geo_data')
    print(f"   SUCCESS - geo_data recuperado de session")
    print(f"   allowed: {retrieved['allowed']}")
    print(f"   city: {retrieved['city']}")
    print(f"   ciudad_data: {retrieved.get('ciudad_data')}")
except Exception as e:
    print(f"   ERROR - Fallo al recuperar de session: {e}")
print()

print("=" * 70)
print("RESULTADO")
print("=" * 70)
print()
print("Si todos los tests muestran 'SUCCESS', el fix esta funcionando.")
print("El Error 500 'TypeError: Object of type CiudadHabilitada is not JSON")
print("serializable' deberia estar resuelto.")
print()
print("=" * 70)
