#!/usr/bin/env python
"""
Runner principal — EduLatam / SubjectSupport
Ejecutar desde la raíz del proyecto:

    TEST_BASE_URL=https://subjectsupport-latammvp-production.up.railway.app \\
    TEST_TUTOR_EMAIL=lelouch@gmail.com \\
    TEST_TUTOR_PASS=sasuke1519 \\
    TEST_CLIENT_EMAIL=schneizel@gmail.com \\
    TEST_CLIENT_PASS=sasuke1519 \\
    TEST_ADMIN_EMAIL=rubenandrade@uees.edu.ec \\
    TEST_ADMIN_PASS=sasuke1519 \\
    TEST_SESSION_ID=25 \\
    python -m tests_functional.run_all

Flags opcionales:
    --suite AUTH
    --suite REGISTRO
    --suite FLUJOS
    --suite SIMULACROS
    (etc — ver SUITES abajo)
"""
import sys

from tests_functional import (
    test_auth,
    test_negocio,
    test_sesiones,
    test_web,
    test_api,
    test_admin,
    test_simulacros,
    test_registro,
    test_flujos,
)

SUITES = [
    ("AUTH",       test_auth),
    ("NEGOCIO",    test_negocio),
    ("SESIONES",   test_sesiones),
    ("WEB",        test_web),
    ("API",        test_api),
    ("ADMIN",      test_admin),
    ("SIMULACROS", test_simulacros),
    ("REGISTRO",   test_registro),
    ("FLUJOS",     test_flujos),
]


def main() -> None:
    filter_suite = None
    if "--suite" in sys.argv:
        idx = sys.argv.index("--suite")
        if idx + 1 < len(sys.argv):
            filter_suite = sys.argv[idx + 1].upper()

    active_suites = [
        (name, mod) for name, mod in SUITES
        if filter_suite is None or name == filter_suite
    ]

    if not active_suites:
        print(f"Suite '{filter_suite}' no encontrada. Opciones: {[n for n, _ in SUITES]}")
        sys.exit(1)

    total, passed, failed_items = 0, 0, []

    for suite_name, module in active_suites:
        print(f"\n{'=' * 55}")
        print(f"  SUITE: {suite_name}")
        print(f"{'=' * 55}")
        try:
            results = module.run()
        except Exception as e:
            results = [(f"{suite_name} SUITE CRASHED: {e}", False)]

        for label, ok in results:
            icon = "✅" if ok else "❌"
            print(f"  [{icon}] {label}")
            total += 1
            passed += ok
            if not ok:
                failed_items.append(f"[{suite_name}] {label}")

    print(f"\n{'=' * 55}")
    print(f"  RESULTADO FINAL: {passed}/{total} tests pasaron")
    print(f"{'=' * 55}")

    if failed_items:
        print(f"\nFALLIDOS ({len(failed_items)}):")
        for item in failed_items:
            print(f"  ❌ {item}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
