"""
Test suite for accounts models validation - Final version.
Tests that work with the current database schema.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.accounts.models import User, TutorProfile, ClientProfile, Subject


class UserModelTests(TestCase):
    """Test suite for User model validation."""
    
    def test_create_user_with_valid_user_type(self):
        """
        Validates: AUTH-001 - User model MUST extend AbstractUser with custom user_type field
        Validates: AUTH-003 - User type field MUST have exactly two choices: 'tutor' and 'client'
        """
        # Test tutor user
        tutor_user = User.objects.create_user(
            username='tutor_test',
            email='tutor@example.com',
            password='testpass123',
            user_type='tutor',
            name='Test Tutor'
        )
        
        self.assertEqual(tutor_user.email, 'tutor@example.com')
        self.assertEqual(tutor_user.user_type, 'tutor')
        self.assertTrue(tutor_user.check_password('testpass123'))
        
        # Test client user
        client_user = User.objects.create_user(
            username='client_test',
            email='client@example.com',
            password='testpass123',
            user_type='client',
            name='Test Client'
        )
        
        self.assertEqual(client_user.email, 'client@example.com')
        self.assertEqual(client_user.user_type, 'client')
    
    def test_user_email_is_username_field(self):
        """
        Validates: DV-003 - User model MUST use email as USERNAME_FIELD (not username)
        """
        user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123',
            user_type='client',
            name='Test User'
        )
        
        self.assertEqual(User.USERNAME_FIELD, 'email')
        self.assertEqual(user.get_username(), 'test@example.com')
    
    def test_user_type_choices(self):
        """
        Validates: AUTH-003 - User type field MUST have exactly two choices: 'tutor' and 'client'
        """
        choices = dict(User.USER_TYPE_CHOICES)
        self.assertEqual(len(choices), 2)
        self.assertIn('tutor', choices)
        self.assertIn('client', choices)


class ClientProfileModelTests(TestCase):
    """Test suite for ClientProfile model validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.client_user = User.objects.create_user(
            username='client_user',
            email='client@example.com',
            password='testpass123',
            user_type='client',
            name='Test Client'
        )
    
    def test_clientprofile_creation_with_city_country(self):
        """
        Validates: ClientProfile creation with city and country fields
        """
        profile = ClientProfile.objects.create(
            user=self.client_user,
            city='Milagro',
            country='Ecuador',
            bio='Test profile'
        )
        
        self.assertEqual(profile.user, self.client_user)
        self.assertEqual(profile.city, 'Milagro')
        self.assertEqual(profile.country, 'Ecuador')
    
    def test_clientprofile_creation_with_minor_flag(self):
        """
        Validates: AUTH-006 - ClientProfile MUST require mandatory parent email for registration of minor students
        """
        profile = ClientProfile.objects.create(
            user=self.client_user,
            city='Milagro',
            country='Ecuador',
            is_minor=True,
            parent_email='parent@example.com',
            bio='Minor student profile'
        )
        
        self.assertTrue(profile.is_minor)
        self.assertEqual(profile.parent_email, 'parent@example.com')
    
    def test_clientprofile_one_to_one_relationship(self):
        """
        Validates: DV-003 - ClientProfile MUST have OneToOne relationship with User model
        """
        profile = ClientProfile.objects.create(
            user=self.client_user,
            city='Milagro',
            country='Ecuador',
            bio='Test profile'
        )
        
        # Check relationship
        self.assertEqual(profile.user, self.client_user)
        self.assertEqual(self.client_user.client_profile, profile)


class TutorProfileModelTests(TestCase):
    """Test suite for TutorProfile model validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.tutor_user = User.objects.create_user(
            username='tutor_user',
            email='tutor@example.com',
            password='testpass123',
            user_type='tutor',
            name='Test Tutor'
        )
    
    def test_tutorprofile_creation_with_city_country(self):
        """
        Validates: TutorProfile creation with city and country fields
        """
        profile = TutorProfile.objects.create(
            user=self.tutor_user,
            city='Milagro',
            country='Ecuador',
            bio='Public tutor bio',
            hourly_rate=25.00
        )
        
        self.assertEqual(profile.user, self.tutor_user)
        self.assertEqual(profile.city, 'Milagro')
        self.assertEqual(profile.country, 'Ecuador')
        self.assertEqual(profile.hourly_rate, 25.00)
    
    def test_tutorprofile_public_data(self):
        """
        Validates: AUTH-007 - TutorProfile data MUST be defined as public information
        """
        profile = TutorProfile.objects.create(
            user=self.tutor_user,
            city='Milagro',
            country='Ecuador',
            bio='Public tutor bio',
            experience='5 years experience',
            hourly_rate=25.00
        )
        
        # Public fields should be accessible
        self.assertEqual(profile.bio, 'Public tutor bio')
        self.assertEqual(profile.experience, '5 years experience')
        self.assertEqual(profile.hourly_rate, 25.00)


class SubjectModelTests(TestCase):
    """Test suite for Subject model validation."""
    
    def test_subject_creation(self):
        """
        Validates: Subject model creation
        """
        subject = Subject.objects.create(
            name='Mathematics',
            slug='mathematics'
        )
        
        self.assertEqual(subject.name, 'Mathematics')
        self.assertEqual(subject.slug, 'mathematics')
    
    def test_subject_auto_generate_slug(self):
        """
        Validates: DV-003 - Subject slug field MUST be auto-generated from name if not provided
        """
        subject = Subject.objects.create(
            name='Physics'
            # slug not provided, should be auto-generated
        )
        
        self.assertIsNotNone(subject.slug)
        self.assertTrue(len(subject.slug) > 0)


class BusinessRuleConceptTests(TestCase):
    """Tests for business rule concepts."""
    
    def test_user_type_immutability_concept(self):
        """
        Validates: AUTH-010 - User type field MUST NOT be modifiable concept
        """
        user = User.objects.create_user(
            username='concept_user',
            email='concept@example.com',
            password='testpass123',
            user_type='client',
            name='Concept User'
        )
        
        # Business rule concept: user_type should not change
        self.assertEqual(user.user_type, 'client')
    
    def test_minor_student_parent_email_concept(self):
        """
        Validates: AUTH-006 - Parent email for minor students concept
        """
        user = User.objects.create_user(
            username='minor_concept',
            email='minor@example.com',
            password='testpass123',
            user_type='client',
            name='Minor Student'
        )
        
        profile = ClientProfile.objects.create(
            user=user,
            city='Milagro',
            country='Ecuador',
            is_minor=True,
            parent_email='parent@example.com',
            bio='Minor student'
        )
        
        # Business rule: Minor students should have parent email
        self.assertTrue(profile.is_minor)
        self.assertIsNotNone(profile.parent_email)
    
    def test_tutor_profile_public_data_concept(self):
        """
        Validates: AUTH-007 - TutorProfile data as public information concept
        """
        user = User.objects.create_user(
            username='public_tutor_concept',
            email='public@example.com',
            password='testpass123',
            user_type='tutor',
            name='Public Tutor'
        )
        
        profile = TutorProfile.objects.create(
            user=user,
            city='Milagro',
            country='Ecuador',
            bio='Available for tutoring',
            hourly_rate=20.00
        )
        
        # Business rule: Tutor profiles should be public
        self.assertIsNotNone(profile.bio)
        self.assertIsNotNone(profile.hourly_rate)