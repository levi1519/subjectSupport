"""
Utilidades de geolocalización para restricción geográfica del servicio.

Soporta:
- Detección de ciudad por IP usando ipgeolocation.io (50,000 req/mes)
- Caché en sesión para evitar consultas repetidas
- Bypass para desarrollo/testing
- Logging de ubicaciones detectadas
"""

import os
import requests
import logging
from django.conf import settings
from django.core.cache import cache
from core.models import CiudadHabilitada

logger = logging.getLogger(__name__)


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
        # IP de prueba de Milagro, Ecuador (puedes cambiarla)
        # En producción esto será la IP real del usuario
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
        # Timeout de 3 segundos para no bloquear la request
        response = requests.get(
            'https://api.ipgeolocation.io/ipgeo',
            params={'apiKey': api_key, 'ip': ip_address},
            timeout=3
        )

        if response.status_code == 200:
            data = response.json()

            # Verificar si hay error en la respuesta
            if 'message' in data and 'error' in data.get('message', '').lower():
                logger.warning(f"IP API error for {ip_address}: {data.get('message', 'Unknown')}")
                return None

            location_data = {
                'city': data.get('city'),
                'region': data.get('state_prov'),  # ipgeolocation.io usa state_prov
                'country': data.get('country_name'),
                'country_code': data.get('country_code2'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
            }

            # Guardar en caché por 1 hora
            cache.set(cache_key, location_data, 3600)

            logger.info(f"Geo data obtained for IP {ip_address}: {location_data['city']}, {location_data['region']}")
            return location_data
        else:
            logger.error(f"IP API returned status {response.status_code} for {ip_address}")
            return None

    except requests.RequestException as e:
        logger.error(f"Error fetching geo data for IP {ip_address}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_location_from_ip: {str(e)}")
        return None


def is_service_available_in_city(ciudad, provincia=None):
    """
    Verifica si el servicio está disponible en una ciudad específica.

    Args:
        ciudad: Nombre de la ciudad
        provincia: Nombre de la provincia (opcional, mejora precisión)

    Returns:
        tuple: (disponible: bool, ciudad_obj: CiudadHabilitada or None)
    """
    if not ciudad:
        return False, None

    # Normalizar ciudad (quitar acentos, mayúsculas, etc. para mejor matching)
    ciudad_normalizada = ciudad.strip()

    try:
        # Buscar ciudad habilitada
        query = CiudadHabilitada.objects.filter(
            ciudad__iexact=ciudad_normalizada,
            activo=True
        )

        if provincia:
            # Si tenemos provincia, buscar match exacto
            provincia_normalizada = provincia.strip()
            query = query.filter(provincia__iexact=provincia_normalizada)

        ciudad_obj = query.first()

        if ciudad_obj:
            logger.info(f"Service available in {ciudad}, {provincia}")
            return True, ciudad_obj
        else:
            logger.info(f"Service NOT available in {ciudad}, {provincia}")
            return False, None

    except Exception as e:
        logger.error(f"Error checking service availability: {str(e)}")
        return False, None


def get_available_cities():
    """
    Retorna lista de ciudades donde el servicio está disponible.
    Útil para mostrar en landing page.
    """
    try:
        cities = CiudadHabilitada.objects.filter(activo=True).order_by('orden_prioridad', 'ciudad')
        return cities
    except Exception as e:
        logger.error(f"Error getting available cities: {str(e)}")
        return []


def check_geo_restriction(request):
    """
    Función principal para verificar restricción geográfica.

    Args:
        request: HttpRequest object

    Returns:
        dict con:
        - allowed: bool (si tiene acceso)
        - city: str (ciudad detectada)
        - region: str (provincia detectada)
        - ciudad_obj: CiudadHabilitada (si está disponible)
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
            'ciudad_obj': None,
            'skip_check': True
        }

    # Verificar si ya está en sesión (para no consultar API repetidamente)
    geo_data_session = request.session.get('geo_data')
    if geo_data_session:
        logger.debug("Using geo data from session")
        # Volver a verificar disponibilidad por si cambió en admin
        allowed, ciudad_obj = is_service_available_in_city(
            geo_data_session.get('city'),
            geo_data_session.get('region')
        )
        geo_data_session['allowed'] = allowed
        geo_data_session['ciudad_obj'] = ciudad_obj
        return geo_data_session

    # Obtener IP del cliente
    ip_address = get_client_ip(request)
    logger.info(f"Checking geo restriction for IP: {ip_address}")

    # Obtener ubicación desde IP
    location_data = get_location_from_ip(ip_address)

    if not location_data:
        # Si no podemos detectar ubicación, permitir acceso por defecto
        # (o podrías cambiar a denegar acceso)
        logger.warning(f"Could not detect location for IP {ip_address}, allowing access by default")
        geo_result = {
            'allowed': True,  # Cambiar a False para ser más restrictivo
            'city': 'Unknown',
            'region': 'Unknown',
            'ciudad_obj': None,
            'skip_check': False,
            'detection_failed': True
        }
        request.session['geo_data'] = geo_result
        return geo_result

    # Verificar si la ciudad está habilitada
    city = location_data.get('city', 'Unknown')
    region = location_data.get('region', 'Unknown')

    allowed, ciudad_obj = is_service_available_in_city(city, region)

    geo_result = {
        'allowed': allowed,
        'city': city,
        'region': region,
        'country': location_data.get('country', 'Unknown'),
        'ciudad_obj': ciudad_obj,
        'skip_check': False,
        'ip_address': ip_address
    }

    # Guardar en sesión
    request.session['geo_data'] = geo_result

    return geo_result


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


def get_cities_by_proximity(user_city, user_region):
    """
    Retorna ciudades ordenadas por proximidad al usuario.

    Orden de prioridad:
    1. Misma ciudad
    2. Misma provincia/región
    3. Mismo país
    4. Resto (por orden_prioridad)
    """
    try:
        all_cities = CiudadHabilitada.objects.filter(activo=True)

        # Ordenar por proximidad
        same_city = []
        same_region = []
        same_country = []
        others = []

        for city in all_cities:
            if city.ciudad.lower() == user_city.lower():
                same_city.append(city)
            elif city.provincia.lower() == user_region.lower():
                same_region.append(city)
            elif city.pais == 'Ecuador':  # Asumiendo usuario en Ecuador
                same_country.append(city)
            else:
                others.append(city)

        # Concatenar listas en orden de prioridad
        ordered_cities = same_city + same_region + same_country + others

        return ordered_cities

    except Exception as e:
        logger.error(f"Error getting cities by proximity: {str(e)}")
        return get_available_cities()
