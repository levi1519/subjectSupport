from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, TutorProfile, ClientProfile, Subject


class TutorRegistrationForm(UserCreationForm):
    """Form for tutor registration"""
    subjects_taught = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all().order_by('knowledge_area__name', 'name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='Materias que enseñas',
        help_text='Selecciona hasta 5 materias'
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
    cedula = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 0912345678'}),
        label='Cédula / ID Nacional',
        help_text='Documento de identidad de tu país.',
    )
    university_name = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Universidad de Guayaquil, ESPOL, UCSG'
        }),
        label='Universidad / Institución donde enseñas',
        help_text='Si actualmente enseñas en una universidad o institución'
    )
    is_foreign_institution = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input',
                                            'id': 'id_is_foreign_institution'}),
        label='La institución es del extranjero'
    )
    university_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://www.universidad.edu',
            'id': 'university_url_field'
        }),
        label='URL de la institución extranjera',
        help_text='Requerido si la institución es extranjera'
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
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/webp'
        }),
        label='Foto de Perfil',
        help_text='Sube tu foto (JPG, PNG, máximo 5MB). Opcional.'
    )
    cv_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
        label='Curriculum Vitae (PDF)',
        help_text='Sube tu CV en formato PDF. Maximo 5MB.'
    )
    employment_status = forms.ChoiceField(
        choices=[('', 'Selecciona tu situacion laboral')] + [
            ('desempleado', 'Desempleado / Freelancer'),
            ('empleado_no_docente', 'Empleado (no sector educativo)'),
            ('docente_activo', 'Docente activo en institucion'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Situacion laboral actual',
    )
    education_level = forms.ChoiceField(
        choices=[('', 'Selecciona tu nivel educativo')] + [
            ('bachiller', 'Bachiller'),
            ('tecnico', 'Tecnico / Tecnologo'),
            ('universitario', 'Universitario / Egresado'),
            ('posgrado', 'Posgrado (Maestria / Doctorado)'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Nivel de educacion alcanzado',
    )
    education_certificate_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        label='Certificado de nivel educativo',
        help_text='Titulo, diploma o certificado que acredite el nivel declarado'
    )
    institution_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
        label='ID de institucion seleccionada'
    )
    institution_manual = forms.CharField(
        required=False,
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de la institucion si no aparece en la lista'
        }),
        label='Institucion (ingreso manual)',
    )
    institutional_credential_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        label='Credencial institucional',
        help_text='Carnet o ID de la institucion donde eres docente activo'
    )
    knowledge_document_file = forms.FileField(
        required=False,
        label='Justificacion de conocimientos (PDF)',
        help_text='Documento que justifique tu dominio del area (tesis, certificado, portafolio, etc.)'
    )
    birth_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Fecha de nacimiento',
        help_text='Debes ser mayor de 18 anos para registrarte como tutor.',
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
        self.fields['subjects_taught'].error_messages = {
            'required': 'Por favor ingresa las materias que enseñas.',
            'max_length': 'La descripción de materias es demasiado larga.',
        }

    def clean_email(self):
        """Validate email is unique"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_subjects_taught(self):
        from apps.academicTutoring.models import PlatformConfig
        subjects = self.cleaned_data.get('subjects_taught')
        if not subjects or subjects.count() == 0:
            raise ValidationError('Debes seleccionar al menos una materia.')
        max_subjects = PlatformConfig.get_config().max_subjects_per_tutor
        if subjects.count() > max_subjects:
            raise ValidationError(
                f'Solo puedes seleccionar un maximo de {max_subjects} materias.'
            )
        return subjects

    def clean_password2(self):
        """Validate passwords match"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Las contraseñas no coinciden.')
        return password2

    def clean(self):
        cleaned_data = super().clean()
        from apps.academicTutoring.models import PlatformConfig
        config = PlatformConfig.get_config()

        # Validar CV
        cv_file = cleaned_data.get('cv_file')
        if config.require_tutor_cv and not cv_file:
            self.add_error('cv_file', 'El CV en PDF es obligatorio para registrarte como tutor.')

        # Validar tamano y extension del CV
        if cv_file:
            max_bytes = config.max_file_size_mb * 1024 * 1024
            if cv_file.size > max_bytes:
                self.add_error('cv_file', f'El archivo supera el limite de {config.max_file_size_mb}MB.')
            if not cv_file.name.lower().endswith('.pdf'):
                self.add_error('cv_file', 'El CV debe estar en formato PDF.')

        # Validar credencial institucional si es docente activo
        employment_status = cleaned_data.get('employment_status')
        institutional_file = cleaned_data.get('institutional_credential_file')
        if employment_status == 'docente_activo':
            if config.require_tutor_institutional_credential and not institutional_file:
                self.add_error(
                    'institutional_credential_file',
                    'Debes subir tu carnet o ID institucional si eres docente activo.'
                )

        # Validar certificado educativo
        education_cert = cleaned_data.get('education_certificate_file')
        if config.require_tutor_education_certificate and not education_cert:
            self.add_error(
                'education_certificate_file',
                'Debes subir el certificado de tu nivel educativo.'
            )

        # Validar documento de conocimientos
        knowledge_doc = cleaned_data.get('knowledge_document_file')
        if config.require_tutor_knowledge_document and not knowledge_doc:
            self.add_error('knowledge_document_file', 'Este documento es requerido segun la configuracion de la plataforma.')
        if knowledge_doc:
            max_mb = config.max_file_size_mb
            if knowledge_doc.size > max_mb * 1024 * 1024:
                self.add_error('knowledge_document_file', f'El archivo no debe superar {max_mb}MB.')
            if not knowledge_doc.name.lower().endswith('.pdf'):
                self.add_error('knowledge_document_file', 'Solo se aceptan archivos PDF.')

        return cleaned_data

    def clean_birth_date(self):
        from datetime import date
        from apps.academicTutoring.models import PlatformConfig
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
            min_age = PlatformConfig.get_config().min_tutor_age
            if age < min_age:
                raise forms.ValidationError(
                    f'Debes tener al menos {min_age} anos para registrarte como tutor.'
                )
        return birth_date

    def save(self, commit=True, country_code=''):
        user = super().save(commit=False)
        user.user_type = 'tutor'
        user.username = self.cleaned_data['email']
        user.country_code = country_code
        if commit:
            user.save()
            # Create tutor profile
            profile = TutorProfile.objects.create(
                user=user,
                bio=self.cleaned_data.get('bio', ''),
                experience=self.cleaned_data.get('experience', ''),
                phone_number=self.cleaned_data.get('phone_number', '')
            )
            profile.cedula = self.cleaned_data.get('cedula', '')
            if self.cleaned_data.get('avatar'):
                profile.avatar = self.cleaned_data.get('avatar')
            profile.university_name = self.cleaned_data.get('university_name', '')
            profile.university_url = self.cleaned_data.get('university_url', '')
            profile.is_foreign_institution = self.cleaned_data.get('is_foreign_institution', False)
            if self.cleaned_data.get('university_name'):
                profile.university_name = self.cleaned_data['university_name']
            if self.cleaned_data.get('cv_file'):
                profile.cv_file = self.cleaned_data['cv_file']
            if self.cleaned_data.get('institutional_credential_file'):
                profile.institutional_credential_file = self.cleaned_data['institutional_credential_file']
            profile.save()
            # Save ManyToMany relationships (subjects)
            subjects = self.cleaned_data.get('subjects_taught')
            if subjects:
                profile.subjects_taught.set(subjects)
        return user


