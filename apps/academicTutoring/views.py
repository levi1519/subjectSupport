from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.views.generic import View, TemplateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta

from .models import ClassSession, NotificacionExpansion, SessionMaterial, PlatformConfig
from .forms import SessionRequestForm, SessionConfirmationForm, NotificacionExpansionForm
from . import services as academic_services
from apps.accounts.models import User, TutorProfile, Notification, KnowledgeArea
from .services.meeting_service import update_session_with_meeting
from .utils import send_cancellation_email

from apps.accounts.mixins.roles import ClientRequiredMixin, TutorRequiredMixin
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)


@login_required
def mark_notification_read(request, notif_id):
    """Mark a notification as read via POST."""
    if request.method == 'POST':
        from django.utils import timezone as tz
        Notification.objects.filter(
            id=notif_id, recipient=request.user
        ).update(is_read=True, read_at=tz.now())
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
    if request.user.is_authenticated:
        if request.user.user_type == 'tutor':
            return redirect('tutor_dashboard')
        return redirect('client_dashboard')
    return render(request, 'landing/student_landing.html', {'user_type': 'Estudiante'})


def tutor_landing_view(request):
    """Landing page for tutors"""
    if request.user.is_authenticated:
        if request.user.user_type == 'tutor':
            return redirect('tutor_dashboard')
        return redirect('client_dashboard')
    return render(request, 'landing/tutor_landing.html', {'user_type': 'Tutor'})


