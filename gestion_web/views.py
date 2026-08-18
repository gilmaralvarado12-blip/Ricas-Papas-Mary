import json
import unicodedata
import re

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from datetime import datetime, timedelta
from decimal import Decimal
from math import ceil
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.http import require_http_methods
from django.core.exceptions import PermissionDenied
from django.templatetags.static import static
from django.urls import reverse
from django.http import HttpResponse
from urllib.parse import quote_plus

# Importamos los modelos que alimentan la interfaz principal del cliente.
# - Pedido/Producto: pestaña de pedidos.
# - Reserva/Mesa: pestaña de reservas y mapa de selección de mesa.
from .models import ConfiguracionSitio, Pedido, Reserva, Producto, Mesa, DetallePedido, Entrega, Insumo
from .forms import RegistroForm
from reservas.utils import send_reserva_confirmada_email
from .horarios import dentro_del_horario, horario_atencion_texto


def _normalize_chat_message(message):
    normalized = unicodedata.normalize('NFKD', message.lower())
    return ''.join(character for character in normalized if not unicodedata.combining(character))


@require_http_methods(['POST'])
def chatbot_response(request):
    try:
        payload = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({'error': 'El mensaje debe enviarse como JSON válido.'}, status=400)

    if not isinstance(payload, dict) or not isinstance(payload.get('message'), str):
        return JsonResponse({'error': 'El campo message es obligatorio.'}, status=400)

    message = payload['message'].strip()
    if not message:
        return JsonResponse({'error': 'Escribe un mensaje para continuar.'}, status=400)

    normalized_message = _normalize_chat_message(message)
    # Versión simple (sin signos ni tildes) para búsquedas más robustas
    simple_message = re.sub(r'[^a-z0-9\s]', ' ', normalized_message).strip()
    menu_keywords = (
        'menu', 'plato', 'platos', 'combo', 'combos', 'papa', 'papas',
        'bebida', 'venden', 'ofrecen', 'comida',
    )
    price_keywords = ('precio', 'precios', 'cuesta', 'cuánto', 'cuanto', 'valor')
    schedule_keywords = ('horario', 'abierto', 'hora', 'atienden')
    location_keywords = ('donde', 'ubicacion', 'direccion', 'lugar', 'encuentran')
    order_keywords = ('pedir', 'pedido', 'domicilio', 'reservar', 'reserva', 'comprar')

    # Helper: construir HTML de tarjetas para un queryset de Productos
    def build_cards_from_qs(qs):
        items = []
        base_url = reverse('ver_menu')
        for p in qs:
            precio = format(p.precio, '.2f') if getattr(p, 'precio', None) is not None else 'Precio no disponible'
            url = request.build_absolute_uri(f"{base_url}?q={quote_plus(p.nombre)}")
            disponible_text = 'Disponible' if p.disponible else 'No disponible'
            try:
                img_url = request.build_absolute_uri(p.imagen.url) if getattr(p, 'imagen', None) else request.build_absolute_uri(static('images/logo.png'))
            except Exception:
                img_url = request.build_absolute_uri(static('images/logo.png'))
            items.append({'nombre': p.nombre, 'precio': precio, 'disponible': disponible_text, 'url': url, 'img': img_url, 'descripcion': p.descripcion or ''})

        # Texto plano
        if not items:
            return None, '<p>No hay productos registrados para mostrar.</p>'

        lines = [f"{it['nombre']} — ${it['precio']}" for it in items]
        response_text = 'Resultados:\n- ' + '\n- '.join(lines)

        # HTML cards
        html_cards = []
        for it in items:
            nombre = escape(it['nombre'])
            precio = escape(it['precio'])
            url = escape(it['url'])
            disponible = escape(it['disponible'])
            img = escape(it['img'])
            desc = escape(it['descripcion'])
            card_html = (
                f'<div class="rpm-bot-card">'
                f'  <div class="rpm-bot-card-img"><img src="{img}" alt="{nombre}"/></div>'
                f'  <div class="rpm-bot-card-body">'
                f'    <div class="rpm-bot-card-title">{nombre}</div>'
                f'    <div class="rpm-bot-card-desc">{desc}</div>'
                f'    <div class="rpm-bot-card-price">${precio} · {disponible}</div>'
                f'  </div>'
                f'  <div class="rpm-bot-card-actions">'
                f'    <a class="btn btn-sm btn-outline-primary" href="{url}" target="_blank" rel="noopener noreferrer">Ver</a>'
                f'  </div>'
                f'</div>'
            )
            html_cards.append(card_html)
        response_html = '<div class="rpm-bot-cards">' + ''.join(html_cards) + '</div>'
        return response_text, response_html

    # Manejo explícito de preguntas frecuentes conocidas
    # Productos / Menú
    if 'combos' in simple_message or 'que combos' in simple_message:
        combos_qs = Producto.objects.filter(disponible=True, nombre__icontains='combo').order_by('-id')[:8]
        text, html = build_cards_from_qs(combos_qs)
        if text is None:
            text = 'No tenemos combos registrados actualmente.'
            html = '<p>No tenemos combos registrados actualmente.</p>'
        return JsonResponse({'response': text, 'response_html': html})

    if 'salchipapa grande' in simple_message or ('salchipapa' in simple_message and 'grande' in simple_message):
        p = Producto.objects.filter(disponible=True).filter(Q(nombre__icontains='salchipapa grande') | (Q(nombre__icontains='salchipapa') & Q(nombre__icontains='grande'))).first()
        if not p:
            p = Producto.objects.filter(disponible=True).filter(nombre__icontains='salchipapa').first()
        if p:
            url = request.build_absolute_uri(f"{reverse('ver_menu')}?q={quote_plus(p.nombre)}")
            text = f"El precio de {p.nombre} es ${format(p.precio, '.2f')}."
            html = f'<div class="rpm-bot-card"><div class="rpm-bot-card-img"><img src="{escape(request.build_absolute_uri(p.imagen.url)) if getattr(p, "imagen", None) else escape(request.build_absolute_uri(static("images/logo.png")))}" alt="{escape(p.nombre)}"/></div><div class="rpm-bot-card-body"><div class="rpm-bot-card-title">{escape(p.nombre)}</div><div class="rpm-bot-card-price">${escape(format(p.precio, ".2f"))}</div></div><div class="rpm-bot-card-actions"><a class="btn btn-sm btn-outline-primary" href="{escape(url)}" target="_blank" rel="noopener noreferrer">Ver</a></div></div>'
        else:
            text = 'No pude encontrar una Salchipapa Grande en el menú.'
            html = '<p>No pude encontrar una Salchipapa Grande en el menú.</p>'
        return JsonResponse({'response': text, 'response_html': html})

    if 'combo 1' in simple_message or 'combo1' in simple_message or 'combo uno' in simple_message:
        p = Producto.objects.filter(disponible=True, nombre__icontains='combo 1').first()
        if not p:
            p = Producto.objects.filter(disponible=True, nombre__icontains='combo').first()
        if p:
            desc = p.descripcion or 'Sin descripción del combo.'
            text = f"{p.nombre}: {desc}"
            url = request.build_absolute_uri(f"{reverse('ver_menu')}?q={quote_plus(p.nombre)}")
            html = f'<p><strong>{escape(p.nombre)}</strong></p><p>{escape(desc)}</p><p><a href="{escape(url)}" target="_blank" rel="noopener noreferrer">Ver en el menú</a></p>'
        else:
            text = 'No encontré el Combo 1 en el menú. Revisa la sección Menú.'
            html = '<p>No encontré el Combo 1 en el menú. Revisa la sección Menú.</p>'
        return JsonResponse({'response': text, 'response_html': html})

    if 'bebidas sin azucar' in simple_message or 'sin azucar' in simple_message or 'sin azucar' in simple_message or 'light' in simple_message:
        drinks = Producto.objects.filter(disponible=True).filter(Q(nombre__icontains='sin azucar') | Q(nombre__icontains='sin azúcar') | Q(descripcion__icontains='sin azucar') | Q(descripcion__icontains='sin azúcar') | Q(nombre__icontains='light') | Q(descripcion__icontains='light')).order_by('-id')[:8]
        text, html = build_cards_from_qs(drinks)
        if text is None:
            text = 'No tenemos bebidas sin azúcar registradas. Revisa las opciones en el menú.'
            html = '<p>No tenemos bebidas sin azúcar registradas. Revisa las opciones en el menú.</p>'
        return JsonResponse({'response': text, 'response_html': html})

    # Promociones
    if 'promoc' in simple_message or 'oferta' in simple_message or 'descuento' in simple_message:
        promos = Producto.objects.filter(disponible=True).filter(Q(nombre__icontains='promo') | Q(nombre__icontains='oferta') | Q(descripcion__icontains='promo') | Q(descripcion__icontains='oferta'))[:8]
        if promos.exists():
            text, html = build_cards_from_qs(promos)
        else:
            text = 'No hay promociones activas hoy. Revisa el menú o consulta con atención al cliente para ofertas especiales.'
            html = '<p>No hay promociones activas hoy. Revisa el menú o consulta con atención al cliente para ofertas especiales.</p>'
        return JsonResponse({'response': text, 'response_html': html})

    # Pedidos
    if 'como hago un pedido' in simple_message or 'como hago pedido' in simple_message or 'hacer un pedido' in simple_message or 'hacer pedido' in simple_message:
        text = 'Para pedir en línea: entra a Menú, selecciona los productos que quieras y agrégalos al carrito. Luego finaliza en el checkout y sigue las instrucciones de pago.'
        html = f'<p>{escape(text)}</p><p><a href="{escape(request.build_absolute_uri(reverse("ver_menu")))}" target="_blank">Ir al Menú</a></p>'
        return JsonResponse({'response': text, 'response_html': html})

    if 'pedido minimo' in simple_message or 'pedido minimo' in simple_message or 'minimo' in simple_message or 'pedido minimo' in simple_message:
        cfg = ConfiguracionSitio.objects.first()
        minimo = cfg.delivery_min_order if cfg else None
        if minimo:
            text = f'El pedido mínimo para delivery es ${format(minimo, ".2f")}.'
            html = f'<p>{escape(text)}</p>'
        else:
            text = 'No tenemos un monto mínimo de pedido configurado.'
            html = f'<p>{escape(text)}</p>'
        return JsonResponse({'response': text, 'response_html': html})

    if 'cuanto tarda' in simple_message or 'tarda en llegar' in simple_message or 'cuanto tarda en llegar' in simple_message or 'tiempo' in simple_message:
        cfg = ConfiguracionSitio.objects.first()
        base_min = getattr(cfg, 'delivery_base_prep_minutes', 20) if cfg else 20
        estimate = base_min + 30
        text = f'Los pedidos suelen tardar aproximadamente {estimate} minutos (preparación + entrega). El tiempo exacto depende de la distancia y del tráfico.'
        html = f'<p>{escape(text)}</p>'
        return JsonResponse({'response': text, 'response_html': html})

    if 'cancelar' in simple_message and 'pedido' in simple_message:
        text = 'Puedes cancelar un pedido si aún no ha sido preparado o enviado. Revisa tu historial de pedidos y selecciona la opción de cancelar o contacta a atención al cliente.'
        html = f'<p>{escape(text)}</p>'
        return JsonResponse({'response': text, 'response_html': html})

    if 'repetir un pedido' in simple_message or 'repetir pedido' in simple_message or 'repetir pedido anterior' in simple_message or 'volver a pedir' in simple_message:
        text = 'Puedes repetir un pedido anterior desde tu historial de pedidos: abre el pedido y selecciona la opción correspondiente (Repetir / Volver a pedir). Si no está disponible, contacta a atención al cliente.'
        html = f'<p>{escape(text)}</p>'
        return JsonResponse({'response': text, 'response_html': html})

    # Primero: intento de coincidencia directa con productos (nombre o descripción)
    try:
        productos_coincidentes = Producto.objects.filter(disponible=True).filter(
            Q(nombre__icontains=message) | Q(descripcion__icontains=message)
        ).order_by('-id')[:6]
    except Exception:
        productos_coincidentes = Producto.objects.none()

    if productos_coincidentes.exists():
        items = []
        base_url = reverse('ver_menu')
        for p in productos_coincidentes:
            precio = format(p.precio, '.2f') if getattr(p, 'precio', None) is not None else 'Precio no disponible'
            url = request.build_absolute_uri(f"{base_url}?q={quote_plus(p.nombre)}")
            disponible_text = 'Disponible' if p.disponible else 'No disponible'
            items.append({
                'nombre': p.nombre,
                'precio': precio,
                'disponible': disponible_text,
                'url': url,
            })

        # Texto plano para compatibilidad
        if len(items) == 1:
            single = items[0]
            response = f"Encontré 1 plato que coincide:\n{single['nombre']} — ${single['precio']} — {single['disponible']}. Ver: {single['url']}\n¿Deseas agregarlo al carrito?"
        else:
            lines = [f"{it['nombre']} — ${it['precio']} — {it['disponible']}. Ver: {it['url']}" for it in items]
            response = "Encontré varios platos que coinciden:\n- " + "\n- ".join(lines)

        # HTML enriquecido: tarjetas con imagen, precio y botón
        html_cards = []
        for it in items:
            nombre = escape(it['nombre'])
            precio = escape(it['precio'])
            disponible = escape(it['disponible'])
            url = escape(it['url'])
            # Imagen: intentar recuperar la imagen real del producto; si no, usar logo como placeholder
            try:
                p_obj = Producto.objects.filter(nombre=it['nombre']).first()
                if p_obj and getattr(p_obj, 'imagen', None):
                    img_url = request.build_absolute_uri(p_obj.imagen.url)
                else:
                    img_url = request.build_absolute_uri(static('images/logo.png'))
            except Exception:
                img_url = request.build_absolute_uri(static('images/logo.png'))

            img_url = escape(img_url)
            card_html = (
                f'<div class="rpm-bot-card">'
                f'  <div class="rpm-bot-card-img"><img src="{img_url}" alt="{nombre}"/></div>'
                f'  <div class="rpm-bot-card-body">'
                f'    <div class="rpm-bot-card-title">{nombre}</div>'
                f'    <div class="rpm-bot-card-price">${precio} · {disponible}</div>'
                f'  </div>'
                f'  <div class="rpm-bot-card-actions">'
                f'    <a class="btn btn-sm btn-outline-primary" href="{url}" target="_blank" rel="noopener noreferrer">Ver</a>'
                f'  </div>'
                f'</div>'
            )
            html_cards.append(card_html)

        response_html = '<div class="rpm-bot-cards">' + ''.join(html_cards) + '</div>'
        if len(items) == 1:
            response_html += '<p>¿Deseas agregarlo al carrito?</p>'

        return JsonResponse({'response': response, 'response_html': response_html})

    # Si no hay coincidencias directas de producto, intentar búsqueda por tokens (palabras cortas dentro del mensaje)
    tokens = [t for t in re.split(r'\W+', simple_message) if len(t) > 2]
    productos_tokens = Producto.objects.none()
    if tokens:
        try:
            q_obj = Q()
            for t in tokens:
                q_obj |= Q(nombre__icontains=t) | Q(descripcion__icontains=t)
            productos_tokens = Producto.objects.filter(disponible=True).filter(q_obj).distinct().order_by('-id')[:6]
        except Exception:
            productos_tokens = Producto.objects.none()

    if productos_tokens.exists():
        items = []
        base_url = reverse('ver_menu')
        for p in productos_tokens:
            precio = format(p.precio, '.2f') if getattr(p, 'precio', None) is not None else 'Precio no disponible'
            url = request.build_absolute_uri(f"{base_url}?q={quote_plus(p.nombre)}")
            disponible_text = 'Disponible' if p.disponible else 'No disponible'
            items.append({
                'nombre': p.nombre,
                'precio': precio,
                'disponible': disponible_text,
                'url': url,
            })

        lines = [f"{it['nombre']} — ${it['precio']} — {it['disponible']}. Ver: {it['url']}" for it in items]
        response = "Encontré los siguientes platos relacionados con tu consulta:\n- " + "\n- ".join(lines)

        # HTML enriquecido: tarjetas con imagen, precio y botón (para resultados por tokens)
        html_cards = []
        for it in items:
            nombre = escape(it['nombre'])
            precio = escape(it['precio'])
            disponible = escape(it['disponible'])
            url = escape(it['url'])
            try:
                p_obj = Producto.objects.filter(nombre=it['nombre']).first()
                if p_obj and getattr(p_obj, 'imagen', None):
                    img_url = request.build_absolute_uri(p_obj.imagen.url)
                else:
                    img_url = request.build_absolute_uri(static('images/logo.png'))
            except Exception:
                img_url = request.build_absolute_uri(static('images/logo.png'))
            img_url = escape(img_url)

            card_html = (
                f'<div class="rpm-bot-card">'
                f'  <div class="rpm-bot-card-img"><img src="{img_url}" alt="{nombre}"/></div>'
                f'  <div class="rpm-bot-card-body">'
                f'    <div class="rpm-bot-card-title">{nombre}</div>'
                f'    <div class="rpm-bot-card-price">${precio} · {disponible}</div>'
                f'  </div>'
                f'  <div class="rpm-bot-card-actions">'
                f'    <a class="btn btn-sm btn-outline-primary" href="{url}" target="_blank" rel="noopener noreferrer">Ver</a>'
                f'  </div>'
                f'</div>'
            )
            html_cards.append(card_html)

        response_html = '<div class="rpm-bot-cards">' + ''.join(html_cards) + '</div>'

        return JsonResponse({'response': response, 'response_html': response_html})

    # Si el usuario consultó por precios explícitamente, devolvemos una lista con precios de los primeros productos
    if any(keyword in simple_message for keyword in price_keywords):
        productos_precio = Producto.objects.filter(disponible=True).order_by('-id')[:8]
        if productos_precio.exists():
            items = []
            base_url = reverse('ver_menu')
            for p in productos_precio:
                items.append({'nombre': p.nombre, 'precio': format(p.precio, '.2f'), 'url': request.build_absolute_uri(f"{base_url}?q={quote_plus(p.nombre)}")})

            lines = [f"{it['nombre']} — ${it['precio']}" for it in items]
            response = "Aquí tienes algunos precios:\n- " + "\n- ".join(lines) + "\nPuedes ver el menú completo en la sección Menú."

            # Convertir en tarjetas
            html_cards = []
            for it in items:
                nombre = escape(it['nombre'])
                precio = escape(it['precio'])
                url = escape(it['url'])
                try:
                    p_obj = Producto.objects.filter(nombre=it['nombre']).first()
                    if p_obj and getattr(p_obj, 'imagen', None):
                        img_url = request.build_absolute_uri(p_obj.imagen.url)
                    else:
                        img_url = request.build_absolute_uri(static('images/logo.png'))
                except Exception:
                    img_url = request.build_absolute_uri(static('images/logo.png'))
                img_url = escape(img_url)
                card_html = (
                    f'<div class="rpm-bot-card">'
                    f'  <div class="rpm-bot-card-img"><img src="{img_url}" alt="{nombre}"/></div>'
                    f'  <div class="rpm-bot-card-body">'
                    f'    <div class="rpm-bot-card-title">{nombre}</div>'
                    f'    <div class="rpm-bot-card-price">${precio}</div>'
                    f'  </div>'
                    f'  <div class="rpm-bot-card-actions">'
                    f'    <a class="btn btn-sm btn-outline-primary" href="{url}" target="_blank" rel="noopener noreferrer">Ver</a>'
                    f'  </div>'
                    f'</div>'
                )
                html_cards.append(card_html)
            response_html = '<div class="rpm-bot-cards">' + ''.join(html_cards) + '</div>'
        else:
            response = 'Lo siento, no hay productos disponibles para mostrar precios en este momento.'
            response_html = '<p>Lo siento, no hay productos disponibles para mostrar precios en este momento.</p>'
        return JsonResponse({'response': response, 'response_html': response_html})

    # Si no, usamos heurísticas por palabra clave
    if any(keyword in simple_message for keyword in menu_keywords):
        products = list(
            Producto.objects.filter(disponible=True).values_list('nombre', flat=True)[:8]
        )
        menu_detail = ', '.join(products) if products else 'combos, papas fritas y bebidas'
        response = f'Contamos con: {menu_detail}. Puedes revisar el menú completo desde la sección Menú.'
    elif any(keyword in simple_message for keyword in schedule_keywords):
        response = 'Atendemos de lunes a domingo, de 08:00 AM a 21:00 PM.'
    elif any(keyword in simple_message for keyword in location_keywords):
        response = 'Estamos en Archidona - Rukullakta, Ecuador. Puedes ver el mapa y cómo llegar en la sección Nuestra Ubicación.'
    elif any(keyword in simple_message for keyword in order_keywords):
        response = 'Para realizar un pedido, entra en Menú, elige tus productos y agrégalos al carrito. Para reservar, ingresa a la sección Reservas.'
    else:
        response = 'Puedo ayudarte con el menú, horarios, ubicación, pedidos y reservas. ¿Qué deseas consultar?'
        response_html = f'<p>{escape(response)}</p>'

    return JsonResponse({'response': response, 'response_html': response_html})

