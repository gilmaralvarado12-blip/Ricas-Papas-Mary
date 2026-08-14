from django.urls import path
from . import views

urlpatterns = [
    path('subir/<int:pedido_id>/', views.subir_comprobante, name='subir_comprobante'),
    path('validar/<int:comprobante_id>/', views.validar_comprobante, name='validar_comprobante'),
    path('lista/', views.lista_comprobantes, name='lista_comprobantes'),
]
