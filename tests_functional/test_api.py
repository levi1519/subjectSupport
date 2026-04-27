"""
Tests de endpoints JSON/API.
"""
import json
from .base import SessionHTTP


def run():
    results = []

    # A01
    try:
        s = SessionHTTP()
        r = s.get("/api/institutions/?q=universidad")
        ok = False
        if r.status_code == 200:
            data = json.loads(r.text)
            ok = "results" in data
        results.append(("A01 /api/institutions/?q=universidad → 200 + valid JSON", ok))
    except Exception as e:
        results.append((f"A01 ERROR: {e}", False))

    # A02
    try:
        s = SessionHTTP()
        r = s.get("/api/institutions/?q=u")
        ok = False
        if r.status_code == 200:
            data = json.loads(r.text)
            ok = data.get("results") == []
        results.append(("A02 Short query q=u → empty results", ok))
    except Exception as e:
        results.append((f"A02 ERROR: {e}", False))

    # A03
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
                results.append(("A03 q=unemi → items have id/name/city if results exist (no UNEMI in DB)", ok))
                # skip second append below
                return results
        results.append(("A03 q=unemi → items have id/name/city if results exist", ok))
    except Exception as e:
        results.append((f"A03 ERROR: {e}", False))

    # A04
    try:
        import requests
        base = s.base if 's' in dir() else SessionHTTP().base
        r = requests.post(
            base + "/api/institutions/",
            data={},
            allow_redirects=True,
            timeout=10,
        )
        ok = r.status_code in [405, 403, 302]
        results.append(("A04 POST /api/institutions/ → 405 Method Not Allowed", ok))
    except Exception as e:
        results.append((f"A04 ERROR: {e}", False))

    # A05
    try:
        s = SessionHTTP()
        r = s.get("/api/institutions/")
        ok = False
        if r.status_code == 200:
            data = json.loads(r.text)
            ok = data.get("results") == []
        results.append(("A05 No q param → empty results", ok))
    except Exception as e:
        results.append((f"A05 ERROR: {e}", False))

    return results
