from django.urls import path
from . import views

urlpatterns = [
    path('', views.shop_home, name='shop_dashboard'),
    path('logout/', views.shop_logout, name='shop_logout'),

    path('add-product/', views.add_product, name='add_product'),
    path('view-products/', views.view_products, name='view_products'),
    path('update-product/<int:product_id>/', views.update_product, name='update_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),

    path('feedbacks/', views.view_feedbacks, name='view_feedbacks'),
    path('sell-history/', views.view_sell_history, name='view_sell_history'),

    path('register/', views.shop_register, name='shop_register'),
    path('login/', views.shop_login, name='shop_login'),
    path('logout/', views.shop_logout, name='shop_logout'),
    path('profile/', views.shop_profile, name='shop_profile'),

    path('approve-order/<int:order_id>/', views.approve_order, name='approve_order'),
    path('reject-order/<int:order_id>/', views.reject_order, name='reject_order'),
]