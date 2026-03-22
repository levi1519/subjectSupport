"""
URLs específicas para TUTORES (Todo Ecuador).
Todas estas rutas están protegidas por GeoRestrictionMiddleware.
Solo accesibles si country='Ecuador'.
"""
from django.urls import path
from . import views
from apps.academicTutoring.core import views as core_views

urlpatterns = [
    # Landing de tutores
    path('', core_views.tutor_landing_view, name='tutor_landing'),

    # Autenticación de tutores
    path('login/', views.TutorLoginView.as_view(), name='tutor_login'),
    path('registro/', views.register_tutor, name='tutor_register'),

    # Dashboard de tutores
    path('dashboard/', views.tutor_dashboard, name='tutor_dashboard'),
]
