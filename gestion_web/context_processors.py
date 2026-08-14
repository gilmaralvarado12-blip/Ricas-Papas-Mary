from django.templatetags.static import static
from django.conf import settings

from .models import Producto
from .models import ConfiguracionSitio
from pedidos.models import Cart

def cart_summary(request):
    # prefer persistent cart for authenticated users
    count = 0
    total = 0.0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.filter(cliente=request.user, estado=Cart.Estado.OPEN).first()
            if cart:
                for ci in cart.items.select_related('producto').all():
                    count += int(ci.cantidad)
                    total += float(ci.subtotal())
                return {'cart_count': count, 'cart_total': total}
        except Exception:
            pass
    # fallback to session cart
    cart_s = request.session.get('cart', {})
    for pid, qty in cart_s.items():
        try:
            prod = Producto.objects.get(id=int(pid))
            count += int(qty)
            total += float(prod.precio) * int(qty)
        except Exception:
            continue
    return {'cart_count': count, 'cart_total': total}


def site_background(request):
    fondo_sitio_url = static('images/papas_mary.jpg')

    configuracion = ConfiguracionSitio.objects.first()
    if configuracion and configuracion.fondo:
        fondo_sitio_url = configuracion.fondo.url

    return {'fondo_sitio_url': fondo_sitio_url}


def site_branding(request):
    site_logo_url = static('images/logo.png')
    site_logo_subtitle = 'Rukullacta'

    configuracion = ConfiguracionSitio.objects.first()
    if configuracion:
        if configuracion.logo_principal and configuracion.logo_principal.name:
            try:
                if configuracion.logo_principal.storage.exists(configuracion.logo_principal.name):
                    site_logo_url = configuracion.logo_principal.url
            except Exception:
                # Si hay problema con storage o URL, conservamos el logo estandar.
                pass
        if configuracion.subtitulo_logo:
            site_logo_subtitle = configuracion.subtitulo_logo

    return {
        'site_logo_url': site_logo_url,
        'site_logo_subtitle': site_logo_subtitle,
    }


def session_notice(request):
    if not request.user.is_authenticated:
        return {}

    rol = getattr(request.user, 'rol', None)
    timeout_seconds = 60 * 60 * 8
    timeout_label = '8 horas'

    if rol == 'ADMIN':
        timeout_seconds = 60 * 60 * 24 * 7
        timeout_label = '7 días'
    elif rol in ('EMPLEADO', 'REPARTIDOR'):
        timeout_seconds = 60 * 60 * 12
        timeout_label = '12 horas'
    elif rol == 'CLIENTE':
        timeout_seconds = settings.SESSION_COOKIE_AGE
        timeout_label = '8 horas'

    return {
        'session_timeout_seconds': timeout_seconds,
        'session_timeout_label': timeout_label,
    }


def google_maps_config(request):
    return {
        'google_maps_api_key': getattr(settings, 'GOOGLE_MAPS_API_KEY', ''),
    }
