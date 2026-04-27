#!/usr/bin/env python
"""
Runner principal. Ejecutar desde la raíz del proyecto:
    python -m tests_functional.run_all
"""
import sys
from tests_functional import (
    test_auth, test_negocio, test_sesiones,
    test_web, test_api, test_admin,
)

SUITES = [
    ("AUTH",     test_auth),
    ("NEGOCIO",  test_negocio),
    ("SESIONES", test_sesiones),
    ("WEB",      test_web),
    ("API",      test_api),
    ("ADMIN",    test_admin),
]


def main():
    total, passed = 0, 0
    for suite_name, module in SUITES:
        print(f"\n== {suite_name} ==")
        try:
            results = module.run()
        except Exception as e:
            results = [(f"{suite_name} SUITE CRASHED: {e}", False)]
        for label, ok in results:
            icon = "OK" if ok else "FAIL"
            print(f"  [{icon}] {label}")
            total += 1
            passed += ok

    print(f"\n== RESULTADO: {passed}/{total} ==")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
