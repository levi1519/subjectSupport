"""
Middleware para restricción geográfica del servicio basado en CountryConfig.
"""

import logging
from django.shortcuts import redirect
from geoconfig.geo import check_geo_restriction

logger = logging.getLogger(__name__)


class GeoRestrictionMiddleware:
    """
    Middleware que restringe el acceso basado en CountryConfig.
    """

    EXCLUDED_PATHS = [
        '/admin/',
        '/servicio-no-disponible/',
        '/notificarme/',
        '/static/',
        '/media/',
        '/accounts/logout/',
        '/internal/',
        '/gestion-ss-2026/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # A) Rutas Exentas
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return self.get_response(request)

        # B) BYPASS: Usuarios Autenticados
        if request.user.is_authenticated:
            return self.get_response(request)

        # C) Obtener datos de geolocalización
        geo_data = check_geo_restriction(request)
        country_config = geo_data.get('country_config')
        service_area = geo_data.get('service_area')

        # RULE-1: Country not in active CountryConfig
        if country_config is None or not country_config.get('active'):
            country_code = geo_data.get('country_code', 'Unknown')
            logger.warning(f"GEO DENIED: country={country_code} not in active CountryConfig")
            request.session['geo_blocked'] = True
            request.session['geo_city'] = geo_data.get('city', 'Unknown')
            request.session['geo_region'] = geo_data.get('region', 'Unknown')
            request.session['geo_country'] = geo_data.get('country', 'Unknown')
            return redirect('servicio_no_disponible')

        # RULE-2: Active and NOT geo_restricted - allow ALL routes
        if country_config.get('active') and not country_config.get('geo_restricted'):
            country_code = country_config.get('country_code')
            logger.info(f"GEO ALLOWED: country={country_code} geo_restricted=False")
            request.geo_data = geo_data
            return self.get_response(request)

        # RULE-3: Active and geo_restricted - check service_area for /estudiantes/
        if country_config.get('active') and country_config.get('geo_restricted'):
            if path.startswith('/estudiantes/'):
                if service_area is not None:
                    logger.info(f"GEO ALLOWED: path={path}, service_area={service_area}")
                    request.geo_data = geo_data
                    return self.get_response(request)
                else:
                    logger.warning(f"GEO DENIED: path={path}, no service_area")
                    request.session['geo_blocked'] = True
                    return redirect('servicio_no_disponible')
            else:
                # /tutores/ and other paths allowed
                logger.info(f"GEO ALLOWED: path={path}, geo_restricted but not /estudiantes/")
                request.geo_data = geo_data
                return self.get_response(request)

        # Fallback - deny access
        logger.warning(f"GEO DENIED: fallback for path={path}")
        return redirect('servicio_no_disponible')
