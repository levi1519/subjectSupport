"""
Middleware para restricción geográfica del servicio.

NUEVA ARQUITECTURA GEODJANGO:
- Usa consultas espaciales PostGIS para verificar si un usuario está en el área de servicio
- Elimina comparación frágil de strings de ciudades
- Política basada en geometría precisa de polígonos

Este middleware intercepta requests y verifica si el usuario está
accediendo desde una ubicación dentro del área de servicio definida.
"""

import logging
from django.shortcuts import redirect
from core.utils.geo import check_geo_restriction

logger = logging.getLogger(__name__)


class GeoRestrictionMiddleware:
    """
    Middleware que restringe el acceso al sitio basado en geolocalización espacial.

    NUEVA POLÍTICA DE SEGURIDAD GEOGRÁFICA (GeoDjango):
    1. /estudiantes/* → SOLO usuarios dentro del polígono de ServiceArea activo (Milagro)
    2. /tutores/* → TODO Ecuador (verificado por país en API)
    3. Usuarios autenticados → Bypass (ya verificados al registrarse)
    4. Admin y logout → Exentos siempre

    La verificación usa coordenadas GPS y consultas PostGIS para precisión máxima.
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
        service_area = geo_result.get('service_area')  # Dict con info del ServiceArea si matched
        is_in_service_area = geo_result.get('allowed')  # True = dentro de polígono activo

        # D) Implementar reglas de acceso ESTRICTAS por prefijo de ruta
        access_granted = False

        # POLÍTICA ESTUDIANTES: SOLO dentro del área de servicio (Milagro)
        if path.startswith('/estudiantes/'):
            # NUEVA LÓGICA: Solo permitir si está dentro del polígono de ServiceArea
            if service_area:
                access_granted = True
            logger.info(
                f"Student route access attempt: path={path}, "
                f"service_area={service_area}, granted={access_granted}"
            )

        # POLÍTICA TUTORES: TODO ECUADOR
        elif path.startswith('/tutores/'):
            # Permitir si el país es Ecuador (sin cambios en esta política)
            if country == 'Ecuador':
                access_granted = True
            logger.info(
                f"Tutor route access attempt: path={path}, "
                f"country={country}, granted={access_granted}"
            )

        # POLÍTICA ROOT Y OTRAS RUTAS: Usar validación de área de servicio
        else:
            if is_in_service_area:
                access_granted = True
            logger.info(
                f"Default route access: path={path}, "
                f"is_in_service_area={is_in_service_area}, granted={access_granted}"
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
