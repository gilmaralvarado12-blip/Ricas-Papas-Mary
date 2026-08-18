import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

## Obtenemos dinámicamente tu modelo 'gestion_web.Usuario'
UsuarioActual = get_user_model()


class RegistroForm(UserCreationForm):
    acepta_politica_datos = forms.BooleanField(
        required=True,
        label='Acepto la política de protección de datos personales',
        error_messages={'required': 'Debes aceptar la política de protección de datos para crear la cuenta.'},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    password1 = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
    )
    password2 = forms.CharField(
        label='Confirmación de contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password',
        })
    )

    class Meta(UserCreationForm.Meta):
        model = UsuarioActual
        fields = ('username',)
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'autocomplete': 'username',
            }),
        }

    def clean_username(self):
        username = (self.cleaned_data.get('username') or '').strip()
        if not username:
            raise ValidationError('El nombre de usuario es obligatorio.')
        if re.search(r'<[^>]+>|["\']', username):
            raise ValidationError('El nombre de usuario contiene caracteres no permitidos.')
        if len(username) < 3:
            raise ValidationError('El nombre de usuario debe tener al menos 3 caracteres.')
        return username

    def clean_password1(self):
        password = self.cleaned_data.get('password1') or ''
        if len(password) < 8:
            raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r'[A-Z]', password):
            raise ValidationError('La contraseña debe incluir al menos una letra mayúscula.')
        if not re.search(r'[0-9]', password):
            raise ValidationError('La contraseña debe incluir al menos un número.')
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError('La contraseña debe incluir al menos un símbolo especial.')
        return password