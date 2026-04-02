#!/usr/bin/env python
"""
Script de prueba para verificar configuración de logging.
Ejecutar: python test_logging.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')
django.setup()

import logging

# Obtener loggers
logger_core = logging.getLogger('core')
logger_accounts = logging.getLogger('accounts')
logger_django = logging.getLogger('django')
logger_root = logging.getLogger()

print("=" * 70)
print("TEST DE CONFIGURACIÓN DE LOGGING")
print("=" * 70)
print()

# Test 1: Logger core
print("1. Testing logger 'core'...")
logger_core.debug("DEBUG message from core (should NOT appear)")
logger_core.info("INFO message from core (should appear)")
logger_core.warning("WARNING message from core (should appear)")
logger_core.error("ERROR message from core (should appear)")
print()

# Test 2: Logger accounts
print("2. Testing logger 'accounts'...")
logger_accounts.info("INFO message from accounts (should appear)")
print()

# Test 3: Logger django
print("3. Testing logger 'django'...")
logger_django.info("INFO message from django (should appear)")
print()

# Test 4: Root logger
print("4. Testing root logger...")
logger_root.info("INFO message from root (should appear)")
print()

# Test 5: Simular mensaje del middleware
print("5. Simulating middleware log...")
logger_middleware = logging.getLogger('core.middleware')
logger_middleware.info("Middleware IP Detectada: 192.168.1.1. Headers: X-Forwarded-For: None, REMOTE_ADDR: 192.168.1.1")
print()

# Test 6: Simular mensaje de geolocalización
print("6. Simulating geo log...")
logger_geo = logging.getLogger('core.utils.geo')
logger_geo.info("Geo API called with IP: 8.8.8.8")
logger_geo.info("API Status for IP 8.8.8.8: 200")
logger_geo.info("Raw API Response for IP 8.8.8.8: {'city': 'Mountain View', 'state_prov': 'California', 'country_name': 'United States'}")
print()

print("=" * 70)
print("RESULTADO")
print("=" * 70)
print()
print("Si ves mensajes con 'INFO', 'WARNING' y 'ERROR' arriba,")
print("la configuración de logging está funcionando correctamente.")
print()
print("Los mensajes DEBUG NO deben aparecer (nivel configurado a INFO).")
print()
print("=" * 70)
