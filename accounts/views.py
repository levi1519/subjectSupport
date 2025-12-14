from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse
from .forms import TutorRegistrationForm, ClientRegistrationForm, LoginForm, TutorSubjectsForm


def register_view(request):
    """
    Generic registration view that allows users to choose their type.
    Serves as entry point for registration process.
    """
    return render(request, 'accounts/register_choice.html')


def register_tutor(request):
    """
    Vista de registro para tutores (profesores/docentes).
    
    Accesible desde todo Ecuador (sin restricciones geográficas).
    
    Proceso:
    1. Muestra formulario de registro con campos específicos para tutores
    2. Valida datos del formulario (TutorRegistrationForm)
    3. Crea usuario con user_type='tutor' y perfil de tutor asociado
    4. Inicia sesión automáticamente al usuario recién creado
    5. Redirige directamente a 'tutor_dashboard' (sin pasar por dashboard genérico)
    
    Seguridad:
    - Redirección directa a dashboard específico previene errores NoReverseMatch
    - Sincronizado con URLs definidas en accounts/urls.py
    - Mensaje de éxito informativo para el usuario
    
    Returns:
        - GET: Renderiza formulario de registro (register_tutor.html)
        - POST exitoso: Redirige a 'tutor_dashboard'
        - POST con errores: Re-renderiza formulario con mensajes de error
    """
    if request.method == 'POST':
        form = TutorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Bienvenido! Tu cuenta de tutor ha sido creada exitosamente.')
            return redirect('tutor_dashboard')
    else:
        form = TutorRegistrationForm()

    return render(request, 'accounts/register_tutor.html', {'form': form})


def register_client(request):
    """
    Vista de registro para clientes/estudiantes - SOLO accesible desde Milagro.
    
    ⚠️ PROTECCIÓN CRÍTICA DE SEGURIDAD ⚠️
    Esta vista implementa validación geográfica estricta antes de permitir el registro.
    
    Flujo de seguridad:
    1. Para usuarios NO autenticados:
       a. Obtiene datos de geolocalización (check_geo_restriction)
       b. Verifica que ciudad sea exactamente 'Milagro' (case-insensitive)
       c. Si NO es Milagro:
          - Registra intento de acceso con nivel ERROR
          - Muestra mensaje de error explicativo
          - Redirige a 'tutor_landing' (opción alternativa)
          - BLOQUEA el registro
    
    2. Si la validación geográfica pasa:
       a. Muestra formulario de registro (ClientRegistrationForm)
       b. Valida datos del formulario
       c. Crea usuario con user_type='client' y perfil de cliente asociado
       d. Inicia sesión automáticamente
       e. Redirige directamente a 'client_dashboard'
    
    Seguridad adicional:
    - Logging completo de intentos de acceso no autorizados
    - Mensajes informativos sin exponer detalles del sistema
    - Redirección directa a dashboard específico (evita NoReverseMatch)
    - Sincronizado con URLs en accounts/urls.py
    
    Args:
        request: HttpRequest con datos de geolocalización en sesión/middleware
        
    Returns:
        - Usuarios fuera de Milagro: Redirige a 'tutor_landing' con mensaje de error
        - GET (Milagro): Renderiza formulario (register_client.html)
        - POST exitoso (Milagro): Redirige a 'client_dashboard'
        - POST con errores: Re-renderiza formulario con mensajes de error
    """
    from core.utils.geo import check_geo_restriction
    import logging

    logger = logging.getLogger(__name__)

    # PROTECCIÓN CRÍTICA: Solo usuarios de Milagro pueden registrarse como estudiantes
    if not request.user.is_authenticated:
        geo_data = check_geo_restriction(request)
        city = geo_data.get('city', 'Unknown')
        country = geo_data.get('country', 'Unknown')

        logger.warning(
            f"Student registration access attempt: city={city}, country={country}"
        )

        # Verificar que la ciudad sea exactamente Milagro (case-insensitive)
        if not (city and city.strip().lower() == 'milagro'):
            logger.error(
                f"SECURITY: Non-Milagro user tried to access student registration. "
                f"City={city}, Country={country}. Redirecting to tutor_landing."
            )
            messages.error(
                request,
                'El registro de estudiantes solo está disponible en Milagro. '
                'Como estás en otra ciudad de Ecuador, puedes registrarte como tutor.'
            )
            return redirect('tutor_landing')

    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Bienvenido! Tu cuenta ha sido creada exitosamente.')
            return redirect('client_dashboard')
    else:
        form = ClientRegistrationForm()

    return render(request, 'accounts/register_client.html', {'form': form})


class CustomLoginView(LoginView):
    """Custom login view - DEPRECATED, use StudentLoginView or TutorLoginView"""
    form_class = LoginForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        messages.success(self.request, f'¡Bienvenido de nuevo, {form.get_user().name}!')
        return super().form_valid(form)


