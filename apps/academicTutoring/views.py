from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.views.generic import View, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse

from .models import ClassSession, NotificacionExpansion
from .forms import SessionRequestForm, SessionConfirmationForm, NotificacionExpansionForm
from . import services as academic_services
from apps.accounts.models import User, TutorProfile, Notification, KnowledgeArea
from .services.meeting_service import update_session_with_meeting
from .utils import send_cancellation_email

import logging

logger = logging.getLogger(__name__)


@login_required
def mark_notification_read(request, notif_id):
    """Mark a notification as read via POST."""
    if request.method == 'POST':
        Notification.objects.filter(
            id=notif_id, recipient=request.user
        ).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


class GeoRootRouterView(View):
    """
    Vista inteligente que redirige a usuarios anónimos según su ubicación geográfica.

    NUEVA LÓGICA GEODJANGO:
    - Dentro del polígono de ServiceArea (Milagro) → /estudiantes/
    - Ecuador pero fuera del polígono → /tutores/
    - Fuera de Ecuador → /servicio-no-disponible/

    Usa consultas espaciales PostGIS para precisión máxima.
    """

    def get(self, request):
        # Si el usuario está autenticado, redirigir según su tipo
        if request.user.is_authenticated:
            if request.user.user_type == 'tutor':
                return redirect('tutor_landing')
            else:
                return redirect('student_landing')

        # Para usuarios anónimos, usar datos de geolocalización del middleware
        geo_data = getattr(request, 'geo_data', None)

        if not geo_data:
            # Intentar obtener de sesión como fallback
            geo_data = request.session.get('geo_data', {})

        country_config = geo_data.get('country_config')
        service_area = geo_data.get('service_area')

        if not country_config or not country_config.get('active'):
            return redirect('servicio_no_disponible')

        if service_area:
            return redirect('student_landing')

        return redirect('tutor_landing')


def landing_page(request):
    """Landing page with registration options"""
    return render(request, 'core/landing.html')


def student_landing_view(request):
    """Landing page for students"""
    return render(request, 'landing/student_landing.html', {'user_type': 'Estudiante'})


def tutor_landing_view(request):
    """Landing page for tutors"""
    return render(request, 'landing/tutor_landing.html', {'user_type': 'Tutor'})


class TutorSelectionView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    View for clients to see and select tutors with geographical prioritization.
    Uses TutorProfileManager for optimized queries.
    """
    template_name = 'core/tutor_selection.html'
    
    def test_func(self):
        """Only clients can view tutor selection"""
        return self.request.user.user_type == 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            client_country = self.request.user.country_code or ''
        except Exception:
            client_country = ''

        # Get active country codes
        from geoconfig.geo import get_active_country_codes
        active_codes = get_active_country_codes()
        from apps.academicTutoring.models import CountryConfig

        # Get filter params
        search_query   = self.request.GET.get('search', '')
        country_filter = self.request.GET.get('country_code', '')

        # Query tutors — country filter takes precedence
        if country_filter:
            tutors_qs = TutorProfile.objects.get_tutors_filtered_by_country(country_filter, active_codes=active_codes)
        elif client_country:
            tutors_qs = TutorProfile.objects.get_tutors_by_country_priority(client_country, active_codes=active_codes)
        else:
            tutors_qs = TutorProfile.objects.get_tutors_fallback(active_codes=active_codes)

        # Apply knowledge area filter if provided
        knowledge_area_slug = self.request.GET.get('knowledge_area', '')
        if knowledge_area_slug:
            tutors_qs = TutorProfile.objects.get_tutors_by_knowledge_area(
                knowledge_area_slug, active_codes=active_codes
            )

        # Apply search filter
        tutors_qs = TutorProfile.objects.filter_by_search(tutors_qs, search_query)

        context.update({
            'tutors':         tutors_qs,
            'client_country': client_country,
            'search_query':   search_query,
            'country_filter': country_filter,
            'countries':      CountryConfig.objects.filter(active=True).order_by('country_name'),
            'knowledge_areas': KnowledgeArea.objects.all().order_by('name'),
            'knowledge_area_filter': knowledge_area_slug,
        })

        return context


class RequestSessionView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    View for clients to request a new session with a specific tutor.
    Uses SessionService for business logic.
    """
    template_name = 'core/request_session.html'
    form_class = SessionRequestForm
    
    def test_func(self):
        """Only clients can request sessions"""
        return self.request.user.user_type == 'client'
    
    def dispatch(self, request, *args, **kwargs):
        """Get tutor from URL parameter"""
        self.tutor = get_object_or_404(
            User.objects.select_related('tutor_profile'),
            id=kwargs['tutor_id'],
            user_type='tutor',
            is_active=True
        )
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tutor': self.tutor,
            'tutor_profile': getattr(self.tutor, 'tutor_profile', None),
            'tutor_subjects': getattr(self.tutor, 'tutor_profile', None).subjects_taught.all() if getattr(self.tutor, 'tutor_profile', None) else []
        })
        return context
    
    def get_form_kwargs(self):
        """Pre-fill form with tutor selection"""
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'tutor': self.tutor}
        return kwargs
    
    def form_valid(self, form):
        """Use academic_services to create session"""
        success, session, error = academic_services.create_session(
            self.tutor,
            self.request.user,
            form  # ← form object, NOT form.cleaned_data
        )
        
        if success:
            messages.success(
                self.request,
                f'¡Solicitud enviada! El tutor {session.tutor.name} revisará tu solicitud pronto.'
            )
            return redirect('client_dashboard')
        else:
            messages.error(self.request, f'Error al crear sesión: {error}')
            return self.form_invalid(form)


