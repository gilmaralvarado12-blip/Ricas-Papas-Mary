from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .forms import ComprobanteForm
from .models import Comprobante
from .utils import send_comprobante_validado_email, send_comprobante_rechazado_email
from gestion_web.models import Pedido

@login_required
def subir_comprobante(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    # Cada pedido solo puede tener un comprobante. Si ya existe uno, lo reutilizamos para evitar violar la restricción única.
    comprobante_existente = getattr(pedido, 'comprobante', None)
    if request.method == 'POST':
        if not request.FILES.get('imagen') and not comprobante_existente:
            messages.error(request, 'Error: comprobante faltante.')
            form = ComprobanteForm(request.POST, request.FILES, instance=comprobante_existente)
            return render(request, 'pagos/subir_comprobante.html', {'form': form, 'pedido': pedido})
        form = ComprobanteForm(request.POST, request.FILES, instance=comprobante_existente)
        if form.is_valid():
            comprobante = form.save(commit=False)
            comprobante.pedido = pedido
            # Al subir una nueva imagen, dejamos el comprobante en revisión para que el empleado lo vuelva a aprobar.
            comprobante.estado = 'PENDIENTE'
            comprobante.validado_por = None
            comprobante.save()
            pedido.estado = 'PENDIENTE_PAGO'
            pedido.save()
            messages.success(request, 'Tu comprobante se recibió correctamente. Ahora está pendiente de revisión.')
            return redirect('ver_menu')
        messages.error(request, 'No se subió el comprobante o el archivo no es válido.')
    else:
        form = ComprobanteForm(instance=comprobante_existente)
    return render(request, 'pagos/subir_comprobante.html', {'form': form, 'pedido': pedido})

# Helper: check if user is empleado or admin
def is_empleado_or_admin(user):
    try:
        return user.rol in ('EMPLEADO', 'ADMIN')
    except Exception:
        return False

@login_required
@user_passes_test(is_empleado_or_admin)
def validar_comprobante(request, comprobante_id):
    comprobante = get_object_or_404(Comprobante, id=comprobante_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'validar':
            comprobante.estado = 'VALIDADO'
            comprobante.validado_por = request.user
            comprobante.save()
            # marcar pedido como pagado
            pedido = comprobante.pedido
            Pedido.objects.filter(pk=pedido.pk).update(estado='PAGADO')
            pedido.refresh_from_db(fields=['estado'])
            from gestion_web.models import Pago
            pago_obj, _ = Pago.objects.get_or_create(
                pedido=pedido,
                defaults={'monto': pedido.total, 'metodo_pago': 'TRANSFERENCIA'},
            )
            pago_obj.estado = Pago.EstadoPago.CONFIRMADO
            pago_obj.confirmado_por = request.user
            pago_obj.confirmado_en = timezone.now()
            pago_obj.save(update_fields=['estado', 'confirmado_por', 'confirmado_en'])

            send_comprobante_validado_email(comprobante)
            messages.success(request, f'El comprobante del pedido #{pedido.id} fue aprobado. El pago quedó registrado y se avisó al cliente.')
        elif action == 'rechazar':
            comprobante.estado = 'RECHAZADO'
            comprobante.validado_por = request.user
            comprobante.save()
            send_comprobante_rechazado_email(comprobante)
            messages.error(request, f'El comprobante del pedido #{comprobante.pedido.id} fue rechazado. El cliente ya fue notificado.')
        return redirect('lista_comprobantes')

    return render(request, 'pagos/validar_comprobante.html', {'comprobante': comprobante})

@login_required
@user_passes_test(is_empleado_or_admin)
def lista_comprobantes(request):
    comprobantes = Comprobante.objects.order_by('-fecha_subida')
    for comprobante in comprobantes:
        comprobante.estado_display = comprobante.get_estado_display()
        comprobante.pedido_estado_display = comprobante.pedido.get_estado_display()
    return render(request, 'pagos/lista_comprobantes.html', {'comprobantes': comprobantes})
