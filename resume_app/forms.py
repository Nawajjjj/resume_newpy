# resume_app/forms.py
from django import forms
from .models import Certificate


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

