from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from gestion_web.models import Entrega, Pedido, Pago
from gestion_web.views import _requiere_rol
from urllib.parse import quote_plus

# permission helper
def is_empleado_or_admin(user):
    try:
        return user.rol in ('EMPLEADO', 'ADMIN')
    except Exception:
        return False

@login_required
@_requiere_rol('EMPLEADO', 'ADMIN', 'REPARTIDOR')
def lista_entregas(request):
    entregas = Entrega.objects.select_related(
        'pedido__cliente',
        'pedido__pago',
        'pedido__comprobante',
    ).prefetch_related('pedido__detalles__producto').order_by('-pedido__fecha_creacion')

    can_update_estado = getattr(request.user, 'rol', None) in ('EMPLEADO', 'ADMIN', 'REPARTIDOR')

    for entrega in entregas:
        entrega.pedido_estado_display = entrega.pedido.get_estado_display()
        entrega.pago_actual = getattr(entrega.pedido, 'pago', None)
        has_coords = entrega.latitud is not None and entrega.longitud is not None
        if has_coords:
            destination = f'{entrega.latitud},{entrega.longitud}'
        else:
            destination = quote_plus(entrega.direccion or '')

        entrega.google_maps_url = f'https://www.google.com/maps?q={destination}'
        entrega.google_maps_directions_url = f'https://www.google.com/maps/dir/?api=1&destination={destination}'

    return render(request, 'entregas/lista_entregas.html', {
        'entregas': entregas,
        'can_update_estado': can_update_estado,
    })

@login_required
@_requiere_rol('EMPLEADO', 'ADMIN', 'REPARTIDOR')
def actualizar_estado(request, entrega_id):
    entrega = get_object_or_404(Entrega, id=entrega_id)
    if request.method == 'POST':
        nuevo = request.POST.get('nuevo_estado')
        if nuevo not in ('Pendiente', 'En camino', 'Entregado'):
            messages.error(request, 'El estado elegido no es válido.')
            return redirect('entregas:lista_entregas')
        entrega.estado_envio = nuevo
        entrega.save()
        # sincronizar estado del pedido
        pedido = entrega.pedido
        if nuevo == 'En camino':
            pedido.estado = 'PREPARANDO'
        elif nuevo == 'Entregado':
            pedido.estado = 'ENTREGADO'
        pedido.save()
        messages.success(request, f'La entrega #{entrega.id} se actualizó a {nuevo}.')
    return redirect('entregas:lista_entregas')


@login_required
@_requiere_rol('EMPLEADO', 'ADMIN', 'REPARTIDOR')
def confirmar_pago(request, entrega_id):
    if request.method != 'POST':
        return redirect('entregas:lista_entregas')

    entrega = get_object_or_404(
        Entrega.objects.select_related('pedido', 'pedido__pago', 'pedido__comprobante'),
        id=entrega_id,
    )
    pago = getattr(entrega.pedido, 'pago', None)
    if not pago:
        messages.error(request, f'El pedido #{entrega.pedido.id} no tiene un registro de pago.')
        return redirect('entregas:lista_entregas')

    if pago.metodo_pago.upper() == 'TRANSFERENCIA' and not hasattr(entrega.pedido, 'comprobante'):
        messages.error(
            request,
            'No se puede reportar la transferencia sin el comprobante del cliente.',
        )
        return redirect('entregas:lista_entregas')

    pago.estado = Pago.EstadoPago.REPORTADO_REPARTIDOR
    pago.confirmado_por = request.user
    pago.confirmado_en = timezone.now()
    pago.save(update_fields=['estado', 'confirmado_por', 'confirmado_en'])
    messages.success(
        request,
        f'El pago del pedido #{entrega.pedido.id} fue reportado al administrador para su confirmación.',
    )
    return redirect('entregas:lista_entregas')
