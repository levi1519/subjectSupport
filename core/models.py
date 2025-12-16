from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

# Importar GIS models solo si está disponible
try:
    from django.contrib.gis.db import models as gis_models
    GIS_AVAILABLE = True
except ImportError:
    gis_models = models  # Fallback a models normales
    GIS_AVAILABLE = False


class ServiceArea(gis_models.Model):
    """
    Modelo para definir zonas geográficas de cobertura del servicio usando polígonos.

    Reemplaza la lógica de comparación de strings por consultas espaciales precisas.
    Utiliza PostGIS en producción y SpatiaLite en desarrollo.
    """
    city_name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Ciudad',
        help_text='Nombre de la ciudad que cubre esta área de servicio'
    )

    # Usar PolygonField si GIS está disponible, sino TextField como fallback
    if GIS_AVAILABLE:
        area = gis_models.PolygonField(
            verbose_name='Área de Cobertura',
            help_text='Polígono que define el área geográfica donde el servicio está disponible',
            srid=4326  # WGS84 - Sistema de coordenadas estándar GPS
        )
    else:
        # Fallback para desarrollo sin GDAL: almacenar WKT como texto
        area = models.TextField(
            verbose_name='Área de Cobertura (WKT)',
            help_text='Polígono en formato WKT. En producción se usará PolygonField de PostGIS.',
            default='POLYGON EMPTY'
        )
    activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Si está activo, usuarios dentro del polígono tendrán acceso al servicio'
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name='Descripción',
        help_text='Descripción del área (ej: Cantón Milagro, Provincia Guayas)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    class Meta:
        verbose_name = 'Área de Servicio'
        verbose_name_plural = 'Áreas de Servicio'
        ordering = ['city_name']

    def __str__(self):
        status = "✓ Activo" if self.activo else "✗ Inactivo"
        return f"{self.city_name} ({status})"

    def contains_point(self, latitude, longitude):
        """
        Verifica si un punto (lat, lon) está dentro del área de servicio.

        Args:
            latitude: Latitud del punto
            longitude: Longitud del punto

        Returns:
            bool: True si el punto está dentro del polígono
        """
        from django.contrib.gis.geos import Point
        point = Point(longitude, latitude, srid=4326)
        return self.area.contains(point)


class CiudadHabilitada(models.Model):
    """
    DEPRECADO: Modelo legado basado en comparación de strings de ciudades.

    Este modelo ha sido reemplazado por ServiceArea que usa geometría PostGIS.
    Se mantiene temporalmente para compatibilidad con datos existentes,
    pero NO se debe usar para nueva lógica de restricción geográfica.

    Usar ServiceArea en su lugar para consultas espaciales precisas.
    """
    ciudad = models.CharField(
        max_length=100,
        verbose_name='Ciudad'
    )
    provincia = models.CharField(
        max_length=100,
        verbose_name='Provincia/Estado'
    )
    pais = models.CharField(
        max_length=100,
        default='Ecuador',
        verbose_name='País'
    )
    activo = models.BooleanField(
        default=True,
        verbose_name='Servicio Activo',
        help_text='Si está activo, los usuarios de esta ciudad pueden acceder al servicio'
    )
    fecha_habilitacion = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de Habilitación'
    )
    orden_prioridad = models.IntegerField(
        default=100,
        verbose_name='Prioridad',
        help_text='Menor número = mayor prioridad en el listado'
    )
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notas Administrativas'
    )

    class Meta:
        verbose_name = 'Ciudad Habilitada'
        verbose_name_plural = 'Ciudades Habilitadas'
        ordering = ['orden_prioridad', 'ciudad']
        unique_together = [['ciudad', 'provincia', 'pais']]

    def __str__(self):
        status = "✓ Activo" if self.activo else "✗ Inactivo"
        return f"{self.ciudad}, {self.provincia} ({status})"


class NotificacionExpansion(models.Model):
    """
    Modelo para almacenar solicitudes de notificación cuando el servicio
    llegue a una ciudad nueva.
    """
    email = models.EmailField(
        verbose_name='Email'
    )
    ciudad_deseada = models.CharField(
        max_length=100,
        verbose_name='Ciudad Deseada'
    )
    provincia_deseada = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Provincia Deseada'
    )
    pais = models.CharField(
        max_length=100,
        default='Ecuador',
        verbose_name='País'
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='IP del Visitante'
    )
    ciudad_detectada = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Ciudad Detectada (IP)'
    )
    notificado = models.BooleanField(
        default=False,
        verbose_name='Notificación Enviada'
    )
    fecha_solicitud = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Solicitud'
    )
    fecha_notificacion = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Fecha de Notificación'
    )

    class Meta:
        verbose_name = 'Notificación de Expansión'
        verbose_name_plural = 'Notificaciones de Expansión'
        ordering = ['-fecha_solicitud']

    def __str__(self):
        status = "✓ Notificado" if self.notificado else "⏳ Pendiente"
        return f"{self.email} - {self.ciudad_deseada} ({status})"


class TutorLead(models.Model):
    """Model to store tutor lead information"""
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'Tutor Lead'
        verbose_name_plural = 'Tutor Leads'

    def __str__(self):
        return f"{self.name} - {self.subject}"


class ClassSession(models.Model):
    """Model for class sessions between tutors and clients"""
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    )

    DURATION_CHOICES = (
        (30, '30 minutos'),
        (60, '1 hora'),
        (90, '1.5 horas'),
        (120, '2 horas'),
    )

    MEETING_PLATFORM_CHOICES = (
        ('google_meet', 'Google Meet'),
        ('zoom', 'Zoom'),
        ('custom', 'Personalizado'),
    )

    tutor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tutor_sessions',
        limit_choices_to={'user_type': 'tutor'}
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_sessions',
        limit_choices_to={'user_type': 'client'}
    )
    subject = models.CharField(max_length=200, verbose_name='Materia')
    scheduled_date = models.DateField(verbose_name='Fecha')
    scheduled_time = models.TimeField(verbose_name='Hora')
    duration = models.IntegerField(
        choices=DURATION_CHOICES,
        default=60,
        verbose_name='Duración (minutos)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Estado'
    )

    # Meeting Platform Fields
    meeting_platform = models.CharField(
        max_length=20,
        choices=MEETING_PLATFORM_CHOICES,
        default='google_meet',
        verbose_name='Plataforma de Reunión'
    )
    meeting_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL de Reunión'
    )
    meeting_id = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='ID de Reunión'
    )
    meeting_password = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Contraseña de Reunión'
    )
    host_join_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL de Host'
    )
    meeting_started = models.BooleanField(
        default=False,
        verbose_name='Reunión Iniciada'
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='Notas'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']
        verbose_name = 'Sesión de Clase'
        verbose_name_plural = 'Sesiones de Clase'

    def __str__(self):
        return f"{self.subject} - {self.tutor.name} con {self.client.name} ({self.get_status_display()})"

    def is_upcoming(self):
        """Check if session is in the future"""
        from datetime import datetime
        session_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
        return session_datetime > datetime.now() and self.status in ['pending', 'confirmed']

    def is_past(self):
        """Check if session is in the past"""
        from datetime import datetime
        session_datetime = datetime.combine(self.scheduled_date, self.scheduled_time)
        return session_datetime < datetime.now()
