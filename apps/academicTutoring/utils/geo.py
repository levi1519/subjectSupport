"""
Re-export desde geoconfig. La lógica real de geolocalización vive en geoconfig/geo.py (raíz del proyecto).
"""
from geoconfig.geo import (
    get_client_ip,
    get_location_from_ip,
    is_point_in_service_area,
    check_geo_restriction,
    get_available_service_areas,
    set_test_ip
)
