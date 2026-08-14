from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from gestion_web import views as gestion_views

urlpatterns = [
    path('', gestion_views.splash, name='splash'),
    path('admin/reportes/', gestion_views.reportes_admin, name='admin_reportes'),
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')), #Ruta Nativa para procesar los cambios de idioma
    # 1. Sistema de autenticación nativo e independiente
    path('ingresar/', auth_views.LoginView.as_view(template_name='gestion_web/login.html'), name='login'),
    path('login/', RedirectView.as_view(pattern_name='home', permanent=False)),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('registro/', gestion_views.registrar_usuario, name='registro'), # Ruta para crear cuenta
    
    # Rutas para recuperación de contraseña (Password Reset)
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # Aplicación independiente para la lógica de negocio
    path('', include('gestion_web.urls')),
    path('pagos/', include(('pagos.urls','pagos'), namespace='pagos')),
    path('pedidos/', include(('pedidos.urls','pedidos'), namespace='pedidos')),
    path('reservas/', include(('reservas.urls','reservas'), namespace='reservas')),
    path('entregas/', include(('entregas.urls','entregas'), namespace='entregas')),
    path('usuarios/', include(('usuarios.urls', 'usuarios'), namespace='usuarios')),
]


# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)