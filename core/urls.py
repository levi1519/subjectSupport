from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('tutors/', views.tutor_selection, name='tutor_selection'),
    path('sessions/request/<int:tutor_id>/', views.request_session, name='request_session'),
    path('sessions/<int:session_id>/confirm/', views.confirm_session, name='confirm_session'),
    path('sessions/<int:session_id>/cancel/', views.cancel_session, name='cancel_session'),
    path('sessions/<int:session_id>/meeting/', views.meeting_room, name='meeting_room'),
]
