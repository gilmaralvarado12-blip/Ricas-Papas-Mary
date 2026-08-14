from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from gestion_web.models import Reserva

@login_required
def crear_reserva(request):
    # Delegate to gestion_web.crear_reserva which performs assignment
    from gestion_web.views import crear_reserva as gw_crear
    return gw_crear(request)

@login_required
def mis_reservas(request):
    reservas = list(Reserva.objects.filter(cliente=request.user).order_by('-fecha'))
    # Añadir atributo legible para estado en cada reserva
    for r in reservas:
        try:
            r.estado_display = r.get_estado_display()
        except Exception:
            r.estado_display = str(r.estado)
    return render(request, 'reservas/mis_reservas.html', {'reservas': reservas})