class TutorSelectionView(ClientRequiredMixin, TemplateView):
    """
    View for clients to see and select tutors with geographical prioritization.
    Uses TutorProfileManager for optimized queries.
    """
    template_name = 'core/tutor_selection.html'
    
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

        search_query         = self.request.GET.get('search', '')
        province_filter      = self.request.GET.get('province', '').strip()
        city_filter          = self.request.GET.get('city', '').strip()
        knowledge_area_slug  = self.request.GET.get('knowledge_area', '')
        subject_filter       = self.request.GET.get('subject', '').strip()

        # Base queryset
        if city_filter:
            tutors_qs = TutorProfile.objects.get_tutors_fallback(
                active_codes=['EC']
            ).filter(city__icontains=city_filter)
        elif province_filter:
            tutors_qs = TutorProfile.objects.get_tutors_fallback(
                active_codes=['EC']
            ).filter(country__icontains='Ecuador')
        elif client_country:
            tutors_qs = TutorProfile.objects.get_tutors_by_country_priority(
                client_country, active_codes=active_codes
            )
        else:
            tutors_qs = TutorProfile.objects.get_tutors_fallback(
                active_codes=active_codes
            )

        # Filtro por área
        if knowledge_area_slug:
            tutors_qs = TutorProfile.objects.get_tutors_by_knowledge_area(
                knowledge_area_slug, active_codes=active_codes
            )

        # Filtro por materia específica
        if subject_filter:
            tutors_qs = tutors_qs.filter(
                subjects_taught__name__icontains=subject_filter
            ).distinct()

        # Filtro por búsqueda libre
        tutors_qs = TutorProfile.objects.filter_by_search(tutors_qs, search_query)

        # REGLA DE NEGOCIO: tutor visible SOLO si tiene tarifa Y materias configuradas
        tutors_qs = tutors_qs.filter(
            hourly_rate__isnull=False,
            hourly_rate__gt=0,
        ).exclude(subjects_taught=None)
        from django.db.models import Count
        tutors_qs = tutors_qs.annotate(
            num_subjects=Count('subjects_taught')
        ).filter(num_subjects__gt=0)

        # D14-A: Paginación
        paginator = Paginator(tutors_qs, 12)
        page_number = self.request.GET.get('page', 1)
        try:
            page_obj = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.page(1)

        context.update({
            'tutors':            page_obj,
            'paginator':         paginator,
            'page_obj':          page_obj,
            'is_paginated':      paginator.num_pages > 1,
            'client_country':    client_country,
            'search_query':      search_query,
            'province_filter':   province_filter,
            'city_filter':       city_filter,
            'knowledge_area_filter': knowledge_area_slug,
            'subject_filter':    subject_filter,
            'countries':         CountryConfig.objects.filter(active=True).order_by('country_name'),
            'knowledge_areas':   KnowledgeArea.objects.prefetch_related('subjects').all().order_by('name'),
            'ecuador_provinces': [
                ('Azuay', ['Cuenca', 'Gualaceo', 'Paute']),
                ('Bolívar', ['Guaranda', 'Chillanes']),
                ('Cañar', ['Azogues', 'Cañar', 'La Troncal']),
                ('Carchi', ['Tulcán', 'Montúfar']),
                ('Chimborazo', ['Riobamba', 'Alausí', 'Guano']),
                ('Cotopaxi', ['Latacunga', 'La Maná', 'Salcedo']),
                ('El Oro', ['Machala', 'Pasaje', 'Santa Rosa', 'Huaquillas']),
                ('Esmeraldas', ['Esmeraldas', 'Atacames', 'Quinindé']),
                ('Galápagos', ['Puerto Ayora', 'Puerto Baquerizo Moreno']),
                ('Guayas', ['Guayaquil', 'Milagro', 'Durán', 'Samborondón', 'Daule', 'El Triunfo', 'Naranjito', 'Yaguachi']),
                ('Imbabura', ['Ibarra', 'Otavalo', 'Cotacachi']),
                ('Loja', ['Loja', 'Catamayo', 'Cariamanga']),
                ('Los Ríos', ['Babahoyo', 'Quevedo', 'Ventanas', 'Vinces']),
                ('Manabí', ['Portoviejo', 'Manta', 'Chone', 'Jipijapa', 'Pedernales']),
                ('Morona Santiago', ['Macas', 'Gualaquiza']),
                ('Napo', ['Tena', 'Archidona']),
                ('Orellana', ['Francisco de Orellana', 'Loreto']),
                ('Pastaza', ['Puyo', 'Mera']),
                ('Pichincha', ['Quito', 'Cayambe', 'Rumiñahui', 'Mejía']),
                ('Santa Elena', ['Santa Elena', 'Salinas', 'La Libertad']),
                ('Santo Domingo de los Tsáchilas', ['Santo Domingo']),
                ('Sucumbíos', ['Nueva Loja', 'Shushufindi']),
                ('Tungurahua', ['Ambato', 'Baños', 'Pelileo']),
                ('Zamora Chinchipe', ['Zamora', 'Yantzaza']),
            ],
        })

        return context


class RequestSessionView(ClientRequiredMixin, FormView):
    """
    View for clients to request a new session with a specific tutor.
    Uses SessionService for business logic.
    """
    template_name = 'core/request_session.html'
    form_class = SessionRequestForm
    
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
        from .forms import SessionMaterialForm
        from .models import PlatformConfig
        config = PlatformConfig.get_config()
        context.update({
            'tutor': self.tutor,
            'tutor_profile': getattr(self.tutor, 'tutor_profile', None),
            'tutor_subjects': getattr(self.tutor, 'tutor_profile', None).subjects_taught.all() if getattr(self.tutor, 'tutor_profile', None) else [],
            'material_form': SessionMaterialForm(),
            'config': config,
        })
        return context
    
    def get_form_kwargs(self):
        """Pre-fill form with tutor selection"""
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'tutor': self.tutor}
        return kwargs
    
    def form_valid(self, form):
        """Use academic_services to create session"""
        from .models import PlatformConfig
        config = PlatformConfig.get_config()
        if config:
            if config.require_session_material_url:
                if not self.request.POST.get('material_url', '').strip():
                    form.add_error('material_url', 'La URL del material es obligatoria.')
                    return self.form_invalid(form)
            if config.require_session_material_file:
                if not self.request.FILES.get('material_file'):
                    messages.error(self.request, 'Debes subir un archivo de material para solicitar la clase.')
                    return self.form_invalid(form)

        success, session, error = academic_services.create_session(
            self.tutor,
            self.request.user,
            form  # ← form object, NOT form.cleaned_data
        )
        
        if not success:
            messages.error(self.request, f'Error al crear sesion: {error}')
            return self.form_invalid(form)

        # Guardar materiales adjuntos
        from .models import SessionMaterial
        material_count = 0

        url = self.request.POST.get('material_url', '').strip()
        if url:
            SessionMaterial.objects.create(
                session=session,
                type='url',
                url=url,
                uploaded_by=self.request.user
            )
            material_count += 1

        material_file = self.request.FILES.get('material_file')
        if material_file and material_count < config.max_session_materials:
            SessionMaterial.objects.create(
                session=session,
                type='file',
                file=material_file,
                filename=material_file.name,
                uploaded_by=self.request.user
            )

        messages.success(
            self.request,
            f'Solicitud enviada! El tutor {session.tutor.name} revisara tu solicitud pronto.'
        )
        return redirect('client_dashboard')


