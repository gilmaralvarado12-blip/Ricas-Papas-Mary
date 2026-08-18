from datetime import time

from django.utils import timezone


HORA_APERTURA = time(8, 0)
HORA_CIERRE = time(21, 0)


def dentro_del_horario(hora):
    """Indica si una hora está dentro de atención (08:00 incluido, 21:00 cierre)."""
    return HORA_APERTURA <= hora < HORA_CIERRE


def restaurante_atendiendo():
    """Indica si actualmente se pueden confirmar pedidos."""
    return dentro_del_horario(timezone.localtime().time().replace(second=0, microsecond=0))


def horario_atencion_texto():
    return 'El restaurante atiende de 08:00 a 21:00.'
