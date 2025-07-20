# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
import re
import random


class LoginForm(forms.Form):
    username = forms.CharField(label="Username or Email")
    password = forms.CharField(widget=forms.PasswordInput)


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, help_text="Required. Please provide a valid email address."
    )
    first_name = forms.CharField(
        required=True,
        help_text="Required. Please use your real first name.",
        min_length=2,
        error_messages={"min_length": "First name must be at least 2 characters long."},
    )
    last_name = forms.CharField(required=False, help_text="Optional. Your last name.")

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        )

    def clean_username(self):
        username = self.cleaned_data.get("username").strip().lower()

        # Enforce length
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")

        # Enforce allowed characters: letters, numbers, underscore
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise forms.ValidationError(
                "Username can only contain letters, numbers, and underscores."
            )

        # Optional: override with slugified version
        self.cleaned_data["username"] = username
        return username

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        if username and len(username) < 3:
            base = email.split("@")[0] if email else "user"
            suggested = f"{base}_{random.randint(1000, 9999)}"
            self.add_error(
                "username", f"Username is too short. Try something like: {suggested}"
            )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "w-full rounded-md border-gray-300 shadow-sm"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "w-full rounded-md border-gray-300 shadow-sm"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "w-full rounded-md border-gray-300 shadow-sm"}
            ),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("bio",)
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "class": "w-full rounded-md border-gray-300 shadow-sm",
                }
            ),
        }
