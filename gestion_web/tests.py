from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .forms import RegistroForm
from .middleware import SessionExpiryByRoleMiddleware


class SeguridadTests(TestCase):
    def test_registro_rechaza_entrada_html_en_username(self):
        form = RegistroForm(data={
            'username': '<script>alert("x")</script>',
            'password1': 'Password123!',
            'password2': 'Password123!',
            'acepta_politica_datos': True,
        })

        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_sesion_expira_por_inactividad_en_5_minutos_solo_para_clientes(self):
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)
        self.assertTrue(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)

        Usuario = get_user_model()

        cliente = Usuario.objects.create_user(username='cliente_test', password='Password123!', rol='CLIENTE')
        admin = Usuario.objects.create_user(username='admin_test', password='Password123!', rol='ADMIN')

        middleware = SessionExpiryByRoleMiddleware(lambda request: None)

        request_cliente = RequestFactory().get('/')
        request_cliente.user = cliente
        request_cliente.session = SessionStore()
        middleware(request_cliente)
        self.assertEqual(request_cliente.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)

        request_admin = RequestFactory().get('/')
        request_admin.user = admin
        request_admin.session = SessionStore()
        middleware(request_admin)
        self.assertGreater(request_admin.session.get_expiry_age(), settings.SESSION_COOKIE_AGE)
