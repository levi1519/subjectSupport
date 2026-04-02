"""
Service layer for academicTutoring app.
Handles business logic for session management and tutoring operations.
"""

from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from ..models import ClassSession
from .meeting_service import update_session_with_meeting
import logging

logger = logging.getLogger(__name__)


class SessionService:
    """
    Service class for session-related operations.
    Centralizes business logic for session lifecycle management.
    """
    
    @staticmethod
    @transaction.atomic
    def create_session(tutor, client, form_data):
        """
        Create a new tutoring session.
        
        Args:
            tutor: User instance (must be tutor)
            client: User instance (must be client)
            form_data: Cleaned form data
            
        Returns:
            tuple: (success: bool, session: ClassSession or None, error: str or None)
        """
        try:
            session = ClassSession.objects.create(
                tutor=tutor,
                client=client,
                subject=form_data.get('subject'),
                scheduled_date=form_data.get('scheduled_date'),
                scheduled_time=form_data.get('scheduled_time'),
                duration=form_data.get('duration', 60),
                status='pending',
                notes=form_data.get('notes', '')
            )
            return True, session, None
            
        except Exception as e:
            return False, None, str(e)
    
    @staticmethod
    @transaction.atomic
    def confirm_session(session, platform):
        """
        Confirm a tutoring session and generate meeting URL.
        
        Args:
            session: ClassSession instance
            platform: Meeting platform choice
            
        Returns:
            tuple: (success: bool, session: ClassSession or None, error: str or None)
        """
        try:
            if session.status != 'pending':
                return False, None, 'Session already processed'
            
            session.status = 'confirmed'
            session.meeting_platform = platform
            update_session_with_meeting(session, save=False)
            session.save()
            
            return True, session, None
            
        except Exception as e:
            return False, None, str(e)
    
    @staticmethod
    @transaction.atomic
    def cancel_session(session, user):
        """
        Cancel a tutoring session with ownership validation.
        
        Args:
            session: ClassSession instance
            user: User requesting cancellation
            
        Returns:
            tuple: (success: bool, session: ClassSession or None, error: str or None)
        """
        try:
            # Validate ownership
            if user != session.tutor and user != session.client:
                return False, None, 'No permission to cancel this session'
            
            # Validate session status
            if session.status == 'cancelled':
                return False, None, 'Session already cancelled'
            
            if session.status == 'completed':
                return False, None, 'Cannot cancel completed session'
            
            session.status = 'cancelled'
            session.save()
            
            return True, session, None
            
        except Exception as e:
            return False, None, str(e)
    
    @staticmethod
    @transaction.atomic
    def start_meeting(session):
        """
        Start a meeting session.
        
        Args:
            session: ClassSession instance
            
        Returns:
            tuple: (success: bool, session: ClassSession or None, error: str or None)
        """
        try:
            if not session.meeting_started:
                session.meeting_started = True
                session.save()
            
            return True, session, None
            
        except Exception as e:
            return False, None, str(e)
