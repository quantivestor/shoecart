from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):  # Use Django's UserAdmin for extra controls
    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
    )  # Customize columns
    list_filter = ("role", "is_active")  # Add filters
    search_fields = ("username", "email")  # Enable search
