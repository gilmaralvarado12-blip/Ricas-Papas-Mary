from gestion_web.models import Mesa

class MesaProxy(Mesa):
    class Meta:
        proxy = True
        app_label = 'mesas'
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'
