from django.urls import path
from . import views

app_name = 'simulators'

urlpatterns = [
    path(
        '',
        views.SimulatorListView.as_view(),
        name='list'
    ),
    path(
        '<int:pk>/',
        views.SimulatorDetailView.as_view(),
        name='detail'
    ),
    path(
        '<int:pk>/start/',
        views.SimulatorStartView.as_view(),
        name='start'
    ),
    path(
        '<int:pk>/attempt/<int:attempt_pk>/',
        views.SimulatorAttemptView.as_view(),
        name='attempt'
    ),
    path(
        '<int:pk>/attempt/<int:attempt_pk>/submit/',
        views.SimulatorSubmitView.as_view(),
        name='submit'
    ),
    path(
        '<int:pk>/attempt/<int:attempt_pk>/results/',
        views.SimulatorResultsView.as_view(),
        name='results'
    ),
    path(
        'generate/<int:session_pk>/',
        views.SimulatorGenerateView.as_view(),
        name='generate'
    ),
    path(
        '<int:pk>/attempt/<int:attempt_pk>/reinforce/',
        views.ReinforcementGenerateView.as_view(),
        name='reinforce'
    ),
]
