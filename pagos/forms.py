from django import forms
from .models import Comprobante

class ComprobanteForm(forms.ModelForm):
    class Meta:
        model = Comprobante
        fields = ['imagen']
        widgets = {
            'imagen': forms.ClearableFileInput(attrs={'accept': 'image/*,application/pdf'})
        }

    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if imagen:
            valid_mime = [
                'image/jpeg',
                'image/png',
                'image/gif',
                'image/webp',
                'application/pdf',
            ]
            if hasattr(imagen, 'content_type') and imagen.content_type not in valid_mime:
                raise forms.ValidationError('Solo se permiten imágenes o archivos PDF para el comprobante.')
        return imagen