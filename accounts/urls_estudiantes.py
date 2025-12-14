"""
URLs específicas para ESTUDIANTES (Solo Milagro).
Todas estas rutas están protegidas por GeoRestrictionMiddleware.
Solo accesibles si ciudad_data=True (Milagro verificado).
"""
from django.urls import path
from . import views
from core import views as core_views

urlpatterns = [
    # Landing de estudiantes
    path('', core_views.student_landing_view, name='student_landing'),

    # Autenticación de estudiantes
    path('login/', views.StudentLoginView.as_view(), name='student_login'),
    path('registro/', views.register_client, name='register_client'),

    # Dashboard de estudiantes
    path('dashboard/', views.client_dashboard, name='client_dashboard'),
]
