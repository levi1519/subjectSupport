from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator
from django.utils.text import slugify


class Subject(models.Model):
    """Model for subjects/materias that tutors can teach"""
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
    name = models.CharField(max_length=200, verbose_name='Nombre Completo')
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        verbose_name='Tipo de Usuario'
    )
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name', 'user_type']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.name} ({self.get_user_type_display()})"


class TutorProfile(models.Model):
    """Profile for tutors with additional information"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='tutor_profile'
    )
    # ManyToMany relationship with Subject model
    subjects = models.ManyToManyField(
        Subject,
        related_name='tutors',
        verbose_name='Materias',
        blank=True,
        help_text='Materias que enseña este tutor'
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
    city = models.CharField(
        max_length=100,
        default='Quito',
        verbose_name='Ciudad'
    )
    country = models.CharField(
        max_length=100,
        default='Ecuador',
        verbose_name='País'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil de Tutor'
        verbose_name_plural = 'Perfiles de Tutores'

    def __str__(self):
        return f"Perfil de {self.user.name}"


class ClientProfile(models.Model):
    """Profile for clients/students"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile'
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
    city = models.CharField(
        max_length=100,
        default='Quito',
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