class ConfirmSessionView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    View for tutors to confirm a session.
    Uses SessionService for business logic.
    """
    template_name = 'core/confirm_session.html'
    form_class = SessionConfirmationForm
    
    def test_func(self):
        """Only tutors can confirm sessions and must own the session"""
        session = get_object_or_404(ClassSession, id=self.kwargs['session_id'])
        return (self.request.user.user_type == 'tutor' and 
                self.request.user == session.tutor)
    
    def dispatch(self, request, *args, **kwargs):
        """Get session and validate status"""
        self.session = get_object_or_404(ClassSession, id=kwargs['session_id'])
        
        if self.session.status != 'pending':
            messages.warning(request, 'Esta sesión ya ha sido procesada.')
            return redirect('tutor_dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session'] = self.session
        return context
    
    def get_form_kwargs(self):
        """Pass session instance to form"""
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.session
        return kwargs
    
    def form_valid(self, form):
        """Use academic_services to confirm session"""
        platform = form.cleaned_data.get('meeting_platform', 'google_meet')
        success, session, error = academic_services.confirm_session(
            self.session, self.request.user, form
        )
        
        if success:
            # Show platform-specific success message
            platform_name = session.get_meeting_platform_display()
            messages.success(
                self.request,
                f'¡Sesión confirmada! Se ha generado el enlace de {platform_name}.'
            )
            return redirect('tutor_dashboard')
        else:
            messages.error(self.request, f'Error al confirmar sesión: {error}')
            return self.form_invalid(form)


class CancelSessionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    View to cancel a session.
    Uses SessionService for business logic.
    """
    
    def test_func(self):
        """User must be either tutor or client associated with the session"""
        self.session = get_object_or_404(ClassSession, id=self.kwargs['session_id'])
        user = self.request.user
        return user == self.session.tutor or user == self.session.client
    
    def get(self, request, *args, **kwargs):
        """Show confirmation page"""
        session = self.session
        
        # Check session status
        if session.status == 'cancelled':
            messages.warning(request, 'Esta sesión ya está cancelada.')
            return redirect(self.get_success_url())
        
        if session.status == 'completed':
            messages.warning(request, 'No puedes cancelar una sesión completada.')
            return redirect(self.get_success_url())
        
        return render(request, 'core/cancel_session.html', {'session': session})
    
    def post(self, request, *args, **kwargs):
        """Cancel the session using academic_services"""
        # Guardar estado previo para idempotencia (no enviar email si ya estaba cancelada)
        prev_status = self.session.status

        success, session, error = academic_services.cancel_session(
            self.session,
            request.user
        )

        if success:
            # Enviar email SOLO si la sesión NO estaba ya cancelada (idempotencia)
            if prev_status != 'cancelled':
                # Determinar contraparte: quien NO canceló recibe el email
                if request.user == session.tutor:
                    recipient = session.client
                else:
                    recipient = session.tutor
                send_cancellation_email(session, request.user, recipient)
                Notification.objects.create(
                    recipient=recipient,
                    message=f'{request.user.name} canceló la clase de {session.subject} del {session.scheduled_date.strftime("%d/%m/%Y")} a las {session.scheduled_time.strftime("%H:%M")}'
                )
                messages.info(request, f'La sesión ha sido cancelada. Se notificó a {recipient.name}.')
            else:
                messages.info(request, 'La sesión ha sido cancelada.')
        else:
            messages.error(request, f'Error al cancelar sesión: {error}')

        return redirect(self.get_success_url())
    
    def get_success_url(self):
        """Redirect to appropriate dashboard"""
        if self.request.user.user_type == 'tutor':
            return reverse('tutor_dashboard')
        else:
            return reverse('client_dashboard')


class CompleteSessionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Mark a confirmed session as completed. Tutor only."""

    def test_func(self):
        self.session = get_object_or_404(ClassSession, id=self.kwargs['session_id'])
        return self.request.user == self.session.tutor

    def post(self, request, *args, **kwargs):
        session = self.session
        if session.status != 'confirmed':
            messages.warning(request, 'Solo puedes completar sesiones confirmadas.')
            return redirect('tutor_dashboard')
        session.status = 'completed'
        session.save()
        messages.success(request, f'Sesión de {session.subject} marcada como completada.')
        return redirect('tutor_dashboard')


class UpdateMeetingUrlView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Allow tutor to update meeting_url of a confirmed session."""

    def test_func(self):
        self.session = get_object_or_404(ClassSession, id=self.kwargs['session_id'])
        return self.request.user == self.session.tutor

    def post(self, request, *args, **kwargs):
        session = self.session
        if session.status != 'confirmed':
            messages.warning(request, 'Solo puedes actualizar el enlace de sesiones confirmadas.')
            return redirect('tutor_dashboard')
        meeting_url = request.POST.get('meeting_url', '').strip()
        if meeting_url:
            session.meeting_url = meeting_url
            session.save()
            messages.success(request, 'Enlace de reunión actualizado.')
        else:
            messages.warning(request, 'El enlace no puede estar vacío.')
        return redirect('tutor_dashboard')


class MeetingRoomView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    View for accessing the meeting room for a session.
    Uses SessionService for meeting start logic.
    """
    template_name = 'core/meeting_room.html'
    
    def test_func(self):
        """User must be either tutor or client associated with the session"""
        self.session = get_object_or_404(ClassSession, id=self.kwargs['session_id'])
        user = self.request.user
        return user == self.session.tutor or user == self.session.client
    
    def dispatch(self, request, *args, **kwargs):
        """Validate session status"""
        self.session = get_object_or_404(ClassSession, id=kwargs['session_id'])
        if self.session.status != 'confirmed':
            messages.warning(request, 'Esta sesión aún no ha sido confirmada.')
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        """Redirect to appropriate dashboard"""
        if self.request.user.user_type == 'tutor':
            return reverse('tutor_dashboard')
        else:
            return reverse('client_dashboard')
    
    def get_context_data(self, **kwargs):
        """Get context data and start meeting if tutor"""
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        is_host = user == self.session.tutor
        
        # Start meeting if tutor is accessing
        if is_host and not self.session.meeting_started:
            success, session, error = academic_services.start_meeting(self.session, user)
            if success:
                self.session = session  # Update session with meeting_started=True
        
        context.update({
            'session': self.session,
            'is_host': is_host
        })
        
        return context


def servicio_no_disponible(request):
    """
    Página mostrada cuando el servicio no está disponible en la ubicación del usuario.
    Muestra formulario para solicitar notificación cuando llegue a su ciudad.
    """
    # Obtener información de geolocalización de la sesión
    geo_city = request.session.get('geo_city', 'Desconocida')
    geo_region = request.session.get('geo_region', 'Desconocida')
    geo_country = request.session.get('geo_country', 'Ecuador')

    # Obtener áreas de servicio disponibles (NUEVA LÓGICA GEODJANGO)
    service_areas = academic_services.get_service_areas_for_display()

    # Crear formulario pre-llenado con la ciudad detectada
    initial_data = {
        'ciudad_deseada': geo_city if geo_city != 'Desconocida' else '',
        'provincia_deseada': geo_region if geo_region != 'Desconocida' else '',
    }
    form = NotificacionExpansionForm(initial=initial_data)

    context = {
        'form': form,
        'geo_city': geo_city,
        'geo_region': geo_region,
        'geo_country': geo_country,
        'service_areas': service_areas,  # NUEVA: ServiceArea objects
    }

    return render(request, 'core/servicio_no_disponible.html', context)


class NotificarmeExpansionView(View):
    """
    View para procesar el formulario de solicitud de notificación.
    """
    
    def post(self, request):
        form = NotificacionExpansionForm(request.POST)
        if form.is_valid():
            success, notificacion, error = academic_services.save_expansion_notification(form, request)
            if not success:
                messages.error(request, 'Error al procesar tu solicitud.')
                return redirect('servicio_no_disponible')

            logger.info(
                f"Nueva notificación de expansión: {notificacion.email} "
                f"quiere servicio en {notificacion.ciudad_deseada}"
            )

            messages.success(
                request,
                '¡Gracias! Te avisaremos cuando SubjectSupport llegue a tu ciudad. '
                'Revisa tu correo para confirmar la suscripción.'
            )

            # Redirigir de vuelta a la página de servicio no disponible
            return redirect('servicio_no_disponible')
        else:
            # Si hay errores en el formulario, mostrar en la página
            messages.error(
                request,
                'Hubo un error al procesar tu solicitud. Por favor verifica los datos.'
            )
            return redirect('servicio_no_disponible')
    
    def get(self, request):
        # Si no es POST, redirigir a servicio_no_disponible
        return redirect('servicio_no_disponible')