# resume_app/forms.py
from django import forms
from .models import Certificate
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        # Add custom password validation logic if needed
        # For example, you could add a check for a minimum length or custom characters.
        return password1

    def clean_password2(self):
        password2 = self.cleaned_data.get('password2')
        # Check if password1 and password2 match
        if password2 != self.cleaned_data.get('password1'):
            raise forms.ValidationError("The two password fields must match.")
        return password2


class CertificateUploadForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['certificate_file']


class UserInformationForm(forms.Form):
    name = forms.CharField(label='Full Name', max_length=100, required=True)
    phone = forms.CharField(label='Phone Number', max_length=15, required=True)
    email = forms.EmailField(label='Email Address', required=True)
    linkedin = forms.URLField(label='LinkedIn Profile', required=False)
    gmail = forms.EmailField(label='Gmail Address', required=False)


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',  # Bootstrap 5 form-control class
            'placeholder': 'Enter your username'
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',  # Bootstrap 5 form-control class
            'placeholder': 'Enter your password'
        }),
    )