from django.urls import path, include

from customer_module import views

urlpatterns = [
    path('', views.user_home, name='user_home'),
    path('login/', views.user_home, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('register/', views.user_register, name='user_register'),

    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:cart_id>/', views.remove_from_cart, name='remove_from_cart'),

    path('orders/place/', views.place_order, name='place_order'),
    path('orders/', views.view_orders, name='view_orders'),
    path('orders/deliver/<int:order_id>/', views.mark_order_delivered, name='mark_order_delivered'),

]