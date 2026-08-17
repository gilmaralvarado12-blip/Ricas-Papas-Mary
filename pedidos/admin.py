# PedidoProxy admin intentionally NOT registered to avoid duplicate admin entries.
# The main Pedido model is registered in gestion_web.admin.
# DetallePedido proxy admin is also intentionally not registered here.
from django.contrib import admin
from .models import Plato, Categoria, Pedido # Usa los nombres exactos de tu models.py

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'disponible')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)