def splash(request):
    return render(request, 'gestion_web/splash.html')

def home(request):
    search_query = request.GET.get('q', '').strip()
    active_category = request.GET.get('categoria', '').strip().lower()
    configuracion_sitio = ConfiguracionSitio.objects.first()
    platos_destacados = []
    mostrar_seccion_destacados = True
    featured_section_kicker = 'Menu completo'
    featured_section_title = 'Todos nuestros platos en movimiento'
    featured_section_subtitle = 'Recorre todo el menu disponible y agrega tus favoritos al carrito.'
    hero_primary_button_text = 'Explorar pedidos'
    hero_primary_button_url = reverse('ver_menu')
    hero_secondary_button_text = 'Crear cuenta'
    hero_secondary_button_url = reverse('registro')
    destacados_curados = []

    if configuracion_sitio:
        mostrar_seccion_destacados = configuracion_sitio.mostrar_seccion_destacados
        featured_section_kicker = configuracion_sitio.etiqueta_seccion_destacados or featured_section_kicker
        featured_section_title = configuracion_sitio.titulo_seccion_destacados or featured_section_title
        featured_section_subtitle = configuracion_sitio.subtitulo_seccion_destacados or featured_section_subtitle
        hero_primary_button_text = configuracion_sitio.texto_boton_principal_hero or hero_primary_button_text
        hero_primary_button_url = configuracion_sitio.enlace_boton_principal_hero or hero_primary_button_url
        hero_secondary_button_text = configuracion_sitio.texto_boton_secundario_hero or hero_secondary_button_text
        hero_secondary_button_url = configuracion_sitio.enlace_boton_secundario_hero or hero_secondary_button_url

        destacados_curados = [
            {
                'producto': destacado.producto,
                'descripcion_corta': destacado.descripcion_corta,
            }
            for destacado in configuracion_sitio.destacados_portada.select_related('producto').all()
            if destacado.producto.disponible
        ]

        if not destacados_curados:
            destacados_curados = list(
                {
                    'producto': producto,
                    'descripcion_corta': '',
                }
                for producto in configuracion_sitio.platos_destacados.filter(disponible=True).order_by('-id')[:5]
            )

    # El carrusel principal debe mostrar TODO el catalogo disponible.
    # Si hay destacados curados, los mostramos primero y luego anexamos el resto.
    destacados_ids = []
    destacados_lookup = {}
    for destacado in destacados_curados:
        producto = destacado['producto']
        if producto.id in destacados_lookup:
            continue
        destacados_ids.append(producto.id)
        destacados_lookup[producto.id] = destacado.get('descripcion_corta', '')

    if destacados_ids:
        for destacado in destacados_curados:
            producto = destacado['producto']
            if not producto.disponible:
                continue
            platos_destacados.append({
                'producto': producto,
                'descripcion_corta': destacado.get('descripcion_corta', ''),
            })

    productos_restantes = Producto.objects.filter(disponible=True)
    if destacados_ids:
        productos_restantes = productos_restantes.exclude(id__in=destacados_ids)

    for producto in productos_restantes.order_by('-id'):
        platos_destacados.append({
            'producto': producto,
            'descripcion_corta': destacados_lookup.get(producto.id, ''),
        })

    filter_terms = {
        'combos': ('combo',),
        'papas': ('papa', 'papas', 'frita', 'fritas'),
        'bebidas': ('bebida', 'jugo', 'agua', 'gaseosa', 'cola'),
    }
    category_labels = {
        'combos': 'Combos',
        'papas': 'Papas Fritas',
        'bebidas': 'Bebidas',
    }
    if active_category in filter_terms:
        search_terms = filter_terms[active_category]
        platos_destacados = [
            plato for plato in platos_destacados
            if any(
                term in f"{plato['producto'].nombre} {plato['producto'].descripcion or ''}".lower()
                for term in search_terms
            )
        ]

    if search_query:
        normalized_query = search_query.lower()
        platos_destacados = [
            plato for plato in platos_destacados
            if normalized_query in plato['producto'].nombre.lower()
            or normalized_query in (plato['producto'].descripcion or '').lower(            )
        ]

    if active_category in category_labels:
        featured_section_kicker = f'Categoría seleccionada: {category_labels[active_category]}'
        featured_section_title = category_labels[active_category]
        featured_section_subtitle = 'Selecciona un producto para conocer sus detalles y agregarlo a tu pedido.'

    return render(request, 'gestion_web/home.html', {
        'configuracion_sitio': configuracion_sitio,
        'platos_destacados': platos_destacados,
        'mostrar_seccion_destacados': mostrar_seccion_destacados,
        'featured_section_kicker': featured_section_kicker,
        'featured_section_title': featured_section_title,
        'featured_section_subtitle': featured_section_subtitle,
        'hero_primary_button_text': hero_primary_button_text,
        'hero_primary_button_url': hero_primary_button_url,
        'hero_secondary_button_text': hero_secondary_button_text,
        'hero_secondary_button_url': hero_secondary_button_url,
        'search_query': search_query,
        'active_category': active_category,
        'category_label': category_labels.get(active_category, ''),
    })

