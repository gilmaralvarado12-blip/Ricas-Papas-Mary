from django.contrib import admin
from django.db import models
from . import models as platos_models

# Registrar dinámicamente los modelos existentes en platos/models.py
for attr in dir(platos_models):
    model = getattr(platos_models, attr)
    if isinstance(model, type) and issubclass(model, models.Model) and not model._meta.abstract:
        try:
            admin.site.register(model)
        except admin.sites.AlreadyRegistered:
            pass