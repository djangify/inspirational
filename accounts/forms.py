# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class LoginForm(forms.Form):
    username = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required. Please provide a valid email address.")
    first_name = forms.CharField(required=False, help_text="Optional. Your first name.")
    last_name = forms.CharField(required=False, help_text="Optional. Your last name.")
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm'}),
            'email': forms.EmailInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm'}),
        }

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('bio',)
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'w-full rounded-md border-gray-300 shadow-sm'}),
        }
