"""
Service functions for academicTutoring app.
Handles business logic for session management and tutoring operations.
"""

from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from ..models import ClassSession


class SessionError(Exception):
    """Custom exception for session-related errors"""
    pass


@transaction.atomic
def create_session(tutor, client, form):
    if not form.is_valid():
        return False, None, 'Invalid form data.'
    session = form.save(commit=False)
    session.tutor = tutor
    session.client = client
    session.status = 'pending'
    session.save()
    return True, session, None


@transaction.atomic
def confirm_session(session, user, form):
    """
    Confirm a tutoring session and generate meeting URL.
    Returns: (success: bool, session: ClassSession|None, error: str|None)
    """
    try:
        if session.tutor != user:
            return False, None, 'No tienes permiso para confirmar esta sesión'
        if not form.is_valid():
            return False, None, 'Invalid confirmation form data.'
        session.meeting_platform = form.cleaned_data['meeting_platform']
        session.notes = form.cleaned_data.get('notes', '')
        session.status = 'confirmed'
        session.save()
        return True, session, None
    except Exception as e:
        return False, None, str(e)


@transaction.atomic
def cancel_session(session, user):
    """
    Cancel a tutoring session with ownership validation.
    Returns: (success: bool, session: ClassSession|None, error: str|None)
    """
    try:
        if session.tutor != user and session.client != user:
            return False, None, 'No tienes permiso para cancelar esta sesión'
        if session.status not in ['pending', 'confirmed']:
            return False, None, f'Cannot cancel session with status: {session.status}'
        session.status = 'cancelled'
        session.save()
        return True, session, None
    except Exception as e:
        return False, None, str(e)


@transaction.atomic
def start_meeting(session, user):
    """
    Start a meeting session.
    
    Args:
        session: ClassSession instance
        user: User starting the meeting (must be tutor)
        
    Raises:
        PermissionDenied: If user is not the tutor
        
    Returns:
        ClassSession: The session with meeting started
    """
    if session.tutor != user:
        raise PermissionDenied('Only the tutor can start the meeting.')
    session.meeting_started = True
    session.save()
    return session


# Backwards compatibility: keep SessionService class for existing code
from .services import SessionService

__all__ = [
    'SessionError', 'create_session', 'confirm_session', 
    'cancel_session', 'start_meeting', 'SessionService'
]
