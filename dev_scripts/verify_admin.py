#!/usr/bin/env python
"""
Script de verificación de configuración del Admin de Django.
Ejecutar: python verify_admin.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'subjectSupport.settings')
django.setup()

from django.conf import settings
from django.urls import get_resolver, URLPattern, URLResolver
from django.contrib import admin


def check_admin_in_installed_apps():
    """Verifica que django.contrib.admin está en INSTALLED_APPS"""
    return 'django.contrib.admin' in settings.INSTALLED_APPS


def check_admin_url_configured():
    """Verifica que la URL /admin/ está configurada"""
    resolver = get_resolver()

    for pattern in resolver.url_patterns:
        if hasattr(pattern, 'pattern'):
            pattern_str = str(pattern.pattern)
            if 'admin/' in pattern_str:
                return True, pattern_str

    return False, None


def check_middleware_excludes_admin():
    """Verifica que el middleware de geo excluye /admin/"""
    from core.middleware import GeoRestrictionMiddleware

    return '/admin/' in GeoRestrictionMiddleware.EXCLUDED_PATHS


def check_admin_migrations():
    """Verifica que las migraciones del admin están aplicadas"""
    from django.db.migrations.recorder import MigrationRecorder

    try:
        applied = MigrationRecorder.Migration.objects.filter(app='admin').exists()
        return applied
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("VERIFICACIÓN DE CONFIGURACIÓN DEL ADMIN DE DJANGO")
    print("=" * 60)
    print()

    # 1. INSTALLED_APPS
    print("✓ 1. Verificando INSTALLED_APPS...")
    if check_admin_in_installed_apps():
        print("   ✅ django.contrib.admin está en INSTALLED_APPS")
    else:
        print("   ❌ django.contrib.admin NO está en INSTALLED_APPS")
        print("   → Añadir 'django.contrib.admin' a INSTALLED_APPS en settings.py")
    print()

    # 2. URL Configuration
    print("✓ 2. Verificando configuración de URLs...")
    configured, pattern = check_admin_url_configured()
    if configured:
        print(f"   ✅ URL del admin configurada: {pattern}")
    else:
        print("   ❌ URL del admin NO está configurada")
        print("   → Añadir path('admin/', admin.site.urls) a urls.py")
    print()

    # 3. Middleware Exclusion
    print("✓ 3. Verificando middleware de geolocalización...")
    if check_middleware_excludes_admin():
        print("   ✅ /admin/ está excluido del middleware de geolocalización")
    else:
        print("   ⚠️  /admin/ NO está excluido del middleware")
        print("   → Añadir '/admin/' a EXCLUDED_PATHS en GeoRestrictionMiddleware")
    print()

    # 4. Migrations
    print("✓ 4. Verificando migraciones del admin...")
    migrations_result = check_admin_migrations()
    if migrations_result is True:
        print("   ✅ Migraciones del admin aplicadas")
    elif migrations_result is False:
        print("   ❌ Migraciones del admin NO aplicadas")
        print("   → Ejecutar: python manage.py migrate")
    else:
        applied, error = migrations_result
        print(f"   ⚠️  Error al verificar migraciones: {error}")
    print()

    # 5. Admin Site
    print("✓ 5. Verificando Django Admin Site...")
    try:
        admin_site = admin.site
        print(f"   ✅ Admin site: {admin_site}")
        print(f"   ✅ Admin site name: {admin_site.site_header}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()

    # Resumen
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print()
    print("URL del admin: http://localhost:8000/admin/")
    print("URL de producción: https://tu-app.onrender.com/admin/")
    print()
    print("Para crear superusuario:")
    print("  python manage.py createsuperuser")
    print()
    print("Para verificar en producción (Render):")
    print("  Dashboard → Shell → python manage.py createsuperuser")
    print()
    print("=" * 60)


if __name__ == '__main__':
    main()
