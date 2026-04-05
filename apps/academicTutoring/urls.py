from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('tutors/', views.TutorSelectionView.as_view(), name='tutor_selection'),
    path('sessions/request/<int:tutor_id>/', views.RequestSessionView.as_view(), name='request_session'),
    path('sessions/<int:session_id>/confirm/', views.ConfirmSessionView.as_view(), name='confirm_session'),
    path('sessions/<int:session_id>/cancel/', views.CancelSessionView.as_view(), name='cancel_session'),
    path('sessions/<int:session_id>/complete/', views.CompleteSessionView.as_view(), name='complete_session'),
    path('sessions/<int:session_id>/meeting/', views.MeetingRoomView.as_view(), name='meeting_room'),
    # Geolocalización
    path('servicio-no-disponible/', views.servicio_no_disponible, name='servicio_no_disponible'),
    path('notificarme/', views.NotificarmeExpansionView.as_view(), name='notificarme'),
]
