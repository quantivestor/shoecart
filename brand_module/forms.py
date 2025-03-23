import re

from django import forms
from django.core.exceptions import ValidationError

from .models import Brand, Product


class ProductForm(forms.ModelForm):
    left_image = forms.ImageField(required=False, help_text="Upload left view image of the product.")
    straight_image = forms.ImageField(required=False, help_text="Upload straight view image of the product.")
    right_image = forms.ImageField(required=False, help_text="Upload right view image of the product.")

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "price",
            "stock",
            "category",
            "material",
            "color",
            "left_image",
            "straight_image",
            "right_image",
            "sizes",
            "offer_percentage",
        ]

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)

        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

            # Set specific attributes for certain fields
            if field_name == "description":
                field.widget.attrs["rows"] = 5  # Set rows for the description textarea
            if field_name == "price":
                field.widget.attrs["step"] = "0.01"  # Allow decimal values for price

        # Help text for sizes
        self.fields["sizes"].help_text = "Enter sizes as comma-separated values (e.g., S,M,L,XL)."


class brandRegistrationForm(forms.Form):
    email = forms.EmailField()  # Add this field
    username = forms.CharField(max_length=150, label="Owner Name", help_text="Enter the owner's full name")
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput())
    brand_name = forms.CharField(max_length=100)
    address = forms.CharField(max_length=200)
    contact_info = forms.CharField(max_length=15)

    def clean_phone_number(self):
        phone = self.cleaned_data.get("contact_info")

        # Phone number should be 10 digits (for local numbers) or follow international format
        pattern = re.compile(r"^\+?\d{10,15}$")
        if not pattern.match(phone):
            raise ValidationError(
                "Enter a valid phone number (10-15 digits, can start with +)."
            )

        return phone

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


class brandLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class brandProfileForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ["brand_name", "address", "contact_info"]
        widgets = {
            "brand_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Brand Name"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Address"}
            ),
            "contact_info": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Contact Info"}
            ),
        }
