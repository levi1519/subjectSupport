"""
Service functions for accounts app.
Handles business logic for profile management and user operations.
"""

from django.db import transaction
from django.contrib.auth import login
from .models import TutorProfile, ClientProfile, User


def validate_student_registration_access(request):
    """
    Validates that the request originates from Milagro service area.
    Returns: (is_allowed: bool, redirect_url: str | None)
    """
    from apps.academicTutoring.utils.geo import check_geo_restriction
    import logging

    logger = logging.getLogger(__name__)
    
    geo_data = check_geo_restriction(request)
    city = geo_data.get('city', 'Unknown')
    country = geo_data.get('country', 'Unknown')
    
    logger.warning(
        f"Student registration access attempt: city={city}, country={country}"
    )
    
    # Verificar que la ciudad sea exactamente Milagro (case-insensitive)
    is_in_service_area = city and city.strip().lower() == 'milagro'
    
    if not is_in_service_area:
        logger.error(
            f"SECURITY: Non-Milagro user tried to access student registration. "
            f"City={city}, Country={country}. Redirecting to tutor_landing."
        )
        return False, 'tutor_landing'
    
    return True, None


def register_tutor(request, form):
    """
    Creates User with user_type='tutor' and associated TutorProfile.
    MUST NOT be called from template logic.
    Returns: (success: bool, user: User, error: str)
    """
    if not form.is_valid():
        return False, None, 'Invalid form data'
    try:
        user = form.save()
        login(request, user)
        return True, user, None
    except Exception as e:
        return False, None, str(e)


def register_client(request, form):
    """
    Creates User with user_type='client' and associated ClientProfile.
    Returns: (success: bool, user: User, error: str)
    """
    if not form.is_valid():
        return False, None, 'Invalid form data'
    try:
        user = form.save()
        login(request, user)
        return True, user, None
    except Exception as e:
        return False, None, str(e)


@transaction.atomic
def update_tutor_profile(user, form):
    """
    Updates TutorProfile and User.email atomically.
    Returns: (success: bool, error: str)
    """
    if not form.is_valid():
        return False, 'Invalid form data'
    try:
        form.save()
        return True, None
    except Exception as e:
        return False, str(e)


@transaction.atomic
def update_client_profile(user, form):
    """
    Updates ClientProfile and User.email atomically.
    Returns: (success: bool, error: str)
    """
    if not form.is_valid():
        return False, 'Invalid form data'
    try:
        form.save()
        return True, None
    except Exception as e:
        return False, str(e)


@transaction.atomic
def manage_tutor_subjects(user, form):
    """
    Updates TutorProfile.subjects ManyToMany.
    Returns: (success: bool, error: str)
    """
    if not form.is_valid():
        return False, 'Invalid form data'
    try:
        form.save()
        return True, None
    except Exception as e:
        return False, str(e)
