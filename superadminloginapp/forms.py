from django import forms

class LoginForm(forms.Form):
    user_id = forms.CharField(max_length=50, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
