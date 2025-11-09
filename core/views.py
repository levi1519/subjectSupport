from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import ClassSession
from .forms import SessionRequestForm, SessionConfirmationForm
from accounts.models import User, TutorProfile
from .services.meeting_service import update_session_with_meeting


def landing_page(request):
    """Landing page with registration options"""
    return render(request, 'core/landing.html')


@login_required
def tutor_selection(request):
    """View for clients to see and select tutors with geographical prioritization"""
    if request.user.user_type != 'client':
        messages.error(request, 'Solo los clientes pueden ver la lista de tutores.')
        return redirect('dashboard')

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
        return redirect('dashboard')

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
        return redirect('dashboard')

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
    """View to cancel a session"""
    session = get_object_or_404(ClassSession, id=session_id)

    # Check if user is either the tutor or client for this session
    if request.user != session.tutor and request.user != session.client:
        messages.error(request, 'No tienes permiso para cancelar esta sesión.')
        return redirect('dashboard')

    if session.status == 'cancelled':
        messages.warning(request, 'Esta sesión ya está cancelada.')
        return redirect('dashboard')

    if session.status == 'completed':
        messages.warning(request, 'No puedes cancelar una sesión completada.')
        return redirect('dashboard')

    if request.method == 'POST':
        session.status = 'cancelled'
        session.save()
        messages.info(request, 'La sesión ha sido cancelada.')
        return redirect('dashboard')

    return render(request, 'core/cancel_session.html', {'session': session})


@login_required
def meeting_room(request, session_id):
    """View for accessing the meeting room for a session"""
    session = get_object_or_404(ClassSession, id=session_id)

    # Check if user is either the tutor or client for this session
    if request.user != session.tutor and request.user != session.client:
        messages.error(request, 'No tienes permiso para acceder a esta reunión.')
        return redirect('dashboard')

    # Check if session is confirmed
    if session.status != 'confirmed':
        messages.warning(request, 'Esta sesión aún no ha sido confirmada.')
        return redirect('dashboard')

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
