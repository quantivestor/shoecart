from django import forms
from admin_module.models import User
from customer_module.models import Order

class StaffRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

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
        fields = ['track_status', 'is_delivered']
        widgets = {
            'track_status': forms.TextInput(attrs={'placeholder': 'Enter tracking status...'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('is_delivered'):
            cleaned_data['track_status'] = "Delivered"
        return cleaned_data
