from django.db import models
from django.conf import settings
from django.utils import timezone
from gestion_web.models import Pedido, DetallePedido, Producto

class PedidoProxy(Pedido):
    class Meta:
        proxy = True
        app_label = 'pedidos'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

class DetallePedidoProxy(DetallePedido):
    class Meta:
        proxy = True
        app_label = 'pedidos'
        verbose_name = 'Detalle de Pedido'
        verbose_name_plural = 'Detalles de Pedido'

# Carrito persistente
class Cart(models.Model):
    class Estado(models.TextChoices):
        OPEN = 'OPEN', 'Abierto'
        ORDERED = 'ORDERED', 'Ordenado'

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='carts')
    session_key = models.CharField(max_length=64, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.OPEN)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    def __str__(self):
        owner = self.cliente.username if self.cliente else f"session:{self.session_key}"
        return f"Carrito {self.id} ({owner}) - {self.get_estado_display()}"

    def total(self):
        return sum([item.subtotal() for item in self.items.all()])

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ('cart', 'producto')

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    def subtotal(self):
        return float(self.precio_unitario) * int(self.cantidad)
