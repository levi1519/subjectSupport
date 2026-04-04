"""
Utility functions for academicTutoring app.
Handles email notifications and helper functions.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_cancellation_email(session, cancelled_by, recipient):
    """
    Send cancellation notification email to the affected party.

    Args:
        session: ClassSession instance that was cancelled
        cancelled_by: User instance who cancelled the session
        recipient: User instance who should receive the email (the affected party)

    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    subject = f"[SubjectSupport] {cancelled_by.name} canceló la clase de {session.subject}"

    # Determine dashboard URL based on recipient type
    from django.urls import reverse
    if recipient.user_type == 'tutor':
        dashboard_url = settings.SITE_URL + reverse('tutor_dashboard') if hasattr(settings, 'SITE_URL') else reverse('tutor_dashboard')
    else:
        dashboard_url = settings.SITE_URL + reverse('client_dashboard') if hasattr(settings, 'SITE_URL') else reverse('client_dashboard')

    context = {
        'recipient_name': recipient.name,
        'cancelled_by_name': cancelled_by.name,
        'session_subject': session.subject,
        'session_date': session.scheduled_date.strftime('%d/%m/%Y'),
        'session_time': session.scheduled_time.strftime('%H:%M'),
        'cancellation_reason': getattr(session, 'cancellation_reason', None),
        'dashboard_url': dashboard_url,
    }

    html_message = render_to_string('emails/session_cancelled.html', context)
    plain_message = render_to_string('emails/session_cancelled.txt', context)

    try:
        print(f"EMAIL SENT TO {recipient.email}")
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=True,
            html_message=html_message,
        )
        logger.info(f"Cancellation email sent to {recipient.email} for session {session.id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send cancellation email to {recipient.email}: {e}")
        return False
