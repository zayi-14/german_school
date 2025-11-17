from django import forms
from django.contrib.auth.models import User
from .models import Student, Registration, Feedback 

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


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['rating', 'message']
        widgets = {
            'rating': forms.RadioSelect(attrs={'class': 'flex gap-2'}),
            'message': forms.Textarea(attrs={
                'class': 'w-full p-3 border rounded',
                'placeholder': 'Write your feedback here...',
                'rows': 4
            }),
        }
