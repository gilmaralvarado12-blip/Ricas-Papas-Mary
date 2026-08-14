from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from platos.models import ProductoProxy as Producto
from gestion_web.models import Pedido, DetallePedido, Entrega, ConfiguracionSitio, Pago
from .models import Cart, CartItem
from pagos.forms import ComprobanteForm
from gestion_web.horarios import horario_atencion_texto, restaurante_atendiendo
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
from math import radians, cos, sin, asin, sqrt


# Parametrización base del despacho a domicilio
DEFAULT_MIN_DELIVERY_ORDER = Decimal('10.00')
ARCHIDONA_CENTER = (-0.9089, -77.8072)
TENA_CENTER = (-0.9930, -77.8127)
DEFAULT_STANDARD_RADIUS_KM = 8.0
DEFAULT_BASE_PREP_MINUTES = 20
DEFAULT_AVERAGE_SPEED_KMH = 28.0
DEFAULT_OUT_OF_RANGE_BASE_FEE = Decimal('1.50')
DEFAULT_OUT_OF_RANGE_PER_KM = Decimal('0.35')
DEFAULT_TENA_EXTRA_FEE = Decimal('0.75')


def _get_cart_session(session):
    return session.setdefault('cart', {})


def _save_cart_session(session, cart):
    session['cart'] = cart
    session.modified = True


def _get_or_create_cart_for_user(request):
    # Return an open cart for authenticated user, or None
    if not request.user.is_authenticated:
        return None
    cart, _ = Cart.objects.get_or_create(cliente=request.user, estado=Cart.Estado.OPEN)
    return cart


def _build_checkout_items(active_cart, active_session_cart):
    checkout_items = []
    checkout_total = 0.0

    if active_cart:
        for ci in active_cart.items.select_related('producto').all():
            subtotal = float(ci.subtotal())
            checkout_items.append({
                'producto': ci.producto,
                'qty': ci.cantidad,
                'subtotal': subtotal,
                'cart_item_id': ci.id,
            })
            checkout_total += subtotal
        return checkout_items, checkout_total

    for pid, qty in active_session_cart.items():
        try:
            producto = Producto.objects.get(id=int(pid))
        except Producto.DoesNotExist:
            continue
        subtotal = float(producto.precio) * int(qty)
        checkout_items.append({'producto': producto, 'qty': int(qty), 'subtotal': subtotal})
        checkout_total += subtotal

    return checkout_items, checkout_total


def _to_money(value):
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _get_delivery_config():
    config = ConfiguracionSitio.objects.first()
    if not config:
        return {
            'min_delivery_order': DEFAULT_MIN_DELIVERY_ORDER,
            'standard_radius_km': DEFAULT_STANDARD_RADIUS_KM,
            'base_prep_minutes': DEFAULT_BASE_PREP_MINUTES,
            'average_speed_kmh': DEFAULT_AVERAGE_SPEED_KMH,
            'out_of_range_base_fee': DEFAULT_OUT_OF_RANGE_BASE_FEE,
            'out_of_range_per_km': DEFAULT_OUT_OF_RANGE_PER_KM,
            'tena_extra_fee': DEFAULT_TENA_EXTRA_FEE,
        }

    return {
        'min_delivery_order': _to_money(config.delivery_min_order),
        'standard_radius_km': float(config.delivery_standard_radius_km),
        'base_prep_minutes': int(config.delivery_base_prep_minutes),
        'average_speed_kmh': float(config.delivery_average_speed_kmh),
        'out_of_range_base_fee': _to_money(config.delivery_out_of_range_base_fee),
        'out_of_range_per_km': _to_money(config.delivery_out_of_range_per_km),
        'tena_extra_fee': _to_money(config.delivery_tena_extra_fee),
    }


def _haversine_km(lat1, lon1, lat2, lon2):
    # Distancia geodésica aproximada para estimar tiempo y recargo de entrega.
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    earth_radius_km = 6371
    return earth_radius_km * c


TENA_THRESHOLD_KM = _haversine_km(
    ARCHIDONA_CENTER[0],
    ARCHIDONA_CENTER[1],
    TENA_CENTER[0],
    TENA_CENTER[1],
)


