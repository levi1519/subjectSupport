"""
tests_functional/test_flujos.py

Suite FLUJOS — FT01-FT10, FE01-FE10, FC01-FC10
Tests de flujos completos por rol: tutor, estudiante, y cruzados.
"""
import os
import re
import time
from .base import SessionHTTP

TUTOR_EMAIL  = os.getenv("TEST_TUTOR_EMAIL", "")
TUTOR_PASS   = os.getenv("TEST_TUTOR_PASS", "")
CLIENT_EMAIL = os.getenv("TEST_CLIENT_EMAIL", "")
CLIENT_PASS  = os.getenv("TEST_CLIENT_PASS", "")
SESSION_ID   = os.getenv("TEST_SESSION_ID", "25")


def _login_tutor(s: SessionHTTP) -> None:
    s.post(
        "/tutores/login/",
        {"username": TUTOR_EMAIL, "password": TUTOR_PASS},
        "/tutores/login/",
    )


def _login_student(s: SessionHTTP) -> None:
    s.post(
        "/estudiantes/login/",
        {"username": CLIENT_EMAIL, "password": CLIENT_PASS},
        "/estudiantes/login/",
    )


# ══════════════════════════════════════════════════════════
#  FLUJOS TUTOR  (FT01–FT10)
# ══════════════════════════════════════════════════════════

