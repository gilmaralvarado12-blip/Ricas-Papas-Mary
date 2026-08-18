from gestion_web.models import Insumo, Insumo_Producto

class InsumoProxy(Insumo):
    class Meta:
        proxy = True
        app_label = 'insumos'
        verbose_name = 'Insumo'
        verbose_name_plural = 'Insumos'

class InsumoProductoProxy(Insumo_Producto):
    class Meta:
        proxy = True
        app_label = 'insumos'
        verbose_name = 'Insumo por Producto'
        verbose_name_plural = 'Insumos por Producto'