# Vista principal "Realizar Pedido"
@login_required
def ver_menu(request):
    # Mensaje de confirmación de pedidos (placeholder actual del flujo de pedidos).
    mensaje_confirmacion = None
    modulo = request.GET.get('modulo', '').strip().lower()
    modulo_reservas = modulo == 'reservas'
    modulo_pedidos = modulo != 'reservas'

    # Mensajes flash de reservas (se leen desde sesión y se consumen una sola vez).
    # Esto permite redirigir tras POST y mostrar feedback en el GET siguiente.
    reserva_confirmacion = request.session.pop('reserva_confirmacion', None)
    reserva_error = request.session.pop('reserva_error', None)
    reserva_sugerencias = request.session.pop('reserva_sugerencias', [])
    reserva_sugerida_mesa_id = request.session.pop('reserva_sugerida_mesa_id', None)

    # Filtrado obligatorio solicitado:
    # solamente exponemos al cliente mesas cuyo estado operativo sea DISPONIBLE.
    mesas_disponibles = list(
        Mesa.objects.filter(estado=Mesa.EstadoMesa.DISPONIBLE).order_by('numero')
    )

    # Catálogo de productos visible en la pestaña de pedidos.
    productos = Producto.objects.filter(disponible=True)
    
    mis_reservas = []
    mis_pedidos = []

    # Cargamos historial del usuario para las pestañas "Mis Reservas" y "Mis Entregas".
    if request.user.is_authenticated:
        mis_reservas = list(Reserva.objects.filter(cliente=request.user).order_by('-fecha'))
        mis_pedidos = list(Pedido.objects.filter(cliente=request.user).select_related('pago', 'comprobante', 'entrega').order_by('-fecha_creacion'))

        # Añadir atributos legibles para estado para evitar problemas de renderizado literal
        for r in mis_reservas:
            try:
                r.estado_display = r.get_estado_display()
            except Exception:
                r.estado_display = str(r.estado)
        for p in mis_pedidos:
            try:
                p.estado_display = p.get_estado_display()
            except Exception:
                p.estado_display = str(p.estado)
            # Detectamos si el pago fue confirmado por cualquiera de las vías del sistema.
            comprobante_validado = False
            try:
                comprobante_validado = p.comprobante.estado == 'VALIDADO'
            except Exception:
                comprobante_validado = False
            pago_reportado = False
            try:
                pago_reportado = p.pago.estado == 'CONFIRMADO'
            except Exception:
                pago_reportado = False
            p.tiene_pago_aprobado = (
                p.estado == 'PAGADO'
                or pago_reportado
                or comprobante_validado
            )

            # Mantenemos el estado real del pedido para evitar incoherencias en el historial.
            # Solo usamos "Pago confirmado" cuando realmente está en etapa de pago.
            if p.estado == 'PENDIENTE_PAGO':
                p.estado_display_cliente = 'Pago confirmado' if p.tiene_pago_aprobado else 'Pendiente de pago'
            elif p.estado == 'PAGADO':
                p.estado_display_cliente = 'Pago confirmado'
            else:
                p.estado_display_cliente = p.estado_display

            # Si el pedido es a domicilio, compartimos la ubicación para cliente,
            # admin y repartidor desde la misma fuente de datos.
            p.entrega_direccion = ''
            p.entrega_latitud = None
            p.entrega_longitud = None
            p.entrega_mapa_url = ''
            p.entrega_ruta_url = ''
            entrega = getattr(p, 'entrega', None)
            if entrega:
                p.entrega_direccion = entrega.direccion or ''
                p.entrega_latitud = entrega.latitud
                p.entrega_longitud = entrega.longitud

                if entrega.latitud is not None and entrega.longitud is not None:
                    destination = f'{entrega.latitud},{entrega.longitud}'
                else:
                    destination = quote_plus(entrega.direccion or '')

                if destination:
                    p.entrega_mapa_url = f'https://www.google.com/maps?q={destination}'
                    p.entrega_ruta_url = f'https://www.google.com/maps/dir/?api=1&destination={destination}'

            # ETA visible para el cliente en pedidos a domicilio.
            p.tiempo_estimado_entrega = ''
            if p.tipo == 'DOMICILIO':
                if p.estado == 'ENTREGADO':
                    p.tiempo_estimado_entrega = 'Entregado'
                elif p.estado == 'CANCELADO':
                    p.tiempo_estimado_entrega = 'Pedido cancelado'
                elif p.estado == 'PENDIENTE_PAGO' and not p.tiene_pago_aprobado:
                    p.tiempo_estimado_entrega = 'Pendiente de confirmación de pago'
                else:
                    entrega_estimada = getattr(entrega, 'tiempo_estimado_minutos', None) if entrega else None
                    if entrega_estimada is None:
                        entrega_estimada = 30

                    referencia = timezone.localtime(p.fecha_creacion)
                    eta_obj = referencia + timedelta(minutes=int(entrega_estimada))
                    ahora = timezone.localtime(timezone.now())
                    minutos_restantes = ceil((eta_obj - ahora).total_seconds() / 60)

                    if minutos_restantes <= 0:
                        p.tiempo_estimado_entrega = 'Llegando en pocos minutos'
                    elif minutos_restantes < 60:
                        p.tiempo_estimado_entrega = f'{minutos_restantes} min aprox.'
                    else:
                        horas = minutos_restantes // 60
                        mins = minutos_restantes % 60
                        if mins == 0:
                            p.tiempo_estimado_entrega = f'{horas} h aprox.'
                        else:
                            p.tiempo_estimado_entrega = f'{horas} h {mins} min aprox.'

    return render(request, 'gestion_web/menu.html', {
        'productos': productos,
        # Solo mesas DISPONIBLE viajan al cliente para evitar selección inválida en UI.
        'mesas_disponibles': mesas_disponibles,
        'mensaje_confirmacion': mensaje_confirmacion,
        'reserva_confirmacion': reserva_confirmacion,
        'reserva_error': reserva_error,
        'reserva_sugerencias': reserva_sugerencias,
        # Si hubo rechazo por mesa ocupada/no válida, preseleccionamos una sugerida.
        'reserva_sugerida_mesa_id': reserva_sugerida_mesa_id,
        'reservas': mis_reservas,
        'pedidos': mis_pedidos,
        'test_valor': 'FUNCIONA_CORRECTAMENTE',
        'modulo_reservas': modulo_reservas,
        'modulo_pedidos': modulo_pedidos,
    })

