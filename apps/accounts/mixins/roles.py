from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

class ClientRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin que garantiza que el usuario esté autenticado y tenga el rol 'client'.
    """
    def test_func(self):
        # Validamos que esté autenticado y sea cliente
        return self.request.user.is_authenticated and self.request.user.user_type == 'client'
    
    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            # Si está logueado pero es un tutor intentando acceder a vista de estudiante
            raise PermissionDenied("Acceso restringido. Esta sección es exclusiva para estudiantes.")

        # Si no está logueado, el comportamiento por defecto lo redirige a la URL de login
        return super().handle_no_permission()
    
class TutorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin que garantiza que el usuario esté autenticado y tenga el rol 'tutor'.
    """
    def test_func(self):
        # Validamos que esté autenticado y sea tutor
        return self.request.user.is_authenticated and self.request.user.user_type == 'tutor'

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            # Si está logueado pero es un estudiante intentando acceder a vista de tutor
            raise PermissionDenied("Acceso restringido. Esta sección es exclusiva para tutores.")

        # Si no está logueado, el comportamiento por defecto lo redirige a la URL de login
        return super().handle_no_permission()