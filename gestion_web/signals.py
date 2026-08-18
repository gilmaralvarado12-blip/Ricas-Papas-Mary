from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import DetallePedido, Insumo_Producto

@receiver(post_save, sender=DetallePedido)
def descontar_insumos_bodega(sender, instance, created, **kwargs):
    if created:
        # Obtiene las relaciones insumo-producto para el producto vendido
        insumos_producto = Insumo_Producto.objects.filter(producto=instance.producto)
        
        for item in insumos_producto:
            insumo = item.insumo
            total_descuento = item.cantidad_utilizada * instance.cantidad
            
            # Cambiado 'cantidad_disponible' por 'stock'
            insumo.stock -= total_descuento
            insumo.save()