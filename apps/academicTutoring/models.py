from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Count
import uuid

# Importar GIS models solo si está disponible en settings
# En desarrollo sin GDAL, usar models normales
GIS_AVAILABLE = getattr(settings, 'GIS_AVAILABLE', False)

if GIS_AVAILABLE:
    try:
        from django.contrib.gis.db import models as gis_models
    except (ImportError, Exception):
        gis_models = models
        GIS_AVAILABLE = False
else:
    gis_models = models


class CountryConfig(models.Model):
    """
    Configuration for country-specific settings and geo-restrictions.
    """
    country_code = models.CharField(
        max_length=2,
        unique=True,
        verbose_name='Código de País'
    )
    country_name = models.CharField(
        max_length=100,
        verbose_name='Nombre del País'
    )
    active = models.BooleanField(
        default=True,
        verbose_name='Activo'
    )
    geo_restricted = models.BooleanField(
        default=False,
        verbose_name='Geo Restringido'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        ordering = ['country_name']

    def __str__(self):
        return f"{self.country_name} ({self.country_code})"


class ServiceArea(gis_models.Model):
    """
    Modelo para definir zonas geográficas de cobertura del servicio usando polígonos.

    Reemplaza la lógica de comparación de strings por consultas espaciales precisas.
    Utiliza PostGIS en producción y SpatiaLite en desarrollo.
    """
    country_config = models.ForeignKey(
        CountryConfig,
        on_delete=models.CASCADE,
        related_name='service_areas',
        verbose_name='Configuración de País'
    )
    city_name = models.CharField(
        max_length=100,
        verbose_name='Ciudad',
        help_text='Nombre de la ciudad que cubre esta área de servicio'
    )
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
        unique_together = [['city_name', 'country_config']]

    def __str__(self):
        status = "✓ Activo" if self.activo else "✗ Inactivo"
        return f"{self.city_name} ({status})"


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
    expiration_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Expiración'
    )

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = 'Tutor Lead'
        verbose_name_plural = 'Tutor Leads'

    def __str__(self):
        return f"{self.name} - {self.subject}"

    def save(self, *args, **kwargs):
        if not self.expiration_date:
            from django.utils import timezone
            self.expiration_date = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)


class ClassSessionManager(models.Manager):
    """
    Custom manager for ClassSession model.
    Provides optimized queries for tutor and client sessions.
    """
    
    def get_tutor_sessions(self, tutor, status=None):
        """
        Get sessions for a specific tutor with optimized queries.
        
        Args:
            tutor: User instance (must be tutor)
            status: Optional status filter
            
        Returns:
            QuerySet: Sessions with select_related optimization
        """
        qs = self.get_queryset().select_related(
            'tutor', 'client',
            'tutor__tutor_profile',
            'client__client_profile'
        ).filter(tutor=tutor)
        
        if status:
            qs = qs.filter(status=status)
            
        return qs.order_by('scheduled_date', 'scheduled_time')
    
    def get_client_sessions(self, client, status=None):
        """
        Get sessions for a specific client with optimized queries.
        
        Args:
            client: User instance (must be client)
            status: Optional status filter
            
        Returns:
            QuerySet: Sessions with select_related optimization
        """
        qs = self.get_queryset().select_related(
            'tutor', 'client',
            'tutor__tutor_profile',
            'client__client_profile'
        ).filter(client=client)
        
        if status:
            qs = qs.filter(status=status)
            
        return qs.order_by('scheduled_date', 'scheduled_time')


class ClassSession(models.Model):
    """Model for class sessions between tutors and clients"""
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    )

    DURATION_CHOICES = (
        (60, '1 hora'),
        (90, '1.5 horas'),
        (120, '2 horas'),
        (150, '2.5 horas'),
        (180, '3 horas'),
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
    # NOTE: scheduled_date and scheduled_time use timezone-aware handling.
    # UTC-5 Ecuador timezone is configured in settings.py with USE_TZ=True.
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
    material_url = models.URLField(
        null=True,
        blank=True,
        max_length=500,
        verbose_name='Material de clase (URL)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom manager
    objects = ClassSessionManager()

    class Meta:
        ordering = ['-scheduled_date', '-scheduled_time']
        verbose_name = 'Sesión de Clase'
        verbose_name_plural = 'Sesiones de Clase'

    def __str__(self):
        return f"{self.subject} - {self.tutor.name} con {self.client.name} ({self.get_status_display()})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.duration and (self.duration < 60 or self.duration > 180):
            raise ValidationError({
                'duration': 'La duración debe estar entre 60 y 180 minutos.'
            })


class Level(models.Model):
    """
    Modelo para niveles educativos (ej: Primaria, Secundaria, Universidad).
    
    Permite organizar las materias por nivel académico para mejor filtrado
    y búsqueda de tutores según el nivel que necesita el estudiante.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre del Nivel',
        help_text='Ej: Primaria, Secundaria, Bachillerato, Universidad'
    )
    order = models.IntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de visualización (menor primero)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Nivel Educativo'
        verbose_name_plural = 'Niveles Educativos'

    def __str__(self):
        return self.name


class SubjectLevel(models.Model):
    """
    Modelo intermedio que relaciona Subject con Level.
    
    Permite que una misma materia (ej: Matemáticas) exista en múltiples
    niveles educativos (Matemáticas de Primaria, Matemáticas de Universidad).
    Los tutores especifican qué combinación Subject+Level pueden enseñar.
    """
    subject = models.ForeignKey(
        'accounts.Subject',
        on_delete=models.CASCADE,
        related_name='subject_levels',
        verbose_name='Materia'
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='subject_levels',
        verbose_name='Nivel'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('subject', 'level')]
        ordering = ['level__order', 'subject__name']
        verbose_name = 'Materia por Nivel'
        verbose_name_plural = 'Materias por Nivel'

    def __str__(self):
        return f"{self.subject.name} - {self.level.name}"
