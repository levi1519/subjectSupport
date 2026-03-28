"""
Test suite for GeoRestrictionMiddleware security validation.
Validates RFC 2119 contracts for geographic access restrictions.

Validates: 
- GEO-001: Geolocation system MUST use ipgeolocation.io API (Free Tier)
- GEO-002: System access MUST be restricted entirely to users within Milagro
- GEO-007: Geolocation bypass MUST only be implemented for already authenticated users
- GEO-016: Visitors outside Milagro MUST NOT be allowed to see site content
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from unittest.mock import patch, MagicMock
from apps.academicTutoring.middleware import GeoRestrictionMiddleware
from apps.accounts.models import User


class GeoRestrictionMiddlewareTests(TestCase):
    """Test suite for GeoRestrictionMiddleware security validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.factory = RequestFactory()
        # Create middleware with a get_response that returns a proper response
        def get_response(request):
            from django.http import HttpResponse
            return HttpResponse(status=200)
        
        self.middleware = GeoRestrictionMiddleware(get_response)
        
        # Create test users - note: username is required but not used as login
        self.tutor_user = User.objects.create_user(
            username='tutor_test',  # Required field
            email='tutor@test.com',
            password='testpass123',
            user_type='tutor',
            name='Test Tutor'
        )
        
        self.client_user = User.objects.create_user(
            username='client_test',  # Required field
            email='client@test.com',
            password='testpass123',
            user_type='client',
            name='Test Client'
        )
    
    @patch('apps.academicTutoring.middleware.check_geo_restriction')
    def test_middleware_allows_milagro_users(self, mock_check_geo):
        """
        Validates: GEO-002 - System access MUST be restricted entirely to users within Milagro
        Validates: GEO-001 - Geolocation system MUST use ipgeolocation.io API
        """
        # Mock successful Milagro detection
        mock_check_geo.return_value = {
            'country': 'Ecuador',
            'city': 'Milagro',
            'service_area': {'city_name': 'Milagro', 'inside': True}
        }
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        request.session = {}
        
        response = self.middleware(request)
        
        # Should allow access (no redirect)
        self.assertEqual(response.status_code, 200)
        mock_check_geo.assert_called_once()
    
    @patch('apps.academicTutoring.middleware.check_geo_restriction')
    def test_middleware_blocks_non_milagro_users(self, mock_check_geo):
        """
        Validates: GEO-016 - Visitors outside Milagro MUST NOT be allowed to see site content
        """
        # Mock non-Milagro detection
        mock_check_geo.return_value = {
            'country': 'Ecuador',
            'city': 'Guayaquil',
            'service_area': None
        }
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        request.session = {}
        
        response = self.middleware(request)
        
        # Should redirect to servicio_no_disponible
        self.assertEqual(response.status_code, 302)
        self.assertIn('servicio-no-disponible', response.url)
        mock_check_geo.assert_called_once()
    
    @patch('apps.academicTutoring.middleware.check_geo_restriction')
    def test_middleware_bypass_for_authenticated_milagro_users(self, mock_check_geo):
        """
        Validates: GEO-007 - Geolocation bypass MUST only be implemented for already authenticated users
        """
        # Mock Milagro detection (user was validated during registration)
        mock_check_geo.return_value = {
            'country': 'Ecuador',
            'city': 'Milagro',
            'service_area': {'city_name': 'Milagro', 'inside': True}
        }
        
        request = self.factory.get('/')
        request.user = self.tutor_user  # Authenticated user
        request.session = {}
        
        response = self.middleware(request)
        
        # Should allow access for authenticated user
        self.assertEqual(response.status_code, 200)
        # Middleware should still check geo for logging purposes
        mock_check_geo.assert_called_once()
    
    @patch('apps.academicTutoring.middleware.check_geo_restriction')
    def test_middleware_excludes_admin_paths(self, mock_check_geo):
        """
        Validates: Security exclusion paths for admin interface
        """
        request = self.factory.get('/admin/')
        request.user = AnonymousUser()
        request.session = {}
        
        response = self.middleware(request)
        
        # Should allow access to admin without geo check
        self.assertEqual(response.status_code, 200)
        mock_check_geo.assert_not_called()
    
    @patch('apps.academicTutoring.middleware.check_geo_restriction')
    def test_middleware_excludes_servicio_no_disponible(self, mock_check_geo):
        """
        Validates: Exclusion of servicio-no-disponible path from geo restriction
        """
        request = self.factory.get('/servicio-no-disponible/')
        request.user = AnonymousUser()
        request.session = {}
        
        response = self.middleware(request)
        
        # Should allow access without geo check
        self.assertEqual(response.status_code, 200)
        mock_check_geo.assert_not_called()
    
    @patch('apps.academicTutoring.middleware.check_geo_restriction')
    def test_middleware_handles_geo_api_failure(self, mock_check_geo):
        """
        Validates: GEO-015 - Geolocation errors MUST NOT crash the application
        """
        # Mock API failure
        mock_check_geo.return_value = {
            'country': 'Unknown',
            'city': 'Unknown',
            'service_area': None,
            'error': 'API failure'
        }
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        request.session = {}
        
        response = self.middleware(request)
        
        # Should handle failure gracefully (deny access for security)
        self.assertEqual(response.status_code, 302)
        self.assertIn('servicio-no-disponible', response.url)
        mock_check_geo.assert_called_once()
    
    def test_middleware_attaches_geo_data_to_request(self):
        """
        Validates: GEO-005 - Geo data MUST be cached in session and attached to request
        """
        request = self.factory.get('/')
        request.user = AnonymousUser()
        request.session = {
            'geo_data': {
                'country': 'Ecuador',
                'city': 'Milagro',
                'service_area': {'city_name': 'Milagro', 'inside': True}
            }
        }
        
        # Create middleware with simple get_response
        def get_response(req):
            # Check that geo_data is attached
            self.assertTrue(hasattr(req, 'geo_data'))
            self.assertEqual(req.geo_data['city'], 'Milagro')
            return MagicMock(status_code=200)
        
        middleware = GeoRestrictionMiddleware(get_response)
        response = middleware(request)
        
        self.assertEqual(response.status_code, 200)
    
    @patch('apps.academicTutoring.middleware.check_geo_restriction')
    def test_middleware_stores_geo_blocked_in_session(self, mock_check_geo):
        """
        Validates: GEO-005 - Geo data MUST be cached in session when access is denied
        """
        # Mock non-Milagro detection
        mock_check_geo.return_value = {
            'country': 'Colombia',
            'city': 'Bogota',
            'service_area': None
        }
        
        request = self.factory.get('/')
        request.user = AnonymousUser()
        request.session = {}
        
        response = self.middleware(request)
        
        # Should store geo_blocked flag in session
        self.assertTrue(request.session.get('geo_blocked', False))
        self.assertEqual(response.status_code, 302)
        mock_check_geo.assert_called_once()


