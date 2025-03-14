from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.profile, name='admin_profile'),
    path('logout/', views.logout_view, name='admin_logout'),

    path('review/', views.review_shop_registrations, name='review_shop_registrations'),
    path('approve/<int:shop_id>/', views.approve_shop, name='approve_shop'),
    path('reject/<int:shop_id>/', views.reject_shop, name='reject_shop'),
    path('shop-list/', views.list_shop_details, name='list_shop_details'),

    path('customer-list/', views.list_customer_details, name='list_customer_details'),
    path('admin/shops/delete/<int:shop_id>/', views.delete_shop, name='delete_shop'),
    path('admin/customer/delete/<int:cus_id>/', views.delete_customer, name='delete_customer'),

    path('login/', views.userlogin, name='login'),
]