# This project already defines a custom user model in gestion_web.models (Usuario).
# To avoid duplicating the database model, this app exposes proxies to the existing model.
from gestion_web.models import Usuario


class UsuarioProxy(Usuario):
    class Meta:
        proxy = True
        app_label = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']


class DueñoProxy(UsuarioProxy):
    class Meta:
        proxy = True
        app_label = 'usuarios'
        verbose_name = 'Dueño'
        verbose_name_plural = 'Dueños'
        ordering = ['username']


class EmpleadoProxy(UsuarioProxy):
    class Meta:
        proxy = True
        app_label = 'usuarios'
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'
        ordering = ['username']


class RepartidorProxy(UsuarioProxy):
    class Meta:
        proxy = True
        app_label = 'usuarios'
        verbose_name = 'Repartidor'
        verbose_name_plural = 'Repartidores'
        ordering = ['username']
