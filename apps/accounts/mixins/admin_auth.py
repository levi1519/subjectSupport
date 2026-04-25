from django.contrib.auth.mixins import AccessMixin
from django.contrib import messages
from django.shortcuts import redirect

class AdminRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is an admin."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not request.user.is_superuser:
            messages.error(request, "You do not have permission to access this page.")
            return redirect('login')
        
        return super().dispatch(request, *args, **kwargs)