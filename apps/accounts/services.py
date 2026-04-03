"""
Service functions for accounts app.
Handles business logic for profile management and user operations.
"""

from django.db import transaction
from django.contrib.auth import login
from .models import TutorProfile, ClientProfile, User


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
        profile = user.tutor_profile
        geo_data = getattr(request, 'geo_data', None)
        if geo_data:
            city = geo_data.get('city', '')
            country = geo_data.get('country', '')
            if city:
                profile.city = city
            if country:
                profile.country = country
            profile.save()
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
        profile = user.client_profile
        geo_data = getattr(request, 'geo_data', None)
        if geo_data:
            city = geo_data.get('city', '')
            country = geo_data.get('country', '')
            if city:
                profile.city = city
            if country:
                profile.country = country
            profile.save()
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
    Updates TutorProfile.subjects_taught ManyToMany.
    Returns: (success: bool, subjects_queryset|None, error: str|None)
    """
    if not form.is_valid():
        return False, None, 'Invalid form data'
    try:
        profile, subjects = form.save()
        profile.subjects_taught.set(subjects)
        return True, profile.subjects_taught.all(), None
    except Exception as e:
        return False, None, str(e)
