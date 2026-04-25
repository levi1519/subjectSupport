"""
Service functions for accounts app.
Handles business logic for profile management and user operations.
"""

import re
import uuid
import os

from django.db import transaction
from django.contrib.auth import login
from .models import TutorProfile, ClientProfile, User


def sanitize_filename(filename):
    """
    Sanitiza el nombre de archivo para compatibilidad con S3.
    Reemplaza espacios y caracteres especiales, conserva la extensión.
    """
    name, ext = os.path.splitext(filename)
    # Eliminar tildes y caracteres especiales
    name = name.encode('ascii', 'ignore').decode('ascii')
    # Reemplazar cualquier caracter no alfanumérico por guión
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    # Limitar longitud + añadir UUID corto para evitar colisiones
    name = name[:40] + '_' + uuid.uuid4().hex[:8]
    return f"{name}{ext.lower()}"


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
        avatar = form.cleaned_data.get('avatar')
        if avatar:
            avatar.name = sanitize_filename(avatar.name)
            profile.avatar = avatar
        geo_data = getattr(request, 'geo_data', {}) or {}
        if geo_data.get('city'):
            profile.city = geo_data['city']
        if geo_data.get('country'):
            profile.country = geo_data['country']
        from apps.academicTutoring.models import PlatformConfig
        config = PlatformConfig.get_config()
        needs_approval = (
            config.require_tutor_knowledge_document or
            config.require_tutor_document or
            config.require_tutor_cv
        )
        if needs_approval:
            profile.is_approved = False
            profile.welcome_shown = False
        profile.save()

        from apps.academicTutoring.models import Institution

        # Guardar campos nuevos
        cv = form.cleaned_data.get('cv_file')
        if cv:
            cv.name = sanitize_filename(cv.name)
            profile.cv_file = cv
        if form.cleaned_data.get('employment_status'):
            profile.employment_status = form.cleaned_data['employment_status']
        if form.cleaned_data.get('education_level'):
            profile.education_level = form.cleaned_data['education_level']
        education_cert = form.cleaned_data.get('education_certificate_file')
        if education_cert:
            education_cert.name = sanitize_filename(education_cert.name)
            profile.education_certificate_file = education_cert
        institutional_cred = form.cleaned_data.get('institutional_credential_file')
        if institutional_cred:
            institutional_cred.name = sanitize_filename(institutional_cred.name)
            profile.institutional_credential_file = institutional_cred
        knowledge_doc = form.cleaned_data.get('knowledge_document_file')
        if knowledge_doc:
            knowledge_doc.name = sanitize_filename(knowledge_doc.name)
            profile.knowledge_document_file = knowledge_doc

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

        if needs_approval:
            # No hacer login automatico — retornar con flag
            return True, user, 'pending_approval'

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

        avatar = form.cleaned_data.get('avatar')
        if avatar:
            avatar.name = sanitize_filename(avatar.name)
            profile.avatar = avatar
        if form.cleaned_data.get('student_type'):
            profile.student_type = form.cleaned_data['student_type']
        id_doc = form.cleaned_data.get('id_document_file')
        if id_doc:
            id_doc.name = sanitize_filename(id_doc.name)
            profile.id_document_file = id_doc
        enrollment = form.cleaned_data.get('enrollment_file')
        if enrollment:
            enrollment.name = sanitize_filename(enrollment.name)
            profile.enrollment_file = enrollment

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
