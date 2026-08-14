from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

Usuario = get_user_model()


def _normalizar_telefono(valor):
    if not valor:
        return ''
    limpio = ''.join(ch for ch in valor if ch.isdigit() or ch == '+')
    return limpio


class UsuarioBaseForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono']

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('El correo electrónico es obligatorio.')

        existe = Usuario.objects.filter(email__iexact=email)
        if self.instance and self.instance.pk:
            existe = existe.exclude(pk=self.instance.pk)
        if existe.exists():
            raise ValidationError('Ya existe un usuario con este correo electrónico.')
        return email

    def clean_telefono(self):
        telefono = _normalizar_telefono(self.cleaned_data.get('telefono'))
        if telefono and len(telefono) < 7:
            raise ValidationError('El teléfono debe tener al menos 7 dígitos.')
        return telefono


class PerfilClienteForm(UsuarioBaseForm):
    pass


class UsuarioAdminCreateForm(UserCreationForm, UsuarioBaseForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'rol', 'is_active']


class UsuarioAdminUpdateForm(UsuarioBaseForm):
    class Meta(UsuarioBaseForm.Meta):
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono', 'rol', 'is_active']
