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
        user = form.save(commit=False, country_code=country_code)
        birth_date = getattr(form.instance, 'birth_date', None) or form.cleaned_data.get('birth_date')
        if birth_date:
            from datetime import date
            today = date.today()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            if age < 18:
                return False, None, 'El tutor debe ser mayor de 18 años.'
        user.save()
        profile = TutorProfile.objects.create(
            user=user,
            bio=form.cleaned_data.get('bio', ''),
            experience=form.cleaned_data.get('experience', ''),
            phone_number=form.cleaned_data.get('phone_number', '')
        )
        profile.cedula = form.cleaned_data.get('cedula', '')
        profile.avatar_url = form.cleaned_data.get('avatar_url', '')
        geo_data = getattr(request, 'geo_data', {}) or {}
        if geo_data.get('city'):
            profile.city = geo_data['city']
        if geo_data.get('country'):
            profile.country = geo_data['country']
        from apps.academicTutoring.models import PlatformConfig
        config = PlatformConfig.get_config()
        if config.require_tutor_document:
            profile.is_approved = False
        # Flujo aprobación por conocimiento
        if config.require_tutor_knowledge_document:
            profile.is_approved = False
        profile.save()

        from apps.academicTutoring.models import Institution

        # Guardar campos nuevos
        if form.cleaned_data.get('cv_file'):
            profile.cv_file = form.cleaned_data['cv_file']
        if form.cleaned_data.get('employment_status'):
            profile.employment_status = form.cleaned_data['employment_status']
        if form.cleaned_data.get('education_level'):
            profile.education_level = form.cleaned_data['education_level']
        if form.cleaned_data.get('education_certificate_file'):
            profile.education_certificate_file = form.cleaned_data['education_certificate_file']
        if form.cleaned_data.get('institutional_credential_file'):
            profile.institutional_credential_file = form.cleaned_data['institutional_credential_file']

        # Manejar institucion
        institution_id = form.cleaned_data.get('institution_id')
        institution_manual = form.cleaned_data.get('institution_manual', '').strip()
        if institution_id:
            try:
                profile.institution = Institution.objects.get(pk=institution_id, active=True)
            except Institution.DoesNotExist:
                pass
        elif institution_manual:
            inst, _ = Institution.objects.get_or_create(
                name=institution_manual,
                defaults={
                    'type': 'universidad',
                    'is_manual': True,
                    'needs_review': True,
                    'active': True,
                }
            )
            profile.institution = inst

        profile.save()
        subjects = form.cleaned_data.get('subjects_taught')
        if subjects:
            profile.subjects_taught.set(subjects)
            profile.refresh_from_db()
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
        geo_data = getattr(request, 'geo_data', {}) or {}
        if geo_data.get('city'):
            profile.city = geo_data['city']
        if geo_data.get('country'):
            profile.country = geo_data['country']
        profile.save()

        from apps.academicTutoring.models import Institution

        if form.cleaned_data.get('student_type'):
            profile.student_type = form.cleaned_data['student_type']
        if form.cleaned_data.get('id_document_file'):
            profile.id_document_file = form.cleaned_data['id_document_file']
        if form.cleaned_data.get('enrollment_file'):
            profile.enrollment_file = form.cleaned_data['enrollment_file']

        institution_id = form.cleaned_data.get('institution_id')
        institution_manual = form.cleaned_data.get('institution_manual', '').strip()
        if institution_id:
            try:
                profile.institution = Institution.objects.get(pk=institution_id, active=True)
            except Institution.DoesNotExist:
                pass
        elif institution_manual:
            inst, _ = Institution.objects.get_or_create(
                name=institution_manual,
                defaults={
                    'type': 'universidad',
                    'is_manual': True,
                    'needs_review': True,
                    'active': True,
                }
            )
            profile.institution = inst

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
        profile = form.save(commit=False)
        subjects = form.cleaned_data['subjects_taught']
        profile.subjects_taught.set(subjects)
        profile.save()
        return True, profile.subjects_taught.all(), None
    except Exception as e:
        return False, None, str(e)
