from django.urls import path

from . import views

urlpatterns = [
    path("", views.brand_home, name="brand_dashboard"),
    path("logout/", views.brand_logout, name="brand_logout"),
    path("add-product/", views.add_product, name="add_product"),
    path("view-products/", views.view_products, name="view_products"),
    path(
        "update-product/<int:product_id>/", views.update_product, name="update_product"
    ),
    path(
        "delete-product/<int:product_id>/", views.delete_product, name="delete_product"
    ),
    path("feedbacks/", views.view_feedbacks, name="view_feedbacks"),
    path("sell-history/", views.view_sell_history, name="view_sell_history"),
    path("register/", views.brand_register, name="brand_register"),
    path("login/", views.brand_login, name="brand_login"),
    path("logout/", views.brand_logout, name="brand_logout"),
    path("profile/", views.brand_profile, name="brand_profile"),
    path("approve-order/<int:order_id>/", views.approve_order, name="approve_order"),
    path("reject-order/<int:order_id>/", views.reject_order, name="reject_order"),
]
