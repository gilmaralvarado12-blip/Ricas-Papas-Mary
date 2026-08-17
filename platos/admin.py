# ProductoProxy admin intentionally NOT registered to avoid duplicate admin entries.
# The main Producto model is registered in gestion_web.admin.
# If a proxy-specific admin is required, consolidate it in gestion_web.admin to prevent duplicates.
from django.contrib import admin
from .models import Plato, Categoria

admin.site.register(Plato)
admin.site.register(Categoria)