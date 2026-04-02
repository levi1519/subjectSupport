from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.generic import View, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse

from .models import ClassSession, NotificacionExpansion
from .forms import SessionRequestForm, SessionConfirmationForm, NotificacionExpansionForm
from . import services as academic_services
from apps.accounts.models import User, TutorProfile
from .services.meeting_service import update_session_with_meeting
from geoconfig.geo import get_available_service_areas, get_client_ip
import logging

logger = logging.getLogger(__name__)


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

        # Obtener información de geolocalización
        country = geo_data.get('country', 'Unknown')
        service_area = geo_data.get('service_area')  # Dict con info si está en área de servicio

        logger.info(
            f"Geo root router: country={country}, service_area={service_area}"
        )

        # NUEVA LÓGICA DE REDIRECCIÓN BASADA EN GEOMETRÍA:
        # 1. Si está dentro del polígono de ServiceArea → Estudiantes
        if service_area:
            logger.info(f"Redirecting to student_landing (inside service area: {service_area['city_name']})")
            return redirect('student_landing')

        # 2. Si NO está en service area pero SÍ es Ecuador → Tutores
        elif country == 'Ecuador':
            logger.info(f"Redirecting to tutor_landing (Ecuador but outside service area)")
            return redirect('tutor_landing')

        # 3. Si no es Ecuador → Servicio no disponible
        else:
            logger.warning(f"User outside Ecuador: country={country}, redirecting to servicio_no_disponible")
            return redirect('servicio_no_disponible')


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
        """Get context data using TutorProfileManager for optimized queries"""
        context = super().get_context_data(**kwargs)
        
        # Get client's profile for location-based filtering
        try:
            client_profile = self.request.user.client_profile
            client_city = client_profile.city
            client_country = client_profile.country
        except:
            client_city = None
            client_country = None
        
        # Get search parameters
        search_query = self.request.GET.get('search', '')
        city_filter = self.request.GET.get('city', '')
        
        # Use TutorProfileManager for location-based tutor selection
        if client_city and client_country:
            prioritized_tutors = TutorProfile.objects.get_tutors_by_location(client_city, client_country)
        else:
            # Fallback to basic active tutors query
            prioritized_tutors = TutorProfile.objects.select_related('user').filter(
                user__user_type='tutor',
                user__is_active=True
            ).order_by('user__name')
        
        # Apply search filters if provided
        if search_query:
            prioritized_tutors = prioritized_tutors.filter(
                Q(user__name__icontains=search_query) |
                Q(subjects__name__icontains=search_query)
            ).distinct()
        
        if city_filter:
            prioritized_tutors = prioritized_tutors.filter(city__icontains=city_filter)
        
        # Separate tutors by location for template context
        same_city_tutors = []
        same_country_tutors = []
        other_tutors = []
        
        for tutor_profile in prioritized_tutors:
            if client_city and tutor_profile.city == client_city:
                same_city_tutors.append(tutor_profile.user)
            elif client_country and tutor_profile.country == client_country:
                same_country_tutors.append(tutor_profile.user)
            else:
                other_tutors.append(tutor_profile.user)
        
        context.update({
            'tutors': [tutor for tutor in prioritized_tutors],
            'same_city_tutors': same_city_tutors,
            'same_country_tutors': same_country_tutors,
            'other_tutors': other_tutors,
            'client_city': client_city,
            'client_country': client_country,
            'search_query': search_query,
            'city_filter': city_filter,
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
        self.tutor = get_object_or_404(User, id=kwargs['tutor_id'], user_type='tutor', is_active=True)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'tutor': self.tutor,
            'tutor_profile': getattr(self.tutor, 'tutor_profile', None)
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
        success, session, error = academic_services.confirm_session(self.session, platform)
        
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
        success, session, error = academic_services.cancel_session(
            self.session,
            request.user
        )
        
        if success:
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
            success, session, error = academic_services.start_meeting(self.session)
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
    service_areas = get_available_service_areas()

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
            notificacion = form.save(commit=False)

            # Añadir información de IP y ciudad detectada
            notificacion.ip_address = get_client_ip(request)
            notificacion.ciudad_detectada = request.session.get('geo_city', 'Desconocida')

            # Guardar
            notificacion.save()

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