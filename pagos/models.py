from django.db import models
from django.conf import settings
from gestion_web.models import Pago, Factura, Pedido

class PagoProxy(Pago):
    class Meta:
        proxy = True
        app_label = 'pagos'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'

class FacturaProxy(Factura):
    class Meta:
        proxy = True
        app_label = 'pagos'
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'

# Comprobante: almacenará la imagen del comprobante subida por el cliente
class Comprobante(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        VALIDADO = 'VALIDADO', 'Validado'
        RECHAZADO = 'RECHAZADO', 'Rechazado'

    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='comprobante')
    imagen = models.FileField(upload_to='comprobantes/')
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PENDIENTE)
    fecha_subida = models.DateTimeField(auto_now_add=True)
    validado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Comprobante Pedido #{self.pedido.id} - {self.estado}"

    @property
    def is_pdf(self):
        return self.imagen.name.lower().endswith('.pdf')

    @property
    def is_image(self):
        return not self.is_pdf
