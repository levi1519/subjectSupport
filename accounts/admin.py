from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TutorProfile, ClientProfile, Subject


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Admin configuration for Subject model"""
    list_display = ['name', 'slug', 'created_at']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at']


class TutorProfileInline(admin.StackedInline):
    """Inline for tutor profile"""
    model = TutorProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Tutor'
    fk_name = 'user'
    filter_horizontal = ['subjects']


class ClientProfileInline(admin.StackedInline):
    """Inline for client profile"""
    model = ClientProfile
    can_delete = False
    verbose_name_plural = 'Perfil de Cliente'
    fk_name = 'user'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model"""
    list_display = ['email', 'name', 'user_type', 'is_active', 'date_joined']
    list_filter = ['user_type', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'name', 'username']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Información Personal', {'fields': ('name', 'user_type')}),
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
    """Admin configuration for TutorProfile model"""
    list_display = ['user', 'get_subjects_display', 'hourly_rate', 'phone_number', 'created_at']
    search_fields = ['user__name', 'user__email', 'phone_number']
    list_filter = ['created_at']
    readonly_fields = ['created_at']
    filter_horizontal = ['subjects']

    def get_subjects_display(self, obj):
        """Display subjects as comma-separated list"""
        return ", ".join([subject.name for subject in obj.subjects.all()[:3]])
    get_subjects_display.short_description = 'Materias'


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Admin configuration for ClientProfile model"""
    list_display = ['user', 'is_minor', 'parent_name', 'created_at']
    search_fields = ['user__name', 'user__email', 'parent_name']
    list_filter = ['is_minor', 'created_at']
    readonly_fields = ['created_at']
