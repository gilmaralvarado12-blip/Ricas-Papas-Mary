from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_reserva_confirmada_email(reserva):
    """Enviar notificación de reserva confirmada al cliente."""
    destinatario = reserva.cliente.email
    if not destinatario:
        return

    subject = f'Reserva confirmada - Mesa #{reserva.mesa.numero if reserva.mesa else "N/A"}'
    context = {
        'reserva': reserva,
    }

    text_body = render_to_string('reservas/email/reserva_confirmada.txt', context)
    html_body = render_to_string('reservas/email/reserva_confirmada.html', context)

    email = EmailMultiAlternatives(subject, text_body, settings.DEFAULT_FROM_EMAIL, [destinatario])
    email.attach_alternative(html_body, 'text/html')
    email.send()
