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

    POLÍTICAS DE SEGURIDAD GEOGRÁFICA:
    1. /estudiantes/* → SOLO MILAGRO (ciudad_data must be True)
    2. /tutores/* → TODO ECUADOR (country must be 'Ecuador')
    3. Usuarios autenticados → Bypass (ya tienen cuenta)
    4. Admin y logout → Exentos siempre
    """

    # URLs que NO requieren verificación geográfica
    # SOLO admin, logout, y páginas de error/notificación
    EXCLUDED_PATHS = [
        '/admin/',
        '/servicio-no-disponible/',
        '/notificarme/',
        '/static/',
        '/media/',
        '/accounts/logout/',  # Permitir logout siempre
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # A) Rutas Exentas (solo admin, logout, static, error pages)
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return self.get_response(request)

        # B) BYPASS: Usuarios Autenticados (ya verificados al registrarse)
        if request.user.is_authenticated:
            return self.get_response(request)

        # C) Obtener datos de geolocalización
        geo_result = check_geo_restriction(request)

        country = geo_result.get('country')
        ciudad_data = geo_result.get('ciudad_data')  # True = Milagro
        is_city_allowed = geo_result.get('allowed')  # True = ciudad habilitada en DB

        # D) Implementar reglas de acceso ESTRICTAS por prefijo de ruta
        access_granted = False

        # POLÍTICA ESTUDIANTES: SOLO MILAGRO
        if path.startswith('/estudiantes/'):
            # Solo permitir si ciudad_data es True (Milagro verificado)
            if ciudad_data:
                access_granted = True
            logger.info(
                f"Student route access attempt: path={path}, "
                f"ciudad_data={ciudad_data}, granted={access_granted}"
            )

        # POLÍTICA TUTORES: TODO ECUADOR
        elif path.startswith('/tutores/'):
            # Permitir si el país es Ecuador
            if country == 'Ecuador':
                access_granted = True
            logger.info(
                f"Tutor route access attempt: path={path}, "
                f"country={country}, granted={access_granted}"
            )

        # POLÍTICA ROOT Y OTRAS RUTAS: Usar validación estándar (Milagro)
        else:
            if is_city_allowed:
                access_granted = True
            logger.info(
                f"Default route access: path={path}, "
                f"is_city_allowed={is_city_allowed}, granted={access_granted}"
            )

        # E) Redirección si el acceso es denegado
        if not access_granted:
            request.session['geo_blocked'] = True
            request.session['geo_city'] = geo_result.get('city', 'Unknown')
            request.session['geo_region'] = geo_result.get('region', 'Unknown')
            request.session['geo_country'] = geo_result.get('country', 'Unknown')

            logger.warning(
                f"GEO ACCESS DENIED: {geo_result.get('city')}, "
                f"{geo_result.get('region')}, {country} → {path}"
            )

            # Redirigir a página de "servicio no disponible"
            return redirect('servicio_no_disponible')

        # F) Guardar geo_data en request para uso posterior
        request.geo_data = geo_result

        return self.get_response(request)
