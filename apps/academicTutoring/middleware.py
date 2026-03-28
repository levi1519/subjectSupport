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
from apps.academicTutoring.utils.geo import check_geo_restriction

logger = logging.getLogger(__name__)


class GeoRestrictionMiddleware:
    """
    Middleware que restringe el acceso al sitio basado en geolocalización espacial.

    POLÍTICA DE SEGURIDAD GEOGRÁFICA (GeoDjango):

    ENFORCEMENT POR RUTA:
    1. /estudiantes/* → SOLO polígono de Milagro (verificación espacial PostGIS estricta)
    2. /tutores/* → TODO Ecuador (verificación por país, sin polígono)
    3. / (raíz) → TODO Ecuador (GeoRootRouterView redirige internamente según ubicación)
    4. Otras rutas → TODO Ecuador (acceso general para ecuatorianos)

    BYPASSES:
    - Usuarios autenticados → Bypass completo (ya verificados al registrarse)
    - Whitelist → /admin/, /servicio-no-disponible/, /notificarme/, /static/, /media/, /accounts/logout/

    FLUJO DE USUARIO:
    - Usuario en Milagro → Acceso a /estudiantes/* y /tutores/*
    - Usuario en Guayaquil (u otra ciudad de Ecuador) → Acceso a /tutores/* únicamente
    - Usuario fuera de Ecuador → Bloqueado con redirección a /servicio-no-disponible/

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
        '/internal/',
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

        # D) NUEVA POLÍTICA DE ENFORCEMENT POR RUTA:
        # - /estudiantes/* → SOLO polígono de Milagro (estricto)
        # - /tutores/* → TODO Ecuador
        # - / (raíz) → TODO Ecuador (GeoRootRouterView maneja redirección interna)
        # - Otras rutas → TODO Ecuador

        access_granted = False

        # POLÍTICA ESTUDIANTES: SOLO MILAGRO (verificación espacial estricta)
        if path.startswith('/estudiantes/'):
            # Requiere estar DENTRO del polígono de ServiceArea (Milagro)
            if is_in_service_area and service_area:
                access_granted = True
            logger.info(
                f"Student route access attempt: path={path}, "
                f"is_in_service_area={is_in_service_area}, "
                f"service_area={service_area}, granted={access_granted}"
            )

        # POLÍTICA TUTORES: TODO ECUADOR
        elif path.startswith('/tutores/'):
            # Solo requiere estar en Ecuador (sin verificación de polígono)
            if country == 'Ecuador':
                access_granted = True
            logger.info(
                f"Tutor route access attempt: path={path}, "
                f"country={country}, granted={access_granted}"
            )

        # POLÍTICA RAÍZ Y OTRAS RUTAS: TODO ECUADOR
        else:
            # Permitir acceso a usuarios de Ecuador
            # GeoRootRouterView en views.py maneja redirección interna (Milagro→estudiantes, otros→tutores)
            if country == 'Ecuador':
                access_granted = True
            logger.info(
                f"General route access attempt: path={path}, "
                f"country={country}, granted={access_granted}"
            )

        # E) Redirección FORZADA si el acceso es denegado
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
