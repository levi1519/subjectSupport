"""
Tests RNF (non-functional requirements) web.
"""
import os
import requests
from .base import SessionHTTP

BASE = os.getenv("TEST_BASE_URL", "http://localhost:8000").rstrip("/")


def run():
    results = []

    # W01
    try:
        s = SessionHTTP()
        r = s.get("/")
        val = r.headers.get("X-Frame-Options", "").upper()
        ok = "X-Frame-Options" in r.headers and val in ["DENY", "SAMEORIGIN"]
        results.append(("W01 X-Frame-Options header present", ok))
    except Exception as e:
        results.append((f"W01 ERROR: {e}", False))

    # W02
    try:
        s = SessionHTTP()
        r = s.get("/")
        ok = "text/html" in r.headers.get("Content-Type", "")
        results.append(("W02 Content-Type is text/html for base URL", ok))
    except Exception as e:
        results.append((f"W02 ERROR: {e}", False))

    # W03
    try:
        s = SessionHTTP()
        r = s.get("/accounts/login/")
        ok = "csrfmiddlewaretoken" in r.text
        results.append(("W03 CSRF token present in login form", ok))
    except Exception as e:
        results.append((f"W03 ERROR: {e}", False))

    # W04
    try:
        s = SessionHTTP()
        r = s.get("/accounts/register/tutor/")
        ok = "csrfmiddlewaretoken" in r.text
        results.append(("W04 CSRF token present in tutor registration form", ok))
    except Exception as e:
        results.append((f"W04 ERROR: {e}", False))

    # W05
    try:
        s = SessionHTTP()
        r = s.get("/accounts/register/client/")
        ok = "csrfmiddlewaretoken" in r.text
        results.append(("W05 CSRF token present in student registration form", ok))
    except Exception as e:
        results.append((f"W05 ERROR: {e}", False))

    # W06
    try:
        s = SessionHTTP()
        r = s.get("/nonexistent-page-xyz-000/")
        ok = r.status_code == 404
        results.append(("W06 404 page returns 404 not 500", ok))
    except Exception as e:
        results.append((f"W06 ERROR: {e}", False))

    # W07
    try:
        s = SessionHTTP()
        r = s.get("/nonexistent-page-xyz-000/")
        ok = ("Traceback" not in r.text and "Exception Value" not in r.text and "Django Version" not in r.text)
        results.append(("W07 No Django debug stack trace exposed on errors", ok))
    except Exception as e:
        results.append((f"W07 ERROR: {e}", False))

    # W08
    try:
        s = SessionHTTP()
        r = s.get("/api/institutions/?q=test")
        ok = "application/json" in r.headers.get("Content-Type", "")
        results.append(("W08 Institution API returns application/json", ok))
    except Exception as e:
        results.append((f"W08 ERROR: {e}", False))

    # W09
    try:
        all_ok = True
        for path in ["/accounts/dashboard/", "/accounts/dashboard/tutor/", "/accounts/dashboard/client/"]:
            s = SessionHTTP()
            r = s.get(path)
            if not ("login" in r.url or len(r.history) > 0):
                all_ok = False
                break
        results.append(("W09 All dashboard URLs redirect anonymous to login", all_ok))
    except Exception as e:
        results.append((f"W09 ERROR: {e}", False))

    # W10
    try:
        sess = requests.Session()
        sess.headers.update({"User-Agent": "EduLatam-TestSuite/1.0"})
        sess.get(BASE + "/accounts/login/", allow_redirects=True, timeout=10)
        r = sess.post(
            BASE + "/tutores/login/",
            data={"username": "x@x.com", "password": "x"},
            allow_redirects=True,
            timeout=10,
        )
        ok = r.status_code == 403
        results.append(("W10 POST without CSRF token → 403", ok))
    except Exception as e:
        results.append((f"W10 ERROR: {e}", False))

    return results
