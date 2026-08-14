# This project already defines a custom user model in gestion_web.models (Usuario).
# To avoid duplicating the database model, this app exposes a proxy to the existing model.
from gestion_web.models import Usuario

class UsuarioProxy(Usuario):
    class Meta:
        proxy = True
        app_label = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
