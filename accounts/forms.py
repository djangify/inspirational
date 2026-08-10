# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, SupportRequest
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
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)
    subscribe = forms.BooleanField(
        required=False,
        initial=True,
        label="Yes — send me the free “ALIVE List” template and occasional supportive emails.",
    )

    class Meta:
        model = User
        fields = (
            "email",
            "first_name",
            "password1",
            "password2",
        )

    def clean(self):
        cleaned_data = super().clean()

        # Honeypot spam trap
        honeypot = cleaned_data.get("honeypot")
        if honeypot:
            raise forms.ValidationError("Spam detected.")

        # Timestamp bot trap
        form_time = self.data.get("form_time")
        import time

        if form_time:
            try:
                submitted_time = int(form_time)
                current_time = int(time.time())

                # Reject forms submitted too quickly (bots)
                if current_time - submitted_time < 4:
                    raise forms.ValidationError("Form submitted too quickly.")
            except ValueError:
                raise forms.ValidationError("Invalid form submission.")

        return cleaned_data

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email address is already in use.")
        return email

    @staticmethod
    def _generate_username(email):
        """Build a unique username behind the scenes.

        The user never picks one -- they sign in with their email (or this
        username) via EmailOrUsernameModelBackend. We take the part of the
        email before the @, strip it to safe characters, and add random
        digits until it's unique. Django requires usernames to be unique
        and non-empty.
        """
        base = re.sub(r"[^a-z0-9_]", "", email.split("@")[0].lower())[:20] or "user"
        username = base
        while User.objects.filter(username=username).exists():
            username = f"{base}_{random.randint(1000, 9999)}"
        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self._generate_username(self.cleaned_data["email"])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "w-full rounded-md border-gray-300 shadow-sm"}
        ),
    )
    last_name = forms.CharField(
        required=False,
        label="Last name (optional)",
        widget=forms.TextInput(
            attrs={"class": "w-full rounded-md border-gray-300 shadow-sm"}
        ),
    )

    class Meta:
        model = User
        fields = ("first_name", "last_name")


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


class SupportForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = ["subject", "message"]
        widgets = {
            "subject": forms.TextInput(
                attrs={
                    "placeholder": "What can we help you with?",
                    "class": "w-full rounded-md border-gray-300 shadow-sm",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 6,
                    "placeholder": "Please describe your question or issue in as much detail as you can...",
                    "class": "w-full rounded-md border-gray-300 shadow-sm",
                }
            ),
        }
