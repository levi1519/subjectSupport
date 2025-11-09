"""
Comprehensive test suite for core app
Tests class booking, meeting integration, geographical search, and session workflow
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from core.models import ClassSession, TutorLead
from core.forms import SessionRequestForm, SessionConfirmationForm, TutorLeadForm
from core.services.meeting_service import (
    generate_google_meet_url,
    generate_zoom_url,
    generate_custom_meeting_url,
    create_meeting_for_session,
    update_session_with_meeting
)
from accounts.test_utils import UserFactory


class ClassSessionModelTest(TestCase):
    """Test ClassSession model functionality"""

    def setUp(self):
        self.tutor = UserFactory.create_tutor(email='tutor@test.com')
        self.client_user = UserFactory.create_client(email='client@test.com')

    def test_create_class_session(self):
        """Test creating a class session"""
        session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.client_user,
            subject='Mathematics',
            scheduled_date=date.today() + timedelta(days=1),
            scheduled_time=time(14, 0),
            duration=60,
            status='pending'
        )
        self.assertEqual(session.subject, 'Mathematics')
        self.assertEqual(session.status, 'pending')
        self.assertEqual(session.duration, 60)

    def test_session_str_representation(self):
        """Test session string representation"""
        session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.client_user,
            subject='Physics',
            scheduled_date=date.today() + timedelta(days=1),
            scheduled_time=time(14, 0),
            status='confirmed'
        )
        session_str = str(session)
        self.assertIn('Physics', session_str)
        self.assertIn(self.tutor.name, session_str)
        self.assertIn(self.client_user.name, session_str)

    def test_session_status_choices(self):
        """Test session status can be set to all valid choices"""
        session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.client_user,
            subject='Math',
            scheduled_date=date.today() + timedelta(days=1),
            scheduled_time=time(14, 0)
        )

        valid_statuses = ['pending', 'confirmed', 'completed', 'cancelled']
        for status in valid_statuses:
            session.status = status
            session.save()
            session.refresh_from_db()
            self.assertEqual(session.status, status)

    def test_session_with_meeting_platform(self):
        """Test session with meeting platform fields"""
        session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.client_user,
            subject='Math',
            scheduled_date=date.today() + timedelta(days=1),
            scheduled_time=time(14, 0),
            meeting_platform='google_meet',
            meeting_url='https://meet.google.com/abc-defg-hij',
            meeting_id='abc-defg-hij'
        )
        self.assertEqual(session.meeting_platform, 'google_meet')
        self.assertIsNotNone(session.meeting_url)
        self.assertIsNotNone(session.meeting_id)

    def test_is_upcoming_method(self):
        """Test is_upcoming method"""
        # Future session
        future_session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.client_user,
            subject='Math',
            scheduled_date=date.today() + timedelta(days=7),
            scheduled_time=time(14, 0),
            status='confirmed'
        )
        self.assertTrue(future_session.is_upcoming())

        # Past session
        past_session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.client_user,
            subject='Math',
            scheduled_date=date.today() - timedelta(days=7),
            scheduled_time=time(14, 0),
            status='confirmed'
        )
        self.assertFalse(past_session.is_upcoming())

    def test_is_past_method(self):
        """Test is_past method"""
        past_session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.client_user,
            subject='Math',
            scheduled_date=date.today() - timedelta(days=1),
            scheduled_time=time(14, 0)
        )
        self.assertTrue(past_session.is_past())


class TutorLeadModelTest(TestCase):
    """Test TutorLead model"""

    def test_create_tutor_lead(self):
        """Test creating a tutor lead"""
        lead = TutorLead.objects.create(
            name='John Doe',
            email='john@example.com',
            subject='Mathematics'
        )
        self.assertEqual(lead.name, 'John Doe')
        self.assertEqual(lead.email, 'john@example.com')
        self.assertEqual(lead.subject, 'Mathematics')

    def test_tutor_lead_ordering(self):
        """Test tutor leads are ordered by -created_at"""
        lead1 = TutorLead.objects.create(
            name='First', email='first@test.com', subject='Math'
        )
        lead2 = TutorLead.objects.create(
            name='Second', email='second@test.com', subject='Physics'
        )
        leads = TutorLead.objects.all()
        self.assertEqual(leads[0], lead2)  # Most recent first


class SessionRequestFormTest(TestCase):
    """Test SessionRequestForm"""

    def test_valid_session_request(self):
        """Test valid session request form"""
        form_data = {
            'subject': 'Mathematics - Algebra',
            'scheduled_date': (date.today() + timedelta(days=7)).isoformat(),
            'scheduled_time': '14:00',
            'duration': 60,
            'notes': 'Need help with quadratic equations'
        }
        form = SessionRequestForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_past_date_validation(self):
        """Test that past dates are rejected"""
        form_data = {
            'subject': 'Math',
            'scheduled_date': (date.today() - timedelta(days=1)).isoformat(),
            'scheduled_time': '14:00',
            'duration': 60
        }
        form = SessionRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('scheduled_date', form.errors)


class SessionConfirmationFormTest(TestCase):
    """Test SessionConfirmationForm"""

    def test_form_includes_meeting_platform(self):
        """Test form includes meeting platform field"""
        form = SessionConfirmationForm()
        self.assertIn('meeting_platform', form.fields)
        self.assertIn('notes', form.fields)

    def test_form_valid_with_platform(self):
        """Test form is valid with meeting platform"""
        form_data = {
            'meeting_platform': 'zoom',
            'notes': 'Looking forward to the session'
        }
        form = SessionConfirmationForm(data=form_data)
        self.assertTrue(form.is_valid())


class MeetingServiceTest(TestCase):
    """Test meeting URL generation service"""

    def setUp(self):
        self.tutor = UserFactory.create_tutor(name='Tutor')
        self.client_user = UserFactory.create_client(name='Student')
        self.session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.client_user,
            subject='Mathematics',
            scheduled_date=date.today() + timedelta(days=1),
            scheduled_time=time(14, 0),
            duration=60
        )

    def test_generate_google_meet_url(self):
        """Test Google Meet URL generation"""
        result = generate_google_meet_url(self.session)
        self.assertIn('meeting_url', result)
        self.assertIn('meet.google.com', result['meeting_url'])
        self.assertIsNotNone(result['meeting_id'])
        self.assertIsNone(result['meeting_password'])  # Google Meet doesn't use passwords

    def test_generate_zoom_url(self):
        """Test Zoom URL generation"""
        result = generate_zoom_url(self.session)
        self.assertIn('meeting_url', result)
        self.assertIn('zoom.us', result['meeting_url'])
        self.assertIsNotNone(result['meeting_id'])
        self.assertIsNotNone(result['meeting_password'])
        self.assertIsNotNone(result['host_join_url'])

    def test_generate_custom_meeting_url(self):
        """Test custom meeting URL generation"""
        result = generate_custom_meeting_url(self.session)
        self.assertIn('meeting_url', result)
        self.assertIn('meet.subjectsupport.com', result['meeting_url'])
        self.assertIsNotNone(result['meeting_id'])
        self.assertIsNotNone(result['meeting_password'])

    def test_create_meeting_google_meet(self):
        """Test creating meeting with Google Meet platform"""
        self.session.meeting_platform = 'google_meet'
        result = create_meeting_for_session(self.session)
        self.assertIn('meet.google.com', result['meeting_url'])

    def test_create_meeting_zoom(self):
        """Test creating meeting with Zoom platform"""
        self.session.meeting_platform = 'zoom'
        result = create_meeting_for_session(self.session)
        self.assertIn('zoom.us', result['meeting_url'])

    def test_update_session_with_meeting(self):
        """Test updating session with meeting details"""
        self.session.meeting_platform = 'google_meet'
        updated_session = update_session_with_meeting(self.session, save=True)
        self.assertIsNotNone(updated_session.meeting_url)
        self.assertIsNotNone(updated_session.meeting_id)

        # Verify it was saved
        self.session.refresh_from_db()
        self.assertIsNotNone(self.session.meeting_url)


class TutorSelectionViewTest(TestCase):
    """Test tutor selection and geographical filtering"""

    def setUp(self):
        self.client_http = Client()
        self.student = UserFactory.create_client(
            email='student@test.com',
            password='testpass123',
            city='Quito',
            country='Ecuador'
        )

        # Create tutors in different locations
        self.tutor_quito = UserFactory.create_tutor(
            email='tutor_quito@test.com',
            name='Quito Tutor',
            city='Quito',
            country='Ecuador'
        )
        self.tutor_guayaquil = UserFactory.create_tutor(
            email='tutor_guayaquil@test.com',
            name='Guayaquil Tutor',
            city='Guayaquil',
            country='Ecuador'
        )
        self.tutor_colombia = UserFactory.create_tutor(
            email='tutor_colombia@test.com',
            name='Colombia Tutor',
            city='Bogota',
            country='Colombia'
        )

    def test_tutor_selection_page_loads(self):
        """Test tutor selection page loads"""
        self.client_http.login(username='student@test.com', password='testpass123')
        response = self.client_http.get(reverse('tutor_selection'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/tutor_selection.html')

    def test_tutor_selection_requires_client(self):
        """Test only clients can access tutor selection"""
        tutor = UserFactory.create_tutor(email='tutor@test.com', password='testpass123')
        self.client_http.login(username='tutor@test.com', password='testpass123')
        response = self.client_http.get(reverse('tutor_selection'))
        self.assertEqual(response.status_code, 302)  # Redirected

    def test_geographical_prioritization(self):
        """Test tutors are prioritized by location"""
        self.client_http.login(username='student@test.com', password='testpass123')
        response = self.client_http.get(reverse('tutor_selection'))

        same_city = response.context['same_city_tutors']
        same_country = response.context['same_country_tutors']
        others = response.context['other_tutors']

        # Verify prioritization
        self.assertEqual(len(same_city), 1)
        self.assertEqual(same_city[0], self.tutor_quito)

        self.assertEqual(len(same_country), 1)
        self.assertEqual(same_country[0], self.tutor_guayaquil)

        self.assertEqual(len(others), 1)
        self.assertEqual(others[0], self.tutor_colombia)

    def test_search_filter(self):
        """Test search functionality"""
        self.client_http.login(username='student@test.com', password='testpass123')
        response = self.client_http.get(reverse('tutor_selection'), {'search': 'Quito'})

        tutors = response.context['tutors']
        self.assertEqual(len(tutors), 1)
        self.assertEqual(tutors[0], self.tutor_quito)


class SessionRequestViewTest(TestCase):
    """Test session request view"""

    def setUp(self):
        self.client_http = Client()
        self.tutor = UserFactory.create_tutor(email='tutor@test.com')
        self.student = UserFactory.create_client(
            email='student@test.com',
            password='testpass123'
        )

    def test_request_session_page_loads(self):
        """Test request session page loads"""
        self.client_http.login(username='student@test.com', password='testpass123')
        url = reverse('request_session', kwargs={'tutor_id': self.tutor.id})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/request_session.html')

    def test_successful_session_request(self):
        """Test successful session request creation"""
        self.client_http.login(username='student@test.com', password='testpass123')
        url = reverse('request_session', kwargs={'tutor_id': self.tutor.id})

        form_data = {
            'subject': 'Mathematics',
            'scheduled_date': (date.today() + timedelta(days=7)).isoformat(),
            'scheduled_time': '14:00',
            'duration': 60,
            'notes': 'Need help with calculus'
        }

        response = self.client_http.post(url, data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard

        # Verify session was created
        session = ClassSession.objects.get(client=self.student, tutor=self.tutor)
        self.assertEqual(session.subject, 'Mathematics')
        self.assertEqual(session.status, 'pending')

    def test_only_client_can_request_session(self):
        """Test only clients can request sessions"""
        tutor2 = UserFactory.create_tutor(
            email='tutor2@test.com',
            password='testpass123'
        )
        self.client_http.login(username='tutor2@test.com', password='testpass123')
        url = reverse('request_session', kwargs={'tutor_id': self.tutor.id})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)  # Redirected


class SessionConfirmViewTest(TestCase):
    """Test session confirmation view"""

    def setUp(self):
        self.client_http = Client()
        self.tutor = UserFactory.create_tutor(
            email='tutor@test.com',
            password='testpass123'
        )
        self.student = UserFactory.create_client(email='student@test.com')

        self.session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.student,
            subject='Mathematics',
            scheduled_date=date.today() + timedelta(days=7),
            scheduled_time=time(14, 0),
            duration=60,
            status='pending'
        )

    def test_confirm_session_page_loads(self):
        """Test confirm session page loads"""
        self.client_http.login(username='tutor@test.com', password='testpass123')
        url = reverse('confirm_session', kwargs={'session_id': self.session.id})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/confirm_session.html')

    def test_successful_session_confirmation(self):
        """Test successful session confirmation with meeting generation"""
        self.client_http.login(username='tutor@test.com', password='testpass123')
        url = reverse('confirm_session', kwargs={'session_id': self.session.id})

        form_data = {
            'meeting_platform': 'google_meet',
            'notes': 'Bring your textbook'
        }

        response = self.client_http.post(url, data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirect to dashboard

        # Verify session was confirmed
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'confirmed')
        self.assertEqual(self.session.meeting_platform, 'google_meet')
        self.assertIsNotNone(self.session.meeting_url)
        self.assertIsNotNone(self.session.meeting_id)

    def test_only_tutor_can_confirm(self):
        """Test only the session tutor can confirm"""
        another_tutor = UserFactory.create_tutor(
            email='another@test.com',
            password='testpass123'
        )
        self.client_http.login(username='another@test.com', password='testpass123')
        url = reverse('confirm_session', kwargs={'session_id': self.session.id})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 404)  # Not found

    def test_cannot_confirm_already_confirmed(self):
        """Test cannot confirm already confirmed session"""
        self.session.status = 'confirmed'
        self.session.save()

        self.client_http.login(username='tutor@test.com', password='testpass123')
        url = reverse('confirm_session', kwargs={'session_id': self.session.id})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)  # Redirected with warning


class SessionCancelViewTest(TestCase):
    """Test session cancellation"""

    def setUp(self):
        self.client_http = Client()
        self.tutor = UserFactory.create_tutor(
            email='tutor@test.com',
            password='testpass123'
        )
        self.student = UserFactory.create_client(
            email='student@test.com',
            password='testpass123'
        )

        self.session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.student,
            subject='Mathematics',
            scheduled_date=date.today() + timedelta(days=7),
            scheduled_time=time(14, 0),
            status='pending'
        )

    def test_tutor_can_cancel_session(self):
        """Test tutor can cancel session"""
        self.client_http.login(username='tutor@test.com', password='testpass123')
        url = reverse('cancel_session', kwargs={'session_id': self.session.id})

        response = self.client_http.post(url)
        self.assertEqual(response.status_code, 302)

        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'cancelled')

    def test_client_can_cancel_session(self):
        """Test client can cancel session"""
        self.client_http.login(username='student@test.com', password='testpass123')
        url = reverse('cancel_session', kwargs={'session_id': self.session.id})

        response = self.client_http.post(url)
        self.assertEqual(response.status_code, 302)

        self.session.refresh_from_db()
        self.assertEqual(self.session.status, 'cancelled')

    def test_unauthorized_user_cannot_cancel(self):
        """Test unauthorized user cannot cancel session"""
        other_user = UserFactory.create_client(
            email='other@test.com',
            password='testpass123'
        )
        self.client_http.login(username='other@test.com', password='testpass123')
        url = reverse('cancel_session', kwargs={'session_id': self.session.id})

        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)  # Redirected with error


class MeetingRoomViewTest(TestCase):
    """Test meeting room access"""

    def setUp(self):
        self.client_http = Client()
        self.tutor = UserFactory.create_tutor(
            email='tutor@test.com',
            password='testpass123'
        )
        self.student = UserFactory.create_client(
            email='student@test.com',
            password='testpass123'
        )

        self.session = ClassSession.objects.create(
            tutor=self.tutor,
            client=self.student,
            subject='Mathematics',
            scheduled_date=date.today() + timedelta(days=1),
            scheduled_time=time(14, 0),
            status='confirmed',
            meeting_platform='google_meet',
            meeting_url='https://meet.google.com/abc-defg-hij',
            meeting_id='abc-defg-hij'
        )

    def test_meeting_room_page_loads(self):
        """Test meeting room page loads for authorized users"""
        self.client_http.login(username='student@test.com', password='testpass123')
        url = reverse('meeting_room', kwargs={'session_id': self.session.id})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/meeting_room.html')

    def test_tutor_is_host(self):
        """Test tutor is identified as host"""
        self.client_http.login(username='tutor@test.com', password='testpass123')
        url = reverse('meeting_room', kwargs={'session_id': self.session.id})
        response = self.client_http.get(url)
        self.assertTrue(response.context['is_host'])

    def test_client_is_not_host(self):
        """Test client is not identified as host"""
        self.client_http.login(username='student@test.com', password='testpass123')
        url = reverse('meeting_room', kwargs={'session_id': self.session.id})
        response = self.client_http.get(url)
        self.assertFalse(response.context['is_host'])

    def test_unauthorized_user_cannot_access_meeting(self):
        """Test unauthorized user cannot access meeting room"""
        other_user = UserFactory.create_client(
            email='other@test.com',
            password='testpass123'
        )
        self.client_http.login(username='other@test.com', password='testpass123')
        url = reverse('meeting_room', kwargs={'session_id': self.session.id})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)  # Redirected

    def test_cannot_access_unconfirmed_meeting(self):
        """Test cannot access meeting room for unconfirmed session"""
        self.session.status = 'pending'
        self.session.save()

        self.client_http.login(username='student@test.com', password='testpass123')
        url = reverse('meeting_room', kwargs={'session_id': self.session.id})
        response = self.client_http.get(url)
        self.assertEqual(response.status_code, 302)  # Redirected

    def test_meeting_started_flag_set(self):
        """Test meeting_started flag is set when tutor accesses"""
        self.assertFalse(self.session.meeting_started)

        self.client_http.login(username='tutor@test.com', password='testpass123')
        url = reverse('meeting_room', kwargs={'session_id': self.session.id})
        self.client_http.get(url)

        self.session.refresh_from_db()
        self.assertTrue(self.session.meeting_started)


class LandingPageTest(TestCase):
    """Test landing page"""

    def test_landing_page_loads(self):
        """Test landing page loads for anonymous users"""
        client = Client()
        response = client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/landing.html')
