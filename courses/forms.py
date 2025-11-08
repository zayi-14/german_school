from django import forms
from django.contrib.auth.models import User
from .models import Student, Registration

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        cpwd = cleaned.get("confirm_password")
        if pwd != cpwd:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['full_name', 'email', 'phone']


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['course', 'notes']
