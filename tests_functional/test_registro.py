"""
tests_functional/test_registro.py

Suite REGISTRO — R01 a R15
Tests de flujos HTTP de registro sin subida de archivos.
Cubre tutores y estudiantes con distintas combinaciones de validación.
"""
import os
import re
import uuid
from .base import SessionHTTP

ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL", "")
ADMIN_PASS  = os.getenv("TEST_ADMIN_PASS", "")

RUN_ID = uuid.uuid4().hex[:6]


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def _unique_email(role: str) -> str:
    return f"test_{role}_{RUN_ID}@autotest.com"


def _tutor_payload(email: str, **overrides) -> dict:
    base = {
        "name": f"AutoTutor {RUN_ID}",
        "email": email,
        "password1": "TestPass2026!",
        "password2": "TestPass2026!",
        "birth_date": "1990-05-15",
        "cedula": "0999999999",
        "phone_number": "+593999999999",
        "employment_status": "desempleado",
        "education_level": "universitario",
    }
    base.update(overrides)
    return base


def _student_payload(email: str, **overrides) -> dict:
    base = {
        "name": f"AutoStudent {RUN_ID}",
        "email": email,
        "password1": "TestPass2026!",
        "password2": "TestPass2026!",
        "birth_date": "2000-03-20",
        "phone_number": "+593888888888",
        "student_type": "autodidacta",
    }
    base.update(overrides)
    return base


# ──────────────────────────────────────────────────────────
# Suite
# ──────────────────────────────────────────────────────────

