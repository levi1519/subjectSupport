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
    list_display = [
        'get_full_name', 'get_email', 'is_approved',
        'get_subjects_display', 'hourly_rate',
        'employment_status', 'get_location_display',
        'get_cv_link', 'created_at'
    ]
    list_display_links = ['get_full_name']
    list_editable = ['is_approved']
    list_filter = ['is_approved', 'employment_status', 'created_at']
    search_fields = ['user__name', 'user__email', 'cedula']
    readonly_fields = [
        'created_at', 'get_cv_link', 'get_knowledge_link',
        'get_credential_link', 'get_education_cert_link',
        'get_avatar_preview', 'senescyt_helper'
    ]
    filter_horizontal = ['subjects_taught']
    actions = ['approve_tutors', 'reject_tutors']

    fieldsets = (
        ('Usuario', {
            'fields': ('get_avatar_preview', 'get_full_name_display', 'get_email_display')
        }),
        ('Aprobación', {
            'fields': ('is_approved', 'welcome_shown'),
        }),
        ('Perfil Profesional', {
            'fields': ('bio', 'experience', 'hourly_rate', 'employment_status', 'education_level'),
        }),
        ('Materias', {
            'fields': ('subjects_taught',),
        }),
        ('Documentos', {
            'fields': (
                'get_cv_link', 'get_knowledge_link',
                'get_credential_link', 'get_education_cert_link',
                'senescyt_helper',
            ),
        }),
        ('Datos Personales', {
            'fields': ('cedula', 'birth_date', 'phone_number'),
        }),
        ('Ubicación', {
            'fields': ('city', 'country'),
        }),
        ('Metadatos', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    # --- list_display methods ---
    def get_full_name(self, obj):
        return obj.user.name
    get_full_name.short_description = 'Nombre'
    get_full_name.admin_order_field = 'user__name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def get_subjects_display(self, obj):
        subjects = obj.subjects_taught.all()[:3]
        return ', '.join(s.name for s in subjects) or '—'
    get_subjects_display.short_description = 'Materias'

    def get_location_display(self, obj):
        parts = [p for p in [obj.city, obj.country] if p]
        return ', '.join(parts) or '—'
    get_location_display.short_description = 'Ubicación'

    # --- readonly_fields methods ---
    def get_full_name_display(self, obj):
        return obj.user.name
    get_full_name_display.short_description = 'Nombre completo'

    def get_email_display(self, obj):
        return obj.user.email
    get_email_display.short_description = 'Email'

    def get_avatar_preview(self, obj):
        from django.utils.html import format_html
        url = getattr(obj, 'avatar_url', None) or getattr(obj, 'avatar', None)
        if url:
            import re
            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', str(url))
            if match:
                url = f'https://drive.google.com/uc?export=view&id={match.group(1)}'
            return format_html(
                '<img src="{}" style="width:80px;height:80px;border-radius:50%;'
                'object-fit:cover;border:3px solid #6C63FF;" '
                'onerror="this.style.display=\'none\'" />',
                url
            )
        initials = obj.user.name[:1].upper() if obj.user.name else '?'
        return format_html(
            '<div style="width:80px;height:80px;border-radius:50%;background:#6C63FF;'
            'display:flex;align-items:center;justify-content:center;'
            'color:white;font-size:2rem;font-weight:700;">{}</div>',
            initials
        )
    get_avatar_preview.short_description = 'Foto de perfil'

    def get_cv_link(self, obj):
        from django.utils.html import format_html
        cv = getattr(obj, 'cv_file', None)
        if cv:
            return format_html('<a href="{}" target="_blank">📄 Ver CV</a>', cv.url)
        return '—'
    get_cv_link.short_description = 'CV'

    def get_knowledge_link(self, obj):
        from django.utils.html import format_html
        doc = getattr(obj, 'knowledge_document_file', None)
        if doc:
            return format_html('<a href="{}" target="_blank">📄 Ver doc. conocimiento</a>', doc.url)
        return '—'
    get_knowledge_link.short_description = 'Doc. conocimiento'

    def get_credential_link(self, obj):
        from django.utils.html import format_html
        doc = getattr(obj, 'institutional_credential_file', None)
        if doc:
            return format_html('<a href="{}" target="_blank">🏫 Ver credencial</a>', doc.url)
        return '—'
    get_credential_link.short_description = 'Credencial institucional'

    def get_education_cert_link(self, obj):
        from django.utils.html import format_html
        doc = getattr(obj, 'education_certificate_file', None)
        if doc:
            return format_html('<a href="{}" target="_blank">🎓 Ver cert. educación</a>', doc.url)
        return '—'
    get_education_cert_link.short_description = 'Cert. educación'

    def senescyt_helper(self, obj):
        from django.utils.html import format_html
        if not obj or not obj.user:
            return '—'
        nombre = obj.user.get_full_name() or obj.user.name or obj.user.username
        cedula = obj.cedula or '—'
        url = 'https://senescyt.info/'
        return format_html(
            '''<div style="background:#1a1a2e;border:1px solid #444;border-radius:6px;padding:12px;max-width:420px;">
                <p style="margin:0 0 8px;color:#aaa;font-size:12px;">Datos para consulta SENESCYT</p>
                <div style="margin-bottom:6px;">
                    <span style="color:#eee;font-size:13px;">Nombre: </span>
                    <code style="color:#7dd3fc;">{}</code>
                    <button type="button" onclick="navigator.clipboard.writeText('{}')"
                        style="background:#2563eb;color:white;border:none;border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer;margin-left:6px;">
                        Copiar
                    </button>
                </div>
                <div style="margin-bottom:10px;">
                    <span style="color:#eee;font-size:13px;">Cedula: </span>
                    <code style="color:#7dd3fc;">{}</code>
                    <button type="button" onclick="navigator.clipboard.writeText('{}')"
                        style="background:#2563eb;color:white;border:none;border-radius:4px;padding:2px 8px;font-size:11px;cursor:pointer;margin-left:6px;">
                        Copiar
                    </button>
                </div>
                <a href="{}" target="_blank"
                   style="background:#16a34a;color:white;padding:6px 14px;border-radius:4px;text-decoration:none;font-size:12px;">
                    Abrir SENESCYT
                </a>
            </div>''',
            nombre, nombre, cedula, cedula, url
        )
    senescyt_helper.short_description = 'Consulta SENESCYT'

    # --- actions ---
    def approve_tutors(self, request, queryset):
        from apps.accounts.models import Notification
        updated = queryset.update(is_approved=True)
        for profile in queryset:
            Notification.objects.get_or_create(
                recipient=profile.user,
                message='Tu cuenta de tutor ha sido aprobada. ¡Ya puedes recibir estudiantes!'
            )
        self.message_user(request, f'{updated} tutor(es) aprobado(s).')
    approve_tutors.short_description = 'Aprobar tutores seleccionados'

    def reject_tutors(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} tutor(es) rechazado(s).')
    reject_tutors.short_description = 'Rechazar tutores seleccionados'

    # --- delete override ---
    def delete_model(self, request, obj):
        obj.user.delete()

    def delete_queryset(self, request, queryset):
        from apps.accounts.models import User
        user_ids = list(queryset.values_list('user_id', flat=True))
        User.objects.filter(id__in=user_ids).delete()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('subjects_taught')


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Admin configuration for ClientProfile model"""
    list_display = ['user', 'get_avatar_preview', 'is_minor', 'parent_name', 'cedula', 'birth_date', 'get_location_display', 'created_at']
    search_fields = ['user__name', 'user__email', 'parent_name', 'city', 'country']
    list_filter = ['is_minor', 'created_at', 'country']
    readonly_fields = ['created_at', 'get_avatar_preview']

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

    def get_avatar_preview(self, obj):
        from django.utils.html import format_html
        import re
        url = getattr(obj, 'avatar_url', None) or getattr(obj, 'avatar', None)
        if url:
            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', str(url))
            if match:
                url = f'https://drive.google.com/uc?export=view&id={match.group(1)}'
            return format_html(
                '<img src="{}" style="width:40px;height:40px;border-radius:50%;'
                'object-fit:cover;border:2px solid #43D9AD;" '
                'onerror="this.style.display=\'none\'" />',
                url
            )
        initials = obj.user.name[:1].upper() if obj.user.name else '?'
        return format_html(
            '<div style="width:40px;height:40px;border-radius:50%;background:#43D9AD;'
            'display:inline-flex;align-items:center;justify-content:center;'
            'color:#1A1A2E;font-weight:700;">{}</div>',
            initials
        )
    get_avatar_preview.short_description = 'Foto'

    def delete_model(self, request, obj):
        obj.user.delete()

    def delete_queryset(self, request, queryset):
        from apps.accounts.models import User
        user_ids = list(queryset.values_list('user_id', flat=True))
        User.objects.filter(id__in=user_ids).delete()
