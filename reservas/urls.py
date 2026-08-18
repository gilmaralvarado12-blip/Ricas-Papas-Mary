from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('crear/', views.crear_reserva, name='crear_reserva'),
    path('mis_reservas/', views.mis_reservas, name='mis_reservas'),
]
