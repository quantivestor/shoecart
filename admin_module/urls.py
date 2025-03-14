from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('profile/', views.profile, name='admin_profile'),
    path('logout/', views.logout_view, name='admin_logout'),

    path('review/', views.review_brand_registrations, name='review_brand_registrations'),
    path('approve/<int:brand_id>/', views.approve_brand, name='approve_brand'),
    path('reject/<int:brand_id>/', views.reject_brand, name='reject_brand'),
    path('brand-list/', views.list_brand_details, name='list_brand_details'),

    path('customer-list/', views.list_customer_details, name='list_customer_details'),
    path('admin/brands/delete/<int:brand_id>/', views.delete_brand, name='delete_brand'),
    path('admin/customer/delete/<int:cus_id>/', views.delete_customer, name='delete_customer'),

    path('login/', views.userlogin, name='login'),
]