class StudentLoginView(LoginView):
    """Login view for students - ONLY accessible from Milagro"""
    form_class = LoginForm
    template_name = 'accounts/login_student.html'

    def form_valid(self, form):
        user = form.get_user()
        # Verify user is actually a student
        if user.user_type != 'client':
            messages.error(self.request, 'Esta es la página de inicio de sesión para estudiantes. Por favor usa el login de tutores.')
            return redirect('tutor_login')
        messages.success(self.request, f'¡Bienvenido de nuevo, {user.name}!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('client_dashboard')


class TutorLoginView(LoginView):
    """Login view for tutors - Accessible from all Ecuador"""
    form_class = LoginForm
    template_name = 'accounts/login_tutor.html'

    def form_valid(self, form):
        user = form.get_user()
        # Verify user is actually a tutor
        if user.user_type != 'tutor':
            messages.error(self.request, 'Esta es la página de inicio de sesión para tutores. Por favor usa el login de estudiantes.')
            return redirect('student_login')
        messages.success(self.request, f'¡Bienvenido de nuevo, {user.name}!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tutor_dashboard')


@login_required
def dashboard(request):
    """Dashboard view - redirects to appropriate dashboard based on user type"""
    if request.user.user_type == 'tutor':
        return redirect('tutor_dashboard')
    else:
        return redirect('client_dashboard')


@login_required
def tutor_dashboard(request):
    """
    Dashboard for tutors - ONLY accessible to tutors.

    Displays session statistics and management interface for tutors.

    Context variables provided:
    - pending_sessions: Sessions awaiting tutor confirmation (status='pending')
    - upcoming_sessions: Next 5 confirmed sessions scheduled for future dates
    - all_active_sessions: ALL sessions with status 'pending' OR 'confirmed'
      (This represents SESSIONS OF CLASSES, not user login sessions)
    - pending_count: Number of pending session requests

    Note: "Total Sesiones Activas" in template = count of CLASS SESSIONS
    that are either waiting for confirmation or already confirmed.
    This does NOT track user login sessions.
    """
    from core.models import ClassSession
    from datetime import datetime

    # CRITICAL: Ensure only tutors can access this dashboard
    if request.user.user_type != 'tutor':
        messages.error(request, 'Acceso denegado. Esta sección es solo para tutores.')
        return redirect('client_dashboard')

    try:
        profile = request.user.tutor_profile
    except:
        profile = None

    # Get pending session requests (waiting for tutor to confirm/reject)
    pending_sessions = ClassSession.objects.filter(
        tutor=request.user,
        status='pending'
    ).order_by('scheduled_date', 'scheduled_time')

    # Get upcoming confirmed sessions (next 5 classes scheduled for future dates)
    upcoming_sessions = ClassSession.objects.filter(
        tutor=request.user,
        status='confirmed',
        scheduled_date__gte=datetime.now().date()
    ).order_by('scheduled_date', 'scheduled_time')[:5]

    # Get all active sessions (pending + confirmed)
    # IMPORTANT: This counts CLASS SESSIONS (tutoring sessions with students),
    # NOT user login sessions. Each item represents a scheduled or pending class.
    all_active_sessions = ClassSession.objects.filter(
        tutor=request.user,
        status__in=['pending', 'confirmed']
    ).order_by('scheduled_date', 'scheduled_time')

    context = {
        'user': request.user,
        'profile': profile,
        'pending_sessions': pending_sessions,
        'upcoming_sessions': upcoming_sessions,
        'all_active_sessions': all_active_sessions,
        'pending_count': pending_sessions.count(),
    }
    return render(request, 'accounts/tutor_dashboard.html', context)


@login_required
def client_dashboard(request):
    """Dashboard for clients/students - ONLY accessible to clients"""
    from core.models import ClassSession
    from datetime import datetime

    # CRITICAL: Ensure only clients can access this dashboard
    if request.user.user_type != 'client':
        messages.error(request, 'Acceso denegado. Esta sección es solo para estudiantes.')
        return redirect('tutor_dashboard')

    try:
        profile = request.user.client_profile
    except:
        profile = None

    # Get upcoming sessions (confirmed)
    upcoming_sessions = ClassSession.objects.filter(
        client=request.user,
        status='confirmed',
        scheduled_date__gte=datetime.now().date()
    ).order_by('scheduled_date', 'scheduled_time')

    # Get pending requests
    pending_sessions = ClassSession.objects.filter(
        client=request.user,
        status='pending'
    ).order_by('scheduled_date', 'scheduled_time')

    # Get past sessions
    past_sessions = ClassSession.objects.filter(
        client=request.user,
        status__in=['completed', 'cancelled']
    ).order_by('-scheduled_date', '-scheduled_time')[:5]

    context = {
        'user': request.user,
        'profile': profile,
        'upcoming_sessions': upcoming_sessions,
        'pending_sessions': pending_sessions,
        'past_sessions': past_sessions,
    }
    return render(request, 'accounts/client_dashboard.html', context)


@login_required
def manage_tutor_subjects(request):
    """
    Vista para gestión de materias del tutor.
    Solo accesible para usuarios con user_type='tutor'.
    """
    # CRITICAL: Ensure only tutors can access this view
    if request.user.user_type != 'tutor':
        messages.error(request, 'Acceso denegado. Esta sección es solo para tutores.')
        return redirect('client_dashboard')

    try:
        profile = request.user.tutor_profile
    except:
        messages.error(request, 'Error: No se encontró el perfil de tutor.')
        return redirect('tutor_dashboard')

    if request.method == 'POST':
        form = TutorSubjectsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                '¡Materias actualizadas exitosamente! Ahora los estudiantes podrán '
                'encontrarte cuando busquen tutores para estas materias.'
            )
            return redirect('tutor_dashboard')
        else:
            messages.error(
                request,
                'Hubo un error al actualizar las materias. Por favor verifica el formulario.'
            )
    else:
        form = TutorSubjectsForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        'user': request.user,
    }
    return render(request, 'accounts/manage_subjects.html', context)


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('landing')