def run():
    results = []

    # ─── R01: Formulario de registro tutor carga ───────────
    try:
        s = SessionHTTP()
        r = s.get("/accounts/register/tutor/")
        ok = r.status_code == 200 and "employment_status" in r.text
        results.append(("R01 GET /accounts/register/tutor/ → 200 + campo employment_status", ok))
    except Exception as e:
        results.append((f"R01 ERROR: {e}", False))

    # ─── R02: Formulario de registro estudiante carga ──────
    try:
        s = SessionHTTP()
        r = s.get("/accounts/register/client/")
        ok = r.status_code == 200 and "student_type" in r.text
        results.append(("R02 GET /accounts/register/client/ → 200 + campo student_type", ok))
    except Exception as e:
        results.append((f"R02 ERROR: {e}", False))

    # ─── R03: Registro estudiante autodidacta válido ───────
    # CRITERIO: no debe retornar la misma página con errores de form
    # (si redirige a dashboard o a login de confirmación = éxito)
    try:
        s = SessionHTTP()
        email = _unique_email("autodidacta")
        r = s.post(
            "/accounts/register/client/",
            _student_payload(email, student_type="autodidacta"),
            "/accounts/register/client/",
        )
        # Éxito = redirect (history > 0) y no hay "error" ni "requerido" en body final
        redirected = len(r.history) > 0
        has_form_errors = any(
            kw in r.text.lower()
            for kw in ["is-invalid", "errorlist", "requerido", "required", "invalid"]
        )
        ok = redirected and not has_form_errors
        detail = "redirect OK" if redirected else f"status={r.status_code} sin redirect"
        results.append((f"R03 Registro estudiante autodidacta válido → {detail}", ok))
    except Exception as e:
        results.append((f"R03 ERROR: {e}", False))

    # ─── R04: Email duplicado rechazado en registro estudiante ─
    try:
        CLIENT_EMAIL = os.getenv("TEST_CLIENT_EMAIL", "schneizel@gmail.com")
        s = SessionHTTP()
        r = s.post(
            "/accounts/register/client/",
            _student_payload(CLIENT_EMAIL),
            "/accounts/register/client/",
        )
        ok = r.status_code == 200 and (
            "registrado" in r.text.lower()
            or "already" in r.text.lower()
            or "email" in r.text.lower()
        ) and len(r.history) == 0  # no redirigió = form rechazado
        results.append(("R04 Email duplicado estudiante → error de validación, sin redirect", ok))
    except Exception as e:
        results.append((f"R04 ERROR: {e}", False))

    # ─── R05: Email duplicado rechazado en registro tutor ──
    try:
        TUTOR_EMAIL = os.getenv("TEST_TUTOR_EMAIL", "lelouch@gmail.com")
        s = SessionHTTP()
        r = s.post(
            "/accounts/register/tutor/",
            _tutor_payload(TUTOR_EMAIL),
            "/accounts/register/tutor/",
        )
        ok = r.status_code == 200 and (
            "registrado" in r.text.lower()
            or "already" in r.text.lower()
            or "email" in r.text.lower()
        ) and len(r.history) == 0
        results.append(("R05 Email duplicado tutor → error de validación, sin redirect", ok))
    except Exception as e:
        results.append((f"R05 ERROR: {e}", False))

    # ─── R06: Contraseñas no coinciden → error ─────────────
    try:
        s = SessionHTTP()
        email = _unique_email("mismatch")
        r = s.post(
            "/accounts/register/client/",
            _student_payload(email, password2="OtraClave999!"),
            "/accounts/register/client/",
        )
        ok = r.status_code == 200 and len(r.history) == 0 and (
            "coinc" in r.text.lower()
            or "match" in r.text.lower()
            or "password" in r.text.lower()
        )
        results.append(("R06 Contraseñas no coinciden → error, sin redirect", ok))
    except Exception as e:
        results.append((f"R06 ERROR: {e}", False))

    # ─── R07: Menor de edad (< 15 años) rechazado ──────────
    try:
        s = SessionHTTP()
        email = _unique_email("minor_reject")
        r = s.post(
            "/accounts/register/client/",
            _student_payload(email, birth_date="2020-01-01"),
            "/accounts/register/client/",
        )
        ok = r.status_code == 200 and len(r.history) == 0 and (
            "edad" in r.text.lower()
            or "age" in r.text.lower()
            or "años" in r.text.lower()
            or "menor" in r.text.lower()
            or "15" in r.text
        )
        results.append(("R07 Estudiante menor de 15 años → error de edad, sin redirect", ok))
    except Exception as e:
        results.append((f"R07 ERROR: {e}", False))

    # ─── R08: Tutor menor de 18 rechazado ─────────────────
    try:
        s = SessionHTTP()
        email = _unique_email("tutor_minor")
        r = s.post(
            "/accounts/register/tutor/",
            _tutor_payload(email, birth_date="2015-01-01"),
            "/accounts/register/tutor/",
        )
        ok = r.status_code == 200 and len(r.history) == 0 and (
            "edad" in r.text.lower()
            or "18" in r.text
            or "mayor" in r.text.lower()
        )
        results.append(("R08 Tutor menor de 18 años → error de edad, sin redirect", ok))
    except Exception as e:
        results.append((f"R08 ERROR: {e}", False))

    # ─── R09: Registro sin campo obligatorio → rechazado ───
    try:
        s = SessionHTTP()
        email = _unique_email("missing_field")
        payload = _student_payload(email)
        payload.pop("birth_date", None)
        r = s.post("/accounts/register/client/", payload, "/accounts/register/client/")
        ok = r.status_code == 200 and len(r.history) == 0
        results.append(("R09 Registro sin birth_date → no redirige (form inválido)", ok))
    except Exception as e:
        results.append((f"R09 ERROR: {e}", False))

    # ─── R10: Contraseña numérica rechazada ────────────────
    try:
        s = SessionHTTP()
        email = _unique_email("numpass")
        r = s.post(
            "/accounts/register/client/",
            _student_payload(email, password1="12345678", password2="12345678"),
            "/accounts/register/client/",
        )
        ok = r.status_code == 200 and len(r.history) == 0
        results.append(("R10 Contraseña numérica → rechazada por validador Django, sin redirect", ok))
    except Exception as e:
        results.append((f"R10 ERROR: {e}", False))

    # ─── R11: Tutor sin materias seleccionadas → no redirige ─
    try:
        s = SessionHTTP()
        email = _unique_email("no_subjects")
        payload = _tutor_payload(email)
        # subjects_taught omitido intencionalmente
        r = s.post("/accounts/register/tutor/", payload, "/accounts/register/tutor/")
        ok = r.status_code == 200 and len(r.history) == 0
        results.append(("R11 Tutor sin materias → form rechazado, sin redirect", ok))
    except Exception as e:
        results.append((f"R11 ERROR: {e}", False))

    # ─── R12: employment_status inválido → rechazado ───────
    try:
        s = SessionHTTP()
        email = _unique_email("invalid_status")
        r = s.post(
            "/accounts/register/tutor/",
            _tutor_payload(email, employment_status="INVALID_CHOICE"),
            "/accounts/register/tutor/",
        )
        ok = r.status_code == 200 and len(r.history) == 0
        results.append(("R12 Tutor con employment_status inválido → rechazado, sin redirect", ok))
    except Exception as e:
        results.append((f"R12 ERROR: {e}", False))

    # ─── R13: Form estudiante tiene sección universidad ─────
    try:
        s = SessionHTTP()
        r = s.get("/accounts/register/client/")
        ok = (
            "client_institution_section" in r.text
            or "enrollment" in r.text
            or "university" in r.text.lower()
            or "institución" in r.text.lower()
        )
        results.append(("R13 Form registro estudiante tiene sección institución", ok))
    except Exception as e:
        results.append((f"R13 ERROR: {e}", False))

    # ─── R14: Login tutor válido → llega a tutor dashboard ─
    try:
        TUTOR_EMAIL = os.getenv("TEST_TUTOR_EMAIL", "")
        TUTOR_PASS  = os.getenv("TEST_TUTOR_PASS", "")
        if not TUTOR_EMAIL:
            results.append(("R14 SKIP — TEST_TUTOR_EMAIL no definido", True))
        else:
            s = SessionHTTP()
            r = s.post(
                "/tutores/login/",
                {"username": TUTOR_EMAIL, "password": TUTOR_PASS},
                "/tutores/login/",
            )
            ok = "dashboard" in r.url and "tutor" in r.url
            results.append(("R14 Login tutor válido → redirige a tutor dashboard", ok))
    except Exception as e:
        results.append((f"R14 ERROR: {e}", False))

    # ─── R15: Logout tutor → redirige a landing ────────────
    try:
        TUTOR_EMAIL = os.getenv("TEST_TUTOR_EMAIL", "")
        TUTOR_PASS  = os.getenv("TEST_TUTOR_PASS", "")
        if not TUTOR_EMAIL:
            results.append(("R15 SKIP — TEST_TUTOR_EMAIL no definido", True))
        else:
            s = SessionHTTP()
            s.post(
                "/tutores/login/",
                {"username": TUTOR_EMAIL, "password": TUTOR_PASS},
                "/tutores/login/",
            )
            r = s.get("/accounts/logout/")
            ok = (
                "tutores" in r.url
                or "tutor" in r.url
                or r.status_code == 200
            ) and "dashboard" not in r.url
            results.append(("R15 Logout tutor → redirige a landing (no dashboard)", ok))
    except Exception as e:
        results.append((f"R15 ERROR: {e}", False))

    return results
