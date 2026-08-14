from django.urls import path
from . import views

app_name = 'entregas'

urlpatterns = [
    path('', views.lista_entregas, name='lista_entregas'),
    path('actualizar/<int:entrega_id>/', views.actualizar_estado, name='actualizar_estado'),
    path('confirmar-pago/<int:entrega_id>/', views.confirmar_pago, name='confirmar_pago'),
]
