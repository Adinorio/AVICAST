from django import forms
import logging

logger = logging.getLogger(__name__)

class LoginForm(forms.Form):
    user_id = forms.CharField(
        label='User ID',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your user ID',
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        logger.info('LoginForm clean method called')
        logger.info(f'Cleaned data: {cleaned_data}')
        return cleaned_data
