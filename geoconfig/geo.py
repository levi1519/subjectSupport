"""
Utilidades de geolocalización para restricción geográfica del servicio.
"""

import os
import requests
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    if ip in ['127.0.0.1', 'localhost', '::1']:
        ip = request.session.get('test_ip', ip)

    return ip


def get_location_from_ip(ip_address):
    from django.conf import settings as django_settings
    cache_key = f'geo_ip_{django_settings.CACHE_VERSION}_{ip_address}'
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug(f"Geo data from cache for IP {ip_address}")
        return cached_data

    api_key = os.getenv('IPGEOLOCATION_API_KEY')
    if not api_key:
        logger.warning('IPGEOLOCATION_API_KEY not found')
        return None

    try:
        logger.info(f"Geo API called with IP: {ip_address}")
        response = requests.get(
            'https://api.ipgeolocation.io/ipgeo',
            params={'apiKey': api_key, 'ip': ip_address},
            timeout=3
        )
        logger.info(f"API Status for IP {ip_address}: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            logger.info(f"Raw API Response for IP {ip_address}: {data}")

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
    Verifica si un punto está dentro de algún ServiceArea activo.
    Usa SQL raw para no depender de GIS_AVAILABLE ni de GDAL en runtime.
    """
    try:
        lon_float = float(longitude)
        lat_float = float(latitude)
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid coordinates: lat={latitude}, lon={longitude}, error={e}")
        return False, None

    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, city_name, descripcion, activo
                FROM "academicTutoring_servicearea"
                WHERE activo = true
                AND ST_Contains(area, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                LIMIT 1
            """, [lon_float, lat_float])
            row = cursor.fetchone()

        if row:
            logger.info(f"✓ MATCH: Point ({lat_float}, {lon_float}) is inside {row[1]}")

            class SimpleServiceArea:
                def __init__(self, r):
                    self.city_name = r[1]
                    self.descripcion = r[2]
                    self.activo = r[3]

            return True, SimpleServiceArea(row)
        else:
            logger.warning(f"✗ NO MATCH: Point ({lat_float}, {lon_float}) not in any service area")
            return False, None

    except Exception as e:
        logger.error(f"Error in spatial query: {str(e)}", exc_info=True)
        return False, None


def check_geo_restriction(request):
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

    # Verificar si ya está en sesión
    geo_data_session = request.session.get('geo_data')
    if geo_data_session:
        logger.debug("Using geo data from session")
        return geo_data_session

    ip_address = get_client_ip(request)
    logger.info(f"Checking geo restriction for IP: {ip_address}")

    location_data = get_location_from_ip(ip_address)

    if not location_data:
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

    allowed, service_area_obj = is_point_in_service_area(latitude, longitude)

    service_area_data = None
    if service_area_obj:
        service_area_data = {
            'city_name': service_area_obj.city_name,
            'descripcion': service_area_obj.descripcion,
            'activo': service_area_obj.activo,
        }

    country_code = location_data.get('country_code', '')
    country_config = get_country_config(country_code)
    
    geo_result = {
        'allowed': allowed,
        'city': location_data.get('city', 'Unknown'),
        'region': location_data.get('region', 'Unknown'),
        'country': location_data.get('country', 'Unknown'),
        'country_code': country_code,
        'latitude': latitude,
        'longitude': longitude,
        'service_area': service_area_data,
        'country_config': country_config,
        'skip_check': False,
        'ip_address': ip_address
    }

    request.session['geo_data'] = geo_result

    logger.info(
        f"Geo restriction result for {ip_address}: "
        f"allowed={allowed}, service_area={service_area_data}, country_config={country_config}"
    )

    return geo_result


def get_available_service_areas():
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, city_name, descripcion, activo
                FROM "academicTutoring_servicearea"
                WHERE activo = true
                ORDER BY city_name
            """)
            rows = cursor.fetchall()

        class SimpleServiceArea:
            def __init__(self, r):
                self.id = r[0]
                self.city_name = r[1]
                self.descripcion = r[2]
                self.activo = r[3]

        return [SimpleServiceArea(r) for r in rows]
    except Exception as e:
        logger.error(f"Error getting service areas: {str(e)}")
        return []


def set_test_ip(request, ip_address):
    if settings.DEBUG:
        request.session['test_ip'] = ip_address


def get_country_config(country_code):
    """
    Get CountryConfig for a given country code with caching.
    Returns CountryConfig dict or None if not found/inactive.
    """
    from django.core.cache import cache
    
    from django.conf import settings as django_settings
    cache_key = f'country_config_{django_settings.CACHE_VERSION}_{country_code}'
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        from apps.academicTutoring.models import CountryConfig
        config = CountryConfig.objects.filter(
            country_code=country_code,
            active=True
        ).first()
        
        if config:
            result = {
                'country_code': config.country_code,
                'country_name': config.country_name,
                'active': config.active,
                'geo_restricted': config.geo_restricted,
            }
            cache.set(cache_key, result, 60)
            return result
        return None
    except Exception as e:
        logger.error(f"Error getting country config: {str(e)}")
        return None
        if 'geo_data' in request.session:
            del request.session['geo_data']
        logger.info(f"Test IP set to: {ip_address}")
        return True
    return False