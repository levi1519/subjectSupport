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


@transaction.atomic
def register_tutor(request, form, country_code=''):
    """
    Creates User with user_type='tutor' and associated TutorProfile.
    MUST NOT be called from template logic.
    Returns: (success: bool, user: User, error: str)
    """
    if not form.is_valid():
        return False, None, 'Invalid form data'
    try:
        user = form.save(country_code=country_code)
        login(request, user)
        return True, user, None
    except Exception as e:
        return False, None, str(e)


@transaction.atomic
def register_client(request, form, country_code=''):
    """
    Creates User with user_type='client' and associated ClientProfile.
    Returns: (success: bool, user: User, error: str)
    """
    if not form.is_valid():
        return False, None, 'Invalid form data'
    try:
        user = form.save(country_code=country_code)
        login(request, user)
        return True, user, None
    except Exception as e:
        return False, None, str(e)


@transaction.atomic
def update_tutor_profile(user, form):
    """
    Updates TutorProfile and User.email atomically.
    Returns: (success: bool, profile: TutorProfile|None, error: str|None)
    """
    if not form.is_valid():
        return False, None, 'Invalid form data'
    try:
        profile = form.save()
        return True, profile, None
    except Exception as e:
        return False, None, str(e)


@transaction.atomic
def update_client_profile(user, form):
    """
    Updates ClientProfile and User.email atomically.
    Returns: (success: bool, profile: ClientProfile|None, error: str|None)
    """
    if not form.is_valid():
        return False, None, 'Invalid form data'
    try:
        profile = form.save()
        return True, profile, None
    except Exception as e:
        return False, None, str(e)


@transaction.atomic
def manage_tutor_subjects(user, form):
    """
    Updates TutorProfile.subjects ManyToMany.
    Returns: (success: bool, subjects_queryset|None, error: str|None)
    """
    if not form.is_valid():
        return False, None, 'Invalid form data'
    try:
        profile = form.save()
        return True, profile.subjects.all(), None
    except Exception as e:
        return False, None, str(e)
