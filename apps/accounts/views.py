from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.views.generic import TemplateView, FormView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction

from .forms import (
    TutorRegistrationForm, 
    ClientRegistrationForm, 
    LoginForm, 
    TutorSubjectsForm, 
    ClientProfileEditForm, 
    TutorProfileEditForm
)
from .models import TutorProfile, ClientProfile
from . import services


class RegisterChoiceView(TemplateView):
    """Generic registration view that allows users to choose their type."""
    template_name = 'accounts/register_choice.html'


class RegisterTutorView(FormView):
    """Registration view for tutors"""
    template_name = 'accounts/register_tutor.html'
    form_class = TutorRegistrationForm

    def form_valid(self, form):
        country_code = self.request.geo_data.get('country_code', '') if hasattr(self.request, 'geo_data') else ''
        success, user, error = services.register_tutor(self.request, form, country_code)
        if success:
            messages.success(self.request, '¡Bienvenido! Tu cuenta de tutor ha sido creada exitosamente.')
            return redirect('tutor_dashboard')
        messages.error(self.request, error)
        return self.form_invalid(form)


class RegisterClientView(FormView):
    """Registration view for clients/students"""
    template_name = 'accounts/register_client.html'
    form_class = ClientRegistrationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('client_dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        country_code = self.request.geo_data.get('country_code', '') if hasattr(self.request, 'geo_data') else ''
        success, user, error = services.register_client(self.request, form, country_code)
        if success:
            messages.success(self.request, '¡Bienvenido! Tu cuenta ha sido creada exitosamente.')
            return redirect('client_dashboard')
        messages.error(self.request, error)
        return self.form_invalid(form)


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

    def form_valid(self, form):
        user = form.get_user()
        # Verify user is actually a student
        if user.user_type != 'client':
            form.add_error(None, 'Credenciales incorrectas.')
            return self.form_invalid(form)
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

    def form_valid(self, form):
        user = form.get_user()
        # Verify user is actually a tutor
        if user.user_type != 'tutor':
            form.add_error(None, 'Credenciales incorrectas.')
            return self.form_invalid(form)
        messages.success(self.request, f'¡Bienvenido de nuevo, {user.name}!')
        return super().form_valid(form)

    def get_success_url(self):
        """Redirect based on user role - Admin/Staff go to /admin/"""
        user = self.request.user
        
        # P1.1 FIX: Superusers and staff go to admin panel
        if user.is_superuser or user.is_staff:
            return '/admin/'
        
        # Regular tutor users go to their dashboard
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
        from apps.academicTutoring.models import ClassSession
        context['pending_sessions'] = ClassSession.objects.get_tutor_sessions(
            self.request.user, status='pending'
        )
        context['upcoming_sessions'] = ClassSession.objects.get_tutor_sessions(
            self.request.user, status='confirmed'
        )
        context['past_sessions'] = ClassSession.objects.get_tutor_sessions(
            self.request.user, status='completed'
        )
        try:
            context['profile'] = TutorProfile.objects.get_profile_for_user(
                self.request.user
            )
        except TutorProfile.DoesNotExist:
            context['profile'] = None
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
        from apps.academicTutoring.models import ClassSession
        context['upcoming_sessions'] = ClassSession.objects.get_client_sessions(
            self.request.user, status='confirmed'
        )
        context['pending_sessions'] = ClassSession.objects.get_client_sessions(
            self.request.user, status='pending'
        )
        context['past_sessions'] = ClassSession.objects.get_client_sessions(
            self.request.user, status='completed'
        )
        try:
            context['profile'] = ClientProfile.objects.get_profile_for_user(
                self.request.user
            )
        except ClientProfile.DoesNotExist:
            context['profile'] = None
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
            return redirect('tutor_dashboard')
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
    """Logout view as CBV"""
    
    def get(self, request):
        logout(request)
        messages.info(request, 'Has cerrado sesión exitosamente.')
        return redirect('landing')
    
    def post(self, request):
        logout(request)
        messages.info(request, 'Has cerrado sesión exitosamente.')
        return redirect('landing')


# Backwards compatibility aliases
register_view = RegisterChoiceView.as_view()
register_tutor = RegisterTutorView.as_view()
register_client = RegisterClientView.as_view()
logout_view = LogoutView.as_view()
