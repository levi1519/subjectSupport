from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.views.generic import TemplateView, FormView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from .forms import (
    TutorRegistrationForm, 
    ClientRegistrationForm, 
    LoginForm, 
    TutorSubjectsForm, 
    ClientProfileEditForm, 
    TutorProfileEditForm
)
from .models import TutorProfile, ClientProfile, Notification
from . import services


class RegisterChoiceView(TemplateView):
    """Generic registration view that allows users to choose their type."""
    template_name = 'accounts/register_choice.html'


class RegisterTutorView(FormView):
    """Registration view for tutors"""
    template_name = 'accounts/register_tutor.html'
    form_class = TutorRegistrationForm

    def form_valid(self, form):
        # DEBUG: print(f"DEBUG TUTOR: Form validado OK. Datos: {form.cleaned_data.get('email')}")
        from apps.academicTutoring.models import PlatformConfig
        config = PlatformConfig.get_config()

        # Validar documento genérico (CV o credencial)
        if config.require_tutor_document and not form.cleaned_data.get('document_file'):
            form.add_error('document_file', 'Debes subir un documento (CV o credencial) para registrarte como tutor.')
            return self.form_invalid(form)

        # Validar documento de conocimiento académico
        if config.require_tutor_knowledge_document and not form.cleaned_data.get('document_file'):
            form.add_error('document_file', 'Debes subir tu CV, título o certificados que validen tu conocimiento.')
            return self.form_invalid(form)

        # Validar credencial institucional si declaró universidad
        university_name = form.cleaned_data.get('university_name', '').strip()
        if university_name and not form.cleaned_data.get('institutional_credential_file'):
            form.add_error('institutional_credential_file', 'Si perteneces a una institución, debes subir tu carnet o ID institucional.')
            return self.form_invalid(form)
        country_code = self.request.geo_data.get('country_code', '') if hasattr(self.request, 'geo_data') else ''
        success, user, error = services.register_tutor(self.request, form, country_code)
        if success:
            from apps.academicTutoring.models import PlatformConfig
            config = PlatformConfig.get_config()
            if config.require_tutor_document:
                messages.info(
                    self.request,
                    '¡Registro exitoso! Tu cuenta está pendiente de revisión. '
                    'Te notificaremos por correo cuando sea aprobada. '
                    'Mientras tanto no podrás iniciar sesión.'
                )
                from django.contrib.auth import logout as auth_logout
                auth_logout(self.request)
                return redirect('tutor_login')
            messages.success(self.request, '¡Bienvenido! Tu cuenta de tutor ha sido creada exitosamente.')
            return redirect('tutor_dashboard')
        # DEBUG: print(f"DEBUG TUTOR: Error en services.register_tutor: {error}")
        messages.error(self.request, error)
        return self.form_invalid(form)
    
    def form_invalid(self, form):
        # DEBUG: print(f"DEBUG TUTOR: Form INVÁLIDO. Errores: {form.errors.as_json()}")
        return super().form_invalid(form)