def _format_eta_label(minutes):
    if minutes >= 60:
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f'{hours} hora' if hours == 1 else f'{hours} horas'
        return f'{hours} h {mins} min'
    return f'{minutes} minutos'


def _estimate_delivery_conditions(latitud, longitud, delivery_config):
    if latitud is None or longitud is None:
        eta_minutes = 30
        return {
            'distancia_km': None,
            'eta_minutes': eta_minutes,
            'eta_label': _format_eta_label(eta_minutes),
            'fuera_rango_estandar': False,
            'en_tena_o_mas_alla': False,
            'cargo_adicional': Decimal('0.00'),
        }

    distancia_km = _haversine_km(ARCHIDONA_CENTER[0], ARCHIDONA_CENTER[1], latitud, longitud)
    average_speed = max(8.0, float(delivery_config['average_speed_kmh']))
    travel_minutes = max(8, round((distancia_km / average_speed) * 60))
    eta_minutes = int(delivery_config['base_prep_minutes']) + int(travel_minutes)
    standard_radius = float(delivery_config['standard_radius_km'])
    fuera_rango_estandar = distancia_km > standard_radius
    en_tena_o_mas_alla = distancia_km >= TENA_THRESHOLD_KM

    cargo_adicional = Decimal('0.00')
    if fuera_rango_estandar:
        extra_km = max(0.0, distancia_km - standard_radius)
        cargo_adicional = delivery_config['out_of_range_base_fee'] + (Decimal(str(extra_km)) * delivery_config['out_of_range_per_km'])
        if en_tena_o_mas_alla:
            cargo_adicional += delivery_config['tena_extra_fee']
        cargo_adicional = _to_money(cargo_adicional)

    return {
        'distancia_km': round(distancia_km, 2),
        'eta_minutes': eta_minutes,
        'eta_label': _format_eta_label(eta_minutes),
        'fuera_rango_estandar': fuera_rango_estandar,
        'en_tena_o_mas_alla': en_tena_o_mas_alla,
        'cargo_adicional': cargo_adicional,
    }


def add_to_cart(request, product_id):
    producto = get_object_or_404(Producto, id=product_id)
    qty = 1
    if request.method == 'POST':
        try:
            qty = int(request.POST.get('quantity', 1))
            if qty < 1:
                qty = 1
        except Exception:
            qty = 1

    # If user authenticated, use persistent cart
    cart = _get_or_create_cart_for_user(request)
    if cart:
        ci, created = CartItem.objects.get_or_create(
            cart=cart,
            producto=producto,
            defaults={'cantidad': qty, 'precio_unitario': producto.precio},
        )
        if not created:
            ci.cantidad = ci.cantidad + qty
            ci.precio_unitario = producto.precio
            ci.save()
        messages.success(request, f'Se agregó {producto.nombre} x{qty} al carrito.')
        return redirect(request.META.get('HTTP_REFERER', reverse('ver_menu')))

    # fallback to session cart
    cart_s = _get_cart_session(request.session)
    prod_key = str(product_id)
    cart_s[prod_key] = cart_s.get(prod_key, 0) + qty
    _save_cart_session(request.session, cart_s)
    messages.success(request, f'Se agregó {producto.nombre} x{qty} al carrito.')
    return redirect(request.META.get('HTTP_REFERER', reverse('ver_menu')))


@require_POST
def remove_from_cart(request, product_id):
    # If user has persistent cart
    cart = _get_or_create_cart_for_user(request)
    if cart:
        try:
            ci = CartItem.objects.get(cart=cart, producto_id=product_id)
            ci.delete()
            messages.info(request, 'El producto fue eliminado del carrito.')
        except CartItem.DoesNotExist:
            pass
        return redirect(reverse('pedidos:view_cart'))

    # fallback to session cart
    cart_s = _get_cart_session(request.session)
    prod_key = str(product_id)
    if prod_key in cart_s:
        del cart_s[prod_key]
        _save_cart_session(request.session, cart_s)
        messages.info(request, 'El producto fue eliminado del carrito.')
    return redirect(reverse('pedidos:view_cart'))


