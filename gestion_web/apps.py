from django.apps import AppConfig


class GestionWebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_web'

    def ready(self):
        import gestion_web.signals 
