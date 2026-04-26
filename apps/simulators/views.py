from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from apps.accounts.models import User
from .models import SimulatorAttempt
from .ai_generator import generate_reinforcement_simulator


class ReinforcementGenerateView(LoginRequiredMixin, View):
    """
    Vista para que un estudiante genere un simulacro de refuerzo
    después de completar un intento. El simulador se enfoca en los
    temas donde el estudiante tuvo menos del 60% de aciertos.
    """

    def post(self, request, attempt_id):
        """POST desde el botón 'Generar Simulacro de Refuerzo'."""
        attempt = get_object_or_404(
            SimulatorAttempt,
            id=attempt_id,
            student=request.user,
            status=SimulatorAttempt.AttemptStatus.COMPLETED,
        )

        success, msg = generate_reinforcement_simulator(
            attempt,
            request.user,
        )

        if success:
            messages.success(request, msg)
        else:
            messages.warning(request, msg)

        return redirect("simulators-home")
