from django import forms
from django.contrib.auth.models import User

# New forms will be implemented here

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)  # Ensure password input

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