def update_cart_item(request, product_id):
    if request.method != 'POST':
        return redirect(reverse('pedidos:view_cart'))

    action = request.POST.get('action', '').strip().lower()
    raw_quantity = request.POST.get('quantity')

    cart = _get_or_create_cart_for_user(request)
    if cart:
        try:
            ci = CartItem.objects.get(cart=cart, producto_id=product_id)
        except CartItem.DoesNotExist:
            return redirect(reverse('pedidos:view_cart'))

        if action == 'increase':
            ci.cantidad += 1
            ci.save(update_fields=['cantidad'])
        elif action == 'decrease':
            if ci.cantidad > 1:
                ci.cantidad -= 1
                ci.save(update_fields=['cantidad'])
            else:
                ci.delete()
        else:
            try:
                qty = int(raw_quantity)
            except (TypeError, ValueError):
                qty = ci.cantidad

            if qty <= 0:
                ci.delete()
            else:
                ci.cantidad = qty
                ci.save(update_fields=['cantidad'])

        return redirect(reverse('pedidos:view_cart'))

    cart_s = _get_cart_session(request.session)
    prod_key = str(product_id)
    if prod_key not in cart_s:
        return redirect(reverse('pedidos:view_cart'))

    qty = int(cart_s.get(prod_key, 0))
    if action == 'increase':
        qty += 1
    elif action == 'decrease':
        qty -= 1
    else:
        try:
            qty = int(raw_quantity)
        except (TypeError, ValueError):
            qty = int(cart_s.get(prod_key, 1))

    if qty <= 0:
        del cart_s[prod_key]
    else:
        cart_s[prod_key] = qty

    _save_cart_session(request.session, cart_s)
    return redirect(reverse('pedidos:view_cart'))


def clear_cart(request):
    if request.method != 'POST':
        return redirect(reverse('pedidos:view_cart'))

    cart = _get_or_create_cart_for_user(request)
    if cart:
        cart.items.all().delete()
        messages.info(request, 'El carrito se vació correctamente.')
        return redirect(reverse('pedidos:view_cart'))

    request.session['cart'] = {}
    request.session.modified = True
    messages.info(request, 'El carrito se vació correctamente.')
    return redirect(reverse('pedidos:view_cart'))


def view_cart(request):
    cart = _get_or_create_cart_for_user(request)
    session_cart = _get_cart_session(request.session) if not cart else {}
    items, total = _build_checkout_items(cart, session_cart)
    # Además de los items del carrito, cargamos el catálogo disponible para permitir agregar platos sin volver al menú
    try:
        productos = Producto.objects.filter(disponible=True).order_by('nombre')
    except Exception:
        productos = Producto.objects.none()
    return render(request, 'pedidos/cart.html', {'items': items, 'total': total, 'productos': productos})


@login_required
@transaction.atomic
def cancel_order(request, pedido_id):
    if request.method != 'POST':
        return redirect(reverse('ver_menu') + '?modulo=pedidos')

    pedido = get_object_or_404(Pedido, id=pedido_id, cliente=request.user)
    cancellable_states = {
        Pedido.EstadoPedido.PENDIENTE_PAGO,
        Pedido.EstadoPedido.PENDIENTE,
        Pedido.EstadoPedido.PAGADO,
    }
    if pedido.estado not in cancellable_states:
        messages.error(
            request,
            'Este pedido ya está en preparación o finalizado y no se puede cancelar.',
        )
    else:
        pedido.estado = Pedido.EstadoPedido.CANCELADO
        pedido.save(update_fields=['estado'])
        messages.success(request, f'El pedido #{pedido.id} fue cancelado correctamente.')

    return redirect(reverse('ver_menu') + '?modulo=pedidos')


def edit_cart(request):
    cart = _get_or_create_cart_for_user(request)
    session_cart = _get_cart_session(request.session) if not cart else {}
    items, total = _build_checkout_items(cart, session_cart)
    return render(request, 'pedidos/cart_edit.html', {'items': items, 'total': total})


