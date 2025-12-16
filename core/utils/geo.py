"""
Utilidades de geolocalización para restricción geográfica del servicio.

NUEVA ARQUITECTURA CON GEODJANGO:
- Detección de coordenadas (lat/lon) por IP usando ipgeolocation.io
- Consultas espaciales con PostGIS para verificar si un punto está dentro del área de servicio
- Elimina comparación de strings frágil, usa geometría precisa

Soporta:
- Caché en sesión para evitar consultas repetidas
- Bypass para desarrollo/testing
- Logging de ubicaciones detectadas
- Fallback graceful cuando GIS no está disponible (desarrollo sin GDAL)
"""

import os
import requests
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Verificar si GIS está disponible
try:
    from django.contrib.gis.geos import Point
    from core.models import ServiceArea
    GIS_AVAILABLE = True
except ImportError:
    GIS_AVAILABLE = False
    logger.warning("GIS not available - using fallback mode")


def get_client_ip(request):
    """
    Obtiene la IP real del cliente considerando proxies y balanceadores.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    # Para desarrollo local, usar IP pública de prueba
    if ip in ['127.0.0.1', 'localhost', '::1']:
        # IP de prueba (puedes cambiarla en sesión con set_test_ip)
        ip = request.session.get('test_ip', ip)

    return ip


def get_location_from_ip(ip_address):
    """
    Obtiene información de ubicación desde una IP usando ipgeolocation.io.

    Retorna dict con: city, region, country, latitude, longitude
    o None si falla.

    API: 50,000 requests/mes (plan gratuito)
    Docs: https://ipgeolocation.io/documentation/ip-geolocation-api.html
    """
    # Verificar si está en caché (TTL: 1 hora)
    cache_key = f'geo_ip_{ip_address}'
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug(f"Geo data from cache for IP {ip_address}")
        return cached_data

    # Obtener API key desde variable de entorno
    api_key = os.getenv('IPGEOLOCATION_API_KEY')
    if not api_key:
        logger.warning('IPGEOLOCATION_API_KEY not found in environment variables, geolocation will fail')
        return None

    try:
        logger.info(f"Geo API called with IP: {ip_address}")

        # Timeout de 3 segundos para no bloquear la request
        response = requests.get(
            'https://api.ipgeolocation.io/ipgeo',
            params={'apiKey': api_key, 'ip': ip_address},
            timeout=3
        )

        logger.info(f"API Status for IP {ip_address}: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Raw API Response for IP {ip_address}: {data}")

            # Verificar si hay error en la respuesta
            if 'message' in data and 'error' in data.get('message', '').lower():
                logger.warning(f"IP API error for {ip_address}: {data.get('message', 'Unknown')}")
                return None

            location_data = {
                'city': data.get('city'),
                'region': data.get('state_prov'),
                'country': data.get('country_name'),
                'country_code': data.get('country_code2'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
            }

            # Guardar en caché por 1 hora
            cache.set(cache_key, location_data, 3600)

            logger.info(
                f"Geo data obtained for IP {ip_address}: "
                f"{location_data['city']}, {location_data['region']} "
                f"({location_data['latitude']}, {location_data['longitude']})"
            )
            return location_data
        else:
            logger.error(f"IP API returned status {response.status_code} for {ip_address}")
            return None

    except requests.RequestException as e:
        logger.error(f"Error fetching geo data for IP {ip_address}: {str(e)}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_location_from_ip: {str(e)}", exc_info=True)
        return None


def is_point_in_service_area(latitude, longitude):
    """
    Verifica si un punto geográfico está dentro de alguna área de servicio activa.

    NUEVA LÓGICA GEODJANGO:
    Realiza consulta espacial PostGIS para verificar si el punto está contenido
    en algún polígono de ServiceArea activo.

    Args:
        latitude: Latitud del punto (float)
        longitude: Longitud del punto (float)

    Returns:
        tuple: (allowed: bool, service_area: ServiceArea or None)
    """
    if not GIS_AVAILABLE:
        logger.warning("GIS not available - cannot perform spatial queries")
        # Fallback: permitir acceso (o podrías denegar)
        return True, None

    try:
        # Crear punto geográfico
        user_point = Point(longitude, latitude, srid=4326)

        logger.info(f"Checking if point ({latitude}, {longitude}) is in service area")

        # Consulta espacial: encontrar ServiceArea activa que contenga el punto
        service_area = ServiceArea.objects.filter(
            activo=True,
            area__contains=user_point
        ).first()

        if service_area:
            logger.info(
                f"✓ MATCH: Point ({latitude}, {longitude}) is inside {service_area.city_name} service area"
            )
            return True, service_area
        else:
            logger.warning(
                f"✗ NO MATCH: Point ({latitude}, {longitude}) is NOT inside any active service area"
            )
            return False, None

    except Exception as e:
        logger.error(f"Error in spatial query: {str(e)}", exc_info=True)
        # En caso de error, permitir acceso por defecto (o podrías denegar)
        return True, None


def check_geo_restriction(request):
    """
    Función principal para verificar restricción geográfica.

    NUEVA LÓGICA:
    1. Obtiene coordenadas (lat/lon) del usuario vía API de geolocalización
    2. Realiza consulta espacial PostGIS para verificar si está en área de servicio
    3. Retorna resultado con información detallada

    Args:
        request: HttpRequest object

    Returns:
        dict con:
        - allowed: bool (si tiene acceso)
        - city: str (ciudad detectada por API)
        - region: str (provincia detectada por API)
        - country: str (país detectado por API)
        - latitude: float (coordenada)
        - longitude: float (coordenada)
        - service_area: dict (datos del área de servicio si matched, sino None)
        - skip_check: bool (si se saltó el check)
    """
    # BYPASS para desarrollo/testing
    skip_geo_check = getattr(settings, 'SKIP_GEO_CHECK', False)
    if skip_geo_check:
        logger.info("Geo check skipped (SKIP_GEO_CHECK=True)")
        return {
            'allowed': True,
            'city': 'Development Mode',
            'region': 'N/A',
            'country': 'N/A',
            'latitude': None,
            'longitude': None,
            'service_area': None,
            'skip_check': True
        }

    # Verificar si ya está en sesión (para no consultar API repetidamente)
    geo_data_session = request.session.get('geo_data')
    if geo_data_session:
        logger.debug("Using geo data from session")
        return geo_data_session

    # Obtener IP del cliente
    ip_address = get_client_ip(request)
    logger.info(f"Checking geo restriction for IP: {ip_address}")

    # Obtener ubicación desde IP
    location_data = get_location_from_ip(ip_address)

    if not location_data:
        # Si no podemos detectar ubicación, denegar acceso por seguridad
        logger.warning(f"Could not detect location for IP {ip_address}, DENYING access")
        geo_result = {
            'allowed': False,
            'city': 'Unknown',
            'region': 'Unknown',
            'country': 'Unknown',
            'latitude': None,
            'longitude': None,
            'service_area': None,
            'skip_check': False,
            'detection_failed': True
        }
        request.session['geo_data'] = geo_result
        return geo_result

    # Extraer coordenadas
    latitude = location_data.get('latitude')
    longitude = location_data.get('longitude')

    if not latitude or not longitude:
        logger.warning(f"No coordinates in API response for IP {ip_address}, DENYING access")
        geo_result = {
            'allowed': False,
            'city': location_data.get('city', 'Unknown'),
            'region': location_data.get('region', 'Unknown'),
            'country': location_data.get('country', 'Unknown'),
            'latitude': None,
            'longitude': None,
            'service_area': None,
            'skip_check': False,
            'no_coordinates': True
        }
        request.session['geo_data'] = geo_result
        return geo_result

    # CONSULTA ESPACIAL: Verificar si el punto está en área de servicio
    allowed, service_area_obj = is_point_in_service_area(latitude, longitude)

    # Serializar service_area para guardar en sesión
    service_area_data = None
    if service_area_obj:
        service_area_data = {
            'city_name': service_area_obj.city_name,
            'descripcion': service_area_obj.descripcion,
            'activo': service_area_obj.activo,
        }

    geo_result = {
        'allowed': allowed,
        'city': location_data.get('city', 'Unknown'),
        'region': location_data.get('region', 'Unknown'),
        'country': location_data.get('country', 'Unknown'),
        'latitude': latitude,
        'longitude': longitude,
        'service_area': service_area_data,
        'skip_check': False,
        'ip_address': ip_address
    }

    # Guardar en sesión
    request.session['geo_data'] = geo_result

    logger.info(
        f"Geo restriction result for {ip_address}: "
        f"allowed={allowed}, service_area={service_area_data}"
    )

    return geo_result


def get_available_service_areas():
    """
    Retorna lista de áreas de servicio activas.

    NUEVA FUNCIÓN GEODJANGO:
    Reemplaza get_available_cities() del sistema anterior.
    Retorna ServiceArea objects en lugar de CiudadHabilitada.

    Returns:
        QuerySet de ServiceArea activos, o lista vacía si GIS no está disponible
    """
    if not GIS_AVAILABLE:
        logger.warning("GIS not available - cannot retrieve service areas")
        return []

    try:
        from core.models import ServiceArea
        service_areas = ServiceArea.objects.filter(activo=True).order_by('city_name')
        return service_areas
    except Exception as e:
        logger.error(f"Error getting service areas: {str(e)}")
        return []


def set_test_ip(request, ip_address):
    """
    Útil para testing: permite simular una IP específica.
    Solo funciona en modo DEBUG.
    """
    if settings.DEBUG:
        request.session['test_ip'] = ip_address
        # Limpiar geo_data de sesión para forzar nueva detección
        if 'geo_data' in request.session:
            del request.session['geo_data']
        logger.info(f"Test IP set to: {ip_address}")
        return True
    return False
