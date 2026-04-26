from django.http import HttpResponse
from django.urls import path
from . import views

urlpatterns = [
    path("", lambda request: HttpResponse("Simulators home"), name="simulators-home"),
    path(
        "reinforcement/<int:attempt_id>/generate/",
        views.ReinforcementGenerateView.as_view(),
        name="simulator-reinforcement-generate",
    ),
]
