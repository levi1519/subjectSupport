from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.db.models import Count, Q, Case, When, IntegerField, Value


class KnowledgeArea(models.Model):
    """Model for knowledge areas (e.g., Sciences, Humanities, Arts)"""
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre del Área'
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True,
        verbose_name='Slug'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Área de Conocimiento'
        verbose_name_plural = 'Áreas de Conocimiento'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Model for subjects/materias that tutors can teach"""
    knowledge_area = models.ForeignKey(
        KnowledgeArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects',
        verbose_name='Área de Conocimiento'
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nombre de la Materia'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name='Slug'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Materia'
        verbose_name_plural = 'Materias'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom User model with user_type field"""
    USER_TYPE_CHOICES = (
        ('tutor', 'Tutor'),
        ('client', 'Cliente'),
        
    )

    email = models.EmailField(
        unique=True,
        validators=[EmailValidator()],
        verbose_name='Correo Electrónico'
    )

    username = models.CharField(
    max_length=150,
    unique=True,
    blank=True,
    default='',
    verbose_name='Nombre de usuario'

    )
    name = models.CharField(max_length=200, verbose_name='Nombre Completo')
    country_code = models.CharField(
        max_length=2,
        blank=True,
        default='',
        verbose_name='Código de País'
    )
    user_type = models.CharField(
    max_length=10,
    choices=USER_TYPE_CHOICES,
    blank=True,
    default='',
    verbose_name='Tipo de Usuario'
    )
    is_active = models.BooleanField(default=True)

    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def save(self, *args, **kwargs):
        if not self.username:
            base = self.email.split('@')[0]
            username = base
            counter = 1
            while User.objects.filter(username=username).exclude(pk=self.pk).exists():
                username = f"{base}{counter}"
                counter += 1
            self.username = username
        super().save(*args, **kwargs)

    def __str__(self):
        if self.user_type:
            return f"{self.name}({self.get_user_type_display()})"
        return f"{self.name} (Admin))"


class TutorProfileManager(models.Manager):
    """
    Custom manager for TutorProfile model.
    Provides optimized queries for tutor selection and filtering.
    """
    
    def get_tutors_by_location(self, city, country):
        """
        Get prioritized tutors by location with optimized queries.
        
        Args:
            city: Client's city
            country: Client's country
            
        Returns:
            QuerySet: Tutors prioritized by location with select_related optimization
        """
        # Get all active tutors with optimized queries
        queryset = self.select_related('user').filter(
            user__user_type='tutor',
            user__is_active=True
        )
        
        # Combine with priority: same city > same country > others
        # Using single annotated queryset with Case/When for optimization
        prioritized_queryset = queryset.annotate(
            location_priority=Case(
                When(city__iexact=city, then=Value(1)),
                When(country__iexact=country, then=Value(2)),
                default=Value(3),
                output_field=IntegerField()
            )
        ).order_by('location_priority', 'user__name')
        
        return prioritized_queryset
    
    def get_tutors_categorized_by_location(self, city, country):
        base_qs = self.select_related('user').filter(
            user__user_type='tutor',
            user__is_active=True
        ).prefetch_related('subjects', 'subjects_taught')

        same_city = base_qs.filter(city__iexact=city)
        same_country = base_qs.filter(
            country__iexact=country
        ).exclude(city__iexact=city)
        others = base_qs.exclude(country__iexact=country)
        all_tutors = self.get_tutors_by_location(city, country).prefetch_related(
            'subjects', 'subjects_taught'
        )
        return {
            'same_city': same_city,
            'same_country': same_country,
            'others': others,
            'all': all_tutors
        }

    def get_tutors_by_knowledge_area(self, knowledge_area_slug):
        return TutorProfile.objects.select_related('user').prefetch_related('subjects').filter(
            subjects__knowledge_area__slug=knowledge_area_slug,
            user__is_active=True
        ).distinct()

    def get_profile_for_user(self, user):
        return self.select_related('user').get(user=user)

    def get_or_create_for_user(self, user):
        return self.get_or_create(user=user)


class ClientProfileManager(models.Manager):
    def get_profile_for_user(self, user):
        return self.select_related('user').get(user=user)

    def get_or_create_for_user(self, user):
        return self.get_or_create(user=user)


class TutorProfile(models.Model):
    """Profile for tutors with additional information"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='tutor_profile'
    )
    # ManyToMany relationship with SubjectLevel model (refactorización)
    # Permite especificar materias Y niveles que enseña el tutor
    subjects_taught = models.ManyToManyField(
        'academicTutoring.SubjectLevel',
        related_name='tutors',
        verbose_name='Materias y Niveles',
        blank=True,
        help_text='Materias y niveles educativos que enseña este tutor'
    )
    # DEPRECATED: Mantener por compatibilidad con código legacy
    # TODO: Eliminar después de migración completa
    subjects = models.ManyToManyField(
        Subject,
        related_name='tutors_legacy',
        verbose_name='Materias (Legacy)',
        blank=True,
        help_text='[DEPRECADO] Use subjects_taught en su lugar'
    )
    # Hourly rate for tutoring sessions
    hourly_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Tarifa por Hora (USD)',
        help_text='Precio por hora de tutoría en dólares'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Número de teléfono'
    )
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name='Biografía'
    )
    experience = models.TextField(
        blank=True,
        null=True,
        verbose_name='Experiencia'
    )
    # Location fields for GeoRestrictionMiddleware
    city = models.CharField(
        max_length=100,
        default='Milagro',
        verbose_name='Ciudad'
    )
    country = models.CharField(
        max_length=100,
        default='Ecuador',
        verbose_name='País'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    documents_required = models.BooleanField(
        default=True,
        verbose_name='Documentos Requeridos'
    )

    # Custom manager
    objects = TutorProfileManager()

    class Meta:
        verbose_name = 'Perfil de Tutor'
        verbose_name_plural = 'Perfiles de Tutores'

    def __str__(self):
        return f"Perfil de {self.user.name}"


class ClientProfile(models.Model):
    """Profile for clients/students"""
    objects = ClientProfileManager()
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile'
    )
    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name='Biografía',
        help_text='Cuéntanos un poco sobre ti'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Número de teléfono'
    )
    avatar_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='URL del Avatar',
        help_text='Enlace a tu foto de perfil'
    )
    is_minor = models.BooleanField(
        default=False,
        verbose_name='Es menor de edad'
    )
    parent_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Nombre del padre/tutor legal'
    )
    parent_email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Correo del padre/tutor legal',
        help_text='Requerido para estudiantes menores de edad'
    )
    # Location fields for GeoRestrictionMiddleware
    city = models.CharField(
        max_length=100,
        default='Milagro',
        verbose_name='Ciudad'
    )
    country = models.CharField(
        max_length=100,
        default='Ecuador',
        verbose_name='País'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Cliente'
        verbose_name_plural = 'Perfiles de Clientes'

    def __str__(self):
        return f"Perfil de {self.user.name}"

    def clean(self):
        """Validate parent_email is required when is_minor=True"""
        if self.is_minor and not self.parent_email:
            raise ValidationError({
                'parent_email': 'parent_email is required when is_minor=True.'
            })
