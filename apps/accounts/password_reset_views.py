"""
Flujo de recuperación de contraseña con código OTP.

Pasos:
  1. PasswordResetRequestView  → el usuario ingresa su email
  2. (sistema envía correo con código de 6 dígitos, expira en 15 min)
  3. PasswordResetVerifyView   → el usuario ingresa el código
  4. PasswordResetNewView      → el usuario elige nueva contraseña
  5. Redirect al login correcto (tutor/estudiante)
"""

import random
import string
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import password_validation
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.views import View

from .models import User


# ─────────────────────────────────────────────
# Constantes
# ─────────────────────────────────────────────
OTP_LENGTH = 6
OTP_TTL_MINUTES = 15
OTP_MAX_ATTEMPTS = 5          # intentos fallidos antes de invalidar
SESSION_KEY_EMAIL = "_pr_email"
SESSION_KEY_CODE = "_pr_code"
SESSION_KEY_EXPIRY = "_pr_expiry"   # ISO string
SESSION_KEY_ATTEMPTS = "_pr_attempts"
SESSION_KEY_VERIFIED = "_pr_verified"


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=OTP_LENGTH))


def _clear_pr_session(request):
    for key in [SESSION_KEY_EMAIL, SESSION_KEY_CODE, SESSION_KEY_EXPIRY,
                SESSION_KEY_ATTEMPTS, SESSION_KEY_VERIFIED]:
        request.session.pop(key, None)


def _otp_is_expired(request) -> bool:
    expiry_iso = request.session.get(SESSION_KEY_EXPIRY)
    if not expiry_iso:
        return True
    from datetime import datetime, timezone as dt_tz
    expiry = datetime.fromisoformat(expiry_iso)
    return timezone.now() > expiry


