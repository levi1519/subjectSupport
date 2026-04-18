from django.contrib import admin
from django.conf import settings
from .models import ServiceArea, TutorLead, ClassSession, NotificacionExpansion, Level, SubjectLevel, CountryConfig

# Importar GISModelAdmin solo si está disponible
GIS_AVAILABLE = getattr(settings, 'GIS_AVAILABLE', False)
if GIS_AVAILABLE:
    try:
        from django.contrib.gis.admin import GISModelAdmin
    except (ImportError, Exception):
        GISModelAdmin = admin.ModelAdmin
else:
    GISModelAdmin = admin.ModelAdmin


@admin.register(ServiceArea)
class ServiceAreaAdmin(GISModelAdmin):
    """
    Admin configuration for ServiceArea model with GIS map widget.
    Permite visualizar y editar polígonos de cobertura en un mapa interactivo.
    """
    list_display = ['city_name', 'activo', 'descripcion', 'created_at', 'updated_at']
    list_filter = ['activo', 'created_at']
    search_fields = ['city_name', 'descripcion']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['city_name']

    fieldsets = (
        ('Información Básica', {
            'fields': ('city_name', 'activo', 'descripcion')
        }),
        ('Área Geográfica', {
            'fields': ('area',),
            'description': 'Define el polígono de cobertura del servicio. Usa el mapa para dibujar el área.'
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    list_editable = ['activo']

    # Configuración del widget GIS
    gis_widget_kwargs = {
        'attrs': {
            'default_lat': -2.134,  # Latitud de Milagro
            'default_lon': -79.594,  # Longitud de Milagro
            'default_zoom': 11,
        }
    }


@admin.register(TutorLead)
class TutorLeadAdmin(admin.ModelAdmin):
    """Admin configuration for TutorLead model"""
    list_display = ['name', 'email', 'subject', 'created_at']
    list_filter = ['created_at', 'subject']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Tutor Information', {
            'fields': ('name', 'email', 'subject')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):
    """Admin configuration for ClassSession model"""
    list_display = ['subject', 'tutor', 'client', 'scheduled_date', 'scheduled_time', 'status', 'created_at']
    list_filter = ['status', 'scheduled_date', 'created_at']
    search_fields = ['subject', 'tutor__name', 'tutor__email', 'client__name', 'client__email']
    readonly_fields = ['created_at', 'updated_at', 'meeting_url']
    ordering = ['-scheduled_date', '-scheduled_time']
    date_hierarchy = 'scheduled_date'

    fieldsets = (
        ('Información de la Sesión', {
            'fields': ('tutor', 'client', 'subject')
        }),
        ('Programación', {
            'fields': ('scheduled_date', 'scheduled_time', 'duration')
        }),
        ('Estado y Detalles', {
            'fields': ('status', 'meeting_url', 'notes')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('tutor', 'client')


@admin.register(NotificacionExpansion)
class NotificacionExpansionAdmin(admin.ModelAdmin):
    """
    Admin configuration for NotificacionExpansion model.
    Muestra solicitudes de notificación para nuevas ciudades.
    """
    list_display = [
        'email',
        'ciudad_deseada',
        'provincia_deseada',
        'ciudad_detectada',
        'notificado',
        'fecha_solicitud'
    ]
    list_filter = ['notificado', 'ciudad_deseada', 'fecha_solicitud']
    search_fields = ['email', 'ciudad_deseada', 'provincia_deseada', 'ciudad_detectada']
    readonly_fields = ['fecha_solicitud', 'fecha_notificacion', 'ip_address', 'ciudad_detectada']
    ordering = ['-fecha_solicitud']
    date_hierarchy = 'fecha_solicitud'

    fieldsets = (
        ('Información del Usuario', {
            'fields': ('email', 'ciudad_deseada', 'provincia_deseada', 'pais')
        }),
        ('Detección Automática', {
            'fields': ('ip_address', 'ciudad_detectada'),
            'classes': ('collapse',)
        }),
        ('Estado de Notificación', {
            'fields': ('notificado', 'fecha_solicitud', 'fecha_notificacion')
        }),
    )

    list_editable = ['notificado']

    actions = ['marcar_como_notificado', 'marcar_como_pendiente']

    def marcar_como_notificado(self, request, queryset):
        """Acción para marcar notificaciones como enviadas"""
        from django.utils import timezone
        updated = queryset.update(notificado=True, fecha_notificacion=timezone.now())
        self.message_user(request, f'{updated} notificación(es) marcada(s) como enviada(s)')
    marcar_como_notificado.short_description = 'Marcar como notificado'

    def marcar_como_pendiente(self, request, queryset):
        """Acción para marcar notificaciones como pendientes"""
        updated = queryset.update(notificado=False, fecha_notificacion=None)
        self.message_user(request, f'{updated} notificación(es) marcada(s) como pendiente(s)')
    marcar_como_pendiente.short_description = 'Marcar como pendiente'


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    """
    Admin configuration for Level model.
    Permite gestionar niveles educativos (Primaria, Secundaria, etc.).
    """
    list_display = ['name', 'order', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['order', 'name']

    fieldsets = (
        ('Información del Nivel', {
            'fields': ('name', 'order')
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    list_editable = ['order']


@admin.register(CountryConfig)
class CountryConfigAdmin(admin.ModelAdmin):
    """
    Admin configuration for CountryConfig model.
    """
    list_display = ['country_code', 'country_name', 'active', 'geo_restricted', 'updated_at']
    list_editable = ['active', 'geo_restricted']
    list_filter = ['active', 'geo_restricted']
    search_fields = ['country_code', 'country_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['country_name']


@admin.register(SubjectLevel)
class SubjectLevelAdmin(admin.ModelAdmin):
    """
    Admin configuration for SubjectLevel model.
    Permite gestionar combinaciones de Materia + Nivel Educativo.
    """
    list_display = ['subject', 'level', 'created_at']
    list_filter = ['level', 'subject', 'created_at']
    search_fields = ['subject__name', 'level__name']
    readonly_fields = ['created_at']
    ordering = ['level__order', 'subject__name']

    fieldsets = (
        ('Combinación Materia-Nivel', {
            'fields': ('subject', 'level'),
            'description': 'Selecciona una materia y un nivel educativo. Esta combinación será asignada a tutores.'
        }),
        ('Metadatos', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    # Filtros en barra lateral
    list_filter = ['level', 'created_at']

    # Autocomplete para búsquedas más rápidas con muchos registros
    autocomplete_fields = ['subject']

    # Acciones personalizadas
    actions = ['duplicate_for_all_levels']

    def duplicate_for_all_levels(self, request, queryset):
        """
        Acción para duplicar materias seleccionadas en todos los niveles.
        Útil cuando se agrega una materia nueva que existe en múltiples niveles.
        """
        duplicated_count = 0
        
        for subject_level in queryset:
            # Obtener todos los niveles
            all_levels = Level.objects.all()
            
            for level in all_levels:
                # Crear SubjectLevel si no existe
                _, created = SubjectLevel.objects.get_or_create(
                    subject=subject_level.subject,
                    level=level
                )
                if created:
                    duplicated_count += 1
        
        self.message_user(
            request, 
            f'{duplicated_count} nueva(s) combinación(es) Materia-Nivel creada(s)'
        )
    duplicate_for_all_levels.short_description = 'Duplicar materia en todos los niveles'
