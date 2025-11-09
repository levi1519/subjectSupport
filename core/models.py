from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


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
