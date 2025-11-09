from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, TutorProfile, ClientProfile


class TutorRegistrationForm(UserCreationForm):
    """Form for tutor registration"""
    subjects = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Matemáticas, Física, Química'
        }),
        label='Materias que enseñas'
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad'
        }),
        label='Ciudad',
        initial='Quito'
    )
    country = forms.CharField(
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
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
        self.fields['password2'].label = 'Confirmar Contraseña'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'tutor'
        user.username = self.cleaned_data['email']
        if commit:
            user.save()
            # Create tutor profile
            TutorProfile.objects.create(
                user=user,
                subjects=self.cleaned_data['subjects'],
                city=self.cleaned_data.get('city', 'Quito'),
                country=self.cleaned_data.get('country', 'Ecuador'),
                bio=self.cleaned_data.get('bio', ''),
                experience=self.cleaned_data.get('experience', '')
            )
        return user


class ClientRegistrationForm(UserCreationForm):
    """Form for client/student registration"""
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ciudad'
        }),
        label='Ciudad',
        initial='Quito'
    )
    country = forms.CharField(
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
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar contraseña'
        })
        self.fields['password2'].label = 'Confirmar Contraseña'

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
        label='Correo Electrónico'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        }),
        label='Contraseña'
    )