class RegisterClientView(FormView):
    """Registration view for clients/students"""
    template_name = 'accounts/register_client.html'
    form_class = ClientRegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('client_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.academicTutoring.models import PlatformConfig
        config = PlatformConfig.get_config()
        context['enable_minor_accounts'] = config.enable_minor_accounts
        return context

    def form_valid(self, form):
        # DEBUG: print(f"DEBUG CLIENT: Form validado OK. Datos: {form.cleaned_data.get('email')}")
        from apps.academicTutoring.models import PlatformConfig
        config = PlatformConfig.get_config()
        if config.require_student_document and not form.cleaned_data.get('document_file'):
            form.add_error('document_file', 'Debes subir un documento institucional para registrarte.')
            return self.form_invalid(form)
        country_code = self.request.geo_data.get('country_code', '') if hasattr(self.request, 'geo_data') else ''
        success, user, error = services.register_client(self.request, form, country_code)
        if success:
            # DEBUG: print(f"DEBUG CLIENT: Usuario creado exitosamente, redirigiendo a client_dashboard...")
            messages.success(self.request, '¡Bienvenido! Tu cuenta ha sido creada exitosamente.')
            return redirect('client_dashboard')
        # DEBUG: print(f"DEBUG CLIENT: Error en services.register_client: {error}")
        messages.error(self.request, error)
        return self.form_invalid(form)
    
    def form_invalid(self, form):
        # DEBUG: print(f"DEBUG CLIENT: Form INVÁLIDO. Errores: {form.errors.as_json()}")
        return super().form_invalid(form)


class CustomLoginView(LoginView):
    """Custom login view - DEPRECATED, use StudentLoginView or TutorLoginView"""
    form_class = LoginForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        messages.success(self.request, f'¡Bienvenido de nuevo, {form.get_user().name}!')
        return super().form_valid(form)
    
    def get_success_url(self):
        """Redirect based on user role - Admin/Staff go to /admin/"""
        user = self.request.user
        
        # P1.1 FIX: Superusers and staff go to admin panel
        if user.is_superuser or user.is_staff:
            return '/admin/'
        
        # Regular users go to their role-specific dashboard
        if user.user_type == 'tutor':
            return reverse('tutor_dashboard')
        else:
            return reverse('client_dashboard')


class StudentLoginView(LoginView):
    """Login view for students"""
    form_class = LoginForm
    template_name = 'accounts/login_student.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.user_type == 'tutor':
                return redirect('tutor_dashboard')
            return redirect('client_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        # Verify user is actually a student
        if user.user_type != 'client':
            form.add_error(None, 'Credenciales incorrectas.')
            return self.form_invalid(form)
        from apps.academicTutoring.models import PlatformConfig
        config = PlatformConfig.get_config()
        if config.require_tutor_document:
            try:
                if not user.tutor_profile.is_approved:
                    form.add_error(None, 'Tu cuenta está pendiente de aprobación por el administrador. '
                                         'Recibirás una notificación cuando sea revisada.')
                    return self.form_invalid(form)
            except Exception:
                pass
        messages.success(self.request, f'¡Bienvenido de nuevo, {user.name}!')
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect based on user role - Admin/Staff go to /admin/"""
        user = self.request.user
        
        # P1.1 FIX: Superusers and staff go to admin panel
        if user.is_superuser or user.is_staff:
            return '/admin/'
        
        # Regular client users go to their dashboard
        return reverse('client_dashboard')


class TutorLoginView(LoginView):
    """Login view for tutors"""
    form_class = LoginForm
    template_name = 'accounts/login_tutor.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.user_type == 'tutor':
                return redirect('tutor_dashboard')
            return redirect('client_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        # Verify user is actually a tutor
        if user.user_type != 'tutor':
            form.add_error(None, 'Credenciales incorrectas.')
            return self.form_invalid(form)
        messages.success(self.request, f'¡Bienvenido de nuevo, {user.name}!')
        return super().form_valid(form)

    def get_success_url(self):
        """
        RFC-FLOW-TUTOR: TutorLoginView always redirects to tutor_dashboard.
        This applies to ALL tutors, regardless of is_staff or is_superuser status.
        Admin users who are also tutors should access /admin/ via separate admin login.
        """
        return reverse('tutor_dashboard')


class DashboardView(LoginRequiredMixin, View):
    """Dashboard view - redirects to appropriate dashboard based on user type"""
    
    def get(self, request):
        # P1.1 & P1.2 FIX: Superusers/staff go to admin, regular users to their dashboard
        if request.user.is_superuser or request.user.is_staff:
            return redirect('/admin/')
        
        if request.user.user_type == 'tutor':
            return redirect('tutor_dashboard')
        else:
            return redirect('client_dashboard')


class TutorDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Dashboard for tutors - ONLY accessible to tutors.
    Uses ClassSessionManager for optimized queries.
    """
    template_name = 'accounts/tutor_dashboard.html'
    
    def test_func(self):
        """Only tutors can access this dashboard"""
        return self.request.user.user_type == 'tutor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone as tz
        from datetime import timedelta
        # RF-011-B: eliminar notificaciones leídas hace más de 24h
        Notification.objects.filter(
            recipient=self.request.user,
            is_read=True,
            read_at__lt=tz.now() - timedelta(hours=24)
        ).delete()
        from apps.academicTutoring.models import ClassSession
        context['pending_sessions'] = ClassSession.objects.get_tutor_sessions(
            self.request.user, status='pending'
        )
        context['upcoming_sessions'] = ClassSession.objects.get_tutor_sessions(
            self.request.user, status='confirmed'
        )
        cutoff = timezone.now() - timedelta(hours=24)
        context['past_sessions'] = ClassSession.objects.get_tutor_sessions(
            self.request.user, status='completed'
        ).filter(updated_at__gte=cutoff) if hasattr(ClassSession, 'updated_at') else ClassSession.objects.get_tutor_sessions(
            self.request.user, status='completed'
        ).filter(created_at__gte=cutoff)
        try:
            context['profile'] = TutorProfile.objects.get_profile_for_user(
                self.request.user
            )
        except TutorProfile.DoesNotExist:
            context['profile'] = None
        context['notifications'] = Notification.objects.filter(
            recipient=self.request.user, is_read=False
        )
        context['pending_count'] = context['pending_sessions'].count()
        context['all_active_sessions'] = list(context['pending_sessions']) + list(context['upcoming_sessions'])
        try:
            profile = context.get('profile')
            if profile and not profile.welcome_shown:
                context['show_welcome'] = True
                profile.welcome_shown = True
                profile.save(update_fields=['welcome_shown'])
        except Exception:
            pass
        return context


class ClientDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Dashboard for clients/students - ONLY accessible to clients.
    Uses ClassSessionManager for optimized queries.
    """
    template_name = 'accounts/client_dashboard.html'
    
    def test_func(self):
        """Only clients can access this dashboard"""
        return self.request.user.user_type == 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone as tz
        from datetime import timedelta
        # RF-011-B: eliminar notificaciones leídas hace más de 24h
        Notification.objects.filter(
            recipient=self.request.user,
            is_read=True,
            read_at__lt=tz.now() - timedelta(hours=24)
        ).delete()
        from apps.academicTutoring.models import ClassSession
        context['upcoming_sessions'] = ClassSession.objects.get_client_sessions(
            self.request.user, status='confirmed'
        )
        context['pending_sessions'] = ClassSession.objects.get_client_sessions(
            self.request.user, status='pending'
        )
        cutoff = timezone.now() - timedelta(hours=24)
        context['past_sessions'] = ClassSession.objects.get_client_sessions(
            self.request.user, status='completed'
        ).filter(updated_at__gte=cutoff) if hasattr(ClassSession, 'updated_at') else ClassSession.objects.get_client_sessions(
            self.request.user, status='completed'
        ).filter(created_at__gte=cutoff)
        try:
            context['profile'] = ClientProfile.objects.get_profile_for_user(
                self.request.user
            )
        except ClientProfile.DoesNotExist:
            context['profile'] = None
        context['notifications'] = Notification.objects.filter(
            recipient=self.request.user, is_read=False
        )
        return context


class ManageTutorSubjectsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    Vista para gestión de materias del tutor.
    Uses ProfileService for business logic.
    """
    template_name = 'accounts/manage_subjects.html'
    form_class = TutorSubjectsForm
    success_url = '/accounts/tutor/dashboard/'  # Will be overridden in form_valid
    
    def test_func(self):
        """Only tutors can access this view"""
        return self.request.user.user_type == 'tutor'
    
    def get_form_kwargs(self):
        """Pass profile instance to form"""
        kwargs = super().get_form_kwargs()
        profile, created = TutorProfile.objects.get_or_create_for_user(self.request.user)
        if created:
            messages.info(self.request, 'Tu perfil ha sido creado. Por favor completa tu información.')
        kwargs['instance'] = profile
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Subject
        subjects = Subject.objects.get_subjects_for_grouping()
        subjects_by_area = {}
        for subject in subjects:
            area_name = subject.knowledge_area.name if subject.knowledge_area else 'Sin área'
            subjects_by_area.setdefault(area_name, []).append(subject)
        context['subjects_by_area'] = subjects_by_area
        profile, _ = TutorProfile.objects.get_or_create_for_user(self.request.user)
        context['profile'] = profile
        context['editing'] = self.request.GET.get('edit') == '1' or self.request.method == 'POST'
        return context

    def form_valid(self, form):
        """Use services to manage tutor subjects"""
        success, _, error = services.manage_tutor_subjects(
            self.request.user,
            form
        )
        
        if success:
            messages.success(
                self.request,
                '¡Materias actualizadas exitosamente! Ahora los estudiantes podrán '
                'encontrarte cuando busquen tutores para estas materias.'
            )
            return redirect('manage_subjects')
        else:
            messages.error(
                self.request,
                f'Hubo un error al actualizar las materias: {error}'
            )
            return self.form_invalid(form)


class UserProfileView(LoginRequiredMixin, View):
    """
    Vista de perfil única que redirige al template apropiado según el tipo de usuario.
    """
    
    def get(self, request):
        if request.user.user_type == 'tutor':
            return redirect('tutor_profile')
        else:
            return redirect('client_profile')


class TutorProfileView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Vista de perfil para tutores con gestión de materias integrada.
    """
    template_name = 'accounts/tutor_profile.html'
    
    def test_func(self):
        """Only tutors can access this view"""
        return self.request.user.user_type == 'tutor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create profile if it doesn't exist (defensive logic)
        profile, created = TutorProfile.objects.get_or_create_for_user(self.request.user)
        if created:
            messages.info(self.request, 'Tu perfil ha sido creado. Por favor completa tu información.')
        
        context.update({
            'user': self.request.user,
            'profile': profile,
        })
        
        return context


class ClientProfileView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Vista de perfil para clientes/estudiantes.
    """
    template_name = 'accounts/client_profile.html'
    
    def test_func(self):
        """Only clients can access this view"""
        return self.request.user.user_type == 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create profile if it doesn't exist (defensive logic)
        profile, created = ClientProfile.objects.get_or_create_for_user(self.request.user)
        if created:
            messages.info(self.request, 'Tu perfil ha sido creado. Por favor completa tu información.')
        
        context.update({
            'user': self.request.user,
            'profile': profile,
        })
        
        return context


class EditClientProfileView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    Vista para editar el perfil del estudiante.
    Uses ProfileService for business logic.
    """
    template_name = 'accounts/edit_client_profile.html'
    form_class = ClientProfileEditForm
    
    def test_func(self):
        """Only clients can access this view"""
        return self.request.user.user_type == 'client'
    
    def get_form_kwargs(self):
        """Pass instance and user to form"""
        kwargs = super().get_form_kwargs()
        profile, created = ClientProfile.objects.get_or_create_for_user(self.request.user)
        if created:
            messages.info(self.request, 'Tu perfil ha sido creado. Por favor completa tu información.')
        kwargs['instance'] = profile
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.accounts.models import ClientProfile
        profile, _ = ClientProfile.objects.get_or_create_for_user(self.request.user)
        context['profile'] = profile
        return context

    def form_valid(self, form):
        """Use services to update client profile"""
        success, _, error = services.update_client_profile(
            self.request.user,
            form
        )
        
        if success:
            messages.success(self.request, '¡Perfil actualizado exitosamente!')
            return redirect('user_profile')
        else:
            messages.error(self.request, f'Error al actualizar perfil: {error}')
            return self.form_invalid(form)


class EditTutorProfileView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """
    Vista para editar el perfil del tutor.
    Uses ProfileService for business logic.
    """
    template_name = 'accounts/edit_tutor_profile.html'
    form_class = TutorProfileEditForm
    
    def test_func(self):
        """Only tutors can access this view"""
        return self.request.user.user_type == 'tutor'
    
    def get_form_kwargs(self):
        """Pass instance and user to form"""
        kwargs = super().get_form_kwargs()
        profile, created = TutorProfile.objects.get_or_create_for_user(self.request.user)
        if created:
            messages.info(self.request, 'Tu perfil ha sido creado. Por favor completa tu información.')
        kwargs['instance'] = profile
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = TutorProfile.objects.get_or_create_for_user(self.request.user)
        context['profile'] = profile
        return context

    def form_valid(self, form):
        """Use services to update tutor profile"""
        success, _, error = services.update_tutor_profile(
            self.request.user,
            form
        )
        
        if success:
            messages.success(self.request, '¡Perfil actualizado exitosamente!')
            return redirect('user_profile')
        else:
            messages.error(self.request, f'Error al actualizar perfil: {error}')
            return self.form_invalid(form)


class LogoutView(View):
    """
    RFC-FLOW-STUDENT-LOGOUT: Logout view that redirects based on user type.
    Must capture user_type BEFORE calling logout() to clear the session.
    """
    
    def get(self, request):
        # Capture user_type before logout clears the session
        user_type = None
        if request.user.is_authenticated:
            user_type = getattr(request.user, 'user_type', None)
        
        logout(request)
        messages.info(request, 'Has cerrado sesión exitosamente.')
        
        # Redirect based on user type captured before logout
        if user_type == 'client':
            return redirect('student_landing')
        elif user_type == 'tutor':
            return redirect('tutor_landing')
        else:
            # Admin, staff, or unauthenticated users go to home
            return redirect('home')
    
    def post(self, request):
        # Capture user_type before logout clears the session
        user_type = None
        if request.user.is_authenticated:
            user_type = getattr(request.user, 'user_type', None)
        
        logout(request)
        messages.info(request, 'Has cerrado sesión exitosamente.')
        
        # Redirect based on user type captured before logout
        if user_type == 'client':
            return redirect('student_landing')
        elif user_type == 'tutor':
            return redirect('tutor_landing')
        else:
            # Admin, staff, or unauthenticated users go to home
            return redirect('home')


# Backwards compatibility aliases
register_view = RegisterChoiceView.as_view()
register_tutor = RegisterTutorView.as_view()
register_client = RegisterClientView.as_view()
logout_view = LogoutView.as_view()
