"""
RFC 2119 Unit Tests for accounts.models
Validates Global: GEO-002, AUTH-006, AUTH-007 | Individual: REQ-ACC-MOD-001 to REQ-ACC-MOD-010
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from test_base import UnitTestCase
from apps.accounts.models import User, Subject, TutorProfile, ClientProfile


class AccountsModelsUnitTests(UnitTestCase):
    """Unit tests for accounts.models with RFC 2119 evidence"""
    
    def setUp(self):
        super().setUp()
        self.module_name = "models"
    
    def test_user_creation_with_email_as_username(self):
        """Validates Global: AUTH-003 | Individual: REQ-ACC-MOD-001
        User model MUST use email as USERNAME_FIELD"""
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            name='Test User',
            user_type='client'
        )
        
        self.assertRFC(
            condition=user.USERNAME_FIELD == 'email',
            requirement_id="AUTH-003",
            individual_id="REQ-ACC-MOD-001",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="User model correctly uses email as USERNAME_FIELD",
            failure_msg="User model does not use email as USERNAME_FIELD"
        )
        
        self.assertRFC(
            condition=user.email == 'test@example.com',
            requirement_id="AUTH-003",
            individual_id="REQ-ACC-MOD-001",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="User email matches provided email",
            failure_msg="User email does not match provided email"
        )
    
    def test_user_email_uniqueness(self):
        """Validates Global: AUTH-004 | Individual: REQ-ACC-MOD-002
        Email MUST be unique across all users"""
        
        User.objects.create_user(
            username='user1',
            email='unique@example.com',
            password='testpass123',
            name='User One',
            user_type='client'
        )
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='unique@example.com',
                password='testpass123',
                name='User Two',
                user_type='tutor'
            )
        
        self.add_evidence(
            requirement_id="AUTH-004",
            individual_id="REQ-ACC-MOD-002",
            level=self.level,
            status="PASS",
            rfc_compliance="MUST",
            evidence="Email uniqueness constraint enforced at database level",
            module_name=self.module_name
        )
    
    def test_client_profile_location_fields(self):
        """Validates Global: GEO-002 | Individual: REQ-ACC-MOD-003
        ClientProfile MUST have city and country fields with Milagro/Ecuador defaults"""
        
        user = User.objects.create_user(
            username='client1',
            email='client@example.com',
            password='testpass123',
            name='Test Client',
            user_type='client'
        )
        
        profile = ClientProfile.objects.create(user=user)
        
        self.assertRFC(
            condition=hasattr(profile, 'city'),
            requirement_id="GEO-002",
            individual_id="REQ-ACC-MOD-003",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="ClientProfile has city field",
            failure_msg="ClientProfile missing city field"
        )
        
        self.assertRFC(
            condition=hasattr(profile, 'country'),
            requirement_id="GEO-002",
            individual_id="REQ-ACC-MOD-003",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="ClientProfile has country field",
            failure_msg="ClientProfile missing country field"
        )
        
        self.assertRFC(
            condition=profile.city == 'Milagro',
            requirement_id="GEO-002",
            individual_id="REQ-ACC-MOD-003",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="ClientProfile city defaults to 'Milagro'",
            failure_msg="ClientProfile city does not default to 'Milagro'"
        )
        
        self.assertRFC(
            condition=profile.country == 'Ecuador',
            requirement_id="GEO-002",
            individual_id="REQ-ACC-MOD-003",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="ClientProfile country defaults to 'Ecuador'",
            failure_msg="ClientProfile country does not default to 'Ecuador'"
        )
    
    def test_tutor_profile_location_fields(self):
        """Validates Global: GEO-002 | Individual: REQ-ACC-MOD-004
        TutorProfile MUST have city and country fields with Milagro/Ecuador defaults"""
        
        user = User.objects.create_user(
            username='tutor1',
            email='tutor@example.com',
            password='testpass123',
            name='Test Tutor',
            user_type='tutor'
        )
        
        profile = TutorProfile.objects.create(user=user)
        
        self.assertRFC(
            condition=hasattr(profile, 'city'),
            requirement_id="GEO-002",
            individual_id="REQ-ACC-MOD-004",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="TutorProfile has city field",
            failure_msg="TutorProfile missing city field"
        )
        
        self.assertRFC(
            condition=hasattr(profile, 'country'),
            requirement_id="GEO-002",
            individual_id="REQ-ACC-MOD-004",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="TutorProfile has country field",
            failure_msg="TutorProfile missing country field"
        )
        
        self.assertRFC(
            condition=profile.city == 'Milagro',
            requirement_id="GEO-002",
            individual_id="REQ-ACC-MOD-004",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="TutorProfile city defaults to 'Milagro'",
            failure_msg="TutorProfile city does not default to 'Milagro'"
        )
        
        self.assertRFC(
            condition=profile.country == 'Ecuador',
            requirement_id="GEO-002",
            individual_id="REQ-ACC-MOD-004",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="TutorProfile country defaults to 'Ecuador'",
            failure_msg="TutorProfile country does not default to 'Ecuador'"
        )
    
    def test_client_profile_parent_email_field(self):
        """Validates Global: AUTH-006 | Individual: REQ-ACC-MOD-005
        ClientProfile MUST have parent_email field for minor students"""
        
        user = User.objects.create_user(
            username='minorclient',
            email='minor@example.com',
            password='testpass123',
            name='Minor Client',
            user_type='client'
        )
        
        profile = ClientProfile.objects.create(
            user=user,
            is_minor=True,
            parent_email='parent@example.com'
        )
        
        self.assertRFC(
            condition=hasattr(profile, 'parent_email'),
            requirement_id="AUTH-006",
            individual_id="REQ-ACC-MOD-005",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="ClientProfile has parent_email field",
            failure_msg="ClientProfile missing parent_email field"
        )
        
        self.assertRFC(
            condition=profile.parent_email == 'parent@example.com',
            requirement_id="AUTH-006",
            individual_id="REQ-ACC-MOD-005",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="ClientProfile parent_email stores correctly",
            failure_msg="ClientProfile parent_email not stored correctly"
        )
    
    def test_tutor_profile_public_fields(self):
        """Validates Global: AUTH-007 | Individual: REQ-ACC-MOD-006
        TutorProfile fields MUST be publicly accessible"""
        
        user = User.objects.create_user(
            username='publictutor',
            email='public@example.com',
            password='testpass123',
            name='Public Tutor',
            user_type='tutor'
        )
        
        profile = TutorProfile.objects.create(
            user=user,
            bio='Experienced tutor',
            experience='5 years teaching',
            hourly_rate=25.00
        )
        
        public_fields = ['bio', 'experience', 'hourly_rate', 'city', 'country']
        
        for field in public_fields:
            self.assertRFC(
                condition=hasattr(profile, field),
                requirement_id="AUTH-007",
                individual_id="REQ-ACC-MOD-006",
                level=self.level,
                rfc_compliance="MUST",
                success_msg=f"TutorProfile has public field: {field}",
                failure_msg=f"TutorProfile missing public field: {field}"
            )
    
    def test_subject_model_slug_generation(self):
        """Validates Global: DATA-001 | Individual: REQ-ACC-MOD-007
        Subject model MUST auto-generate slug from name"""
        
        subject = Subject.objects.create(name='Matemáticas Avanzadas')
        
        self.assertRFC(
            condition=hasattr(subject, 'slug'),
            requirement_id="DATA-001",
            individual_id="REQ-ACC-MOD-007",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="Subject model has slug field",
            failure_msg="Subject model missing slug field"
        )
        
        self.assertRFC(
            condition=subject.slug == 'matematicas-avanzadas',
            requirement_id="DATA-001",
            individual_id="REQ-ACC-MOD-007",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="Subject slug auto-generated correctly",
            failure_msg="Subject slug not auto-generated correctly"
        )
    
    def test_user_type_validation(self):
        """Validates Global: USER-001 | Individual: REQ-ACC-MOD-008
        User type MUST be either 'tutor' or 'client'"""
        
        valid_user = User.objects.create_user(
            username='validuser',
            email='valid@example.com',
            password='testpass123',
            name='Valid User',
            user_type='tutor'  # Valid choice
        )
        
        self.assertRFC(
            condition=valid_user.user_type in ['tutor', 'client'],
            requirement_id="USER-001",
            individual_id="REQ-ACC-MOD-008",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="User type validation accepts valid choices",
            failure_msg="User type validation does not accept valid choices"
        )
    
    def test_profile_user_one_to_one_relationship(self):
        """Validates Global: DATA-004 | Individual: REQ-ACC-MOD-009
        Profile MUST have OneToOne relationship with User"""
        
        user = User.objects.create_user(
            username='reluser',
            email='rel@example.com',
            password='testpass123',
            name='Relation User',
            user_type='client'
        )
        
        profile = ClientProfile.objects.create(user=user)
        
        self.assertRFC(
            condition=profile.user == user,
            requirement_id="DATA-004",
            individual_id="REQ-ACC-MOD-009",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="ClientProfile has correct OneToOne relationship with User",
            failure_msg="ClientProfile does not have correct OneToOne relationship with User"
        )
        
        self.assertRFC(
            condition=hasattr(user, 'client_profile'),
            requirement_id="DATA-004",
            individual_id="REQ-ACC-MOD-009",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="User has reverse relation to ClientProfile",
            failure_msg="User missing reverse relation to ClientProfile"
        )
    
    def test_tutor_profile_subjects_relationship(self):
        """Validates Global: DATA-004 | Individual: REQ-ACC-MOD-010
        TutorProfile MUST have ManyToMany relationship with subjects"""
        
        user = User.objects.create_user(
            username='subjecttutor',
            email='subject@example.com',
            password='testpass123',
            name='Subject Tutor',
            user_type='tutor'
        )
        
        profile = TutorProfile.objects.create(user=user)
        subject1 = Subject.objects.create(name='Matemáticas')
        subject2 = Subject.objects.create(name='Física')
        
        profile.subjects.add(subject1, subject2)
        
        self.assertRFC(
            condition=hasattr(profile, 'subjects'),
            requirement_id="DATA-004",
            individual_id="REQ-ACC-MOD-010",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="TutorProfile has subjects ManyToMany field",
            failure_msg="TutorProfile missing subjects ManyToMany field"
        )
        
        self.assertRFC(
            condition=profile.subjects.count() == 2,
            requirement_id="DATA-004",
            individual_id="REQ-ACC-MOD-010",
            level=self.level,
            rfc_compliance="MUST",
            success_msg="TutorProfile can have multiple subjects",
            failure_msg="TutorProfile cannot have multiple subjects"
        )