#!/usr/bin/env python
"""
Runner principal. Ejecutar desde la raíz del proyecto:
    python -m tests_functional.run_all
o con URL de producción:
    TEST_BASE_URL=https://tu-app.railway.app \
    TEST_TUTOR_EMAIL=tutor@real.com TEST_TUTOR_PASS=Pass123 \
    TEST_CLIENT_EMAIL=cliente@real.com TEST_CLIENT_PASS=Pass123 \
    python -m tests_functional.run_all
"""
import sys
from tests_functional import test_auth, test_sesiones, test_api, test_admin

SUITES = [
    ('AUTH',     test_auth),
    ('SESIONES', test_sesiones),
    ('API',      test_api),
    ('ADMIN',    test_admin),
]


def main():
    total, passed = 0, 0
    for suite_name, module in SUITES:
        print(f'\n== {suite_name} ==')
        results = module.run()
        for label, ok in results:
            icon = '✅' if ok else '❌'
            print(f'  {icon} {label}')
            total += 1
            passed += ok

    print(f'\n== RESULTADO: {passed}/{total} ==')
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
