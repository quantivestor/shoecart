import re

from django import forms
from django.core.exceptions import ValidationError

from admin_module.models import User
from customer_module.models import Order


class StaffRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    phone_number = forms.CharField(max_length=15)

    class Meta:
        model = User
        fields = ["email", "username", "password", "confirm_password", "phone_number"]


    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")

        # Phone number should be 10 digits (for local numbers) or follow international format
        pattern = re.compile(r"^\+?\d{10,15}$")
        if not pattern.match(phone_number):
            raise ValidationError(
                "Enter a valid phone number (10-15 digits, can start with +)."
            )

        return phone_number

    def clean_password(self):
        password = self.cleaned_data.get("password")

        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", password):
            raise ValidationError("Password must contain at least one letter.")
        if not re.search(r"\d", password):
            raise ValidationError("Password must contain at least one digit.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError(
                "Password must contain at least one special character (!@#$%^&* etc.)."
            )

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


class OrderStatusUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["track_status", "is_delivered"]
        widgets = {
            "track_status": forms.TextInput(
                attrs={"placeholder": "Enter tracking status..."}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("is_delivered"):
            cleaned_data["track_status"] = "Delivered"
        return cleaned_data
