from django import forms
from .models import Administrator

class AdminInfoForm(forms.ModelForm):
    class Meta:
        model = Administrator
        fields = ['email', 'phone_number']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'Enter email'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter phone number'}),
        }
