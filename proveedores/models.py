from gestion_web.models import Proveedor

class ProveedorProxy(Proveedor):
    class Meta:
        proxy = True
        app_label = 'proveedores'
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'
