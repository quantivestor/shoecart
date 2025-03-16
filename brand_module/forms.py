from django import forms
from django.contrib.gis import forms as gis_forms
from .models import Product, Brand


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 'color', 'image', 'sizes', 'offer_percentage']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Add Bootstrap classes to each form field
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'description':
                field.widget.attrs['rows'] = 5  # Set rows for the description textarea
            if field_name == 'price':
                field.widget.attrs['step'] = '0.01'  # Allow decimal values for price


class brandRegistrationForm(forms.Form):
    email = forms.EmailField()  # Add this field
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    brand_name = forms.CharField(max_length=100)
    address = forms.CharField(max_length=200)
    contact_info = forms.CharField(max_length=15)


class brandLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class brandProfileForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['brand_name', 'address', 'contact_info']
        widgets = {
            'brand_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand Name'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'contact_info': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Info'}),
        }