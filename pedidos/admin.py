from django.contrib import admin
from django.db import models
from . import models as pedidos_models

for attr in dir(pedidos_models):
    model = getattr(pedidos_models, attr)
    if isinstance(model, type) and issubclass(model, models.Model) and not model._meta.abstract:
        try:
            admin.site.register(model)
        except admin.sites.AlreadyRegistered:
            pass