class ConfirmSessionView(TutorRequiredMixin, FormView):
    """
    View for tutors to confirm a session.
    Uses SessionService for business logic.
    """
    template_name = 'core/confirm_session.html'
    form_class = SessionConfirmationForm
    
    def dispatch(self, request, *args, **kwargs):
        """Get session and validate status and ownership"""
        self.session = get_object_or_404(ClassSession, id=kwargs['session_id'])
        
        # NUEVA VALIDACION DE PROPIEDAD
        if request.user != self.session.tutor:
            raise PermissionDenied("No tienes permiso para confirmar esta sesion.")
            
        if self.session.status != 'pending':
            messages.warning(request, 'Esta sesion ya ha sido procesada.')
            return redirect('tutor_dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .forms import SessionMaterialForm
        from .models import SessionMaterial
        context['session'] = self.session
        context['material_form'] = SessionMaterialForm()
        context['existing_materials'] = SessionMaterial.objects.filter(session=self.session)
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
        
        if not success:
            messages.error(self.request, f'Error al confirmar sesion: {error}')
            return self.form_invalid(form)

        # Guardar materiales del tutor
        from .models import SessionMaterial, PlatformConfig
        config = PlatformConfig.get_config()
        existing_count = SessionMaterial.objects.filter(session=session).count()

        url = self.request.POST.get('material_url', '').strip()
        if url and existing_count < config.max_session_materials:
            SessionMaterial.objects.create(
                session=session,
                type='url',
                url=url,
                uploaded_by=self.request.user
            )
            existing_count += 1

        material_file = self.request.FILES.get('material_file')
        if material_file and existing_count < config.max_session_materials:
            SessionMaterial.objects.create(
                session=session,
                type='file',
                file=material_file,
                filename=material_file.name,
                uploaded_by=self.request.user
            )

        # Show platform-specific success message
        platform_name = session.get_meeting_platform_display()
        messages.success(
            self.request,
            f'Sesion confirmada! Se ha generado el enlace de {platform_name}.'
        )
        return redirect('tutor_dashboard')


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
        
        # Obtener motivo de cancelación
        cancellation_reason = request.POST.get('cancellation_reason', '').strip()

        success, session, error = academic_services.cancel_session(
            self.session,
            request.user
        )

        if success:
            # Guardar motivo de cancelación si se proporcionó
            if cancellation_reason:
                session.cancellation_reason = cancellation_reason
                session.save(update_fields=['cancellation_reason'])
            
            # Enviar email SOLO si la sesión NO estaba ya cancelada (idempotencia)
            if prev_status != 'cancelled':
                # Determinar contraparte: quien NO canceló recibe el email
                if request.user == session.tutor:
                    recipient = session.client
                else:
                    recipient = session.tutor
                send_cancellation_email(session, request.user, recipient)
                _reason_text = f' Motivo: {cancellation_reason}' if cancellation_reason else ''
                notification_message = (f'{request.user.name} canceló la clase de {session.subject} '
                                      f'del {session.scheduled_date.strftime("%d/%m/%Y")} a las '
                                      f'{session.scheduled_time.strftime("%H:%M")}.{_reason_text}')
                Notification.objects.create(
                    recipient=recipient,
                    message=notification_message
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


class CompleteSessionView(TutorRequiredMixin, View):
    """Mark a confirmed session as completed. Tutor only."""

    # AGREGADO: Validacion de propiedad en dispatch
    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(ClassSession, id=self.kwargs['session_id'])
        if request.user != self.session.tutor:
            raise PermissionDenied("No tienes permiso para completar esta sesion.")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        session = self.session
        if session.status != 'confirmed':
            messages.warning(request, 'Solo puedes completar sesiones confirmadas.')
            return redirect('tutor_dashboard')
        session.status = 'completed'
        session.save()
        messages.success(request, f'Sesión de {session.subject} marcada como completada.')
        return redirect('tutor_dashboard')


class UpdateMeetingUrlView(TutorRequiredMixin, View):
    """Allow tutor to update meeting_url of a confirmed session."""

    # AGREGADO: Validacion de propiedad en dispatch
    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(ClassSession, id=self.kwargs['session_id'])
        if request.user != self.session.tutor:
            raise PermissionDenied("No puedes actualizar el enlace de esta sesion.")
        return super().dispatch(request, *args, **kwargs)

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
        if getattr(self.request.user, 'user_type', '') == 'tutor':
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


from django.http import JsonResponse
from .models import Institution, SessionMaterial

def institution_search_api(request):
    """API endpoint para búsqueda de instituciones vía autocomplete."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    institutions = Institution.objects.filter(
        name__icontains=q,
        active=True
    ).values('id', 'name', 'type', 'city', 'province')[:10]
    return JsonResponse({'results': list(institutions)})


class TutorSessionHistoryView(TutorRequiredMixin, TemplateView):
    template_name = 'core/tutor_session_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = PlatformConfig.get_config()
        archive_cutoff = timezone.now() - timedelta(
            days=config.session_archive_days
        )

        # Auto-archive old completed sessions
        ClassSession.objects.filter(
            tutor=self.request.user,
            status__in=['completed', 'cancelled'],
            is_archived=False,
            updated_at__lt=archive_cutoff
        ).update(is_archived=True, archived_at=timezone.now())

        # Auto-archivo cuando las 3 condiciones de comisión están cumplidas
        from apps.academicTutoring.models import SessionMaterial as SM
        completed_all = ClassSession.objects.filter(
            tutor=self.request.user,
            status='completed',
            is_archived=False
        )
        for sess in completed_all:
            has_recording = bool(sess.recording_url)
            has_approved_sim = sess.simulators.filter(status='approved').exists()
            has_pdf = SM.objects.filter(session=sess, file__iendswith='.pdf').exists()
            if has_recording and has_approved_sim and has_pdf:
                sess.is_archived = True
                sess.archived_at = timezone.now()
                sess.save(update_fields=['is_archived', 'archived_at'])

        completed = ClassSession.objects.filter(
            tutor=self.request.user,
            status='completed',
            is_archived=False
        ).select_related('client').prefetch_related(
            'materials', 'simulators'
        ).order_by('-scheduled_date')

        cancelled = ClassSession.objects.filter(
            tutor=self.request.user,
            status='cancelled',
            is_archived=False
        ).select_related('client').order_by('-scheduled_date')

        # Simulators pending tutor approval
        from apps.simulators.models import Simulator
        pending_simulators = Simulator.objects.filter(
            tutor=self.request.user,
            status='pending_approval'
        ).select_related('student', 'session').order_by('-created_at')

        # Annotate simulator status per completed session
        for session in completed:
            session.pending_sim = session.simulators.filter(
                status='pending_approval'
            ).first()
            session.approved_sim = session.simulators.filter(
                status='approved'
            ).first()
            session.has_any_sim = session.simulators.exists()
            session.sim_generating = session.simulators.filter(
                generation_status='generating'
            ).exists()
            session.has_pdf = SM.objects.filter(
                session=session, file__iendswith='.pdf'
            ).exists()

        context['completed_sessions'] = completed
        context['cancelled_sessions'] = cancelled
        context['pending_simulators'] = pending_simulators
        context['archive_days'] = config.session_archive_days
        return context


class TutorUploadRecordingView(TutorRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        self.session = get_object_or_404(
            ClassSession,
            pk=kwargs['session_id'],
            tutor=request.user,
            status='completed'
        )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, session_id):
        config = PlatformConfig.get_config()
        recording_url = request.POST.get('recording_url', '').strip()
        now = timezone.now()

        if recording_url:
            self.session.recording_url = recording_url
            self.session.video_uploaded_at = now
            self.session.video_expires_at = now + timedelta(
                days=config.video_retention_days
            )
            self.session.save(update_fields=[
                'recording_url', 'video_uploaded_at', 'video_expires_at'
            ])
            Notification.objects.create(
                recipient=self.session.client,
                message=(
                    f'Tu tutor {self.session.tutor.name} subió el video de la sesión '
                    f'"{self.session.subject}". Disponible para descarga durante '
                    f'{config.video_retention_days} días (hasta '
                    f'{self.session.video_expires_at.strftime("%d/%m/%Y")}).'
                )
            )
            messages.success(request,
                f'Video registrado. El estudiante tiene '
                f'{config.video_retention_days} días para descargarlo.')
        else:
            messages.error(request, 'Ingresa una URL válida para el video.')

        # Also handle additional material upload
        material_url = request.POST.get('material_url', '').strip()
        material_file = request.FILES.get('material_file')
        existing_count = SessionMaterial.objects.filter(
            session=self.session).count()

        if material_url and existing_count < config.max_session_materials:
            SessionMaterial.objects.create(
                session=self.session,
                type='url',
                url=material_url,
                uploaded_by=request.user
            )
            messages.success(request, 'Material adicional agregado.')

        # VALIDACIÓN PDF RATIO — antes de crear SessionMaterial para archivos
        if material_file:
            # 1. Límite máximo de archivos
            if existing_count >= config.max_session_materials:
                messages.error(request,
                    f'Límite de {config.max_session_materials} materiales alcanzado.')
                return redirect('tutor_session_history')

            # 2. Validar extensión
            import os
            ext = os.path.splitext(material_file.name)[1].lower()
            allowed_all = [f'.{e.strip()}' for e in config.allowed_file_types.split(',')]
            if ext not in allowed_all:
                messages.error(request, f'Formato no permitido. Use: {config.allowed_file_types}')
                return redirect('tutor_session_history')

            # 3. Validar ratio de PDFs tras subir
            existing_pdfs = SessionMaterial.objects.filter(
                session=self.session,
                file__endswith='.pdf'
            ).count()
            new_total = existing_count + 1
            new_pdfs  = existing_pdfs + (1 if ext == '.pdf' else 0)
            required_pdfs = max(1, int(new_total * config.min_pdf_materials_ratio))

            # Solo advertir si el material actual ya supera 2 archivos y no hay PDFs
            if new_total > 2 and new_pdfs == 0:
                messages.warning(request,
                    f'Recuerda: al menos {required_pdfs} de tus materiales debe(n) ser PDF '
                    f'para que DeepSeek pueda generar un simulacro de calidad.')
            # (no bloquear — solo advertir; el bloqueo real está en SimulatorGenerateView)

            from apps.accounts.services import sanitize_filename
            material_file.name = sanitize_filename(material_file.name)
            SessionMaterial.objects.create(
                session=self.session,
                type='file',
                file=material_file,
                filename=material_file.name,
                uploaded_by=request.user
            )
            messages.success(request, 'Archivo adicional agregado.')

        return redirect('tutor_session_history')

    def get(self, request, session_id):
        return redirect('tutor_session_history')


class SimulatorApproveView(TutorRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        from apps.simulators.models import Simulator
        self.simulator = get_object_or_404(
            Simulator,
            pk=kwargs['pk'],
            tutor=request.user,
            status='pending_approval'
        )
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk):
        from apps.simulators.models import Simulator
        action = request.POST.get('action')  # 'approve' or 'reject'
        feedback = request.POST.get('feedback', '').strip()
        now = timezone.now()

        if action == 'approve':
            self.simulator.status = 'approved'
            self.simulator.tutor_reviewed_at = now
            self.simulator.tutor_feedback = feedback or None
            self.simulator.save(update_fields=[
                'status', 'tutor_reviewed_at', 'tutor_feedback'
            ])
            Notification.objects.create(
                recipient=self.simulator.student,
                message=(
                    f'Tu simulacro "{self.simulator.title}" fue aprobado '
                    f'por {self.simulator.tutor.name}. ¡Ya puedes hacerlo!'
                )
            )
            messages.success(request, 'Simulacro aprobado.')

        elif action == 'reject':
            self.simulator.status = 'rejected'
            self.simulator.tutor_reviewed_at = now
            self.simulator.tutor_feedback = feedback
            self.simulator.save(update_fields=[
                'status', 'tutor_reviewed_at', 'tutor_feedback'
            ])
            Notification.objects.create(
                recipient=self.simulator.student,
                message=(
                    f'Tu simulacro "{self.simulator.title}" fue rechazado '
                    f'por {self.simulator.tutor.name}. '
                    f'Tu tutor generará uno nuevo cuando esté disponible.'
                    + (f' Motivo: {feedback}' if feedback else '')
                )
            )
            messages.warning(request, 'Simulacro rechazado. El tutor generará uno nuevo cuando esté listo.')
        else:
            messages.error(request, 'Acción inválida.')

        return redirect('tutor_session_history')

    def get(self, request, pk):
        return redirect('tutor_session_history')


class RateSessionView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Both tutor and student can rate a completed session.
    One rating per user per session — cannot re-rate.
    """

    def test_func(self):
        self.session = get_object_or_404(
            ClassSession,
            pk=self.kwargs['session_id'],
            status='completed'
        )
        user = self.request.user
        return (
            user == self.session.tutor or
            user == self.session.client
        )

    def post(self, request, session_id):
        rating_str = request.POST.get('rating', '')
        comment = request.POST.get('comment', '').strip()

        try:
            rating = int(rating_str)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            messages.error(request, 'Calificación inválida. Selecciona entre 1 y 5 estrellas.')
            return redirect(self.get_redirect_url())

        now = timezone.now()

        if request.user == self.session.client:
            if self.session.student_rating is not None:
                messages.warning(request, 'Ya calificaste esta sesión.')
                return redirect(self.get_redirect_url())
            self.session.student_rating = rating
            self.session.student_rating_comment = comment
            self.session.student_rated_at = now
            self.session.save(update_fields=[
                'student_rating', 'student_rating_comment',
                'student_rated_at'
            ])
            messages.success(request,
                f'Calificaste la sesión con {rating} ★.')

        elif request.user == self.session.tutor:
            if self.session.tutor_rating is not None:
                messages.warning(request, 'Ya calificaste esta sesión.')
                return redirect(self.get_redirect_url())
            self.session.tutor_rating = rating
            self.session.tutor_rating_comment = comment
            self.session.tutor_rated_at = now
            self.session.save(update_fields=[
                'tutor_rating', 'tutor_rating_comment',
                'tutor_rated_at'
            ])
            messages.success(request,
                f'Calificaste al estudiante con {rating} ★.')

        return redirect(self.get_redirect_url())

    def get_redirect_url(self):
        if self.request.user.user_type == 'tutor':
            return reverse('tutor_session_history')
        return reverse('client_dashboard')

    def get(self, request, session_id):
        return redirect(self.get_redirect_url())