@login_required
@transaction.atomic
def checkout(request):
    cart = _get_or_create_cart_for_user(request)
    session_cart = {}
    delivery_config = _get_delivery_config()

    if not cart:
        session_cart = _get_cart_session(request.session)

    items, total = _build_checkout_items(cart, session_cart)
    if not items:
        messages.error(request, 'Tu carrito está vacío.')
        return redirect(reverse('pedidos:view_cart'))

    if request.method == 'POST':
        if not restaurante_atendiendo():
            messages.error(
                request,
                f'{horario_atencion_texto()} Los pedidos solo pueden confirmarse durante ese horario.',
            )
            return render(request, 'pedidos/checkout.html', {
                'items': items,
                'total': total,
                'selected_metodo_pago': request.POST.get('metodo_pago', 'EFECTIVO').upper(),
                'selected_tipo': 'DOMICILIO',
                'direccion': request.POST.get('direccion', '').strip(),
                'latitud': request.POST.get('latitud', '').strip(),
                'longitud': request.POST.get('longitud', '').strip(),
                'delivery_min_order': delivery_config['min_delivery_order'],
            })

        metodo_pago = request.POST.get('metodo_pago', 'EFECTIVO').upper()
        if metodo_pago not in ('EFECTIVO', 'TRANSFERENCIA'):
            metodo_pago = 'EFECTIVO'

        # El checkout ofrece únicamente el servicio de envío a domicilio.
        tipo = 'DOMICILIO'
        direccion = request.POST.get('direccion', '').strip()
        latitud = request.POST.get('latitud', '').strip() or None
        longitud = request.POST.get('longitud', '').strip() or None

        if tipo == 'DOMICILIO' and not direccion:
            messages.error(request, 'Debes ingresar la dirección de entrega para pedidos a domicilio.')
            return render(request, 'pedidos/checkout.html', {
                'items': items,
                'total': total,
                'selected_metodo_pago': metodo_pago,
                'selected_tipo': 'DOMICILIO',
                'direccion': direccion,
                'latitud': latitud,
                'longitud': longitud,
            })

        total_actual = _to_money(total)
        if total_actual < delivery_config['min_delivery_order']:
            messages.error(
                request,
                f'El pedido mínimo a domicilio es de ${delivery_config["min_delivery_order"]:.2f}.',
            )
            return render(request, 'pedidos/checkout.html', {
                'items': items,
                'total': total,
                'selected_metodo_pago': metodo_pago,
                'selected_tipo': 'DOMICILIO',
                'direccion': direccion,
                'latitud': latitud,
                'longitud': longitud,
                'delivery_min_order': delivery_config['min_delivery_order'],
            })

        latitud_num = None
        longitud_num = None
        if latitud and longitud:
            try:
                latitud_num = float(latitud)
                longitud_num = float(longitud)
            except ValueError:
                latitud_num = None
                longitud_num = None

        delivery_conditions = _estimate_delivery_conditions(latitud_num, longitud_num, delivery_config) if tipo == 'DOMICILIO' else None

        nuevo_pedido = Pedido.objects.create(
            cliente=request.user,
            tipo=tipo,
            estado='PENDIENTE_PAGO',
            total=0.00,
        )

        total_acumulado = 0.0
        confirmed_items = []

        if cart:
            items_qs = cart.items.select_related('producto').all()
            for ci in items_qs:
                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    producto=ci.producto,
                    cantidad=ci.cantidad,
                    precio_unitario=ci.precio_unitario,
                )
                subtotal_item = float(ci.subtotal())
                total_acumulado += subtotal_item
                confirmed_items.append({'producto': ci.producto, 'qty': ci.cantidad, 'subtotal': subtotal_item})

            cart.estado = Cart.Estado.ORDERED
            cart.save()
        else:
            for pid, qty in session_cart.items():
                try:
                    p = Producto.objects.get(id=int(pid))
                except Producto.DoesNotExist:
                    continue

                DetallePedido.objects.create(
                    pedido=nuevo_pedido,
                    producto=p,
                    cantidad=int(qty),
                    precio_unitario=p.precio,
                )
                subtotal_item = float(p.precio) * int(qty)
                total_acumulado += subtotal_item
                confirmed_items.append({'producto': p, 'qty': int(qty), 'subtotal': subtotal_item})

            request.session['cart'] = {}
            request.session.modified = True

        total_pedido = _to_money(total_acumulado)

        if tipo == 'DOMICILIO' and delivery_conditions:
            total_pedido = _to_money(total_pedido + delivery_conditions['cargo_adicional'])

        nuevo_pedido.total = total_pedido
        nuevo_pedido.save(update_fields=['total'])
        Pago.objects.create(
            pedido=nuevo_pedido,
            monto=total_pedido,
            metodo_pago=metodo_pago,
        )

        if tipo == 'DOMICILIO':
            entrega_data = {
                'pedido': nuevo_pedido,
                'direccion': direccion,
                'distancia_km': delivery_conditions['distancia_km'] if delivery_conditions else None,
                'tiempo_estimado_minutos': delivery_conditions['eta_minutes'] if delivery_conditions else 30,
                'fuera_rango_estandar': delivery_conditions['fuera_rango_estandar'] if delivery_conditions else False,
                'cargo_adicional': delivery_conditions['cargo_adicional'] if delivery_conditions else Decimal('0.00'),
            }
            if latitud_num is not None and longitud_num is not None:
                entrega_data['latitud'] = latitud_num
                entrega_data['longitud'] = longitud_num
            Entrega.objects.create(**entrega_data)

        transfer_holder = 'Lourdes Juana Alvarado Shiguango'
        transfer_bank = 'Banco Pichincha'
        transfer_account = '2214567280'

        eta_confirmacion = ''
        delivery_notices = []
        if tipo == 'DOMICILIO' and delivery_conditions:
            eta_confirmacion = (
                f'Su pedido llegará en aproximadamente {delivery_conditions["eta_label"]}. '
                'Puedes ver tu tiempo de espera en el módulo Estado de Pedido.'
            )
            if delivery_conditions['en_tena_o_mas_alla']:
                delivery_notice = (
                    'Su ubicación está fuera del rango de entrega estándar. '
                    f'Se aplicará un cargo adicional de ${delivery_conditions["cargo_adicional"]:.2f}. '
                    'Esto se refleja en el total de su pedido.'
                )
            elif delivery_conditions['fuera_rango_estandar']:
                delivery_notice = (
                    'Por estar fuera del rango de entrega, se aplicará un cargo adicional de '
                    f'${delivery_conditions["cargo_adicional"]:.2f}.'
                )
            else:
                delivery_notice = ''

            if delivery_notice:
                delivery_notices.append(delivery_notice)
                messages.warning(request, delivery_notice)
        else:
            eta_confirmacion = (
                'Tu pedido ha sido confirmado y estará listo aproximadamente en 30 minutos.'
            )

        messages.success(
            request,
            f'Tu pedido #{nuevo_pedido.id} quedó confirmado correctamente. '
            'Revisa la información de pago y entrega en la siguiente pantalla.'
        )
        return render(request, 'pedidos/checkout.html', {
            'items': [],
            'total': 0,
            'order_confirmed': True,
            'confirmed_order': nuevo_pedido,
            'confirmed_items': confirmed_items,
            'confirmed_total': total_pedido,
            'confirmed_subtotal': _to_money(total_acumulado),
            'delivery_eta_message': eta_confirmacion,
            'delivery_notices': delivery_notices,
            'delivery_extra_fee': delivery_conditions['cargo_adicional'] if delivery_conditions else Decimal('0.00'),
            'selected_metodo_pago': metodo_pago,
            'transfer_holder': transfer_holder,
            'transfer_bank': transfer_bank,
            'transfer_account': transfer_account,
        })

    return render(request, 'pedidos/checkout.html', {
        'items': items,
        'total': total,
        'selected_metodo_pago': 'EFECTIVO',
        'selected_tipo': 'DOMICILIO',
        'direccion': '',
        'latitud': '',
        'longitud': '',
        'delivery_min_order': delivery_config['min_delivery_order'],
    })