class ClientRegistrationForm(UserCreationForm):
    """Form for client/student registration"""
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
    parent_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'correo@ejemplo.com'
        }),
        label='Email del tutor legal'
    )
    cedula = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 0912345678'}),
        label='Cédula / Identificación',
    )
    university_name = forms.CharField(
        required=True,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Universidad de Guayaquil, ESPOL'
        }),
        label='Universidad donde estudias',
        help_text='Universidad en la que estás matriculado actualmente'
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/webp'
        }),
        label='Foto de Perfil',
        help_text='Sube tu foto (JPG, PNG, máximo 5MB). Opcional.'
    )
    student_type = forms.ChoiceField(
        choices=[('', 'Selecciona tu tipo de estudiante')] + [
            ('universitario', 'Estudiante universitario'),
            ('autodidacta', 'Autodidacta / Aprendiz independiente'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Como describirias tu perfil de aprendizaje?',
    )
    id_document_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        label='Cedula de identidad',
        help_text='PDF o imagen de tu cedula vigente'
    )
    enrollment_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'}),
        label='Carnet o constancia de matricula',
        help_text='Carnet estudiantil vigente o constancia de matricula'
    )
    institution_id = forms.IntegerField(
        required=False,
        widget=forms.HiddenInput(),
    )
    institution_manual = forms.CharField(
        required=False,
        max_length=300,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de tu institucion si no aparece en la lista'
        }),
        label='Institucion (ingreso manual)',
    )
    birth_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Fecha de nacimiento',
        help_text='Requerida para verificar si eres menor de edad.',
    )
    phone_number = forms.CharField(
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+593 99 999 9999'
        }),
        label='Número de Teléfono Celular',
        help_text='Número de contacto para emergencias.'
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

    def clean_birth_date(self):
        from datetime import date
        from apps.academicTutoring.models import PlatformConfig
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date:
            today = date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
            config = PlatformConfig.get_config()
            min_age = config.min_student_age
            if age < min_age:
                raise forms.ValidationError(
                    f'Debes tener al menos {min_age} anos para registrarte como estudiante.'
                )
            self.calculated_is_minor = age < 18
        return birth_date

    def clean(self):
        cleaned_data = super().clean()
        from apps.academicTutoring.models import PlatformConfig
        config = PlatformConfig.get_config()

        is_minor = cleaned_data.get('is_minor')
        parent_name = cleaned_data.get('parent_name')
        student_type = cleaned_data.get('student_type')

        # Validar tutor legal si es menor
        if is_minor:
            if not parent_name:
                self.add_error('parent_name', 'Se requiere el nombre del padre o tutor legal para menores de edad.')
            parent_email = cleaned_data.get('parent_email')
            if not parent_email:
                self.add_error('parent_email', 'Se requiere el email del padre o tutor legal para menores de edad.')
        else:
            # Validar cedula para mayores de edad
            id_doc = cleaned_data.get('id_document_file')
            if config.require_student_id_document and not id_doc:
                self.add_error(
                    'id_document_file',
                    'Debes subir tu cedula de identidad.'
                )

        # Validar constancia de matricula si es universitario
        enrollment = cleaned_data.get('enrollment_file')
        if not is_minor and student_type == 'universitario' and config.require_student_enrollment_certificate and not enrollment:
            self.add_error(
                'enrollment_file',
                'Debes subir tu carnet o constancia de matricula como estudiante universitario.'
            )

        return cleaned_data

    def save(self, commit=True, country_code=''):
        user = super().save(commit=False)
        user.user_type = 'client'
        user.username = self.cleaned_data['email']
        user.country_code = country_code
        if commit:
            user.save()
            # Create client profile
            profile = ClientProfile.objects.create(
                user=user,
                is_minor=self.cleaned_data.get('is_minor', False),
                parent_name=self.cleaned_data.get('parent_name', ''),
                parent_email=self.cleaned_data.get('parent_email', '')
            )
            profile.cedula = self.cleaned_data.get('cedula', '')
            if self.cleaned_data.get('avatar'):
                profile.avatar = self.cleaned_data.get('avatar')
            profile.university_name = self.cleaned_data.get('university_name', '')
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            if self.cleaned_data.get('university_name'):
                profile.university_name = self.cleaned_data['university_name']
            if self.cleaned_data.get('id_document_file'):
                profile.id_document_file = self.cleaned_data['id_document_file']
            profile.save()
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
    subjects_taught = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all().order_by('knowledge_area__name', 'name'),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        label='Materias que enseño',
        help_text='Selecciona todas las materias que puedes enseñar (mantén Ctrl/Cmd para selección múltiple)'
    )

    class Meta:
        model = TutorProfile
        fields = ['subjects_taught']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar mensajes de error
        self.fields['subjects_taught'].error_messages = {
            'required': 'Por favor selecciona al menos una materia.',
        }

    def clean_subjects_taught(self):
        subjects = self.cleaned_data.get('subjects_taught')
        if subjects and subjects.count() > 5:
            raise forms.ValidationError(
                'Solo puedes seleccionar un máximo de 5 materias. '
                'Has seleccionado %(count)d.',
                code='too_many',
                params={'count': subjects.count()}
            )
        return subjects


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
    cedula = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 0912345678'}),
        label='Cédula / Identificación',
    )
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Fecha de nacimiento',
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/webp'
        }),
        label='Foto de Perfil',
        help_text='Sube tu foto (JPG, PNG, máximo 5MB). Opcional.'
    )
    document_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label='Documento',
        help_text='Actualiza tu documento de verificación (opcional)'
    )

    class Meta:
        model = ClientProfile
        fields = ['phone_number', 'bio', 'cedula', 'birth_date', 'avatar', 'university_name', 'document_file']
        # Note: 'avatar' is an ImageField on ClientProfile model

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

        from apps.academicTutoring.models import Institution
        institution_id = self.cleaned_data.get('institution_id')
        institution_manual = self.cleaned_data.get('institution_manual', '').strip()
        if institution_id:
            try:
                profile.institution = Institution.objects.get(pk=institution_id, active=True)
            except Institution.DoesNotExist:
                pass
        elif institution_manual:
            inst, _ = Institution.objects.get_or_create(
                name=institution_manual,
                defaults={'type': 'universidad', 'is_manual': True, 'needs_review': True, 'active': True}
            )
            profile.institution = inst
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
    cedula = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 0912345678'}),
        label='Cédula / Identificación',
    )
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Fecha de nacimiento',
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        label='Foto de Perfil',
        help_text='Sube una foto (JPG, PNG, máximo 5MB)'
    )
    document_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        label='Documento',
        help_text='Actualiza tu documento de verificación (opcional)'
    )

    class Meta:
        model = TutorProfile
        fields = ['phone_number', 'bio', 'experience', 'hourly_rate', 'cedula', 'birth_date', 'avatar', 'university_name', 'document_file']

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
        if rate is not None and rate > 50:
            raise forms.ValidationError('La tarifa máxima permitida es $50/hora.')
        if rate is not None and rate < 0:
            raise forms.ValidationError('La tarifa no puede ser negativa.')
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
