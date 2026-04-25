import re
from django.utils.html import format_html

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, TutorProfile, ClientProfile, Subject, KnowledgeArea


def _avatar_html(user, avatar_field, size=40, border_color='#6C63FF'):
    url = None
    if avatar_field:
        try:
            url = avatar_field.url
        except ValueError:
            url = None

    if url:
        match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
        if match:
            url = f'https://drive.google.com/uc?export=view&id={match.group(1)}'

        return format_html(
            '<a href="{}" target="_blank" title="Ver foto completa">'
            '<img src="{}" width="{}" height="{}" '
            'style="border-radius:50%;object-fit:cover;'
            'border:2px solid {};flex-shrink:0;cursor:pointer;'
            'transition:opacity 0.2s;opacity:1;" '
            'onmouseover="this.style.opacity=\'0.75\'" '
            'onmouseout="this.style.opacity=\'1\'" '
            'onerror="this.parentNode.style.display=\'none\'" />'
            '</a>',
            url, url, size, size, border_color
        )

    initial = (user.name or '?')[:1].upper()
    return format_html(
        '<div style="width:{}px;height:{}px;min-width:{}px;border-radius:50%;'
        'background:{};display:flex;align-items:center;justify-content:center;'
        'color:white;font-weight:700;font-size:{}px;flex-shrink:0;">{}</div>',
        size, size, size, border_color, size // 2, initial
    )


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
    list_display = [
        'get_avatar_small', 'email', 'name',
        'get_role_badge', 'is_active', 'date_joined'
    ]
    list_filter = ['user_type', 'is_active', 'is_staff', 'date_joined']
    search_fields = ['email', 'name', 'username']
    ordering = ['-date_joined']

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Información Personal', {'fields': ('name', 'user_type', 'country_code')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'name', 'user_type', 'password1', 'password2'),
        }),
    )

    def get_avatar_small(self, obj):
        # Intentar obtener avatar del perfil asociado
        avatar_field = None
        try:
            if obj.user_type == 'tutor':
                avatar_field = obj.tutor_profile.avatar
            elif obj.user_type == 'client':
                avatar_field = obj.client_profile.avatar
        except Exception:
            pass
        return _avatar_html(obj, avatar_field, size=36, border_color='#6C63FF')
    get_avatar_small.short_description = ''

    def get_role_badge(self, obj):
        colors = {'tutor': '#6C63FF', 'client': '#43D9AD'}
        labels = {'tutor': '👨‍🏫 Tutor', 'client': '🎓 Estudiante'}
        color = colors.get(obj.user_type, '#8892A4')
        label = labels.get(obj.user_type, obj.user_type or 'Admin')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;'
            'border-radius:12px;font-size:0.8rem;font-weight:600;">{}</span>',
            color, label
        )
    get_role_badge.short_description = 'Rol'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        inlines = []
        if obj.user_type == 'tutor':
            inlines.append(TutorProfileInline(self.model, self.admin_site))
        elif obj.user_type == 'client':
            inlines.append(ClientProfileInline(self.model, self.admin_site))
        return inlines


