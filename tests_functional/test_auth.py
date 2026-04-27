"""
Tests de autenticación y reglas de acceso.
"""
import os
from .base import SessionHTTP

TUTOR_EMAIL  = os.getenv("TEST_TUTOR_EMAIL", "")
TUTOR_PASS   = os.getenv("TEST_TUTOR_PASS", "")
CLIENT_EMAIL = os.getenv("TEST_CLIENT_EMAIL", "")
CLIENT_PASS  = os.getenv("TEST_CLIENT_PASS", "")


def run():
    results = []

    # T01
    try:
        s = SessionHTTP()
        r = s.get("/accounts/dashboard/")
        ok = (len(r.history) > 0 and r.history[0].status_code == 302) or "login" in r.url
        results.append(("T01 Anonymous GET /accounts/dashboard/ → 302", ok))
    except Exception as e:
        results.append((f"T01 ERROR: {e}", False))

    # T02
    try:
        s = SessionHTTP()
        r = s.get("/accounts/dashboard/tutor/")
        ok = (len(r.history) > 0 and r.history[0].status_code == 302) or "login" in r.url
        results.append(("T02 Anonymous GET /accounts/dashboard/tutor/ → 302", ok))
    except Exception as e:
        results.append((f"T02 ERROR: {e}", False))

    # T03
    try:
        s = SessionHTTP()
        r = s.get("/accounts/dashboard/client/")
        ok = (len(r.history) > 0 and r.history[0].status_code == 302) or "login" in r.url
        results.append(("T03 Anonymous GET /accounts/dashboard/client/ → 302", ok))
    except Exception as e:
        results.append((f"T03 ERROR: {e}", False))

    # T04
    try:
        s = SessionHTTP()
        r = s.get("/tutors/")
        ok = r.status_code != 500
        results.append((f"T04 Anonymous GET /tutors/ → {r.status_code}", ok))
    except Exception as e:
        results.append((f"T04 ERROR: {e}", False))

    # T05
    if not TUTOR_EMAIL:
        results.append(("T05 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            r = s.post("/tutores/login/", {"username": TUTOR_EMAIL, "password": "WRONGPASS999"}, "/tutores/login/")
            ok = "dashboard" not in r.url and ("login" in r.url or r.status_code == 200)
            results.append(("T05 Tutor login wrong password → no dashboard", ok))
        except Exception as e:
            results.append((f"T05 ERROR: {e}", False))

    # T06
    if not CLIENT_EMAIL:
        results.append(("T06 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            r = s.post("/estudiantes/login/", {"username": CLIENT_EMAIL, "password": "WRONGPASS999"}, "/estudiantes/login/")
            ok = "dashboard" not in r.url and ("login" in r.url or r.status_code == 200)
            results.append(("T06 Student login wrong password → no dashboard", ok))
        except Exception as e:
            results.append((f"T06 ERROR: {e}", False))

    # T07
    if not CLIENT_EMAIL or not CLIENT_PASS:
        results.append(("T07 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            r = s.post("/tutores/login/", {"username": CLIENT_EMAIL, "password": CLIENT_PASS}, "/tutores/login/")
            ok = ("tutor" not in r.url.lower() or "dashboard" not in r.url) or ("incorrectas" in r.text.lower() or "error" in r.text.lower())
            results.append(("T07 Student credentials on tutor login form → rejected", ok))
        except Exception as e:
            results.append((f"T07 ERROR: {e}", False))

    # T08
    if not TUTOR_EMAIL or not TUTOR_PASS:
        results.append(("T08 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            r = s.post("/estudiantes/login/", {"username": TUTOR_EMAIL, "password": TUTOR_PASS}, "/estudiantes/login/")
            ok = ("client" not in r.url or "dashboard" not in r.url) or ("incorrectas" in r.text.lower() or "error" in r.text.lower())
            results.append(("T08 Tutor credentials on student login form → rejected", ok))
        except Exception as e:
            results.append((f"T08 ERROR: {e}", False))

    # T09
    if not TUTOR_EMAIL or not TUTOR_PASS:
        results.append(("T09 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            r = s.post("/tutores/login/", {"username": TUTOR_EMAIL, "password": TUTOR_PASS}, "/tutores/login/")
            ok = "dashboard" in r.url and "tutor" in r.url
            results.append(("T09 Valid tutor login → tutor dashboard", ok))
        except Exception as e:
            results.append((f"T09 ERROR: {e}", False))

    # T10
    if not CLIENT_EMAIL or not CLIENT_PASS:
        results.append(("T10 SKIP — env var not set", True))
    else:
        try:
            s = SessionHTTP()
            r = s.post("/estudiantes/login/", {"username": CLIENT_EMAIL, "password": CLIENT_PASS}, "/estudiantes/login/")
            ok = "dashboard" in r.url and "client" in r.url
            results.append(("T10 Valid student login → client dashboard", ok))
        except Exception as e:
            results.append((f"T10 ERROR: {e}", False))

    return results
