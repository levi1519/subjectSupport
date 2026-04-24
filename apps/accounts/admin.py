from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TutorProfile, ClientProfile, Subject, KnowledgeArea


@admin.register(KnowledgeArea)
class KnowledgeAreaAdmin(admin.ModelAdmin):
    """Admin configuration for KnowledgeArea model"""
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin configuration for Subject model"""
    list_display = ['name', 'knowledge_area', 'slug', 'created_at']
    search_fields = ['name', 'slug']
    list_filter = ['knowledge_area']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']


class TutorProfileInline(admin.StackedInline):
    """Inline for tutor profile"""
    model = TutorProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Tutor'
    fk_name = 'user'
    filter_horizontal = ['subjects_taught']
    fields = ['bio', 'experience', 'hourly_rate', 'phone_number', 'cedula', 'birth_date', 'city', 'country', 'documents_required']
    readonly_fields = ['city', 'country']


class ClientProfileInline(admin.StackedInline):
    """Inline for client profile"""
    model = ClientProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Cliente'
    fk_name = 'user'
    fields = ['is_minor', 'parent_name', 'parent_email', 'phone_number', 'bio', 'cedula', 'birth_date', 'city', 'country']
    readonly_fields = ['city', 'country']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model"""
    list_display = ['email', 'name', 'user_type', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'name', 'username']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Información Personal', {'fields': ('name', 'user_type', 'country_code')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'name', 'user_type', 'password1', 'password2'),
        }),
    )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        inlines = []
        if obj.user_type == 'tutor':
            inlines.append(TutorProfileInline(self.model, self.admin_site))
        elif obj.user_type == 'client':
            inlines.append(ClientProfileInline(self.model, self.admin_site))
        return inlines


@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_approved', 'get_subjects_taught_display', 'cedula',
                    'university_name', 'hourly_rate', 'phone_number',
                    'get_location_display', 'documents_required', 'created_at']
    list_filter = ['is_approved', 'created_at', 'country']
    list_editable = ['is_approved', 'documents_required']
    search_fields = ['user__name', 'user__email', 'phone_number', 'city', 'country']
    readonly_fields = ['created_at', 'welcome_shown']
    filter_horizontal = ['subjects_taught']
    actions = ['approve_tutors']

    def approve_tutors(self, request, queryset):
        from apps.accounts.models import Notification
        updated = 0
        for profile in queryset.filter(is_approved=False):
            profile.is_approved = True
            profile.save()
            Notification.objects.create(
                recipient=profile.user,
                message=f'¡Felicitaciones, {profile.user.name}! Tu cuenta de tutor ha sido aprobada. Ya puedes iniciar sesión y comenzar a recibir estudiantes.'
            )
            updated += 1
        self.message_user(request, f'{updated} tutor(es) aprobado(s) y notificado(s).')
    approve_tutors.short_description = 'Aprobar tutores seleccionados'

    def get_location_display(self, obj):
        if obj.city and obj.country:
            return f"{obj.city}, {obj.country}"
        return obj.country or obj.city or 'No disponible'
    get_location_display.short_description = 'Ubicación'

    def get_subjects_taught_display(self, obj):
        subjects = obj.subjects_taught.all()[:3]
        return ', '.join([s.name for s in subjects]) or 'Ninguno'
    get_subjects_taught_display.short_description = 'Materias'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('subjects_taught')


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Admin configuration for ClientProfile model"""
    list_display = ['user', 'is_minor', 'parent_name', 'cedula', 'birth_date', 'get_location_display', 'created_at']
    search_fields = ['user__name', 'user__email', 'parent_name', 'city', 'country']
    list_filter = ['is_minor', 'created_at', 'country']
    readonly_fields = ['created_at']
    
    def get_location_display(self, obj):
        """Muestra ubicación formateada desde geolocalización"""
        if obj.city and obj.country:
            return f"{obj.city}, {obj.country}"
        elif obj.country:
            return obj.country
        elif obj.city:
            return obj.city
        return "No disponible"
    get_location_display.short_description = 'Ubicación Actual'
