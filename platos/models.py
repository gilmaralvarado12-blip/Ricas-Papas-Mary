from gestion_web.models import Producto

# Proxy model to organize code under the 'platos' app without moving the DB table
class ProductoProxy(Producto):
    class Meta:
        proxy = True
        app_label = 'platos'
        verbose_name = 'Plato'
        verbose_name_plural = 'Platos'
