"""
ArchitectGuard — Internal Shell Probe Endpoint
Usado exclusivamente por n8n Shell Gate JS (Phase 1 Post-LLM Gate).

Protegido por X-AG-Secret header.
NO está disponible en producción (ver urls.py).

Uso:
    GET /internal/shell-probe/?layer=accounts/models
    Header: X-AG-Secret: <ARCHITECTGUARD_SECRET de settings>
"""
import importlib
import json
import sys
import os
from django.http import JsonResponse
from django.views import View
from django.conf import settings


# Mapa: layer_name (del config.json audit_plan) → módulo probe
PROBE_MAP = {
    "accounts/models":                  "shell_tests.shelltests_accounts_models",
    "accounts/services":                "shell_tests.shelltests_accounts_services",
    "accounts/views":                   "shell_tests.shelltests_accounts_views",
    "accounts/forms":                   "shell_tests.shelltests_accounts_forms",
    "accounts/serializers":             "shell_tests.shelltests_accounts_serializers",
    "academicTutoring/models":          "shell_tests.shelltests_academicTutoring_models",
    "academicTutoring/services":        "shell_tests.shelltests_academicTutoring_services",
    "academicTutoring/views":           "shell_tests.shelltests_academicTutoring_views",
    "academicTutoring/forms":           "shell_tests.shelltests_academicTutoring_forms",
    "academicTutoring/middleware":      "shell_tests.shelltests_academicTutoring_middleware",
    "manage_check":                     "shell_tests.shelltests_manage_check",
}


class ShellProbeView(View):
    """
    Endpoint interno para ArchitectGuard Shell Gate.
    Solo accesible con el header X-AG-Secret correcto.
    """

    SHELL_TESTS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'AG', 'PHASE-3', 'shell_tests')
    if SHELL_TESTS_PATH not in sys.path:
        sys.path.insert(0, SHELL_TESTS_PATH)

    def get(self, request):
        # AUTH: verificar secret header
        secret = request.headers.get("X-AG-Secret", "")
        expected = getattr(settings, "ARCHITECTGUARD_SECRET", None)

        if not expected or secret != expected:
            return JsonResponse(
                {"status": "FORBIDDEN", "error": "Invalid or missing X-AG-Secret header"},
                status=403
            )

        # PARAM: qué layer auditar
        layer = request.GET.get("layer", "").strip()
        if not layer:
            return JsonResponse(
                {"status": "ERROR", "error": "Parámetro 'layer' requerido"},
                status=400
            )

        if layer not in PROBE_MAP:
            return JsonResponse(
                {
                    "status": "ERROR",
                    "error": f"Layer '{layer}' no tiene probe registrado",
                    "available_layers": list(PROBE_MAP.keys())
                },
                status=400
            )

        # EJECUTAR probe
        try:
            import sys
            module_path = PROBE_MAP[layer]
            if module_path in sys.modules:
                del sys.modules[module_path]
            module = importlib.import_module(module_path)
            result = module.run_probe()

            status_code = 200 if result.get("status") == "PASS" else 200  # siempre 200, el status va en el JSON
            return JsonResponse(result, status=status_code)

        except Exception as e:
            return JsonResponse(
                {
                    "status": "FAIL",
                    "layer": layer,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "location": "ShellProbeView — importlib.import_module"
                    }
                },
                status=200  # 200 para que n8n pueda leer el JSON del error
            )