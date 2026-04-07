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
   
  
]
