from django.urls import path

from . import views

urlpatterns = [
    path("", views.admin_dashboard, name="admin_dashboard"),
    path("profile/", views.profile, name="admin_profile"),
    path("logout/", views.logout_view, name="admin_logout"),

    path(
        "review-brand/", views.review_brand_registrations, name="review_brand_registrations"
    ),
    path("approve-brand/<int:brand_id>/", views.approve_brand, name="approve_brand"),
    path("reject-brand/<int:brand_id>/", views.reject_brand, name="reject_brand"),
    path("list-brand/", views.list_brand_details, name="list_brand_details"),
    path(
        "delete-brand/<int:brand_id>/", views.delete_brand, name="delete_brand"
    ),

    path("list-customer/", views.list_customer_details, name="list_customer_details"),
    path(
        "admin/customer/delete/<int:cus_id>/",
        views.delete_customer,
        name="delete_customer",
    ),

    path(
        "review-staff/", views.review_staff_registrations, name="review_staff_registrations"
    ),
    path("approve-staff/<int:staff_id>/", views.approve_staff, name="approve_staff"),
    path("reject-staff/<int:staff_id>/", views.reject_staff, name="reject_staff"),
    path("list-staff/", views.list_staff_details, name="list_staff_details"),
    path(
        "delete-staff/<int:staff_id>/", views.delete_staff, name="delete_staff"
    ),

    path("login/", views.userlogin, name="login"),
    path("feedbacks/", views.view_feedbacks, name="view_feedbacks"),
]