@admin.register(TutorProfile)
class TutorProfileAdmin(admin.ModelAdmin):
    list_display = [
        'get_avatar_small',
        'get_full_name',
        'get_email',
        'is_approved',
        'employment_status',
        'education_level',
        'get_subjects_display',
        'hourly_rate',
        'get_location_display',
        'get_docs_status',
        'created_at',
    ]
    list_display_links = ['get_full_name']
    list_editable = ['is_approved']
    list_filter = ['is_approved', 'employment_status', 'education_level', 'created_at']
    search_fields = ['user__name', 'user__email', 'cedula']
    readonly_fields = [
        'created_at',
        'get_avatar_preview',
        'get_user_info',
        'get_cv_link',
        'get_knowledge_link',
        'get_credential_link',
        'get_education_cert_link',
        'senescyt_helper',
        'get_docs_status',
    ]
    filter_horizontal = ['subjects_taught']
    actions = ['approve_tutors', 'reject_tutors']

    fieldsets = (
        ('Usuario', {
            'fields': ('get_avatar_preview', 'get_user_info')
        }),
        ('Aprobación', {
            'fields': ('is_approved', 'welcome_shown'),
        }),
        ('Perfil Profesional', {
            'fields': (
                'bio', 'experience', 'hourly_rate',
                'employment_status', 'education_level',
            ),
        }),
        ('Materias', {
            'fields': ('subjects_taught',),
        }),
        ('Documentos', {
            'fields': (
                'get_cv_link',
                'get_knowledge_link',
                'get_credential_link',
                'get_education_cert_link',
                'senescyt_helper',
            ),
        }),
        ('Datos Personales', {
            'fields': ('cedula', 'birth_date', 'phone_number'),
        }),
        ('Ubicación', {
            'fields': ('city', 'country'),
            'description': 'Detectada por IP al registro. Corregir si es incorrecta.'
        }),
        ('Metadatos', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    # --- list_display ---
    def get_avatar_small(self, obj):
        return _avatar_html(obj.user, obj.avatar, size=36)
    get_avatar_small.short_description = ''

    def get_full_name(self, obj):
        return obj.user.name
    get_full_name.short_description = 'Nombre'
    get_full_name.admin_order_field = 'user__name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'

    def get_subjects_display(self, obj):
        subjects = list(obj.subjects_taught.all()[:3])
        return ', '.join(s.name for s in subjects) or '—'
    get_subjects_display.short_description = 'Materias'

    def get_location_display(self, obj):
        parts = [p for p in [obj.city, obj.country] if p]
        return ', '.join(parts) or '—'
    get_location_display.short_description = 'Ubicación'

    def get_docs_status(self, obj):
        """
        Renderiza un <a> por documento si existe, o <span> gris si no.
        """
        docs = [
            ('CV',     obj.cv_file),
            ('Conoc.', obj.knowledge_document_file),
            ('Cert.',  obj.education_certificate_file),
            ('Cred.',  obj.institutional_credential_file),
        ]
        parts = []
        for label, field in docs:
            has_doc = bool(field and field.name)
            if has_doc:
                try:
                    url = field.url
                    parts.append(
                        format_html(
                            '<a href="{}" target="_blank" '
                            'style="color:#43D9AD;font-size:0.75rem;'
                            'margin-right:4px;text-decoration:none;" '
                            'title="Ver {}">{}</a>',
                            url, label, label
                        )
                    )
                except ValueError:
                    parts.append(format_html(
                        '<span style="color:#8892A4;font-size:0.75rem;'
                        'margin-right:4px;">{}</span>', label
                    ))
            else:
                parts.append(format_html(
                    '<span style="color:#8892A4;font-size:0.75rem;'
                    'margin-right:4px;opacity:0.4;">{}</span>', label
                ))
        from django.utils.safestring import mark_safe
        return mark_safe(''.join(str(p) for p in parts))
    get_docs_status.short_description = 'Docs'

    # --- readonly_fields (detail view) ---
    def get_avatar_preview(self, obj):
        url = None
        if obj.avatar:
            try:
                url = obj.avatar.url
            except ValueError:
                url = None

        if url:
            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
            if match:
                url = f'https://drive.google.com/uc?export=view&id={match.group(1)}'

            return format_html(
                '<a href="{}" target="_blank" title="Ver foto completa">'
                '<img src="{}" width="120" height="120" '
                'style="border-radius:50%;object-fit:cover;'
                'border:3px solid #6C63FF;cursor:pointer;'
                'box-shadow:0 4px 15px rgba(108,99,255,0.4);" />'
                '</a>'
                '<p style="color:#8892A4;font-size:0.8rem;margin-top:6px;">'
                '🔍 Click para ver tamaño completo</p>',
                url, url
            )

        initial = (obj.user.name or '?')[:1].upper()
        return format_html(
            '<div style="width:120px;height:120px;border-radius:50%;'
            'background:#6C63FF;display:flex;align-items:center;'
            'justify-content:center;color:white;font-size:3rem;font-weight:700;">'
            '{}</div>'
            '<p style="color:#8892A4;font-size:0.8rem;margin-top:6px;">'
            'Sin foto de perfil</p>',
            initial
        )
    get_avatar_preview.short_description = 'Foto de perfil'

    def get_user_info(self, obj):
        return format_html(
            '<strong style="font-size:1.1rem">{}</strong><br>'
            '<span style="color:#8892A4">{}</span>',
            obj.user.name, obj.user.email
        )
    get_user_info.short_description = 'Usuario'

    def get_cv_link(self, obj):
        if obj.cv_file and obj.cv_file.name:
            return format_html('<a href="{}" target="_blank">📄 Ver CV</a>', obj.cv_file.url)
        return '—'
    get_cv_link.short_description = 'CV'

    def get_knowledge_link(self, obj):
        if obj.knowledge_document_file and obj.knowledge_document_file.name:
            return format_html('<a href="{}" target="_blank">📄 Justificación</a>',
                             obj.knowledge_document_file.url)
        return '—'
    get_knowledge_link.short_description = 'Doc. conocimiento'

    def get_credential_link(self, obj):
        if obj.institutional_credential_file and obj.institutional_credential_file.name:
            return format_html('<a href="{}" target="_blank">🏫 Credencial</a>',
                             obj.institutional_credential_file.url)
        return '—'
    get_credential_link.short_description = 'Credencial'

    def get_education_cert_link(self, obj):
        if obj.education_certificate_file and obj.education_certificate_file.name:
            return format_html('<a href="{}" target="_blank">🎓 Certificado</a>',
                             obj.education_certificate_file.url)
        return '—'
    get_education_cert_link.short_description = 'Cert. educación'

    def senescyt_helper(self, obj):
        if obj.cedula:
            return format_html(
                '<a href="https://senescyt.info/" target="_blank">'
                '🔍 Verificar cédula {} en SENESCYT</a>', obj.cedula)
        return format_html('<a href="https://senescyt.info/" target="_blank">'
                          '🔍 Verificar en SENESCYT</a>')
    senescyt_helper.short_description = 'SENESCYT'

    # --- actions ---
    def approve_tutors(self, request, queryset):
        from apps.accounts.models import Notification
        count = queryset.update(is_approved=True)
        for profile in queryset:
            Notification.objects.get_or_create(
                recipient=profile.user,
                message='Tu cuenta de tutor ha sido aprobada. ¡Ya puedes recibir estudiantes!'
            )
        self.message_user(request, f'{count} tutor(es) aprobado(s).')
    approve_tutors.short_description = 'Aprobar seleccionados'

    def reject_tutors(self, request, queryset):
        count = queryset.update(is_approved=False)
        self.message_user(request, f'{count} tutor(es) rechazado(s).')
    reject_tutors.short_description = 'Rechazar seleccionados'

    # --- delete override ---
    def delete_model(self, request, obj):
        obj.user.delete()

    def delete_queryset(self, request, queryset):
        from apps.accounts.models import User
        user_ids = list(queryset.values_list('user_id', flat=True))
        User.objects.filter(id__in=user_ids).delete()


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = [
        'get_avatar_small',
        'get_full_name',
        'get_email',
        'get_student_type_badge',
        'is_minor',
        'cedula',
        'birth_date',
        'get_location_display',
        'created_at',
    ]
    list_display_links = ['get_full_name']
    list_filter = ['is_minor', 'student_type', 'created_at']
    search_fields = ['user__name', 'user__email', 'cedula', 'parent_name']
    readonly_fields = [
        'created_at',
        'get_avatar_preview',
        'get_user_info',
        'get_id_doc_link',
        'get_enrollment_link',
    ]

    fieldsets = (
        ('Usuario', {
            'fields': ('get_avatar_preview', 'get_user_info')
        }),
        ('Datos del Estudiante', {
            'fields': ('student_type', 'is_minor', 'parent_name', 'parent_email'),
        }),
        ('Documentos', {
            'fields': ('get_id_doc_link', 'get_enrollment_link'),
        }),
        ('Datos Personales', {
            'fields': ('cedula', 'birth_date', 'phone_number', 'bio'),
        }),
        ('Ubicación', {
            'fields': ('city', 'country'),
        }),
        ('Metadatos', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def get_avatar_small(self, obj):
        return _avatar_html(obj.user, obj.avatar, size=36, border_color='#43D9AD')
    get_avatar_small.short_description = ''

    def get_full_name(self, obj):
        return obj.user.name
    get_full_name.short_description = 'Nombre'
    get_full_name.admin_order_field = 'user__name'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def get_student_type_badge(self, obj):
        val = getattr(obj, 'student_type', '') or ''
        labels = {
            'university': '🎓 Universitario',
            'highschool': '📚 Secundaria',
            'primary': '📖 Primaria',
            'other': '📝 Otro',
        }
        return labels.get(val, val or '—')
    get_student_type_badge.short_description = 'Tipo'

    def get_location_display(self, obj):
        parts = [p for p in [obj.city, obj.country] if p]
        return ', '.join(parts) or '—'
    get_location_display.short_description = 'Ubicación'

    def get_avatar_preview(self, obj):
        url = None
        if obj.avatar:
            try:
                url = obj.avatar.url
            except ValueError:
                url = None

        if url:
            match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
            if match:
                url = f'https://drive.google.com/uc?export=view&id={match.group(1)}'

            return format_html(
                '<a href="{}" target="_blank" title="Ver foto completa">'
                '<img src="{}" width="120" height="120" '
                'style="border-radius:50%;object-fit:cover;'
                'border:3px solid #43D9AD;cursor:pointer;'
                'box-shadow:0 4px 15px rgba(67,217,173,0.4);" />'
                '</a>'
                '<p style="color:#8892A4;font-size:0.8rem;margin-top:6px;">'
                '🔍 Click para ver tamaño completo</p>',
                url, url
            )

        initial = (obj.user.name or '?')[:1].upper()
        return format_html(
            '<div style="width:120px;height:120px;border-radius:50%;'
            'background:#43D9AD;display:flex;align-items:center;'
            'justify-content:center;color:#1A1A2E;font-size:3rem;font-weight:700;">'
            '{}</div>'
            '<p style="color:#8892A4;font-size:0.8rem;margin-top:6px;">'
            'Sin foto de perfil</p>',
            initial
        )
    get_avatar_preview.short_description = 'Foto de perfil'

    def get_user_info(self, obj):
        return format_html(
            '<strong style="font-size:1.1rem">{}</strong><br>'
            '<span style="color:#8892A4">{}</span>',
            obj.user.name, obj.user.email
        )
    get_user_info.short_description = 'Usuario'

    def get_id_doc_link(self, obj):
        doc = getattr(obj, 'id_document_file', None)
        if doc and doc.name:
            return format_html('<a href="{}" target="_blank">🪪 Ver documento ID</a>', doc.url)
        return '—'
    get_id_doc_link.short_description = 'Doc. identidad'

    def get_enrollment_link(self, obj):
        doc = getattr(obj, 'enrollment_file', None)
        if doc and doc.name:
            return format_html('<a href="{}" target="_blank">📋 Ver matrícula</a>', doc.url)
        return '—'
    get_enrollment_link.short_description = 'Matrícula'

    def delete_model(self, request, obj):
        obj.user.delete()

    def delete_queryset(self, request, queryset):
        from apps.accounts.models import User
        user_ids = list(queryset.values_list('user_id', flat=True))
        User.objects.filter(id__in=user_ids).delete()
