from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import ServiceArea, TutorLead, ClassSession, CiudadHabilitada, NotificacionExpansion


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


@admin.register(CiudadHabilitada)
class CiudadHabilitadaAdmin(admin.ModelAdmin):
    """
    Admin configuration for CiudadHabilitada model.
    Permite gestionar ciudades donde el servicio está disponible.
    """
    list_display = ['ciudad', 'provincia', 'pais', 'activo', 'orden_prioridad', 'fecha_habilitacion']
    list_filter = ['activo', 'pais', 'provincia', 'fecha_habilitacion']
    search_fields = ['ciudad', 'provincia', 'pais']
    readonly_fields = ['fecha_habilitacion']
    ordering = ['orden_prioridad', 'ciudad']

    fieldsets = (
        ('Ubicación', {
            'fields': ('ciudad', 'provincia', 'pais')
        }),
        ('Configuración', {
            'fields': ('activo', 'orden_prioridad')
        }),
        ('Información Adicional', {
            'fields': ('notas', 'fecha_habilitacion'),
            'classes': ('collapse',)
        }),
    )

    list_editable = ['activo', 'orden_prioridad']

    actions = ['activar_ciudades', 'desactivar_ciudades']

    def activar_ciudades(self, request, queryset):
        """Acción para activar ciudades seleccionadas"""
        updated = queryset.update(activo=True)
        self.message_user(request, f'{updated} ciudad(es) activada(s)')
    activar_ciudades.short_description = 'Activar ciudades seleccionadas'

    def desactivar_ciudades(self, request, queryset):
        """Acción para desactivar ciudades seleccionadas"""
        updated = queryset.update(activo=False)
        self.message_user(request, f'{updated} ciudad(es) desactivada(s)')
    desactivar_ciudades.short_description = 'Desactivar ciudades seleccionadas'


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
