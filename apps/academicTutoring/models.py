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
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name='Motivo de cancelación'
    )
    material_url = models.URLField(
        null=True,
        blank=True,
        max_length=500,
        verbose_name='Material de clase (URL)'
    )
    recording_url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name='URL del video de la clase',
        help_text='Enlace al video de la sesión (YouTube, Drive, etc.)'
    )
    video_uploaded_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Video subido el'
    )
    video_expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Video disponible hasta'
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name='Sesión archivada',
        help_text='Las sesiones archivadas no aparecen en el dashboard activo'
    )
    archived_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Archivada el'
    )

    # Calificaciones post-sesión
    student_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Calificación del estudiante al tutor',
        help_text='★ 1-5'
    )
    student_rating_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Comentario del estudiante'
    )
    student_rated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Calificado por estudiante el'
    )
    tutor_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Calificación del tutor al estudiante',
        help_text='★ 1-5'
    )
    tutor_rating_comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Comentario del tutor'
    )
    tutor_rated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Calificado por tutor el'
    )
    tutor_ai_context = models.TextField(
        blank=True,
        null=True,
        verbose_name='Contexto para IA',
        help_text='Indicaciones opcionales del tutor para orientar la generación del simulacro'
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


class PlatformConfig(models.Model):
    """
    Singleton de configuración de plataforma.
    Editable desde admin. Solo debe existir una instancia (pk=1).
    """

    # === SECCIÓN 1: Acceso y edad ===
    min_student_age = models.IntegerField(
        default=15,
        verbose_name='Edad mínima de estudiante',
        help_text='Edad mínima absoluta para registrarse como estudiante'
    )
    min_tutor_age = models.IntegerField(
        default=18,
        verbose_name='Edad mínima de tutor',
        help_text='Edad mínima para registrarse como tutor'
    )
    enable_minor_accounts = models.BooleanField(
        default=False,
        verbose_name='Habilitar cuentas de menores de edad',
        help_text='Si activo, muestra el flujo de registro para menores con tutor legal'
    )

    # === SECCIÓN 2: Documentos tutor ===
    require_tutor_cv = models.BooleanField(
        default=True,
        verbose_name='Exigir CV al tutor',
        help_text='CV en PDF obligatorio en el registro del tutor'
    )
    require_tutor_document = models.BooleanField(
        default=False,
        verbose_name='Exigir documento genérico al tutor',
        help_text='Documento genérico (CV o credencial). Activa flujo de aprobación'
    )
    require_tutor_knowledge_document = models.BooleanField(
        default=False,
        verbose_name='Exigir documento de conocimiento al tutor',
        help_text='Títulos, certificados o CV académico. Activa flujo de aprobación hasta revisión del admin'
    )
    require_tutor_education_certificate = models.BooleanField(
        default=False,
        verbose_name='Exigir certificado de nivel educativo',
        help_text='Certificado que acredite el nivel educativo declarado por el tutor'
    )
    require_tutor_institutional_credential = models.BooleanField(
        default=False,
        verbose_name='Exigir credencial institucional al tutor',
        help_text='Carnet o ID de institución. Requerido si el tutor es docente activo'
    )

    # === SECCIÓN 3: Documentos estudiante ===
    require_student_university = models.BooleanField(
        default=True,
        verbose_name='Exigir universidad al estudiante',
        help_text='El estudiante debe declarar su institución educativa al registrarse'
    )
    require_student_id_document = models.BooleanField(
        default=True,
        verbose_name='Exigir cédula al estudiante',
        help_text='Cédula obligatoria para estudiantes mayores de edad'
    )
    require_student_enrollment_certificate = models.BooleanField(
        default=True,
        verbose_name='Exigir carnet/constancia de matrícula',
        help_text='Carnet o constancia de matrícula para estudiantes universitarios'
    )
    require_student_document = models.BooleanField(
        default=False,
        verbose_name='Exigir documento institucional al estudiante',
        help_text='Documento institucional genérico para el estudiante'
    )

    # === SECCIÓN 4: Instituciones ===
    enable_institution_search = models.BooleanField(
        default=True,
        verbose_name='Habilitar búsqueda de instituciones',
        help_text='Permite buscar instituciones del dataset MINEDUC en el registro'
    )
    allow_manual_institution_entry = models.BooleanField(
        default=True,
        verbose_name='Permitir ingreso manual de institución',
        help_text='Si la institución no está en la lista, el usuario puede ingresarla manualmente. Queda en revisión del admin'
    )

    # === SECCIÓN 5: Sesiones ===
    max_subjects_per_tutor = models.IntegerField(
        default=5,
        verbose_name='Máximo de materias por tutor',
        help_text='Cantidad máxima de materias que un tutor puede seleccionar'
    )
    session_cancellation_hours = models.IntegerField(
        default=24,
        verbose_name='Horas mínimas para cancelar sin penalización',
        help_text='Aplica cuando los pagos estén activos (Fase 3)'
    )
    session_reminder_hours = models.IntegerField(
        default=24,
        verbose_name='Horas de anticipación para recordatorio',
        help_text='Muestra banner al tutor cuando tiene sesiones en las próximas N horas'
    )

    # === SECCIÓN 6: Archivos ===
    max_file_size_mb = models.IntegerField(
        default=5,
        verbose_name='Tamaño máximo de archivo (MB)',
        help_text='Límite de tamaño por archivo subido en la plataforma'
    )
    max_session_materials = models.IntegerField(
        default=7,
        verbose_name='Máximo de archivos por sesión',
        help_text='Cantidad máxima de materiales que se pueden adjuntar a una sesión'
    )
    require_session_material_file = models.BooleanField(
        default=False,
        verbose_name='Exigir archivo en solicitud de sesión',
        help_text='Si está marcado, el estudiante DEBE subir un archivo al solicitar una clase'
    )
    require_session_material_url = models.BooleanField(
        default=False,
        verbose_name='Exigir URL de material en solicitud de sesión',
        help_text='Si está marcado, el estudiante DEBE ingresar una URL al solicitar una clase'
    )
    allowed_file_types = models.CharField(
        max_length=200,
        default='pdf,jpg,jpeg,png,doc,docx,ppt,pptx,xlsx',
        verbose_name='Tipos de archivo permitidos',
        help_text='Extensiones separadas por coma (sin puntos)'
    )
    min_pdf_materials_ratio = models.FloatField(
        default=0.5,
        verbose_name='Ratio mínimo de PDFs en materiales',
        help_text='Proporción mínima de archivos PDF respecto al total de materiales subidos'
    )

    # === SECCIÓN 7: Pagos (Fase 3 — inactivos) ===
    platform_commission_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10.00,
        verbose_name='Comisión de plataforma (%)',
        help_text='Porcentaje que retiene la plataforma de cada sesión pagada (Fase 3)'
    )
    enable_payphone = models.BooleanField(
        default=False,
        verbose_name='Habilitar PayPhone',
        help_text='Activa la pasarela de pago PayPhone (Fase 3)'
    )
    enable_deposit_voucher = models.BooleanField(
        default=False,
        verbose_name='Habilitar pago por comprobante de depósito',
        help_text='Permite pago manual con comprobante revisado por admin (Fase 3)'
    )
    refund_policy_hours = models.IntegerField(
        default=24,
        verbose_name='Horas para reembolso completo',
        help_text='Cancelaciones antes de este plazo reciben reembolso completo (Fase 3)'
    )

    # === SECCIÓN 8: Video y Archivado ===
    video_retention_days = models.IntegerField(
        default=7,
        verbose_name='Días de retención del video',
        help_text='Días que el video de la clase estará disponible para descarga por el estudiante'
    )
    session_archive_days = models.IntegerField(
        default=30,
        verbose_name='Días para archivar sesión completada',
        help_text='Días después de completada una sesión para que desaparezca del dashboard activo'
    )

    # === SECCIÓN 9: Tarifa del tutor ===
    hourly_rate_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        verbose_name='Tarifa mínima por hora (USD)',
        help_text='Piso de tarifa que puede establecer un tutor'
    )
    hourly_rate_cooldown_days = models.IntegerField(
        default=30,
        verbose_name='Días de bloqueo para cambio de tarifa',
        help_text='Días que debe esperar un tutor para cambiar su tarifa después de establecerla'
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración de Plataforma'
        verbose_name_plural = 'Configuración de Plataforma'

    def __str__(self):
        return 'Configuración de Plataforma'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Institution(models.Model):
    """
    Instituciones educativas de Ecuador.
    Pobladas desde dataset MINEDUC. Entradas manuales marcadas como needs_review.
    """
    INSTITUTION_TYPE_CHOICES = (
        ('universidad', 'Universidad'),
        ('instituto', 'Instituto Técnico/Tecnológico'),
        ('colegio', 'Colegio'),
        ('escuela', 'Escuela'),
    )

    name = models.CharField(
        max_length=300,
        verbose_name='Nombre de la institución'
    )
    type = models.CharField(
        max_length=20,
        choices=INSTITUTION_TYPE_CHOICES,
        default='universidad',
        verbose_name='Tipo'
    )
    province = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Provincia'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Ciudad'
    )
    is_manual = models.BooleanField(
        default=False,
        verbose_name='Ingresada manualmente',
        help_text='True si fue ingresada por un usuario, no del dataset oficial'
    )
    needs_review = models.BooleanField(
        default=False,
        verbose_name='Requiere revisión admin',
        help_text='True para entradas manuales hasta verificación'
    )
    active = models.BooleanField(
        default=True,
        verbose_name='Activa'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Institución'
        verbose_name_plural = 'Instituciones'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class SessionMaterial(models.Model):
    """
    Materiales adjuntos a una sesión de clase.
    Puede ser URL o archivo. Subido por estudiante o tutor.
    Se conservan permanentemente para uso futuro del simulador IA.
    """
    MATERIAL_TYPE_CHOICES = (
        ('url', 'Enlace URL'),
        ('file', 'Archivo'),
    )

    session = models.ForeignKey(
        'ClassSession',
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name='Sesión'
    )
    type = models.CharField(
        max_length=10,
        choices=MATERIAL_TYPE_CHOICES,
        verbose_name='Tipo'
    )
    url = models.URLField(
        blank=True,
        null=True,
        max_length=500,
        verbose_name='URL'
    )
    file = models.FileField(
        upload_to='sessions/materials/',
        blank=True,
        null=True,
        verbose_name='Archivo'
    )
    filename = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name='Nombre del archivo'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_materials',
        verbose_name='Subido por'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Material de Sesión'
        verbose_name_plural = 'Materiales de Sesión'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_type_display()} — {self.session}"
