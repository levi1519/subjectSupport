"""
Meeting service for automatic Google Meet and Zoom URL generation
"""
import uuid
import secrets
import string
from datetime import datetime


def generate_meeting_topic(session):
    """
    Generate a professional meeting topic based on session details
    Example: "Matemáticas - Juan García con María López"
    """
    return f"{session.subject} - {session.tutor.name} con {session.client.name}"


def generate_meeting_password(length=6):
    """
    Generate a random alphanumeric password for meetings
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_google_meet_url(session):
    """
    Generate a Google Meet URL for the session

    For now, this generates a custom URL with a unique ID.
    In production, integrate with Google Meet API for real meeting creation.

    Returns dict with:
        - meeting_url: Join URL for participants
        - host_join_url: Special URL for host (same as meeting_url for now)
        - meeting_id: Unique meeting identifier
        - meeting_password: None (Google Meet handles auth differently)
    """
    # Generate unique meeting code (format: xxx-xxxx-xxx like real Google Meet)
    unique_id = uuid.uuid4().hex[:10]
    meeting_code = f"{unique_id[:3]}-{unique_id[3:7]}-{unique_id[7:10]}"

    # Create meeting URL
    meeting_url = f"https://meet.google.com/{unique_id}"

    return {
        'meeting_url': meeting_url,
        'host_join_url': meeting_url,  # Same URL for now, can differentiate later
        'meeting_id': meeting_code,
        'meeting_password': None,  # Google Meet doesn't use passwords
    }


def generate_zoom_url(session):
    """
    Generate a Zoom meeting URL for the session

    For now, this generates a placeholder URL with a unique ID.
    In production, integrate with Zoom API for real meeting creation.

    Returns dict with:
        - meeting_url: Join URL for participants
        - host_join_url: Special URL for host to start meeting
        - meeting_id: Zoom meeting ID
        - meeting_password: Meeting password
    """
    # Generate unique meeting ID (format: XXX XXXX XXXX like real Zoom)
    meeting_id_num = secrets.randbelow(99999999999)
    meeting_id = f"{meeting_id_num:011d}"
    meeting_id_formatted = f"{meeting_id[:3]} {meeting_id[3:7]} {meeting_id[7:]}"

    # Generate password
    password = generate_meeting_password()

    # Create URLs (placeholder structure)
    meeting_url = f"https://zoom.us/j/{meeting_id}?pwd={password}"
    host_join_url = f"https://zoom.us/s/{meeting_id}?zak=host_{uuid.uuid4().hex[:16]}"

    return {
        'meeting_url': meeting_url,
        'host_join_url': host_join_url,
        'meeting_id': meeting_id_formatted,
        'meeting_password': password,
    }


def generate_custom_meeting_url(session):
    """
    Generate a custom SubjectSupport meeting URL

    Returns dict with:
        - meeting_url: Custom meeting room URL
        - host_join_url: Same as meeting_url
        - meeting_id: Unique room identifier
        - meeting_password: Room password
    """
    # Generate unique room ID
    room_id = uuid.uuid4().hex[:12]
    password = generate_meeting_password(8)

    # Create custom meeting URL
    meeting_url = f"https://meet.subjectsupport.com/room/{room_id}"

    return {
        'meeting_url': meeting_url,
        'host_join_url': meeting_url,
        'meeting_id': room_id,
        'meeting_password': password,
    }


def create_meeting_for_session(session):
    """
    Main function to create a meeting based on the session's meeting_platform

    Args:
        session: ClassSession instance

    Returns:
        dict with meeting details (meeting_url, host_join_url, meeting_id, meeting_password)
    """
    platform = session.meeting_platform

    if platform == 'google_meet':
        return generate_google_meet_url(session)
    elif platform == 'zoom':
        return generate_zoom_url(session)
    elif platform == 'custom':
        return generate_custom_meeting_url(session)
    else:
        # Default to Google Meet
        return generate_google_meet_url(session)


def update_session_with_meeting(session, save=True):
    """
    Update a ClassSession with automatically generated meeting details

    Args:
        session: ClassSession instance
        save: Whether to save the session after updating (default: True)

    Returns:
        Updated session instance
    """
    meeting_data = create_meeting_for_session(session)

    session.meeting_url = meeting_data['meeting_url']
    session.host_join_url = meeting_data['host_join_url']
    session.meeting_id = meeting_data['meeting_id']
    session.meeting_password = meeting_data.get('meeting_password')

    if save:
        session.save()

    return session
