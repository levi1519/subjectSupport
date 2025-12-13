"""
Middleware para restricción geográfica del servicio.

Este middleware intercepta requests y verifica si el usuario
está accediendo desde una ciudad habilitada.
"""

import logging
from django.shortcuts import redirect
from django.urls import reverse
from core.utils.geo import check_geo_restriction, get_location_from_ip, is_service_available_in_city

logger = logging.getLogger(__name__)


class GeoRestrictionMiddleware:
    """
    Middleware que restringe el acceso al sitio basado en geolocalización.

    Flujo:
    1. Obtiene IP del usuario
    2. Detecta ciudad usando API de geolocalización
    3. Verifica si la ciudad está habilitada en la base de datos
    4. Si NO está habilitada → redirige a página "servicio no disponible"
    5. Si SÍ está habilitada → permite acceso normal
    """

    # URLs que NO requieren verificación geográfica
    # (páginas públicas, admin, API, etc.)
    EXCLUDED_PATHS = [
        '/admin/',
        '/servicio-no-disponible/',
        '/notificarme/',
        '/static/',
        '/media/',
        # Añade más rutas públicas según necesites
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # A) Rutas Exentas
        path = request.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return self.get_response(request)

        # B) BYPASS: Usuarios Autenticados
        if request.user.is_authenticated:
            return self.get_response(request)

        # C) Obtener datos de geolocalización
        geo_result = check_geo_restriction(request)
        
        country = geo_result.get('country')
        is_city_allowed = geo_result.get('allowed')

        # D) Implementar reglas de acceso
        access_granted = False

        # Política Tutores: Ecuador
        if path.startswith('/tutores/'):
            if country == 'Ecuador':
                access_granted = True
            # También permitimos si pasa la validación estricta (por si acaso)
            elif is_city_allowed:
                access_granted = True
        
        # Política Estudiantes (Default): Milagro
        else:
            if is_city_allowed:
                access_granted = True

        # E) Redirección si el acceso es denegado
        if not access_granted:
            request.session['geo_blocked'] = True
            request.session['geo_city'] = geo_result.get('city', 'Unknown')
            request.session['geo_region'] = geo_result.get('region', 'Unknown')
            request.session['geo_country'] = geo_result.get('country', 'Unknown')

            logger.info(
                f"Access blocked for user from {geo_result.get('city')}, "
                f"{geo_result.get('region')}, {country} "
                f"(Target: {path})"
            )

            # Redirigir a página de "servicio no disponible"
            return redirect('servicio_no_disponible')

        request.geo_data = geo_result

        return self.get_response(request)
