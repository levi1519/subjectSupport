"""Tests del flujo de simulacros."""
import os
from .base import SessionHTTP

TUTOR_EMAIL = os.getenv("TEST_TUTOR_EMAIL", "")
TUTOR_PASS  = os.getenv("TEST_TUTOR_PASS", "")
CLIENT_EMAIL = os.getenv("TEST_CLIENT_EMAIL", "")
CLIENT_PASS  = os.getenv("TEST_CLIENT_PASS", "")


def run():
    results = []

    # SIM-01: Lista simulacros accesible para estudiante
    try:
        s = SessionHTTP()
        s.post("/estudiantes/login/", {"username": CLIENT_EMAIL, "password": CLIENT_PASS}, "/estudiantes/login/")
        r = s.get("/simulators/")
        ok = r.status_code == 200 and "Simulacros" in r.text
        results.append(("SIM-01 /simulators/ accesible para estudiante → 200", ok))
    except Exception as e:
        results.append((f"SIM-01 ERROR: {e}", False))

    # SIM-02: Lista simulacros NO accesible para tutor
    try:
        s = SessionHTTP()
        s.post("/tutores/login/", {"username": TUTOR_EMAIL, "password": TUTOR_PASS}, "/tutores/login/")
        r = s.get("/simulators/")
        ok = r.status_code in [302, 403] or "login" in r.url or "403" in r.text
        results.append(("SIM-02 /simulators/ forbidden para tutor", ok))
    except Exception as e:
        results.append((f"SIM-02 ERROR: {e}", False))

    # SIM-03: Historial tutor accesible
    try:
        s = SessionHTTP()
        s.post("/tutores/login/", {"username": TUTOR_EMAIL, "password": TUTOR_PASS}, "/tutores/login/")
        r = s.get("/tutor/historial/")
        ok = r.status_code == 200 and ("Historial" in r.text or "Completadas" in r.text)
        results.append(("SIM-03 /tutor/historial/ accesible para tutor → 200", ok))
    except Exception as e:
        results.append((f"SIM-03 ERROR: {e}", False))

    # SIM-04: Historial tutor NO accesible para estudiante
    try:
        s = SessionHTTP()
        s.post("/estudiantes/login/", {"username": CLIENT_EMAIL, "password": CLIENT_PASS}, "/estudiantes/login/")
        r = s.get("/tutor/historial/")
        ok = r.status_code in [302, 403] or "login" in r.url
        results.append(("SIM-04 /tutor/historial/ forbidden para estudiante", ok))
    except Exception as e:
        results.append((f"SIM-04 ERROR: {e}", False))

    # SIM-05: Simulacros anónimos → redirige a login
    try:
        s = SessionHTTP()
        r = s.get("/simulators/")
        ok = "login" in r.url or len(r.history) > 0
        results.append(("SIM-05 /simulators/ anónimo → redirect", ok))
    except Exception as e:
        results.append((f"SIM-05 ERROR: {e}", False))

    return results