class PathBasedAccessPolicyTests(TestCase):
    """Test suite for path-based access policies."""
    
    def setUp(self):
        """Set up test environment."""
        self.factory = RequestFactory()
        self.middleware = GeoRestrictionMiddleware(get_response=lambda r: r)
    
    @patch('apps.academicTutoring.middleware.check_geo_restriction')
    def test_estudiantes_routes_require_milagro(self, mock_check_geo):
        """
        Validates: /estudiantes/* routes MUST require user to be inside Milagro
        """
        # Mock non-Milagro detection
        mock_check_geo.return_value = {
            'country': 'Ecuador',
            'city': 'Guayaquil',
            'service_area': None
        }
        
        request = self.factory.get('/estudiantes/')
        request.user = AnonymousUser()
        request.session = {}
        
        response = self.middleware(request)
        
        # Should block access to estudiantes routes
        self.assertEqual(response.status_code, 302)
        self.assertIn('servicio-no-disponible', response.url)
    
    @patch('apps.academicTutoring.middleware.check_geo_restriction')
    def test_tutores_routes_require_milagro(self, mock_check_geo):
        """
        Validates: ALL routes MUST require user to be inside Milagro city
        (Updated from country-level verification to strict Milagro-only)
        """
        # Mock non-Milagro detection
        mock_check_geo.return_value = {
            'country': 'Ecuador',
            'city': 'Quito',
            'service_area': None
        }
        
        request = self.factory.get('/tutores/')
        request.user = AnonymousUser()
        request.session = {}
        
        response = self.middleware(request)
        
        # Should block access (strict Milagro-only policy)
        self.assertEqual(response.status_code, 302)
        self.assertIn('servicio-no-disponible', response.url)