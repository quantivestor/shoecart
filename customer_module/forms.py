import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Feedback, User


class CustomerRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(
        widget=forms.PasswordInput(), required=True, min_length=8
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(), required=True
    )
    phone_number = forms.CharField(max_length=15, required=True)

    # Corrected Image Fields
    left_image = forms.ImageField(
        required=True, help_text="Upload the left-side view image of your foot"
    )
    straight_image = forms.ImageField(
        required=True, help_text="Upload the straight front view image of your foot"
    )
    right_image = forms.ImageField(
        required=True, help_text="Upload the right-side view image of your foot"
    )

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "phone_number",
            "left_image",
            "straight_image",  # Fixed typo
            "right_image",
        ]

    def clean_phone_number(self):
        phone = self.cleaned_data.get("phone_number")

        # Regex for a valid phone number (10-15 digits, optional "+")
        pattern = re.compile(r"^\+?\d{10,15}$")
        if not pattern.match(phone):
            raise ValidationError(
                "Enter a valid phone number (10-15 digits, can start with +)."
            )

        return phone

    def clean_password(self):
        password = self.cleaned_data.get("password")

        if not any(char.isalpha() for char in password):
            raise ValidationError("Password must contain at least one letter.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one digit.")
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in password):
            raise ValidationError(
                "Password must contain at least one special character (!@#$%^&* etc.)."
            )

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")
        
        return cleaned_data


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["comment", "rating"]
        widgets = {
            "comment": forms.Textarea(
                attrs={"rows": 5, "placeholder": "Write your feedback here..."}
            ),
            "rating": forms.NumberInput(
                attrs={"min": 1, "max": 5, "placeholder": "Rating (1-5)"}
            ),
        }
