from django import forms
from .models import TutorLead, ClassSession
from accounts.models import User
from datetime import date


class TutorLeadForm(forms.ModelForm):
    """Form for collecting tutor lead information"""

    class Meta:
        model = TutorLead
        fields = ['name', 'email', 'subject']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tu nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu.correo@ejemplo.com'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Materia que quieres enseñar (ej: Matemáticas, Física)'
            }),
        }
        labels = {
            'name': 'Nombre Completo',
            'email': 'Correo Electrónico',
            'subject': 'Materia',
        }
        error_messages = {
            'name': {
                'required': 'Por favor ingresa tu nombre completo.',
                'max_length': 'El nombre no puede tener más de 200 caracteres.',
            },
            'email': {
                'required': 'Por favor ingresa tu correo electrónico.',
                'invalid': 'Por favor ingresa un correo electrónico válido.',
            },
            'subject': {
                'required': 'Por favor ingresa la materia que quieres enseñar.',
                'max_length': 'El nombre de la materia es demasiado largo.',
            },
        }


class SessionRequestForm(forms.ModelForm):
    """Form for clients to request a session with a tutor"""

    class Meta:
        model = ClassSession
        fields = ['subject', 'scheduled_date', 'scheduled_time', 'duration', 'notes']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Matemáticas - Álgebra'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': date.today().isoformat()
            }),
            'scheduled_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'duration': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Temas específicos o detalles adicionales (opcional)'
            }),
        }
        labels = {
            'subject': 'Materia',
            'scheduled_date': 'Fecha',
            'scheduled_time': 'Hora',
            'duration': 'Duración',
            'notes': 'Notas'
        }
        error_messages = {
            'subject': {
                'required': 'Por favor ingresa la materia.',
                'max_length': 'El nombre de la materia es demasiado largo.',
            },
            'scheduled_date': {
                'required': 'Por favor selecciona una fecha.',
                'invalid': 'Por favor ingresa una fecha válida.',
            },
            'scheduled_time': {
                'required': 'Por favor selecciona una hora.',
                'invalid': 'Por favor ingresa una hora válida.',
            },
            'duration': {
                'required': 'Por favor selecciona la duración de la sesión.',
                'invalid_choice': 'Por favor selecciona una opción válida.',
            },
        }

    def clean_scheduled_date(self):
        """Validate that the date is in the future"""
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date < date.today():
            raise forms.ValidationError('La fecha debe ser hoy o en el futuro.')
        return scheduled_date


class SessionConfirmationForm(forms.ModelForm):
    """Form for tutors to confirm or add notes to a session"""

    class Meta:
        model = ClassSession
        fields = ['meeting_platform', 'notes']
        widgets = {
            'meeting_platform': forms.Select(attrs={
                'class': 'form-select'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Agrega notas adicionales para la sesión (opcional)'
            }),
        }
        labels = {
            'meeting_platform': 'Plataforma de Reunión',
            'notes': 'Notas adicionales'
        }
        error_messages = {
            'meeting_platform': {
                'required': 'Por favor selecciona una plataforma de reunión.',
                'invalid_choice': 'Por favor selecciona una opción válida.',
            },
        }
