from gestion_web.models import Entrega

class EntregaProxy(Entrega):
    class Meta:
        proxy = True
        app_label = 'entregas'
        verbose_name = 'Entrega'
        verbose_name_plural = 'Entregas'
