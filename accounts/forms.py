from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, TutorProfile, ClientProfile, Subject


class TutorRegistrationForm(UserCreationForm):
    """Form for tutor registration"""
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all().order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Materias que enseñas',
        help_text='Selecciona todas las materias que puedes enseñar'
    )
    city = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad'
        }),
        label='Ciudad',
        initial='Quito'
    )
    country = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'value': 'Ecuador'
        }),
        label='País',
        initial='Ecuador'
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Cuéntanos sobre ti (opcional)'
        }),
        label='Biografía'
    )
    experience = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Tu experiencia enseñando (opcional)'
        }),
        label='Experiencia'
    )

    class Meta:
        model = User
        fields = ['name', 'email', 'password1', 'password2']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
        }
        labels = {
            'name': 'Nombre Completo',
            'email': 'Correo Electrónico',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password1'].label = 'Contraseña'
        self.fields['password1'].help_text = 'Tu contraseña debe tener al menos 8 caracteres y no puede ser completamente numérica.'

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
        self.fields['password2'].label = 'Confirmar Contraseña'
        self.fields['password2'].help_text = 'Ingresa la misma contraseña para verificación.'

        # Custom error messages
        self.fields['name'].error_messages = {
            'required': 'Por favor ingresa tu nombre completo.',
            'max_length': 'El nombre no puede tener más de 200 caracteres.',
        }
        self.fields['email'].error_messages = {
            'required': 'Por favor ingresa tu correo electrónico.',
            'invalid': 'Por favor ingresa un correo electrónico válido.',
            'unique': 'Este correo electrónico ya está registrado.',
        }
        self.fields['subjects'].error_messages = {
            'required': 'Por favor ingresa las materias que enseñas.',
            'max_length': 'La descripción de materias es demasiado larga.',
        }
        self.fields['city'].error_messages = {
            'required': 'Por favor ingresa tu ciudad.',
            'max_length': 'El nombre de la ciudad es demasiado largo.',
        }
        self.fields['country'].error_messages = {
            'required': 'Por favor ingresa tu país.',
            'max_length': 'El nombre del país es demasiado largo.',
        }

    def clean_email(self):
        """Validate email is unique"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_subjects(self):
        """Validate maximum 5 subjects selected"""
        subjects = self.cleaned_data.get('subjects')
        if subjects and subjects.count() > 5:
            raise ValidationError('Solo puedes seleccionar un máximo de 5 materias.')
        return subjects

    def clean_password2(self):
        """Validate passwords match"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'tutor'
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
            # Create tutor profile
            profile = TutorProfile.objects.create(
                user=user,
                city=self.cleaned_data.get('city', 'Quito'),
                country=self.cleaned_data.get('country', 'Ecuador'),
                bio=self.cleaned_data.get('bio', ''),
                experience=self.cleaned_data.get('experience', '')
            )
            # Save ManyToMany relationships (subjects)
            subjects = self.cleaned_data.get('subjects')
            if subjects:
                profile.subjects.set(subjects)
        return user


class ClientRegistrationForm(UserCreationForm):
    """Form for client/student registration"""
    city = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad'
        }),
        label='Ciudad',
        initial='Quito'
    )
    country = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'value': 'Ecuador'
        }),
        label='País',
        initial='Ecuador'
    )
    is_minor = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Soy menor de edad'
    )
    parent_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del padre o tutor legal'
        }),
        label='Nombre del padre/tutor legal'
    )

    class Meta:
        model = User
        fields = ['name', 'email', 'password1', 'password2']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
        }
        labels = {
            'name': 'Nombre Completo',
            'email': 'Correo Electrónico',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password1'].label = 'Contraseña'
        self.fields['password1'].help_text = 'Tu contraseña debe tener al menos 8 caracteres y no puede ser completamente numérica.'

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
        self.fields['password2'].label = 'Confirmar Contraseña'
        self.fields['password2'].help_text = 'Ingresa la misma contraseña para verificación.'

        # Custom error messages
        self.fields['name'].error_messages = {
            'required': 'Por favor ingresa tu nombre completo.',
            'max_length': 'El nombre no puede tener más de 200 caracteres.',
        }
        self.fields['email'].error_messages = {
            'required': 'Por favor ingresa tu correo electrónico.',
            'invalid': 'Por favor ingresa un correo electrónico válido.',
            'unique': 'Este correo electrónico ya está registrado.',
        }
        self.fields['city'].error_messages = {
            'required': 'Por favor ingresa tu ciudad.',
            'max_length': 'El nombre de la ciudad es demasiado largo.',
        }
        self.fields['country'].error_messages = {
            'required': 'Por favor ingresa tu país.',
            'max_length': 'El nombre del país es demasiado largo.',
        }
        self.fields['parent_name'].error_messages = {
            'max_length': 'El nombre es demasiado largo.',
        }

    def clean_email(self):
        """Validate email is unique"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_password2(self):
        """Validate passwords match"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        return password2

    def clean(self):
        """Validate parent name if minor"""
        cleaned_data = super().clean()
        is_minor = cleaned_data.get('is_minor')
        parent_name = cleaned_data.get('parent_name')

        if is_minor and not parent_name:
            raise ValidationError({
                'parent_name': 'Se requiere el nombre del padre o tutor legal para menores de edad.'
            })

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'client'
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
            # Create client profile
            ClientProfile.objects.create(
                user=user,
                city=self.cleaned_data.get('city', 'Quito'),
                country=self.cleaned_data.get('country', 'Ecuador'),
                is_minor=self.cleaned_data.get('is_minor', False),
                parent_name=self.cleaned_data.get('parent_name', '')
            )
        return user


class LoginForm(AuthenticationForm):
    """Custom login form"""
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo Electrónico',
        error_messages={
            'required': 'Por favor ingresa tu correo electrónico.',
            'invalid': 'Por favor ingresa un correo electrónico válido.',
        }
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        }),
        label='Contraseña',
        error_messages={
            'required': 'Por favor ingresa tu contraseña.',
        }
    )

    error_messages = {
        'invalid_login': 'Por favor ingresa un correo electrónico y contraseña correctos. '
                        'Ten en cuenta que ambos campos pueden ser sensibles a mayúsculas.',
        'inactive': 'Esta cuenta está inactiva.',
    }


