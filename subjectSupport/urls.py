"""
URL configuration for subjectSupport project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.academicTutoring import views as core_views
from apps.accounts import views as accounts_views

urlpatterns = [
    path('gestion-ay-2026-4/', admin.site.urls),

    # Geo-router inteligente en la raíz
    path('', core_views.GeoRootRouterView.as_view(), name='home'),

    # GRUPO ESTUDIANTES (Restricción: SOLO MILAGRO)
    # Todas estas rutas están protegidas por middleware para ciudad_data=True
    path('estudiantes/', include('apps.accounts.urls_estudiantes')),

    # GRUPO TUTORES (Restricción: TODO ECUADOR)
    # Todas estas rutas están protegidas por middleware para country='Ecuador'
    path('tutores/', include('apps.accounts.urls_tutores')),

    # Perfiles de usuario (sin restricción geográfica, requiere login)
    path('accounts/', include('apps.accounts.urls')),

    # Logout global (sin restricción geográfica)
    path('accounts/logout/', accounts_views.logout_view, name='logout'),

    # Core URLs (sesiones, etc.)
    path('', include('apps.academicTutoring.urls')),
    path('simulators/', include('apps.simulators.urls')),
]
