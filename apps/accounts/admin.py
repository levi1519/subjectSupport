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
        'get_nombre', 'get_email', 'is_approved', 'get_employment',
        'get_cv', 'get_knowledge_doc', 'created_at'
    ]
    list_filter = ['is_approved', 'employment_status', 'education_level', 'country', 'created_at']
    search_fields = ['user__name', 'user__email', 'cedula']
    readonly_fields = [
        'created_at', 'senescyt_helper',
        'get_cv_link', 'get_knowledge_link',
        'get_credential_link', 'get_education_cert_link'
    ]
    filter_horizontal = ['subjects_taught']
    actions = ['approve_tutors', 'reject_tutors']

    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Aprobacion', {
            'fields': ('is_approved', 'welcome_shown'),
            'description': 'Aprueba o rechaza al tutor tras revisar sus documentos.',
        }),
        ('Situacion laboral', {
            'fields': ('employment_status', 'education_level', 'institution'),
        }),
        ('Documentos subidos', {
            'fields': (
                'get_cv_link',
                'get_knowledge_link',
                'get_credential_link',
                'get_education_cert_link',
            ),
            'description': 'Haz clic en cada enlace para revisar el documento antes de aprobar.',
        }),
        ('Verificacion SENESCYT', {
            'fields': ('senescyt_helper',),
            'description': 'Abre SENESCYT para verificar titulos manualmente.',
        }),
        ('Materias y datos', {
            'fields': ('subjects_taught', 'cedula', 'birth_date', 'phone_number',
                       'hourly_rate', 'bio', 'experience', 'city', 'country'),
        }),
        ('Metadatos', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def get_nombre(self, obj):
        return obj.user.name if obj.user else '—'
    get_nombre.short_description = 'Nombre'

    def get_email(self, obj):
        return obj.user.email if obj.user else '—'
    get_email.short_description = 'Email'

    def get_employment(self, obj):
        return obj.get_employment_status_display() if obj.employment_status else '—'
    get_employment.short_description = 'Situacion laboral'

    def get_cv(self, obj):
        from django.utils.html import format_html
        if obj.cv_file:
            return format_html('<a href="{}" target="_blank">Ver CV</a>', obj.cv_file.url)
        return 'No subido'
    get_cv.short_description = 'CV'

    def get_knowledge_doc(self, obj):
        from django.utils.html import format_html
        if obj.knowledge_document_file:
            return format_html('<a href="{}" target="_blank">Ver</a>', obj.knowledge_document_file.url)
        return 'No subido'
    get_knowledge_doc.short_description = 'Just. conocimiento'

    def get_cv_link(self, obj):
        from django.utils.html import format_html
        if obj.cv_file:
            return format_html(
                '<a href="{}" target="_blank" style="color:#43D9AD;">Abrir CV</a>', obj.cv_file.url)
        return 'No subido'
    get_cv_link.short_description = 'Curriculum Vitae'

    def get_knowledge_link(self, obj):
        from django.utils.html import format_html
        if obj.knowledge_document_file:
            return format_html(
                '<a href="{}" target="_blank" style="color:#43D9AD;">Abrir justificacion</a>',
                obj.knowledge_document_file.url)
        return 'No subido'
    get_knowledge_link.short_description = 'Justificacion de conocimientos'

    def get_credential_link(self, obj):
        from django.utils.html import format_html
        if obj.institutional_credential_file:
            return format_html(
                '<a href="{}" target="_blank" style="color:#43D9AD;">Abrir credencial</a>',
                obj.institutional_credential_file.url)
        return 'No subido'
    get_credential_link.short_description = 'Credencial institucional'

    def get_education_cert_link(self, obj):
        from django.utils.html import format_html
        if obj.education_certificate_file:
            return format_html(
                '<a href="{}" target="_blank" style="color:#43D9AD;">Abrir certificado</a>',
                obj.education_certificate_file.url)
        return 'No subido'
    get_education_cert_link.short_description = 'Certificado educativo'

    def senescyt_helper(self, obj):
        from django.utils.html import format_html
        if not obj or not obj.user:
            return '—'
        nombre = obj.user.get_full_name() or obj.user.name or obj.user.username
        cedula = obj.cedula or '—'
        url = 'https://www.senescyt.gob.ec/consulta-titulos-web/faces/jsp/consulta/consulta.jsf'
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

    def approve_tutors(self, request, queryset):
        from apps.accounts.models import Notification
        updated = queryset.update(is_approved=True, welcome_shown=False)
        for profile in queryset:
            Notification.objects.create(
                recipient=profile.user,
                message='Tu cuenta ha sido aprobada. Ya puedes iniciar sesion.'
            )
        self.message_user(request, f'{updated} tutor(es) aprobado(s).')
    approve_tutors.short_description = 'Aprobar tutores seleccionados'

    def reject_tutors(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'{updated} tutor(es) marcado(s) como no aprobados.')
    reject_tutors.short_description = 'Rechazar tutores seleccionados'

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