class TutorSubjectsForm(forms.ModelForm):
    """
    Formulario para que los tutores gestionen las materias que enseñan.
    Permite selección múltiple de materias existentes.
    """
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all().order_by('name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        label='Materias que enseño',
        help_text='Selecciona todas las materias que puedes enseñar'
    )

    class Meta:
        model = TutorProfile
        fields = ['subjects']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar mensajes de error
        self.fields['subjects'].error_messages = {
            'required': 'Por favor selecciona al menos una materia.',
        }


class ClientProfileEditForm(forms.ModelForm):
    """
    Formulario para editar el perfil del cliente/estudiante.
    Incluye campos del User (email) y ClientProfile (phone_number, bio).
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo Electrónico',
        help_text='Tu correo para notificaciones y comunicación'
    )
    phone_number = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+593 99 999 9999'
        }),
        label='Número de Teléfono',
        help_text='Número de contacto para emergencias'
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Cuéntanos un poco sobre ti, tus intereses académicos, etc.'
        }),
        label='Biografía',
        help_text='Información adicional sobre ti (opcional)'
    )

    class Meta:
        model = ClientProfile
        fields = ['phone_number', 'bio']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Verificar que el email no esté en uso por otro usuario
        if User.objects.filter(email=email).exclude(id=self.user.id).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            # Actualizar email del usuario
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile


class TutorProfileEditForm(forms.ModelForm):
    """
    Formulario para editar el perfil del tutor.
    Incluye campos del User (email) y TutorProfile (phone_number, bio, experience, hourly_rate).
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Correo Electrónico',
        help_text='Tu correo para notificaciones y comunicación'
    )
    phone_number = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+593 99 999 9999'
        }),
        label='Número de Teléfono',
        help_text='Número de contacto para estudiantes'
    )
    bio = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Cuéntanos sobre tu experiencia, metodología de enseñanza, etc.'
        }),
        label='Biografía',
        help_text='Información sobre ti que verán los estudiantes'
    )
    experience = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ej: 5 años enseñando matemáticas a nivel universitario...'
        }),
        label='Experiencia Profesional',
        help_text='Tu experiencia como tutor o docente (opcional)'
    )
    hourly_rate = forms.DecimalField(
        required=False,
        max_digits=6,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '15.00',
            'step': '0.50'
        }),
        label='Tarifa por Hora (USD)',
        help_text='Precio por hora de tutoría (opcional)'
    )

    class Meta:
        model = TutorProfile
        fields = ['phone_number', 'bio', 'experience', 'hourly_rate']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['email'].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Verificar que el email no esté en uso por otro usuario
        if User.objects.filter(email=email).exclude(id=self.user.id).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_hourly_rate(self):
        rate = self.cleaned_data.get('hourly_rate')
        if rate and rate < 0:
            raise ValidationError('La tarifa no puede ser negativa.')
        if rate and rate > 9999:
            raise ValidationError('La tarifa es demasiado alta.')
        return rate

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            # Actualizar email del usuario
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile
