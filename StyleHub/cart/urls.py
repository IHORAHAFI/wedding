from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('order-history/', views.order_history, name='order_history'),
    path('add/<int:product_id>/', views.add_to_cart, name='add'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='wishlist_add'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='wishlist_toggle'),
    path('update/<int:order_id>/', views.update_order_quantity, name='update_quantity'),
    path('remove/<int:order_id>/', views.remove_order, name='remove_order'),
    path('checkout/', views.checkout, name='checkout'),
    path('receipt/', views.payment_receipt, name='payment_receipt'),
    path('verify/', views.payment_verify, name='payment_verify'),
    path('api/count/', views.cart_count_api, name='api_count'),
]
