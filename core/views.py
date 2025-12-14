from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.views.generic import View
from .models import ClassSession, CiudadHabilitada, NotificacionExpansion
from .forms import SessionRequestForm, SessionConfirmationForm, NotificacionExpansionForm
from accounts.models import User, TutorProfile
from .services.meeting_service import update_session_with_meeting
from .utils.geo import get_available_cities, get_client_ip
import logging

logger = logging.getLogger(__name__)


class GeoRootRouterView(View):
    """
    Vista inteligente que redirige a usuarios anónimos según su ubicación geográfica:
    - Milagro, Guayas → /estudiantes/
    - Resto de Ecuador → /tutores/
    - Fuera de Ecuador → Middleware redirige a /servicio-no-disponible/
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
            geo_data = {
                'city': request.session.get('geo_city', 'Unknown'),
                'region': request.session.get('geo_region', 'Unknown'),
                'country': request.session.get('geo_country', 'Unknown'),
                'allowed': request.session.get('geo_allowed', False),
                'ciudad_data': request.session.get('geo_ciudad_data'),
            }

        # Obtener información de geolocalización
        city = geo_data.get('city', 'Unknown')
        country = geo_data.get('country', 'Unknown')
        ciudad_data = geo_data.get('ciudad_data')

        logger.info(
            f"Geo root router: city={city}, country={country}, ciudad_data={ciudad_data}"
        )

        # LÓGICA ESTRICTA DE REDIRECCIÓN:
        # 1. Si la ciudad es EXACTAMENTE 'Milagro' (case-insensitive) → Estudiantes
        if city and city.strip().lower() == 'milagro':
            logger.info(f"Redirecting to student_landing (Milagro detected: city={city})")
            return redirect('student_landing')

        # 2. Si NO es Milagro pero SÍ es Ecuador → Tutores
        elif country == 'Ecuador':
            logger.info(f"Redirecting to tutor_landing (Ecuador but not Milagro: city={city}, country={country})")
            return redirect('tutor_landing')

        # 3. Si no es Ecuador → Servicio no disponible
        else:
            logger.warning(f"User outside Ecuador: city={city}, country={country}, redirecting to servicio_no_disponible")
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


@login_required
def tutor_selection(request):
    """View for clients to see and select tutors with geographical prioritization"""
    if request.user.user_type != 'client':
        messages.error(request, 'Solo los clientes pueden ver la lista de tutores.')
        return redirect('tutor_dashboard')  # Redirect tutors to their own dashboard

    # Get client's profile for location-based filtering
    try:
        client_profile = request.user.client_profile
        client_city = client_profile.city
        client_country = client_profile.country
    except:
        client_city = None
        client_country = None

    # Get all active tutors
    all_tutors = User.objects.filter(
        user_type='tutor',
        is_active=True
    ).select_related('tutor_profile')

    # Filter by search query if provided
    search_query = request.GET.get('search', '')
    city_filter = request.GET.get('city', '')

    if search_query:
        all_tutors = all_tutors.filter(
            Q(name__icontains=search_query) |
            Q(tutor_profile__subjects__icontains=search_query)
        )

    if city_filter:
        all_tutors = all_tutors.filter(tutor_profile__city__icontains=city_filter)

    # Separate tutors by location for prioritization
    same_city_tutors = []
    same_country_tutors = []
    other_tutors = []

    for tutor in all_tutors:
        try:
            tutor_profile = tutor.tutor_profile
            if client_city and tutor_profile.city == client_city:
                same_city_tutors.append(tutor)
            elif client_country and tutor_profile.country == client_country:
                same_country_tutors.append(tutor)
            else:
                other_tutors.append(tutor)
        except:
            other_tutors.append(tutor)

    # Combine lists with priority: same city > same country > others
    prioritized_tutors = same_city_tutors + same_country_tutors + other_tutors

    context = {
        'tutors': prioritized_tutors,
        'same_city_tutors': same_city_tutors,
        'same_country_tutors': same_country_tutors,
        'other_tutors': other_tutors,
        'client_city': client_city,
        'client_country': client_country,
        'search_query': search_query,
        'city_filter': city_filter,
    }

    return render(request, 'core/tutor_selection.html', context)


@login_required
def request_session(request, tutor_id):
    """View for clients to request a new session with a specific tutor"""
    if request.user.user_type != 'client':
        messages.error(request, 'Solo los clientes pueden solicitar sesiones.')
        return redirect('tutor_dashboard')  # Redirect tutors to their own dashboard

    # Get the selected tutor
    tutor = get_object_or_404(User, id=tutor_id, user_type='tutor', is_active=True)

    if request.method == 'POST':
        form = SessionRequestForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.client = request.user
            session.tutor = tutor  # Set the tutor from URL parameter
            session.status = 'pending'
            session.save()
            messages.success(
                request,
                f'¡Solicitud enviada! El tutor {session.tutor.name} revisará tu solicitud pronto.'
            )
            return redirect('client_dashboard')
    else:
        # Pre-fill form with tutor selection
        form = SessionRequestForm(initial={'tutor': tutor})

    try:
        tutor_profile = tutor.tutor_profile
    except:
        tutor_profile = None

    context = {
        'form': form,
        'tutor': tutor,
        'tutor_profile': tutor_profile
    }

    return render(request, 'core/request_session.html', context)


@login_required
def confirm_session(request, session_id):
    """View for tutors to confirm a session"""
    session = get_object_or_404(ClassSession, id=session_id, tutor=request.user)

    if request.user.user_type != 'tutor':
        messages.error(request, 'Solo los tutores pueden confirmar sesiones.')
        return redirect('client_dashboard')  # Redirect clients to their own dashboard

    if session.status != 'pending':
        messages.warning(request, 'Esta sesión ya ha sido procesada.')
        return redirect('tutor_dashboard')

    if request.method == 'POST':
        form = SessionConfirmationForm(request.POST, instance=session)
        if form.is_valid():
            session = form.save(commit=False)
            session.status = 'confirmed'
            # Automatically generate meeting URL based on selected platform
            update_session_with_meeting(session, save=False)
            session.save()

            # Show platform-specific success message
            platform_name = session.get_meeting_platform_display()
            messages.success(
                request,
                f'¡Sesión confirmada! Se ha generado el enlace de {platform_name}.'
            )
            return redirect('tutor_dashboard')
    else:
        form = SessionConfirmationForm(instance=session)

    return render(request, 'core/confirm_session.html', {
        'form': form,
        'session': session
    })


@login_required
def cancel_session(request, session_id):
    """
    View to cancel a session.

    Allows both tutors and clients to cancel their sessions.
    After cancellation, redirects to the appropriate dashboard based on user type.

    Security:
    - Only the tutor or client associated with the session can cancel it
    - Cannot cancel already cancelled or completed sessions
    - Updates session status to 'cancelled' and saves to database

    Returns:
    - GET: Renders confirmation page (core/cancel_session.html)
    - POST: Cancels session and redirects to user's dashboard
    """
    session = get_object_or_404(ClassSession, id=session_id)

    # Determine the correct dashboard URL for redirection
    if request.user.user_type == 'tutor':
        dashboard_url = 'tutor_dashboard'
    else:
        dashboard_url = 'client_dashboard'

    # Check if user is either the tutor or client for this session
    if request.user != session.tutor and request.user != session.client:
        messages.error(request, 'No tienes permiso para cancelar esta sesión.')
        return redirect(dashboard_url)

    if session.status == 'cancelled':
        messages.warning(request, 'Esta sesión ya está cancelada.')
        return redirect(dashboard_url)

    if session.status == 'completed':
        messages.warning(request, 'No puedes cancelar una sesión completada.')
        return redirect(dashboard_url)

    if request.method == 'POST':
        session.status = 'cancelled'
        session.save()
        messages.info(request, 'La sesión ha sido cancelada.')
        return redirect(dashboard_url)

    return render(request, 'core/cancel_session.html', {'session': session})


@login_required
def meeting_room(request, session_id):
    """View for accessing the meeting room for a session"""
    session = get_object_or_404(ClassSession, id=session_id)

    # Determine the correct dashboard URL for redirection
    if request.user.user_type == 'tutor':
        dashboard_url = 'tutor_dashboard'
    else:
        dashboard_url = 'client_dashboard'

    # Check if user is either the tutor or client for this session
    if request.user != session.tutor and request.user != session.client:
        messages.error(request, 'No tienes permiso para acceder a esta reunión.')
        return redirect(dashboard_url)

    # Check if session is confirmed
    if session.status != 'confirmed':
        messages.warning(request, 'Esta sesión aún no ha sido confirmada.')
        return redirect(dashboard_url)

    # Determine if user is the host (tutor)
    is_host = request.user == session.tutor

    # Mark meeting as started if it's the tutor accessing
    if is_host and not session.meeting_started:
        session.meeting_started = True
        session.save()

    context = {
        'session': session,
        'is_host': is_host
    }

    return render(request, 'core/meeting_room.html', context)


def servicio_no_disponible(request):
    """
    Página mostrada cuando el servicio no está disponible en la ubicación del usuario.
    Muestra formulario para solicitar notificación cuando llegue a su ciudad.
    """
    # Obtener información de geolocalización de la sesión
    geo_city = request.session.get('geo_city', 'Desconocida')
    geo_region = request.session.get('geo_region', 'Desconocida')
    geo_country = request.session.get('geo_country', 'Ecuador')

    # Obtener ciudades disponibles
    ciudades_disponibles = get_available_cities()

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
        'ciudades_disponibles': ciudades_disponibles,
    }

    return render(request, 'core/servicio_no_disponible.html', context)


def notificarme_expansion(request):
    """
    View para procesar el formulario de solicitud de notificación.
    """
    if request.method == 'POST':
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
    else:
        # Si no es POST, redirigir a servicio_no_disponible
        return redirect('servicio_no_disponible')
