from django.contrib import admin
from .models import Comprobante
from gestion_web.admin_permissions import OperacionEmpleadoMixin

# PagoProxy and FacturaProxy are proxies of gestion_web models and are intentionally not registered here
# to prevent duplicate admin entries. See gestion_web.admin for registered models.

@admin.register(Comprobante)
class ComprobanteAdmin(OperacionEmpleadoMixin, admin.ModelAdmin):
    list_display = ('pedido', 'estado', 'fecha_subida', 'validado_por')
    list_filter = ('estado',)
    readonly_fields = ('fecha_subida',)
