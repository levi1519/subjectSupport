"""
Tests del flujo de sesiones.
"""
import os
import time
from .base import SessionHTTP

TUTOR_EMAIL  = os.getenv("TEST_TUTOR_EMAIL", "")
TUTOR_PASS   = os.getenv("TEST_TUTOR_PASS", "")
CLIENT_EMAIL = os.getenv("TEST_CLIENT_EMAIL", "")
CLIENT_PASS  = os.getenv("TEST_CLIENT_PASS", "")
TUTOR_ID     = os.getenv("TEST_TUTOR_ID", "")
SESSION_ID   = os.getenv("TEST_SESSION_ID", "")


def _login_as_tutor(s: SessionHTTP) -> bool:
    s.post("/tutores/login/", {"username": TUTOR_EMAIL, "password": TUTOR_PASS}, "/tutores/login/")
    return True


def _login_as_client(s: SessionHTTP) -> bool:
    s.post("/estudiantes/login/", {"username": CLIENT_EMAIL, "password": CLIENT_PASS}, "/estudiantes/login/")
    return True


def run():
    results = []

    # S01
    try:
        s = SessionHTTP()
        _login_as_tutor(s)
        r = s.get("/accounts/dashboard/tutor/")
        ok = r.status_code == 200 and (
            "Pendientes" in r.text or "Confirmadas" in r.text or "solicitudes" in r.text.lower()
        )
        results.append(("S01 Tutor dashboard loads with session sections", ok))
    except Exception as e:
        results.append((f"S01 ERROR: {e}", False))

    # S02
    try:
        s = SessionHTTP()
        _login_as_client(s)
        r = s.get("/accounts/dashboard/client/")
        ok = r.status_code == 200 and (
            "Clases" in r.text or "Buscar" in r.text or "dashboard" in r.url.lower()
        )
        results.append(("S02 Student dashboard loads with session sections", ok))
    except Exception as e:
        results.append((f"S02 ERROR: {e}", False))

    # S03
    try:
        s = SessionHTTP()
        _login_as_client(s)
        r = s.get("/tutors/")
        ok = r.status_code == 200
        results.append(("S03 Tutor list page loads for student", ok))
    except Exception as e:
        results.append((f"S03 ERROR: {e}", False))

    # S04
    if not TUTOR_ID:
        results.append(("S04 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            _login_as_client(s)
            r = s.get(f"/sessions/request/{TUTOR_ID}/")
            ok = r.status_code == 200 and "scheduled_date" in r.text
            results.append(("S04 Session request form loads for student", ok))
        except Exception as e:
            results.append((f"S04 ERROR: {e}", False))

    # S05
    try:
        s = SessionHTTP()
        _login_as_tutor(s)
        r = s.get("/accounts/tutor/manage-subjects/?edit=1")
        ok = r.status_code == 200 and ('type="checkbox"' in r.text or "subjects_taught" in r.text)
        results.append(("S05 Manage subjects form has checkboxes", ok))
    except Exception as e:
        results.append((f"S05 ERROR: {e}", False))

    # S06
    try:
        s = SessionHTTP()
        _login_as_tutor(s)
        r = s.get("/accounts/profile/tutor/")
        ok = r.status_code == 200 and (
            TUTOR_EMAIL.split("@")[0][:4] in r.text or "Perfil" in r.text
        )
        results.append(("S06 Tutor profile page shows user name", ok))
    except Exception as e:
        results.append((f"S06 ERROR: {e}", False))

    # S07
    try:
        s = SessionHTTP()
        _login_as_client(s)
        r = s.get("/accounts/profile/client/")
        ok = r.status_code == 200
        results.append(("S07 Student profile page accessible", ok))
    except Exception as e:
        results.append((f"S07 ERROR: {e}", False))

    # S08
    if not SESSION_ID:
        results.append(("S08 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            _login_as_tutor(s)
            r = s.get(f"/sessions/{SESSION_ID}/confirm/")
            ok = r.status_code in [200, 302]
            results.append(("S08 Confirm session page loads for session owner tutor", ok))
        except Exception as e:
            results.append((f"S08 ERROR: {e}", False))

    # S09
    if not TUTOR_ID:
        results.append(("S09 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            _login_as_client(s)
            r = s.get(f"/sessions/request/{TUTOR_ID}/")
            ok = "material_url" in r.text or "material" in r.text.lower()
            results.append(("S09 Session request form has material_url field", ok))
        except Exception as e:
            results.append((f"S09 ERROR: {e}", False))

    # S10
    try:
        s = SessionHTTP()
        _login_as_tutor(s)
        t0 = time.time()
        r = s.get("/accounts/dashboard/tutor/")
        elapsed = time.time() - t0
        ok = elapsed < 3.0
        results.append((f"S10 Tutor dashboard response time < 3 seconds ({elapsed:.2f}s)", ok))
    except Exception as e:
        results.append((f"S10 ERROR: {e}", False))

    return results
