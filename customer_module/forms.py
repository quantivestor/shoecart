from django import forms
from .models import Feedback, User

class CustomerRegistrationForm(forms.ModelForm):
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
    
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['comment', 'rating']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your feedback here...'}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'placeholder': 'Rating (1-5)'})
        }
