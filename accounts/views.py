from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from .forms import TutorRegistrationForm, ClientRegistrationForm, LoginForm


def register_tutor(request):
    """Registration view for tutors"""
    if request.method == 'POST':
        form = TutorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Bienvenido! Tu cuenta de tutor ha sido creada exitosamente.')
            return redirect('dashboard')
    else:
        form = TutorRegistrationForm()

    return render(request, 'accounts/register_tutor.html', {'form': form})


def register_client(request):
    """Registration view for clients/students"""
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '¡Bienvenido! Tu cuenta ha sido creada exitosamente.')
            return redirect('dashboard')
    else:
        form = ClientRegistrationForm()

    return render(request, 'accounts/register_client.html', {'form': form})


class CustomLoginView(LoginView):
    """Custom login view"""
    form_class = LoginForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        messages.success(self.request, f'¡Bienvenido de nuevo, {form.get_user().name}!')
        return super().form_valid(form)


@login_required
def dashboard(request):
    """Dashboard view - redirects to appropriate dashboard based on user type"""
    if request.user.user_type == 'tutor':
        return redirect('tutor_dashboard')
    else:
        return redirect('client_dashboard')


@login_required
def tutor_dashboard(request):
    """Dashboard for tutors - ONLY accessible to tutors"""
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

    # Get pending session requests
    pending_sessions = ClassSession.objects.filter(
        tutor=request.user,
        status='pending'
    ).order_by('scheduled_date', 'scheduled_time')

    # Get upcoming confirmed sessions
    upcoming_sessions = ClassSession.objects.filter(
        tutor=request.user,
        status='confirmed',
        scheduled_date__gte=datetime.now().date()
    ).order_by('scheduled_date', 'scheduled_time')[:5]

    # Get all active sessions (pending + confirmed)
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


def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'Has cerrado sesión exitosamente.')
    return redirect('landing')