@login_required
@transaction.atomic
def crear_reserva(request):
    # Este endpoint procesa el formulario de reserva del cliente.
    # Regla de negocio principal:
    # 1) Solo se puede reservar una mesa en estado DISPONIBLE.
    # 2) Si la mesa elegida está ocupada/no disponible, se rechaza y se sugiere una libre.
    # 3) Si no se eligió mesa, el sistema asigna la primera disponible que cumpla capacidad/horario.
    if request.method == 'POST':
        # Capturamos campos básicos del formulario.
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        numero_personas = request.POST.get('numero_personas') or request.POST.get('personas')
        notas = request.POST.get('notas') or request.POST.get('notes') or ''
        mesa_id = request.POST.get('mesa_id')
        prepedido_ids = request.POST.getlist('prepedido_productos')
        # También consideramos como seleccionado cualquier producto cuya cantidad
        # enviada sea mayor a 1 (el usuario pudo aumentar cantidad pero olvidar
        # marcar el checkbox). Evita perder selecciones por errores de UX.
        try:
            # normalizamos a strings (getlist devuelve strings)
            prepedido_set = set(str(x) for x in prepedido_ids)
        except Exception:
            prepedido_set = set()

        for p in Producto.objects.filter(disponible=True):
            try:
                cant = int(request.POST.get(f'prepedido_cantidad_{p.id}', '1'))
            except Exception:
                cant = 1
            if cant > 1:
                prepedido_set.add(str(p.id))

        prepedido_ids = list(prepedido_set)

        # El pre-pedido es opcional: solo se convierte en Pedido si el cliente marcó al menos un plato.
        prepedido_items = []
        prepedido_total = Decimal('0.00')

        # `mesa_asignada` será la mesa final aprobada para la reserva.
        mesa_asignada = None

        # Convertimos personas a entero para poder filtrar por capacidad.
        try:
            miembros = int(numero_personas)
        except Exception:
            miembros = 1

        # Parseamos fecha y hora para validación de solapes por intervalo.
        try:
            reserva_fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
        except Exception:
            reserva_fecha = None
        try:
            reserva_hora = datetime.strptime(hora, '%H:%M').time()
        except Exception:
            reserva_hora = None

        if not reserva_fecha or not reserva_hora:
            request.session['reserva_error'] = 'Ingresa una fecha y hora válidas.'
            return redirect(f"{reverse('ver_menu')}?modulo=reservas")

        if not dentro_del_horario(reserva_hora):
            request.session['reserva_error'] = (
                f'{horario_atencion_texto()} No puedes reservar fuera de ese horario.'
            )
            return redirect(f"{reverse('ver_menu')}?modulo=reservas")

        ahora_local = timezone.localtime()
        if reserva_fecha == ahora_local.date() and reserva_hora < ahora_local.time().replace(second=0, microsecond=0):
            request.session['reserva_error'] = (
                'La hora elegida ya pasó. Selecciona una hora futura dentro del horario de atención.'
            )
            return redirect(f"{reverse('ver_menu')}?modulo=reservas")

        # Duración estándar estimada de ocupación por reserva.
        # Se usa para detectar cruces entre reservas de la misma mesa.
        duration_hours = 2
        start_dt = None
        end_dt = None
        if reserva_fecha and reserva_hora:
            start_dt = datetime.combine(reserva_fecha, reserva_hora)
            end_dt = start_dt + timedelta(hours=duration_hours)

        # Función auxiliar que comprueba si una mesa está libre en un intervalo.
        # Devuelve False si detecta solape con cualquier reserva existente de esa mesa.
        def mesa_disponible_para_intervalo(mesa, inicio, fin):
            existing = Reserva.objects.filter(mesa=mesa, fecha=reserva_fecha)
            for ex in existing:
                try:
                    ex_start = datetime.combine(ex.fecha, ex.hora)
                    ex_end = ex_start + timedelta(hours=duration_hours)
                    if (inicio < ex_end) and (ex_start < fin):
                        return False
                except Exception:
                    continue
            return True

        # Candidatas: solo mesas marcadas por el staff como DISPONIBLE y con capacidad suficiente.
        mesas_candidatas = Mesa.objects.filter(
            estado=Mesa.EstadoMesa.DISPONIBLE,
            capacidad__gte=miembros,
        ).order_by('numero')

        # Definimos la primera mesa libre para este horario como sugerencia automática.
        mesa_sugerida = None
        if start_dt and end_dt:
            for mesa in mesas_candidatas:
                if mesa_disponible_para_intervalo(mesa, start_dt, end_dt):
                    mesa_sugerida = mesa
                    break

        # Si el cliente intentó forzar una mesa específica (mesa_id), la validamos.
        if mesa_id:
            mesa_seleccionada = Mesa.objects.filter(id=mesa_id).first()

            # Caso 1: id inexistente o alterado.
            if not mesa_seleccionada:
                request.session['reserva_error'] = 'La mesa seleccionada no existe.'
                if mesa_sugerida:
                    request.session['reserva_error'] = (
                        f'La mesa seleccionada no existe. Te sugerimos seleccionar la Mesa {mesa_sugerida.numero}.'
                    )
                    request.session['reserva_sugerida_mesa_id'] = mesa_sugerida.id
                return redirect(f"{reverse('ver_menu')}?modulo=reservas")

            # Caso 2: mesa no disponible por estado operativo (ocupada o mantenimiento).
            if mesa_seleccionada.estado != Mesa.EstadoMesa.DISPONIBLE:
                request.session['reserva_error'] = (
                    f'La Mesa {mesa_seleccionada.numero} esta ocupada o no disponible.'
                )
                if mesa_sugerida:
                    request.session['reserva_error'] = (
                        f'La Mesa {mesa_seleccionada.numero} esta ocupada. '
                        f'Te sugerimos seleccionar la Mesa {mesa_sugerida.numero}.'
                    )
                    request.session['reserva_sugerida_mesa_id'] = mesa_sugerida.id
                return redirect(f"{reverse('ver_menu')}?modulo=reservas")

            # Caso 3: mesa disponible por estado, pero ocupada por cruce horario.
            if not (start_dt and end_dt and mesa_disponible_para_intervalo(mesa_seleccionada, start_dt, end_dt)):
                request.session['reserva_error'] = (
                    f'La Mesa {mesa_seleccionada.numero} no esta libre en ese horario.'
                )
                if mesa_sugerida:
                    request.session['reserva_error'] = (
                        f'La Mesa {mesa_seleccionada.numero} esta ocupada. '
                        f'Te sugerimos seleccionar la Mesa {mesa_sugerida.numero}.'
                    )
                    request.session['reserva_sugerida_mesa_id'] = mesa_sugerida.id
                return redirect(f"{reverse('ver_menu')}?modulo=reservas")

            # Caso válido: el cliente eligió una mesa realmente disponible.
            mesa_asignada = mesa_seleccionada
        else:
            # Si no eligió mesa manualmente, asignamos la primera disponible automática.
            mesa_asignada = mesa_sugerida

        # Si no hay mesa disponible en horario exacto, proponemos horarios cercanos.
        if not mesa_asignada:
            sugerencias = []
            if start_dt and reserva_fecha:
                for offset in (-90, -60, -30, 30, 60, 90):
                    candidato_inicio = start_dt + timedelta(minutes=offset)
                    if candidato_inicio.date() != reserva_fecha:
                        continue
                    candidato_fin = candidato_inicio + timedelta(hours=duration_hours)
                    for m in mesas_candidatas:
                        if mesa_disponible_para_intervalo(m, candidato_inicio, candidato_fin):
                            sugerencias.append({
                                'hora': candidato_inicio.strftime('%H:%M'),
                                'mesa_numero': m.numero,
                            })
                            break
                    if len(sugerencias) >= 3:
                        break

            request.session['reserva_error'] = (
                'No hay mesas disponibles para esa fecha y hora. Intenta con otro horario.'
            )
            request.session['reserva_sugerencias'] = sugerencias
            request.session.pop('reserva_sugerida_mesa_id', None)
            return redirect(f"{reverse('ver_menu')}?modulo=reservas")

        # Si la reserva ya es válida, convertimos los platos opcionales en un Pedido vinculado.
        for producto_id in prepedido_ids:
            try:
                producto = Producto.objects.get(id=producto_id, disponible=True)
            except Producto.DoesNotExist:
                continue

            try:
                cantidad = int(request.POST.get(f'prepedido_cantidad_{producto_id}', 1))
            except Exception:
                cantidad = 1

            if cantidad < 1:
                cantidad = 1

            subtotal = Decimal(producto.precio) * Decimal(cantidad)
            prepedido_items.append({
                'producto': producto,
                'cantidad': cantidad,
                'precio_unitario': producto.precio,
                'subtotal': subtotal,
            })
            prepedido_total += subtotal

        pedido_previo = None
        if prepedido_items:
            pedido_previo = Pedido.objects.create(
                cliente=request.user,
                tipo=Pedido.TipoPedido.LOCAL,
                estado=Pedido.EstadoPedido.PENDIENTE_PAGO,
                total=prepedido_total,
            )
            # Creamos los detalles del pedido antes de guardar la reserva para dejar trazado el consumo solicitado.
            for item in prepedido_items:
                DetallePedido.objects.create(
                    pedido=pedido_previo,
                    producto=item['producto'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio_unitario'],
                )

        # Si llegamos aquí, la mesa ya fue validada y la reserva se puede crear.
        estado = Reserva.EstadoReserva.CONFIRMADA

        reserva = Reserva.objects.create(
            cliente=request.user,
            mesa=mesa_asignada,
            pedido=pedido_previo,
            fecha=fecha,
            hora=hora,
            numero_personas=numero_personas,
            estado=estado,
            notes=notas
        )

        # Programamos el correo después del commit para no deshacer la reserva si el envío falla.
        if reserva.estado == 'CONFIRMADA':
            transaction.on_commit(lambda: send_reserva_confirmada_email(reserva))

        # Mensaje de éxito que se mostrará en la pestaña de reservas.
        request.session['reserva_confirmacion'] = (
            f"✅ ¡Reserva agendada con éxito! Te hemos asignado la Mesa #{mesa_asignada.numero}"
        )
        # Limpiamos sugerencias viejas para evitar que aparezcan tras un éxito.
        request.session.pop('reserva_sugerencias', None)
        request.session.pop('reserva_sugerida_mesa_id', None)

        return redirect(f"{reverse('ver_menu')}?modulo=reservas")

    return redirect(f"{reverse('ver_menu')}?modulo=reservas")

@require_http_methods(["GET", "POST"])
def registrar_usuario(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            # Guardamos la aceptación de política de datos al momento de crear la cuenta.
            usuario = form.save(commit=False)
            usuario.acepta_politica_datos = True
            usuario.fecha_aceptacion_politica = timezone.now()
            usuario.version_politica_datos = 'v1.0'
            usuario.set_password(form.cleaned_data['password1'])
            usuario.save()
            messages.success(request, 'Cuenta creada correctamente, inicia sesión para continuar')
            return redirect('login')
    else:
        form = RegistroForm()

    return render(request, 'gestion_web/register.html', {'form': form})


def politica_privacidad(request):
    return render(request, 'gestion_web/politica_privacidad.html')


def _es_personal_administrativo(user):
    return (
        user.is_authenticated
        and user.is_staff
        and getattr(user, 'rol', None) == 'ADMIN'
    )


@login_required
@user_passes_test(_es_personal_administrativo)
def reportes_admin(request):
    """Presenta indicadores operativos calculados desde los registros del sistema."""
    hoy = timezone.localdate()
    fecha_desde = request.GET.get('desde', '').strip()
    fecha_hasta = request.GET.get('hasta', '').strip()

    try:
        desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date() if fecha_desde else hoy.replace(day=1)
        hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date() if fecha_hasta else hoy
    except ValueError:
        desde = hoy.replace(day=1)
        hasta = hoy

    if desde > hasta:
        desde, hasta = hasta, desde

    pedidos = Pedido.objects.filter(
        fecha_creacion__date__range=(desde, hasta),
    ).select_related('cliente')
    reservas = Reserva.objects.filter(fecha__range=(desde, hasta))

    estados_pedido = list(
        pedidos.values('estado').annotate(total=Count('id')).order_by('estado')
    )
    tipos_pedido = list(
        pedidos.values('tipo').annotate(total=Count('id')).order_by('tipo')
    )
    pedidos_no_cancelados = pedidos.exclude(estado=Pedido.EstadoPedido.CANCELADO)
    ventas_registradas = pedidos_no_cancelados.aggregate(total=Sum('total'))['total'] or Decimal('0.00')
    ventas_pagadas = pedidos.filter(
        estado__in=(
            Pedido.EstadoPedido.PAGADO,
            Pedido.EstadoPedido.PREPARANDO,
            Pedido.EstadoPedido.ENTREGADO,
        )
    ).aggregate(total=Sum('total'))['total'] or Decimal('0.00')

    productos_mas_pedidos = list(
        DetallePedido.objects.filter(
            pedido__in=pedidos_no_cancelados,
        ).values(
            'producto__nombre',
        ).annotate(
            cantidad=Sum('cantidad'),
        ).order_by('-cantidad', 'producto__nombre')[:10]
    )
    estados_reserva = list(
        reservas.values('estado').annotate(total=Count('id')).order_by('estado')
    )
    entregas = Entrega.objects.filter(pedido__in=pedidos)
    entregas_por_estado = entregas.values('estado_envio').annotate(total=Count('id')).order_by('estado_envio')

    # Entregas por dia (basado en fecha de creación del pedido asociado)
    entregas_por_dia = list(
        entregas.annotate(fecha=TruncDate('pedido__fecha_creacion')).values('fecha').annotate(total=Count('id')).order_by('fecha')
    )

    # Reservas por dia
    reservas_por_dia = list(
        reservas.annotate(fecha_dia=TruncDate('fecha')).values('fecha_dia').annotate(total=Count('id')).order_by('fecha_dia')
    )

    # Entregas por repartidor: usamos Pago.confirmado_por como proxy cuando esté disponible
    entregas_por_repartidor = list(
        # pagos ligados a pedidos que tengan entrega
        # contamos pagos confirmados por usuario (repartidor) en el rango
        # esto solo actúa como proxy si en tu flujo el repartidor reporta el pago o confirma la entrega
        # (no existe campo repartidor en Entrega en el modelo gestion_web)
        
        # Joins: Pago -> Pedido -> Entrega
        
        # Usar el ORM para agrupar
        
        # Import Pago localmente para evitar circular imports
        
    )

    insumos_sin_stock = list(
        Insumo.objects.filter(stock__lte=0).select_related('proveedor').order_by('nombre')
    )

    # Calculamos entregas por repartidor como conteo de pagos con confirmado_por que tienen entrega asociada
    from .models import Pago
    entregas_por_repartidor_qs = Pago.objects.filter(
        confirmado_por__isnull=False,
        confirmado_en__date__range=(desde, hasta),
        pedido__entrega__isnull=False,
    ).values('confirmado_por__username').annotate(total=Count('id')).order_by('-total')
    entregas_por_repartidor = list(entregas_por_repartidor_qs)

    # CSV export: soportamos detalle específico para entregas o reservas
    if request.GET.get('formato') == 'csv':
        detalle = request.GET.get('detalle')
        if detalle == 'entregas':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = (
                f'attachment; filename="entregas_{desde.isoformat()}_{hasta.isoformat()}.csv"'
            )
            response.write('\ufeff')
            response.write('EntregaID,PedidoID,Cliente,Direccion,EstadoEnvio,FechaPedido,Latitud,Longitud,TiempoEstimadoMinutos, CargoAdicional\r\n')
            for e in entregas.select_related('pedido__cliente').order_by('-pedido__fecha_creacion'):
                fecha_ped = e.pedido.fecha_creacion.strftime('%Y-%m-%d %H:%M:%S') if e.pedido and e.pedido.fecha_creacion else ''
                response.write(f'{e.id},{e.pedido.id},{e.pedido.cliente.username if e.pedido.cliente else ""},"{(e.direccion or "").replace(chr(34), "'")}",{e.estado_envio},{fecha_ped},{e.latitud or ""},{e.longitud or ""},{e.tiempo_estimado_minutos},{e.cargo_adicional}\r\n')
            return response
        elif detalle == 'reservas':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = (
                f'attachment; filename="reservas_{desde.isoformat()}_{hasta.isoformat()}.csv"'
            )
            response.write('\ufeff')
            response.write('ReservaID,Cliente,Fecha,Hora,Personas,Mesa,Estado,Notas\r\n')
            for r in reservas.select_related('cliente','mesa').order_by('-fecha'):
                response.write(f'{r.id},{r.cliente.username if r.cliente else ""},{r.fecha},{r.hora},{r.numero_personas},{r.mesa.numero if r.mesa else ""},{r.estado},"{(r.notes or "").replace(chr(34), "'")}"\r\n')
            return response
        else:
            # Mantener el comportamiento previo para exportación resumida
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = (
                f'attachment; filename="reporte_{desde.isoformat()}_{hasta.isoformat()}.csv"'
            )
            response.write('\ufeff')
            response.write('Indicador,Valor\r\n')
            response.write(f'Periodo,"{desde} a {hasta}"\r\n')
            response.write(f'Pedidos,{pedidos.count()}\r\n')
            response.write(f'Ventas registradas,{ventas_registradas}\r\n')
            response.write(f'Ventas pagadas,{ventas_pagadas}\r\n')
            response.write(f'Reservas,{reservas.count()}\r\n')
            response.write('\r\nEstado de pedidos,Total\r\n')
            for row in estados_pedido:
                response.write(f'{row["estado"]},{row["total"]}\r\n')
            response.write('\r\nProductos mas pedidos,Cantidad\r\n')
            for row in productos_mas_pedidos:
                response.write(f'"{row["producto__nombre"]}",{row["cantidad"]}\r\n')
            response.write('\r\nInsumos sin stock,Unidad de medida\r\n')
            for insumo in insumos_sin_stock:
                response.write(f'"{insumo.nombre}",{insumo.unidad_medida}\r\n')
            return response

    # Serializar series para uso en JS (Chart.js)
    entregas_por_dia_json = json.dumps([{'fecha': str(row['fecha']), 'total': row['total']} for row in entregas_por_dia])
    reservas_por_dia_json = json.dumps([{'fecha_dia': str(row['fecha_dia']), 'total': row['total']} for row in reservas_por_dia])

    context = {
        'desde': desde.isoformat(),
        'hasta': hasta.isoformat(),
        'pedidos_total': pedidos.count(),
        'ventas_registradas': ventas_registradas,
        'ventas_pagadas': ventas_pagadas,
        'reservas_total': reservas.count(),
        'estados_pedido': estados_pedido,
        'tipos_pedido': tipos_pedido,
        'productos_mas_pedidos': productos_mas_pedidos,
        'estados_reserva': estados_reserva,
        'entregas': entregas_por_estado,
        'insumos_sin_stock': insumos_sin_stock,
        'entregas_por_dia': entregas_por_dia_json,
        'reservas_por_dia': reservas_por_dia_json,
        'entregas_por_repartidor': entregas_por_repartidor,
    }
    return render(request, 'admin/reportes.html', context)


def _requiere_rol(*roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if request.user.rol not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
