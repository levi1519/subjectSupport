from django import forms
from .models import TutorLead, ClassSession, NotificacionExpansion
from apps.accounts.models import User
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
        fields = ['subject', 'scheduled_date', 'scheduled_time', 'duration', 'notes', 'material_url']
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
            'material_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://ejemplo.com/material-de-clase.pdf'
            }),
        }
        labels = {
            'subject': 'Materia',
            'scheduled_date': 'Fecha',
            'scheduled_time': 'Hora',
            'duration': 'Duración',
            'notes': 'Notas',
            'material_url': 'Material de clase (URL)'
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
            'material_url': {
                'invalid': 'Por favor ingresa una URL válida.',
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
        fields = ['meeting_platform', 'meeting_url', 'notes']
        widgets = {
            'meeting_platform': forms.Select(attrs={
                'class': 'form-select'
            }),
            'meeting_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://meet.google.com/xxx-xxxx-xxx'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Agrega notas adicionales para la sesión (opcional)'
            }),
        }
        labels = {
            'meeting_platform': 'Plataforma de Reunión',
            'meeting_url': 'Enlace de la reunión',
            'notes': 'Notas adicionales'
        }
        error_messages = {
            'meeting_platform': {
                'required': 'Por favor selecciona una plataforma de reunión.',
                'invalid_choice': 'Por favor selecciona una opción válida.',
            },
        }


class NotificacionExpansionForm(forms.ModelForm):
    """
    Form para solicitar notificación cuando el servicio llegue a una ciudad.
    Usado en la página de "servicio no disponible".
    """

    class Meta:
        model = NotificacionExpansion
        fields = ['email', 'ciudad_deseada', 'provincia_deseada']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'tu.correo@ejemplo.com',
                'required': True
            }),
            'ciudad_deseada': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Quito, Guayaquil, Cuenca',
                'required': True
            }),
            'provincia_deseada': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Pichincha, Guayas, Azuay (opcional)'
            }),
        }
        labels = {
            'email': 'Tu correo electrónico',
            'ciudad_deseada': '¿A qué ciudad quieres que lleguemos?',
            'provincia_deseada': 'Provincia (opcional)',
        }
        help_texts = {
            'email': 'Te avisaremos cuando el servicio esté disponible en tu ciudad',
            'ciudad_deseada': 'Ingresa el nombre de tu ciudad',
            'provincia_deseada': 'Ayuda a identificar mejor tu ubicación',
        }
        error_messages = {
            'email': {
                'required': 'Por favor ingresa tu correo electrónico.',
                'invalid': 'Por favor ingresa un correo electrónico válido.',
            },
            'ciudad_deseada': {
                'required': 'Por favor ingresa el nombre de tu ciudad.',
                'max_length': 'El nombre de la ciudad es demasiado largo.',
            },
        }


class SessionMaterialForm(forms.Form):
    """
    Formulario para adjuntar materiales a una sesión.
    Soporta URL, archivo, o ambos en la misma solicitud.
    """
    material_url = forms.URLField(
        required=False,
        label='Enlace (URL)',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://youtube.com/... o https://drive.google.com/...'
        }),
        help_text='Enlace a material de estudio, video o documento en la nube'
    )
    material_file = forms.FileField(
        required=False,
        label='Archivo adjunto',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.jpg,.jpeg,.png,.doc,.docx,.ppt,.pptx,.xlsx'
        }),
        help_text='PDF, imagen o documento de Office (max. 5MB)'
    )

    def clean(self):
        from apps.academicTutoring.models import PlatformConfig
        cleaned = super().clean()
        config = PlatformConfig.get_config()

        material_file = cleaned.get('material_file')
        if material_file:
            max_bytes = config.max_file_size_mb * 1024 * 1024
            if material_file.size > max_bytes:
                self.add_error('material_file',
                    f'El archivo supera el limite de {config.max_file_size_mb}MB.')

            allowed = [f'.{ext.strip()}' for ext in config.allowed_file_types.split(',')]
            import os
            ext = os.path.splitext(material_file.name)[1].lower()
            if ext not in allowed:
                self.add_error('material_file',
                    f'Tipo de archivo no permitido. Permitidos: {config.allowed_file_types}')

        return cleaned
