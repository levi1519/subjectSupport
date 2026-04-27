"""
Tests HTTP para el panel de administración.
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
    try:
        ok = login_admin(s)
        results.append(('AD01 Login admin OK', ok))
        if not ok:
            results.append(('AD02..AD10 SKIP — login falló', False))
            return results
    except Exception as e:
        results.append((f'AD01 ERROR: {e}', False))
        return results

    # --- AD02: Lista TutorProfile carga ---
    try:
        r = s.get(ADMIN_PATH + 'accounts/tutorprofile/')
        results.append(('AD02 Lista TutorProfile 200', r.status_code == 200))
        results.append(('AD02b Contiene columna is_approved', 'is_approved' in r.text or 'Aprobado' in r.text))
    except Exception as e:
        results.append((f'AD02 ERROR: {e}', False))

    # --- AD03: Lista Users carga ---
    try:
        r = s.get(ADMIN_PATH + 'accounts/user/')
        results.append(('AD03 Lista Users 200', r.status_code == 200))
    except Exception as e:
        results.append((f'AD03 ERROR: {e}', False))

    # --- AD04: Acción approve_tutors ---
    try:
        from bs4 import BeautifulSoup
        r = s.get(ADMIN_PATH + 'accounts/tutorprofile/?is_approved__exact=0')
        soup = BeautifulSoup(r.text, 'html.parser')
        checkboxes = soup.select('input[name="_selected_action"]')
        if checkboxes:
            ids = [cb['value'] for cb in checkboxes[:2]]
            data = {
                'action': 'approve_tutors',
                '_selected_action': ids,
                'index': '0',
                'select_across': '0',
            }
            r2 = s.post(ADMIN_PATH + 'accounts/tutorprofile/', data, ADMIN_PATH + 'accounts/tutorprofile/')
            results.append(('AD04 Acción approve_tutors ejecutada', r2.status_code in [200, 302]))
            results.append(('AD04b Sin error 500', r2.status_code != 500))
        else:
            results.append(('AD04 approve_tutors SKIP — no hay tutores pendientes', True))
            results.append(('AD04b SKIP', True))
    except Exception as e:
        results.append((f'AD04 ERROR: {e}', False))

    # --- AD05: list_editable is_approved ---
    try:
        r = s.get(ADMIN_PATH + 'accounts/tutorprofile/')
        soup = BeautifulSoup(r.text, 'html.parser')
        form = soup.find('form', {'id': 'changelist-form'})
        if form:
            approved_fields = form.select('input[name*="is_approved"], select[name*="is_approved"]')
            results.append(('AD05 list_editable is_approved presente en form', len(approved_fields) > 0))
        else:
            results.append(('AD05 list_editable form presente', False))
    except Exception as e:
        results.append((f'AD05 ERROR: {e}', False))

    # --- AD06: Detalle de TutorProfile individual ---
    try:
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
    except Exception as e:
        results.append((f'AD06 ERROR: {e}', False))

    # --- AD07: Avatar visible en lista ---
    try:
        r = s.get(ADMIN_PATH + 'accounts/tutorprofile/')
        results.append(('AD07 Avatar img en lista admin', '<img' in r.text or 'get_avatar_preview' in r.text))
    except Exception as e:
        results.append((f'AD07 ERROR: {e}', False))

    # --- AD08: Admin ClientProfile list ---
    try:
        r = s.get(ADMIN_PATH + 'accounts/clientprofile/')
        results.append(('AD08 Admin ClientProfile list → 200', r.status_code == 200))
    except Exception as e:
        results.append((f'AD08 ERROR: {e}', False))

    # --- AD09: Admin PlatformConfig list ---
    try:
        r = s.get(ADMIN_PATH + 'academicTutoring/platformconfig/')
        results.append(('AD09 Admin PlatformConfig list → 200', r.status_code == 200))
    except Exception as e:
        results.append((f'AD09 ERROR: {e}', False))

    # --- AD10: Admin Simulator list ---
    try:
        r = s.get(ADMIN_PATH + 'simulators/simulator/')
        results.append(('AD10 Admin Simulator list → 200', r.status_code == 200))
    except Exception as e:
        results.append((f'AD10 ERROR: {e}', False))

    return results
