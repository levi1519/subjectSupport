from django.urls import path
from . import views

urlpatterns = [
    # Registration routes
    path('register/', views.register_view, name='register'),
    path('register/tutor/', views.register_tutor, name='register_tutor'),
    path('register/client/', views.register_client, name='register_client'),
    # Authentication routes
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Dashboard routes
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/tutor/', views.tutor_dashboard, name='tutor_dashboard'),
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),
]
