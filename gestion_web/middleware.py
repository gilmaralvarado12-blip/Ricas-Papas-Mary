from django.conf import settings


class SessionExpiryByRoleMiddleware:
    # Usa el tiempo de sesión global configurado en settings.py.
    CLIENT_SESSION_TIMEOUT_SECONDS = settings.SESSION_COOKIE_AGE
    ADMIN_SESSION_TIMEOUT_SECONDS = 60 * 60 * 24 * 7

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return response

        if getattr(request.user, 'rol', None) == 'CLIENTE':
            request.session.set_expiry(self.CLIENT_SESSION_TIMEOUT_SECONDS)
        else:
            request.session.set_expiry(self.ADMIN_SESSION_TIMEOUT_SECONDS)

        return response
