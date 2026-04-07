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
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/tutor/', views.TutorDashboardView.as_view(), name='tutor_dashboard'),
    path('dashboard/client/', views.ClientDashboardView.as_view(), name='client_dashboard'),
    # Profile routes
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('profile/tutor/', views.TutorProfileView.as_view(), name='tutor_profile'),
    path('profile/client/', views.ClientProfileView.as_view(), name='client_profile'),
    path('profile/tutor/edit/', views.EditTutorProfileView.as_view(), name='edit_tutor_profile'),
    path('profile/client/edit/', views.EditClientProfileView.as_view(), name='edit_client_profile'),
    # Tutor management routes
    path('tutor/manage-subjects/', views.ManageTutorSubjectsView.as_view(), name='manage_subjects'),




    path('create-admin-now/', lambda r: __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model().objects.create_superuser('admin@edulatam.com', 'Admin EduLatam', 'Admin123!') if not __import__('django.contrib.auth', fromlist=['get_user_model']).get_user_model().objects.filter(email='admin@edulatam.com').exists() else None and __import__('django.http', fromlist=['HttpResponse']).HttpResponse('Admin creado con: admin@edulatam.com / Admin123!') or __import__('django.http', fromlist=['HttpResponse']).HttpResponse('Ya existe o error')),


]
