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


class SubjectManager(models.Manager):
    def get_subjects_for_grouping(self):
        return self.select_related('knowledge_area').order_by('knowledge_area__name', 'name')


class Subject(models.Model):
    """Model for subjects/materias that tutors can teach"""
    objects = SubjectManager()
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
    
    def get_tutors_by_knowledge_area(self, knowledge_area_slug):
        return self.select_related('user').prefetch_related(
            'subjects',
            'subjects__knowledge_area',
            'subjects_taught'
        ).filter(
            subjects__knowledge_area__slug=knowledge_area_slug,
            user__user_type='tutor',
            user__is_active=True
        ).distinct()

    def get_tutors_fallback(self):
        """Fallback queryset returning all active tutors ordered by name."""
        from apps.academicTutoring.models import CountryConfig
        active_codes = CountryConfig.objects.filter(active=True).values_list('country_code', flat=True)
        return self.select_related('user').prefetch_related('subjects').filter(
            user__user_type='tutor',
            user__is_active=True,
            user__country_code__in=active_codes
        ).order_by('user__name')

    def filter_by_search(self, queryset, search_query):
        """Filter tutors by name or subject."""
        if not search_query:
            return queryset
        return queryset.filter(
            Q(user__name__icontains=search_query) |
            Q(subjects_taught__name__icontains=search_query)
        ).distinct()

    def get_tutors_by_country_priority(self, country_code):
        """
        Returns all active tutors ordered by country proximity.
        Same country first (using User.country_code), then others.
        """
        from apps.academicTutoring.models import CountryConfig
        active_codes = CountryConfig.objects.filter(active=True).values_list('country_code', flat=True)
        return self.select_related('user').prefetch_related(
            'subjects', 'subjects__knowledge_area'
        ).filter(
            user__user_type='tutor',
            user__is_active=True,
            user__country_code__in=active_codes
        ).annotate(
            country_priority=Case(
                When(user__country_code__iexact=country_code, then=Value(1)),
                default=Value(2),
                output_field=IntegerField()
            )
        ).order_by('country_priority', 'user__name')

    def get_tutors_filtered_by_country(self, country_code):
        """
        Returns active tutors from a specific country only.
        Filters by User.country_code captured at registration.
        """
        from apps.academicTutoring.models import CountryConfig
        active_codes = CountryConfig.objects.filter(active=True).values_list('country_code', flat=True)
        return self.select_related('user').prefetch_related(
            'subjects', 'subjects__knowledge_area'
        ).filter(
            user__user_type='tutor',
            user__is_active=True,
            user__country_code__iexact=country_code,
            user__country_code__in=active_codes
        ).order_by('user__name')

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
    birth_date = models.DateField(null=True, blank=True, verbose_name='Fecha de nacimiento')
    cedula = models.CharField(max_length=20, blank=True, null=True, verbose_name='Cédula / Identificación')
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

    @property
    def age(self):
        if not self.birth_date:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))


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
    birth_date = models.DateField(null=True, blank=True, verbose_name='Fecha de nacimiento')
    cedula = models.CharField(max_length=20, blank=True, null=True, verbose_name='Cédula / Identificación')
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
