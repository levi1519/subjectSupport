from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('tutors/', views.TutorSelectionView.as_view(), name='tutor_selection'),
    path('sessions/request/<int:tutor_id>/', views.RequestSessionView.as_view(), name='request_session'),
    path('sessions/<int:session_id>/confirm/', views.ConfirmSessionView.as_view(), name='confirm_session'),
    path('sessions/<int:session_id>/cancel/', views.CancelSessionView.as_view(), name='cancel_session'),
    path('sessions/<int:session_id>/complete/', views.CompleteSessionView.as_view(), name='complete_session'),
    path('sessions/<int:session_id>/update-meeting/', views.UpdateMeetingUrlView.as_view(), name='update_meeting_url'),
    path('sessions/<int:session_id>/meeting/', views.MeetingRoomView.as_view(), name='meeting_room'),
    path('notifications/read/<int:notif_id>/', views.mark_notification_read, name='mark_notification_read'),
    # Geolocalización
    path('servicio-no-disponible/', views.servicio_no_disponible, name='servicio_no_disponible'),
    path('notificarme/', views.NotificarmeExpansionView.as_view(), name='notificarme'),
    # Instituciones API
    path('api/institutions/', views.institution_search_api, name='institution_search_api'),
]