def _send_otp_email(user: User, otp: str) -> bool:
    """Envía el correo con el código OTP. Retorna True si tuvo éxito."""
    context = {
        "user_name": user.name,
        "otp": otp,
        "otp_ttl": OTP_TTL_MINUTES,
        "app_name": "EduLatam",
    }
    try:
        html_message = render_to_string("emails/password_reset_otp.html", context)
        plain_message = render_to_string("emails/password_reset_otp.txt", context)
        send_mail(
            subject="[EduLatam] Código de recuperación de contraseña",
            message=plain_message,
            from_email=None,   # usa DEFAULT_FROM_EMAIL del settings
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error(
            "Error enviando OTP a %s: %s", user.email, exc
        )
        return False


# ─────────────────────────────────────────────
# Vista 1 – Solicitar email
# ─────────────────────────────────────────────

class PasswordResetRequestView(View):
    template_name = "accounts/password_reset_request.html"

    def get(self, request):
        _clear_pr_session(request)
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get("email", "").strip().lower()

        if not email:
            messages.error(request, "Por favor ingresa tu correo electrónico.")
            return render(request, self.template_name)

        # No revelamos si el email existe o no (seguridad)
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            user = None

        if user:
            otp = _generate_otp()
            expiry = timezone.now() + timedelta(minutes=OTP_TTL_MINUTES)

            request.session[SESSION_KEY_EMAIL] = user.email
            request.session[SESSION_KEY_CODE] = otp
            request.session[SESSION_KEY_EXPIRY] = expiry.isoformat()
            request.session[SESSION_KEY_ATTEMPTS] = 0
            request.session[SESSION_KEY_VERIFIED] = False

            sent = _send_otp_email(user, otp)
            if not sent:
                messages.error(
                    request,
                    "No pudimos enviar el correo. Por favor intenta más tarde."
                )
                _clear_pr_session(request)
                return render(request, self.template_name)

        # Mensaje genérico siempre (no revela si el email existe)
        messages.success(
            request,
            "Si tu correo está registrado, recibirás un código en los próximos minutos. "
            "Revisa también tu carpeta de spam."
        )
        return redirect("password_reset_verify")


# ─────────────────────────────────────────────
# Vista 2 – Verificar código OTP
# ─────────────────────────────────────────────

class PasswordResetVerifyView(View):
    template_name = "accounts/password_reset_verify.html"

    def _redirect_if_invalid_session(self, request):
        """Redirige a la primera pantalla si la sesión no tiene datos válidos."""
        if not request.session.get(SESSION_KEY_CODE):
            messages.warning(request, "Sesión expirada. Vuelve a solicitar el código.")
            return redirect("password_reset_request")
        return None

    def get(self, request):
        redir = self._redirect_if_invalid_session(request)
        if redir:
            return redir
        # Enmascarar el email para mostrarlo al usuario
        email = request.session.get(SESSION_KEY_EMAIL, "")
        masked = _mask_email(email)
        return render(request, self.template_name, {"masked_email": masked})

    def post(self, request):
        redir = self._redirect_if_invalid_session(request)
        if redir:
            return redir

        email = request.session.get(SESSION_KEY_EMAIL, "")
        masked = _mask_email(email)

        # Verificar expiración
        if _otp_is_expired(request):
            _clear_pr_session(request)
            messages.error(
                request,
                "El código expiró. Vuelve a solicitar uno nuevo."
            )
            return redirect("password_reset_request")

        # Verificar intentos
        attempts = request.session.get(SESSION_KEY_ATTEMPTS, 0)
        if attempts >= OTP_MAX_ATTEMPTS:
            _clear_pr_session(request)
            messages.error(
                request,
                "Demasiados intentos fallidos. Vuelve a solicitar el código."
            )
            return redirect("password_reset_request")

        entered = request.POST.get("code", "").strip()
        stored = request.session.get(SESSION_KEY_CODE, "")

        if entered == stored:
            request.session[SESSION_KEY_VERIFIED] = True
            request.session.pop(SESSION_KEY_CODE, None)   # invalidar código ya usado
            return redirect("password_reset_new")
        else:
            request.session[SESSION_KEY_ATTEMPTS] = attempts + 1
            remaining = OTP_MAX_ATTEMPTS - request.session[SESSION_KEY_ATTEMPTS]
            if remaining > 0:
                messages.error(
                    request,
                    f"Código incorrecto. Te quedan {remaining} intento(s)."
                )
            else:
                _clear_pr_session(request)
                messages.error(
                    request,
                    "Demasiados intentos fallidos. Vuelve a solicitar el código."
                )
                return redirect("password_reset_request")

            return render(request, self.template_name, {"masked_email": masked})


def _mask_email(email: str) -> str:
    """Convierte user@example.com → u***@example.com"""
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 1:
        return email
    return f"{local[0]}{'*' * (len(local) - 1)}@{domain}"


# ─────────────────────────────────────────────
# Vista 3 – Nueva contraseña
# ─────────────────────────────────────────────

class PasswordResetNewView(View):
    template_name = "accounts/password_reset_new.html"

    def _check_session(self, request):
        """Retorna (user, error_redirect)."""
        if not request.session.get(SESSION_KEY_VERIFIED):
            messages.warning(request, "Debes verificar tu código primero.")
            return None, redirect("password_reset_request")

        if _otp_is_expired(request):
            _clear_pr_session(request)
            messages.error(request, "Tu sesión expiró. Vuelve a solicitar el código.")
            return None, redirect("password_reset_request")

        email = request.session.get(SESSION_KEY_EMAIL)
        if not email:
            return None, redirect("password_reset_request")

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            _clear_pr_session(request)
            return None, redirect("password_reset_request")

        return user, None

    def get(self, request):
        user, redir = self._check_session(request)
        if redir:
            return redir
        return render(request, self.template_name)

    def post(self, request):
        user, redir = self._check_session(request)
        if redir:
            return redir

        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        errors = []

        if not password1:
            errors.append("La contraseña no puede estar vacía.")
        elif password1 != password2:
            errors.append("Las contraseñas no coinciden.")
        else:
            try:
                validate_password(password1, user=user)
            except ValidationError as exc:
                errors.extend(exc.messages)

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, self.template_name)

        # Actualizar contraseña
        user.set_password(password1)
        user.save()
        _clear_pr_session(request)

        messages.success(
            request,
            "¡Contraseña actualizada correctamente! Ya puedes iniciar sesión."
        )

        # Redirigir al login según el tipo de usuario
        if user.user_type == "tutor":
            return redirect("tutor_login")
        return redirect("student_login")