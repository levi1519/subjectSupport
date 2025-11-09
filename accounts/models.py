from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import EmailValidator


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
    subjects = models.CharField(
        max_length=500,
        help_text='Materias que enseña (separadas por comas)',
        verbose_name='Materias'
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
