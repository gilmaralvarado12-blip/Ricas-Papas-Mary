from django.urls import path
from . import views

app_name = 'pedidos'

urlpatterns = [
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:product_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/editar/', views.edit_cart, name='edit_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('cancelar/<int:pedido_id>/', views.cancel_order, name='cancel_order'),
]
