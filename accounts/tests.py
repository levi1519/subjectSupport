"""
Comprehensive test suite for accounts app
Tests user authentication, registration, profiles, and dashboards
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import TutorProfile, ClientProfile
from accounts.forms import TutorRegistrationForm, ClientRegistrationForm
from accounts.test_utils import UserFactory

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model functionality"""

    def test_create_tutor_user(self):
        """Test creating a tutor user"""
        user = User.objects.create_user(
            email='tutor@test.com',
            username='tutor@test.com',
            password='testpass123',
            name='Test Tutor',
            user_type='tutor'
        )
        self.assertEqual(user.email, 'tutor@test.com')
        self.assertEqual(user.user_type, 'tutor')
        self.assertTrue(user.check_password('testpass123'))

    def test_create_client_user(self):
        """Test creating a client user"""
        user = User.objects.create_user(
            email='client@test.com',
            username='client@test.com',
            password='testpass123',
            name='Test Client',
            user_type='client'
        )
        self.assertEqual(user.email, 'client@test.com')
        self.assertEqual(user.user_type, 'client')

    def test_user_str_representation(self):
        """Test user string representation"""
        user = UserFactory.create_tutor(name='John Doe')
        self.assertEqual(str(user), 'John Doe (Tutor)')

    def test_email_unique_constraint(self):
        """Test that email must be unique"""
        UserFactory.create_tutor(email='test@test.com')
        with self.assertRaises(Exception):
            UserFactory.create_tutor(email='test@test.com')


class TutorProfileModelTest(TestCase):
    """Test TutorProfile model"""

    def test_create_tutor_profile(self):
        """Test creating a tutor profile"""
        tutor = UserFactory.create_tutor(
            subjects='Math, Physics',
            city='Quito',
            country='Ecuador'
        )
        profile = tutor.tutor_profile
        self.assertEqual(profile.subjects, 'Math, Physics')
        self.assertEqual(profile.city, 'Quito')
        self.assertEqual(profile.country, 'Ecuador')

    def test_tutor_profile_str(self):
        """Test tutor profile string representation"""
        tutor = UserFactory.create_tutor(name='Jane Doe')
        self.assertIn('Jane Doe', str(tutor.tutor_profile))

    def test_tutor_profile_one_to_one(self):
        """Test one-to-one relationship"""
        tutor = UserFactory.create_tutor()
        self.assertEqual(tutor.tutor_profile.user, tutor)


class ClientProfileModelTest(TestCase):
    """Test ClientProfile model"""

    def test_create_client_profile(self):
        """Test creating a client profile"""
        client = UserFactory.create_client(
            city='Guayaquil',
            country='Ecuador',
            is_minor=True
        )
        profile = client.client_profile
        self.assertEqual(profile.city, 'Guayaquil')
        self.assertEqual(profile.country, 'Ecuador')
        self.assertTrue(profile.is_minor)

    def test_client_profile_str(self):
        """Test client profile string representation"""
        client = UserFactory.create_client(name='John Student')
        self.assertIn('John Student', str(client.client_profile))

    def test_client_profile_with_parent(self):
        """Test client profile with parent information"""
        client = UserFactory.create_client(is_minor=True)
        profile = client.client_profile
        profile.parent_name = 'Parent Name'
        profile.save()
        self.assertEqual(profile.parent_name, 'Parent Name')


class TutorRegistrationFormTest(TestCase):
    """Test tutor registration form"""

    def test_valid_tutor_registration(self):
        """Test valid tutor registration form"""
        form_data = {
            'name': 'Test Tutor',
            'email': 'tutor@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'subjects': 'Mathematics, Physics',
            'bio': 'Experienced tutor',
            'experience': '5 years',
            'city': 'Quito',
            'country': 'Ecuador'
        }
        form = TutorRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_email_format(self):
        """Test registration with invalid email"""
        form_data = {
            'name': 'Test Tutor',
            'email': 'invalid-email',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'subjects': 'Math'
        }
        form = TutorRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_password_mismatch(self):
        """Test registration with mismatched passwords"""
        form_data = {
            'name': 'Test Tutor',
            'email': 'tutor@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass123!',
            'subjects': 'Math'
        }
        form = TutorRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_tutor_form_creates_user_and_profile(self):
        """Test that form save creates both user and profile"""
        form_data = {
            'name': 'Test Tutor',
            'email': 'tutor@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'subjects': 'Mathematics',
            'city': 'Quito',
            'country': 'Ecuador'
        }
        form = TutorRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.user_type, 'tutor')
        self.assertTrue(hasattr(user, 'tutor_profile'))
        self.assertEqual(user.tutor_profile.subjects, 'Mathematics')


class ClientRegistrationFormTest(TestCase):
    """Test client registration form"""

    def test_valid_client_registration(self):
        """Test valid client registration form"""
        form_data = {
            'name': 'Test Client',
            'email': 'client@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'is_minor': False,
            'city': 'Quito',
            'country': 'Ecuador'
        }
        form = ClientRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_client_form_creates_user_and_profile(self):
        """Test that form save creates both user and profile"""
        form_data = {
            'name': 'Test Client',
            'email': 'client@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'is_minor': True,
            'parent_name': 'Parent Name',
            'city': 'Quito',
            'country': 'Ecuador'
        }
        form = ClientRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.user_type, 'client')
        self.assertTrue(hasattr(user, 'client_profile'))
        self.assertTrue(user.client_profile.is_minor)
        self.assertEqual(user.client_profile.parent_name, 'Parent Name')


