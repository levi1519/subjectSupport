"""
Tests HTTP para el panel de administración.
Prueba: login admin, listado TutorProfile, aprobación masiva, aprobación individual.
"""
import os
from .base import SessionHTTP

ADMIN_EMAIL = os.getenv('TEST_ADMIN_EMAIL', 'admin@edulatam.com')
ADMIN_PASS  = os.getenv('TEST_ADMIN_PASS',  'Admin123!')
ADMIN_PATH  = '/gestion-ay-2026-4/'


def login_admin(s: SessionHTTP) -> bool:
    """Login al admin de Django."""
    s.get(ADMIN_PATH + 'login/')
    r = s.post(ADMIN_PATH + 'login/', {
        'username': ADMIN_EMAIL,
        'password': ADMIN_PASS,
        'next': ADMIN_PATH,
    }, ADMIN_PATH + 'login/')
    return ADMIN_PATH in r.url or r.url.endswith(ADMIN_PATH)


def run():
    results = []
    s = SessionHTTP()

    # --- AD01: Login admin ---
    ok = login_admin(s)
    results.append(('AD01 Login admin OK', ok))
    if not ok:
        results.append(('AD02..AD07 SKIP — login falló', False))
        return results

    # --- AD02: Lista TutorProfile carga ---
    r = s.get(ADMIN_PATH + 'accounts/tutorprofile/')
    results.append(('AD02 Lista TutorProfile 200', r.status_code == 200))
    results.append(('AD02b Contiene columna is_approved', 'is_approved' in r.text or 'Aprobado' in r.text))

    # --- AD03: Lista Users carga ---
    r = s.get(ADMIN_PATH + 'accounts/user/')
    results.append(('AD03 Lista Users 200', r.status_code == 200))

    # --- AD04: Acción approve_tutors (si hay tutores pendientes) ---
    from bs4 import BeautifulSoup
    r = s.get(ADMIN_PATH + 'accounts/tutorprofile/?is_approved__exact=0')
    soup = BeautifulSoup(r.text, 'html.parser')
    checkboxes = soup.select('input[name="_selected_action"]')
    
    if checkboxes:
        ids = [cb['value'] for cb in checkboxes[:2]]  # máximo 2 para el test
        data = {
            'action': 'approve_tutors',
            '_selected_action': ids,
            'index': '0',
            'select_across': '0',
        }
        r2 = s.post(
            ADMIN_PATH + 'accounts/tutorprofile/',
            data,
            ADMIN_PATH + 'accounts/tutorprofile/'
        )
        results.append(('AD04 Acción approve_tutors ejecutada', r2.status_code in [200, 302]))
        results.append(('AD04b Sin error 500', r2.status_code != 500))
    else:
        results.append(('AD04 approve_tutors SKIP — no hay tutores pendientes', True))
        results.append(('AD04b SKIP', True))

    # --- AD05: list_editable is_approved (POST directo) ---
    r = s.get(ADMIN_PATH + 'accounts/tutorprofile/')
    soup = BeautifulSoup(r.text, 'html.parser')
    form = soup.find('form', {'id': 'changelist-form'})
    
    if form:
        approved_fields = form.select('input[name*="is_approved"], select[name*="is_approved"]')
        results.append(('AD05 list_editable is_approved presente en form', len(approved_fields) > 0))
    else:
        results.append(('AD05 list_editable form presente', False))

    # --- AD06: Detalle de TutorProfile individual ---
    r = s.get(ADMIN_PATH + 'accounts/tutorprofile/')
    soup = BeautifulSoup(r.text, 'html.parser')
    first_link = soup.select_one('th.field-get_full_name a')
    if first_link:
        detail_url = first_link['href']
        r2 = s.get(detail_url)
        results.append(('AD06 Detalle TutorProfile 200', r2.status_code == 200))
        results.append(('AD06b Tiene campo is_approved', 'is_approved' in r2.text))
    else:
        results.append(('AD06 SKIP — sin tutores en lista', True))
        results.append(('AD06b SKIP', True))

    # --- AD07: Avatar visible en lista ---
    r = s.get(ADMIN_PATH + 'accounts/tutorprofile/')
    results.append(('AD07 Avatar img en lista admin', '<img' in r.text or 'get_avatar_preview' in r.text))

    return results
