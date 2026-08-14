from gestion_web.models import Reserva

class ReservaProxy(Reserva):
    class Meta:
        proxy = True
        app_label = 'reservas'
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
