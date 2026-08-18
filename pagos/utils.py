from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_comprobante_validado_email(comprobante):
    """Enviar notificación de comprobante validado al cliente."""
    destinatario = comprobante.pedido.cliente.email
    if not destinatario:
        return

    subject = f'Tu comprobante de pago ha sido validado - Pedido #{comprobante.pedido.id}'
    context = {
        'pedido': comprobante.pedido,
        'comprobante': comprobante,
        'pedido_estado_display': comprobante.pedido.get_estado_display(),
    }

    text_body = render_to_string('pagos/email/comprobante_validado.txt', context)
    html_body = render_to_string('pagos/email/comprobante_validado.html', context)

    email = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [destinatario])
    email.attach_alternative(html_body, 'text/html')
    email.send()


def send_comprobante_rechazado_email(comprobante):
    """Enviar notificación de comprobante rechazado al cliente."""
    destinatario = comprobante.pedido.cliente.email
    if not destinatario:
        return

    subject = f'Tu comprobante de pago fue rechazado - Pedido #{comprobante.pedido.id}'
    context = {
        'pedido': comprobante.pedido,
        'comprobante': comprobante,
        'pedido_estado_display': comprobante.pedido.get_estado_display(),
    }

    text_body = render_to_string('pagos/email/comprobante_rechazado.txt', context)
    html_body = render_to_string('pagos/email/comprobante_rechazado.html', context)

    email = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [destinatario])
    email.attach_alternative(html_body, 'text/html')
    email.send()
