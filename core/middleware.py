"""
Middleware para restricción geográfica del servicio.

Este middleware intercepta requests y verifica si el usuario
está accediendo desde una ciudad habilitada.
"""

import logging
from django.shortcuts import redirect
from django.urls import reverse
from core.utils.geo import check_geo_restriction

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
        # Verificar si la ruta actual está excluida
        path = request.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            # Saltar verificación para rutas excluidas
            response = self.get_response(request)
            return response

        # Verificar restricción geográfica
        geo_result = check_geo_restriction(request)

        # Si NO está permitido el acceso
        if not geo_result['allowed']:
            # Guardar información de geolocalización en sesión
            # (útil para mostrar en la página de "no disponible")
            request.session['geo_blocked'] = True
            request.session['geo_city'] = geo_result.get('city', 'Unknown')
            request.session['geo_region'] = geo_result.get('region', 'Unknown')
            request.session['geo_country'] = geo_result.get('country', 'Unknown')

            logger.info(
                f"Access blocked for user from {geo_result.get('city')}, "
                f"{geo_result.get('region')} (IP: {geo_result.get('ip_address')})"
            )

            # Redirigir a página de "servicio no disponible"
            return redirect('servicio_no_disponible')

        # Si está permitido, agregar info de geolocalización al request
        # (útil para filtrar tutores por ubicación, etc.)
        request.geo_data = geo_result

        # Continuar con la request normal
        response = self.get_response(request)
        return response
