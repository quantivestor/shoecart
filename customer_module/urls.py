from django.urls import include, path

from customer_module import views

urlpatterns = [
    path("", views.user_home, name="user_home"),
    path("list-products", views.product_list, name="product_list"),
    path("login/", views.user_home, name="user_login"),
    path("logout/", views.user_logout, name="user_logout"),
    path("register/", views.user_register, name="user_register"),
    path("cart/add/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.view_cart, name="view_cart"),
    path("cart/remove/<int:cart_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("confirm-order/", views.confirm_order, name="confirm_order"),
    path("orders/place/", views.place_order, name="place_order"),
    path("orders/", views.view_orders, name="view_orders"),
    path(
        "orders/deliver/<int:order_id>/",
        views.mark_order_delivered,
        name="mark_order_delivered",
    ),
    path("cancel-order/<int:order_id>/", views.cancel_order, name="cancel_order"),
    path("add-feedback/<int:product_id>/", views.add_feedback, name="add_feedback"),
]
