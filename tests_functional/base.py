"""
SessionHTTP: wrapper sobre requests.Session que maneja CSRF.
BASE_URL configurable via variable de entorno.
"""
import os
import requests


class SessionHTTP:
    def __init__(self):
        self.base = os.getenv("TEST_BASE_URL", "http://localhost:8000").rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "EduLatam-TestSuite/1.0"})

    def get(self, path: str):
        """GET con allow_redirects=True y timeout."""
        return self.session.get(self.base + path, allow_redirects=True, timeout=10)

    def get_csrf(self, path: str) -> str:
        """GET a path para poblar cookies, retorna csrftoken."""
        self.session.get(self.base + path, allow_redirects=True, timeout=10)
        return self.session.cookies.get("csrftoken", "")

    def post(self, path: str, data: dict, referer_path: str = None):
        """POST con CSRF token inyectado y Referer header."""
        self.get_csrf(path)
        csrf = self.session.cookies.get("csrftoken", "")
        payload = dict(data)
        payload["csrfmiddlewaretoken"] = csrf
        headers = {"Referer": self.base + (referer_path or path)}
        return self.session.post(
            self.base + path,
            data=payload,
            headers=headers,
            allow_redirects=True,
            timeout=10,
        )

    def login(self, email: str, password: str, login_path: str) -> bool:
        """Login genérico. Retorna True si parece exitoso."""
        r = self.post(login_path, {"username": email, "password": password}, login_path)
        return "dashboard" in r.url or (r.status_code == 200 and "login" not in r.url)