def run():
    results = []

    # ─── FT01: Dashboard tutor carga ───────────────────────
    try:
        s = SessionHTTP()
        _login_tutor(s)
        r = s.get("/accounts/dashboard/tutor/")
        ok = r.status_code == 200 and "Mi Panel" in r.text
        results.append(("FT01 /accounts/dashboard/tutor/ → 200 + 'Mi Panel'", ok))
    except Exception as e:
        results.append((f"FT01 ERROR: {e}", False))

    # ─── FT02: Historial tutor accesible ───────────────────
    try:
        s = SessionHTTP()
        _login_tutor(s)
        r = s.get("/tutor/historial/")
        ok = r.status_code == 200 and (
            "Completadas" in r.text or "Historial" in r.text
        )
        results.append(("FT02 /tutor/historial/ → 200", ok))
    except Exception as e:
        results.append((f"FT02 ERROR: {e}", False))

    # ─── FT03: Historial contiene sección simulacros ────────
    try:
        s = SessionHTTP()
        _login_tutor(s)
        r = s.get("/tutor/historial/")
        ok = r.status_code == 200 and (
            "simulacro" in r.text.lower()
            or "Aprobación" in r.text
            or "Pendientes" in r.text
        )
        results.append(("FT03 /tutor/historial/ tiene sección simulacros", ok))
    except Exception as e:
        results.append((f"FT03 ERROR: {e}", False))

    # ─── FT04: Tutor puede abrir formulario edición perfil ──
    try:
        s = SessionHTTP()
        _login_tutor(s)
        r = s.get("/accounts/profile/tutor/edit/")
        ok = r.status_code == 200 and "hourly_rate" in r.text
        results.append(("FT04 /accounts/profile/tutor/edit/ → 200 + campo hourly_rate", ok))
    except Exception as e:
        results.append((f"FT04 ERROR: {e}", False))

    # ─── FT05: Gestión de materias tutor accesible ──────────
    try:
        s = SessionHTTP()
        _login_tutor(s)
        r = s.get("/accounts/tutor/manage-subjects/?edit=1")
        ok = r.status_code == 200 and (
            "checkbox" in r.text
            or "subjects_taught" in r.text
            or "materia" in r.text.lower()
        )
        results.append(("FT05 /accounts/tutor/manage-subjects/?edit=1 → 200 + checkboxes", ok))
    except Exception as e:
        results.append((f"FT05 ERROR: {e}", False))

    # ─── FT06: Upload recording URL no produce 500 ──────────
    try:
        s = SessionHTTP()
        _login_tutor(s)
        if not SESSION_ID:
            results.append(("FT06 SKIP — TEST_SESSION_ID no definido", True))
        else:
            r = s.post(
                f"/sessions/{SESSION_ID}/upload-recording/",
                {"recording_url": ""},
                f"/sessions/{SESSION_ID}/upload-recording/",
            )
            ok = r.status_code != 500
            results.append((
                f"FT06 POST /sessions/{SESSION_ID}/upload-recording/ (URL vacía) → {r.status_code} (no 500)",
                ok,
            ))
    except Exception as e:
        results.append((f"FT06 ERROR: {e}", False))

    # ─── FT07: Tutor no puede acceder a dashboard estudiante ─
    try:
        s = SessionHTTP()
        _login_tutor(s)
        r = s.get("/accounts/dashboard/client/")
        ok = r.status_code in [302, 403] or "tutor" in r.url or "login" in r.url
        results.append(("FT07 Tutor GET /accounts/dashboard/client/ → redirigido (no 200)", ok))
    except Exception as e:
        results.append((f"FT07 ERROR: {e}", False))

    # ─── FT08: Tutor no puede ver lista simulacros cliente ──
    # /simulators/ es @client_required — tutor debe ser redirigido
    try:
        s = SessionHTTP()
        _login_tutor(s)
        r = s.get("/simulators/")
        ok = r.status_code in [302, 403] or "login" in r.url or "dashboard" in r.url
        results.append(("FT08 Tutor GET /simulators/ → redirigido (requiere rol cliente)", ok))
    except Exception as e:
        results.append((f"FT08 ERROR: {e}", False))

    # ─── FT09: Tutor puede ver su perfil público ────────────
    try:
        s = SessionHTTP()
        _login_tutor(s)
        r = s.get("/accounts/profile/tutor/")
        ok = r.status_code == 200
        results.append(("FT09 /accounts/profile/tutor/ → 200", ok))
    except Exception as e:
        results.append((f"FT09 ERROR: {e}", False))

    # ─── FT10: Tutor puede aprobar simulacro inexistente sin 500 ─
    try:
        s = SessionHTTP()
        _login_tutor(s)
        r = s.post(
            "/simulators/9999/approve/",
            {"action": "approve", "feedback": ""},
            "/simulators/9999/approve/",
        )
        ok = r.status_code in [302, 404]
        results.append((
            f"FT10 POST /simulators/9999/approve/ → {r.status_code} (302 o 404, no 500)",
            ok,
        ))
    except Exception as e:
        results.append((f"FT10 ERROR: {e}", False))

    # ══════════════════════════════════════════════════════
    #  FLUJOS ESTUDIANTE  (FE01–FE10)
    # ══════════════════════════════════════════════════════

    # ─── FE01: Dashboard estudiante carga ──────────────────
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.get("/accounts/dashboard/client/")
        ok = r.status_code == 200 and "Panel" in r.text
        results.append(("FE01 /accounts/dashboard/client/ → 200 + 'Panel'", ok))
    except Exception as e:
        results.append((f"FE01 ERROR: {e}", False))

    # ─── FE02: Dashboard estudiante NO tiene botón Generar IA ─
    # NOTE: Este test FALLARÁ antes de ejecutar D7 — comportamiento esperado.
    # Tras D7, el form POST a /simulators/generate/ se elimina del template.
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.get("/accounts/dashboard/client/")
        generate_forms = re.findall(
            r'action=["\'][^"\']*simulators/generate[^"\']*["\']',
            r.text,
        )
        ok = len(generate_forms) == 0
        note = "OK (D7 aplicado)" if ok else "FALLA — D7 pendiente"
        results.append((f"FE02 Dashboard estudiante sin form 'simulators/generate' → {note}", ok))
    except Exception as e:
        results.append((f"FE02 ERROR: {e}", False))

    # ─── FE03: Lista simulacros visible para estudiante ────
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.get("/simulators/")
        ok = r.status_code == 200 and "Simulacros" in r.text
        results.append(("FE03 /simulators/ → 200 para estudiante", ok))
    except Exception as e:
        results.append((f"FE03 ERROR: {e}", False))

    # ─── FE04: Estudiante no accede a historial tutor ───────
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.get("/tutor/historial/")
        ok = r.status_code in [302, 403] or "login" in r.url
        results.append(("FE04 Estudiante GET /tutor/historial/ → redirigido", ok))
    except Exception as e:
        results.append((f"FE04 ERROR: {e}", False))

    # ─── FE05: Búsqueda de tutores visible para estudiante ──
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.get("/tutors/")
        ok = r.status_code == 200
        results.append(("FE05 /tutors/ → 200 para estudiante", ok))
    except Exception as e:
        results.append((f"FE05 ERROR: {e}", False))

    # ─── FE06: Estudiante no puede confirmar sesión ─────────
    try:
        s = SessionHTTP()
        _login_student(s)
        if not SESSION_ID:
            results.append(("FE06 SKIP — TEST_SESSION_ID no definido", True))
        else:
            r = s.get(f"/sessions/{SESSION_ID}/confirm/")
            ok = r.status_code in [302, 403, 404]
            results.append((f"FE06 Estudiante GET /sessions/{SESSION_ID}/confirm/ → {r.status_code} (no 200)", ok))
    except Exception as e:
        results.append((f"FE06 ERROR: {e}", False))

    # ─── FE07: Estudiante no puede marcar sesión completada ─
    try:
        s = SessionHTTP()
        _login_student(s)
        if not SESSION_ID:
            results.append(("FE07 SKIP — TEST_SESSION_ID no definido", True))
        else:
            r = s.post(
                f"/sessions/{SESSION_ID}/complete/",
                {},
                f"/sessions/{SESSION_ID}/complete/",
            )
            ok = r.status_code in [302, 403, 404]
            results.append((f"FE07 Estudiante POST /sessions/{SESSION_ID}/complete/ → {r.status_code} (no 200)", ok))
    except Exception as e:
        results.append((f"FE07 ERROR: {e}", False))

    # ─── FE08: POST rating válido (1-5) no produce 500 ──────
    try:
        s = SessionHTTP()
        _login_student(s)
        if not SESSION_ID:
            results.append(("FE08 SKIP — TEST_SESSION_ID no definido", True))
        else:
            r = s.post(
                f"/sessions/{SESSION_ID}/rate/",
                {"rating": "5", "comment": "Excelente tutor"},
                f"/sessions/{SESSION_ID}/rate/",
            )
            ok = r.status_code != 500
            results.append((f"FE08 POST /sessions/{SESSION_ID}/rate/ rating=5 → {r.status_code} (no 500)", ok))
    except Exception as e:
        results.append((f"FE08 ERROR: {e}", False))

    # ─── FE09: POST rating inválido (10) no produce 500 ─────
    try:
        s = SessionHTTP()
        _login_student(s)
        if not SESSION_ID:
            results.append(("FE09 SKIP — TEST_SESSION_ID no definido", True))
        else:
            r = s.post(
                f"/sessions/{SESSION_ID}/rate/",
                {"rating": "10", "comment": ""},
                f"/sessions/{SESSION_ID}/rate/",
            )
            ok = r.status_code != 500
            results.append((f"FE09 POST /sessions/{SESSION_ID}/rate/ rating=10 → {r.status_code} (no 500)", ok))
    except Exception as e:
        results.append((f"FE09 ERROR: {e}", False))

    # ─── FE10: Estudiante puede abrir edición de perfil ─────
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.get("/accounts/profile/client/edit/")
        ok = r.status_code == 200 and "phone_number" in r.text
        results.append(("FE10 /accounts/profile/client/edit/ → 200 + campo phone_number", ok))
    except Exception as e:
        results.append((f"FE10 ERROR: {e}", False))

    # ══════════════════════════════════════════════════════
    #  FLUJOS CRUZADOS  (FC01–FC10)
    # ══════════════════════════════════════════════════════

    # ─── FC01: Rate limiting — 6 logins fallidos sin 500 ───
    # NOTE: Sin D13 no habrá bloqueo real, pero no debe haber 500.
    try:
        s = SessionHTTP()
        blocked = False
        last_r = None
        for i in range(6):
            last_r = s.post(
                "/tutores/login/",
                {"username": "noexiste@autotest.com", "password": f"wrongpass{i}"},
                "/tutores/login/",
            )
            if any(
                kw in last_r.text.lower()
                for kw in ["demasiados", "minutos", "bloqueado", "blocked", "too many"]
            ):
                blocked = True
                break
        ok = last_r is not None and last_r.status_code != 500
        note = "con bloqueo activo ✅" if blocked else "sin bloqueo (D13 pendiente)"
        results.append((f"FC01 6 logins fallidos seguidos → no 500 ({note})", ok))
    except Exception as e:
        results.append((f"FC01 ERROR: {e}", False))

    # ─── FC02: Lista simulacros carga sin errores ───────────
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.get("/simulators/")
        ok = r.status_code == 200
        results.append(("FC02 /simulators/ carga sin errores para estudiante", ok))
    except Exception as e:
        results.append((f"FC02 ERROR: {e}", False))

    # ─── FC03: Dashboard estudiante carga notificaciones ────
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.get("/accounts/dashboard/client/")
        notif_refs = re.findall(r"/notifications/read/\d+/", r.text)
        ok = r.status_code == 200
        detail = f"{len(notif_refs)} notif" if notif_refs else "sin notificaciones activas"
        results.append((f"FC03 Dashboard estudiante carga ({detail})", ok))
    except Exception as e:
        results.append((f"FC03 ERROR: {e}", False))

    # ─── FC04: Mark notification read no produce 500 ────────
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.post("/notifications/read/999/", {}, "/accounts/dashboard/client/")
        ok = r.status_code in [200, 302, 404]
        results.append((f"FC04 POST /notifications/read/999/ → {r.status_code} (no 500)", ok))
    except Exception as e:
        results.append((f"FC04 ERROR: {e}", False))

    # ─── FC05: Meeting room anónimo → redirect a login ──────
    try:
        s = SessionHTTP()  # sin login
        if not SESSION_ID:
            results.append(("FC05 SKIP — TEST_SESSION_ID no definido", True))
        else:
            r = s.get(f"/sessions/{SESSION_ID}/meeting/")
            ok = r.status_code in [302, 403] or (
                len(r.history) > 0 and r.status_code == 200
            )
            results.append(("FC05 Meeting room sin auth → redirect a login", ok))
    except Exception as e:
        results.append((f"FC05 ERROR: {e}", False))

    # ─── FC06: Cancelar sesión como tutor no produce 500 ────
    try:
        s = SessionHTTP()
        _login_tutor(s)
        if not SESSION_ID:
            results.append(("FC06 SKIP — TEST_SESSION_ID no definido", True))
        else:
            r = s.get(f"/sessions/{SESSION_ID}/cancel/")
            ok = r.status_code in [200, 302]
            results.append((f"FC06 Tutor GET /sessions/{SESSION_ID}/cancel/ → {r.status_code} (no 500)", ok))
    except Exception as e:
        results.append((f"FC06 ERROR: {e}", False))

    # ─── FC07: Dashboard tutor responde en < 3s ─────────────
    try:
        s = SessionHTTP()
        _login_tutor(s)
        t0 = time.time()
        r = s.get("/accounts/dashboard/tutor/")
        elapsed = time.time() - t0
        ok = elapsed < 3.0 and r.status_code == 200
        results.append((f"FC07 Tutor dashboard responde en {elapsed:.2f}s (< 3.0s)", ok))
    except Exception as e:
        results.append((f"FC07 ERROR: {e}", False))

    # ─── FC08: Dashboard estudiante responde en < 3s ────────
    try:
        s = SessionHTTP()
        _login_student(s)
        t0 = time.time()
        r = s.get("/accounts/dashboard/client/")
        elapsed = time.time() - t0
        ok = elapsed < 3.0 and r.status_code == 200
        results.append((f"FC08 Student dashboard responde en {elapsed:.2f}s (< 3.0s)", ok))
    except Exception as e:
        results.append((f"FC08 ERROR: {e}", False))

    # ─── FC09: Paginación /tutors/?page=1 funciona ──────────
    try:
        s = SessionHTTP()
        _login_student(s)
        r = s.get("/tutors/?page=1")
        ok = r.status_code == 200
        results.append(("FC09 /tutors/?page=1 → 200 (paginación activa o no falla)", ok))
    except Exception as e:
        results.append((f"FC09 ERROR: {e}", False))

    # ─── FC10: Anónimo no puede acceder a ningún dashboard ──
    try:
        s = SessionHTTP()  # sin login
        r_tutor   = s.get("/accounts/dashboard/tutor/")
        r_student = s.get("/accounts/dashboard/client/")
        ok = (
            r_tutor.status_code in [302, 403] or "login" in r_tutor.url
        ) and (
            r_student.status_code in [302, 403] or "login" in r_student.url
        )
        results.append(("FC10 Anónimo no puede acceder a ningún dashboard → ambos redirigen", ok))
    except Exception as e:
        results.append((f"FC10 ERROR: {e}", False))

    return results