class TutorRegistrationViewTest(TestCase):
    """Test tutor registration view"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('register_tutor')

    def test_tutor_registration_page_loads(self):
        """Test that tutor registration page loads"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register_tutor.html')

    def test_successful_tutor_registration(self):
        """Test successful tutor registration and redirect"""
        form_data = {
            'name': 'New Tutor',
            'email': 'newtutor@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'subjects': 'Mathematics',
            'bio': 'Test bio',
            'experience': 'Test experience',
            'city': 'Quito',
            'country': 'Ecuador'
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success

        # Verify user was created
        user = User.objects.get(email='newtutor@example.com')
        self.assertEqual(user.user_type, 'tutor')
        self.assertTrue(hasattr(user, 'tutor_profile'))

    def test_duplicate_email_registration(self):
        """Test registration with duplicate email"""
        UserFactory.create_tutor(email='existing@example.com')

        form_data = {
            'name': 'New Tutor',
            'email': 'existing@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'subjects': 'Mathematics'
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 200)  # Stays on page with errors


class ClientRegistrationViewTest(TestCase):
    """Test client registration view"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('register_client')

    def test_client_registration_page_loads(self):
        """Test that client registration page loads"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register_client.html')

    def test_successful_client_registration(self):
        """Test successful client registration"""
        form_data = {
            'name': 'New Client',
            'email': 'newclient@example.com',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!',
            'is_minor': False,
            'city': 'Quito',
            'country': 'Ecuador'
        }
        response = self.client.post(self.url, data=form_data)
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(email='newclient@example.com')
        self.assertEqual(user.user_type, 'client')


class LoginViewTest(TestCase):
    """Test login functionality"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('login')
        self.tutor = UserFactory.create_tutor(
            email='tutor@test.com',
            password='testpass123'
        )
        self.student = UserFactory.create_client(
            email='client@test.com',
            password='testpass123'
        )

    def test_login_page_loads(self):
        """Test login page loads"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_successful_tutor_login(self):
        """Test successful tutor login"""
        response = self.client.post(self.url, {
            'username': 'tutor@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        # Login redirects to dashboard which then redirects based on user type
        self.assertIn('dashboard', response.url)

    def test_successful_client_login(self):
        """Test successful client login"""
        response = self.client.post(self.url, {
            'username': 'client@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        # Login redirects to dashboard which then redirects based on user type
        self.assertIn('dashboard', response.url)

    def test_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(self.url, {
            'username': 'tutor@test.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        # Check that form has errors (either English or Spanish message)
        self.assertIn('errorlist', response.content.decode())


class TutorDashboardTest(TestCase):
    """Test tutor dashboard functionality"""

    def setUp(self):
        self.client = Client()
        self.tutor = UserFactory.create_tutor(
            email='tutor@test.com',
            password='testpass123'
        )
        self.student = UserFactory.create_client(
            email='client@test.com',
            password='testpass123'
        )
        self.url = reverse('tutor_dashboard')

    def test_tutor_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_tutor_can_access_dashboard(self):
        """Test tutor can access their dashboard"""
        self.client.login(username='tutor@test.com', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/tutor_dashboard.html')

    def test_client_cannot_access_tutor_dashboard(self):
        """Test client is redirected from tutor dashboard"""
        self.client.login(username='client@test.com', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('client_dashboard')))

    def test_tutor_dashboard_context(self):
        """Test tutor dashboard has correct context"""
        self.client.login(username='tutor@test.com', password='testpass123')
        response = self.client.get(self.url)
        self.assertIn('pending_sessions', response.context)
        self.assertIn('upcoming_sessions', response.context)
        self.assertIn('profile', response.context)


class ClientDashboardTest(TestCase):
    """Test client dashboard functionality"""

    def setUp(self):
        self.client = Client()
        self.student = UserFactory.create_client(
            email='client@test.com',
            password='testpass123'
        )
        self.tutor = UserFactory.create_tutor(
            email='tutor@test.com',
            password='testpass123'
        )
        self.url = reverse('client_dashboard')

    def test_client_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_client_can_access_dashboard(self):
        """Test client can access their dashboard"""
        self.client.login(username='client@test.com', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/client_dashboard.html')

    def test_tutor_cannot_access_client_dashboard(self):
        """Test tutor is redirected from client dashboard"""
        self.client.login(username='tutor@test.com', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('tutor_dashboard')))

    def test_client_dashboard_context(self):
        """Test client dashboard has correct context"""
        self.client.login(username='client@test.com', password='testpass123')
        response = self.client.get(self.url)
        self.assertIn('upcoming_sessions', response.context)
        self.assertIn('pending_sessions', response.context)
        self.assertIn('past_sessions', response.context)


class LogoutTest(TestCase):
    """Test logout functionality"""

    def setUp(self):
        self.client = Client()
        self.user = UserFactory.create_client(
            email='user@test.com',
            password='testpass123'
        )

    def test_logout_redirects(self):
        """Test logout redirects to landing page"""
        self.client.login(username='user@test.com', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('landing')))

    def test_user_logged_out_after_logout(self):
        """Test user is actually logged out"""
        self.client.login(username='user@test.com', password='testpass123')
        self.client.get(reverse('logout'))

        # Try to access protected page
        response = self.client.get(reverse('client_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)


class DashboardRedirectTest(TestCase):
    """Test dashboard redirect functionality"""

    def setUp(self):
        self.client = Client()
        self.tutor = UserFactory.create_tutor(
            email='tutor@test.com',
            password='testpass123'
        )
        self.student = UserFactory.create_client(
            email='client@test.com',
            password='testpass123'
        )

    def test_dashboard_redirect_tutor(self):
        """Test /dashboard redirects tutor to tutor dashboard"""
        self.client.login(username='tutor@test.com', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('tutor_dashboard')))

    def test_dashboard_redirect_client(self):
        """Test /dashboard redirects client to client dashboard"""
        self.client.login(username='client@test.com', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.endswith(reverse('client_dashboard')))
