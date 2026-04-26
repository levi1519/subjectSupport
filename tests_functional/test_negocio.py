"""
Tests de reglas de negocio.
"""
import os
import json
from .base import SessionHTTP

TUTOR_EMAIL  = os.getenv("TEST_TUTOR_EMAIL", "")
TUTOR_PASS   = os.getenv("TEST_TUTOR_PASS", "")
CLIENT_EMAIL = os.getenv("TEST_CLIENT_EMAIL", "")
CLIENT_PASS  = os.getenv("TEST_CLIENT_PASS", "")
SESSION_ID   = os.getenv("TEST_SESSION_ID", "")
TUTOR_ID     = os.getenv("TEST_TUTOR_ID", "")


def _login_as_tutor(s: SessionHTTP) -> bool:
    s.post("/tutores/login/", {"username": TUTOR_EMAIL, "password": TUTOR_PASS}, "/tutores/login/")
    return True


def _login_as_client(s: SessionHTTP) -> bool:
    s.post("/estudiantes/login/", {"username": CLIENT_EMAIL, "password": CLIENT_PASS}, "/estudiantes/login/")
    return True


def run():
    results = []

    # N01
    if not TUTOR_ID:
        results.append(("N01 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            _login_as_client(s)
            r = s.post(
                f"/sessions/request/{TUTOR_ID}/",
                {
                    "subject": "Test",
                    "scheduled_date": "2020-01-01",
                    "scheduled_time": "10:00",
                    "duration": "60",
                },
                f"/sessions/request/{TUTOR_ID}/",
            )
            ok = r.status_code == 200 and "2020" not in r.url
            results.append(("N01 Past date session request → form error", ok))
        except Exception as e:
            results.append((f"N01 ERROR: {e}", False))

    # N02
    if not SESSION_ID:
        results.append(("N02 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            _login_as_client(s)
            r = s.get(f"/sessions/{SESSION_ID}/confirm/")
            ok = r.status_code in [302, 403, 404]
            results.append(("N02 GET confirm session as student → forbidden", ok))
        except Exception as e:
            results.append((f"N02 ERROR: {e}", False))

    # N03
    if not SESSION_ID:
        results.append(("N03 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            r = s.get(f"/sessions/{SESSION_ID}/meeting/")
            ok = "login" in r.url or len(r.history) > 0
            results.append(("N03 GET meeting room anonymous → redirect to login", ok))
        except Exception as e:
            results.append((f"N03 ERROR: {e}", False))

    # N04
    if not SESSION_ID:
        results.append(("N04 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            _login_as_client(s)
            r = s.post(f"/sessions/{SESSION_ID}/complete/", {}, f"/sessions/{SESSION_ID}/complete/")
            ok = r.status_code in [302, 403, 404]
            results.append(("N04 POST complete session as student → forbidden", ok))
        except Exception as e:
            results.append((f"N04 ERROR: {e}", False))

    # N05
    try:
        s = SessionHTTP()
        r = s.get("/api/institutions/?q=universidad")
        ok = False
        if r.status_code == 200:
            data = json.loads(r.text)
            ok = "results" in data and isinstance(data["results"], list)
        results.append(("N05 GET /api/institutions/ returns JSON with results key", ok))
    except Exception as e:
        results.append((f"N05 ERROR: {e}", False))

    # N06
    try:
        s = SessionHTTP()
        r = s.get("/api/institutions/?q=u")
        ok = False
        if r.status_code == 200:
            data = json.loads(r.text)
            ok = data.get("results") == []
        results.append(("N06 /api/institutions/ short query → empty results", ok))
    except Exception as e:
        results.append((f"N06 ERROR: {e}", False))

    # N07
    if not CLIENT_EMAIL:
        results.append(("N07 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            r = s.post(
                "/accounts/register/client/",
                {
                    "name": "Test Duplicado",
                    "email": CLIENT_EMAIL,
                    "password1": "TestPass123!",
                    "password2": "TestPass123!",
                    "birth_date": "2000-01-01",
                    "phone_number": "+593999999999",
                    "student_type": "universitario",
                },
                "/accounts/register/client/",
            )
            ok = r.status_code == 200 and ("registrado" in r.text.lower() or "email" in r.text.lower())
            results.append(("N07 Duplicate email registration rejected", ok))
        except Exception as e:
            results.append((f"N07 ERROR: {e}", False))

    # N08
    try:
        s = SessionHTTP()
        _login_as_client(s)
        r = s.get("/accounts/dashboard/tutor/")
        ok = "login" in r.url or r.status_code == 302 or "tutor" not in r.url
        results.append(("N08 Tutor dashboard forbidden for student", ok))
    except Exception as e:
        results.append((f"N08 ERROR: {e}", False))

    # N09
    try:
        s = SessionHTTP()
        _login_as_tutor(s)
        r = s.get("/accounts/dashboard/client/")
        ok = "login" in r.url or r.status_code == 302 or "client" not in r.url
        results.append(("N09 Student dashboard forbidden for tutor", ok))
    except Exception as e:
        results.append((f"N09 ERROR: {e}", False))

    # N10
    try:
        s = SessionHTTP()
        _login_as_tutor(s)
        r = s.get("/accounts/tutor/manage-subjects/")
        ok = r.status_code == 200
        results.append(("N10 Manage subjects page accessible to tutor only", ok))
    except Exception as e:
        results.append((f"N10 ERROR: {e}", False))

    # N11
    try:
        s = SessionHTTP()
        _login_as_client(s)
        r = s.get("/accounts/tutor/manage-subjects/")
        ok = r.status_code in [302, 403] or "login" in r.url
        results.append(("N11 Manage subjects page forbidden for student", ok))
    except Exception as e:
        results.append((f"N11 ERROR: {e}", False))

    # N12
    try:
        s = SessionHTTP()
        r = s.get("/api/institutions/?q=unemi")
        ok = False
        if r.status_code == 200:
            data = json.loads(r.text)
            if data.get("results"):
                ok = all({"id", "name", "city"} <= set(item.keys()) for item in data["results"])
            else:
                ok = True
                results.append(("N12 Institution API returns items with required keys (no data)", ok))
                # ya agregamos, saltar el append de abajo
                return results
        results.append(("N12 Institution API returns items with required keys", ok))
    except Exception as e:
        results.append((f"N12 ERROR: {e}", False))

    return results
