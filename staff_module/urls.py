from django.urls import path

from . import views

urlpatterns = [
    path("", views.staff_home, name="staff_dashboard"),
    path("logout/", views.staff_logout, name="staff_logout"),
    path("register/", views.staff_register, name="staff_register"),
    path(
        "update_order_status/<int:order_id>/",
        views.update_order_status,
        name="update_order_status",
    ),
    path("profile/", views.staff_profile, name="staff_profile"),
]
