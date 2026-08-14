from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('perfil/', views.mi_perfil, name='mi_perfil'),
    path('gestion/', views.lista_usuarios, name='lista_usuarios'),
    path('gestion/crear/', views.crear_usuario, name='crear_usuario'),
    path('gestion/<int:usuario_id>/editar/', views.editar_usuario, name='editar_usuario'),
    path('gestion/<int:usuario_id>/eliminar/', views.eliminar_usuario, name='eliminar_usuario'),
]
