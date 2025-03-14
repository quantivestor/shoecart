from django import forms
from django.contrib.gis import forms as gis_forms
from .models import Product, Shop


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'category', 'image']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Add Bootstrap classes to each form field
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'description':
                field.widget.attrs['rows'] = 3  # Set rows for the description textarea
            if field_name == 'price':
                field.widget.attrs['step'] = '0.01'  # Allow decimal values for price


class ShopRegistrationForm(forms.Form):
    email = forms.EmailField()  # Add this field
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    shop_name = forms.CharField(max_length=100)
    address = forms.CharField(max_length=200)
    point = forms.CharField(widget=forms.HiddenInput()) 
    contact_info = forms.CharField(max_length=15)


class ShopLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class ShopProfileForm(forms.ModelForm):
    class Meta:
        model = Shop
        fields = ['shop_name', 'address', 'contact_info']
        widgets = {
            'shop_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Shop Name'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Address'}),
            'contact_info': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Info'}),
        }