# shop/forms.py
from django import forms
from .models import ProductReview
from .models import GuestDetails
import re


class GuestDetailsForm(forms.ModelForm):
    class Meta:
        model = GuestDetails
        fields = ["first_name", "last_name", "email", "phone"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                    "placeholder": "First Name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Last Name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Email",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                    "placeholder": "Phone (optional)",
                }
            ),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone:
            # Remove any spaces, dashes, or parentheses
            phone = re.sub(r"[\s\-\(\)]", "", phone)

            # Check if the phone number contains only digits
            if not phone.isdigit():
                raise forms.ValidationError("Phone number can only contain digits.")

            # Check if the length is reasonable (between 10 and 15 digits)
            if len(phone) < 10 or len(phone) > 15:
                raise forms.ValidationError(
                    "Phone number must be between 10 and 15 digits."
                )

            # Format the phone number nicely (optional)
            if len(phone) == 11:  # UK format
                phone = f"{phone[0:5]} {phone[5:8]} {phone[8:]}"
            elif len(phone) == 10:  # Standard format
                phone = f"{phone[0:4]} {phone[4:7]} {phone[7:]}"

        return phone

    def clean_first_name(self):
        first_name = self.cleaned_data.get("first_name")
        if not first_name.replace(" ", "").isalpha():
            raise forms.ValidationError("First name can only contain letters.")
        return first_name.strip()

    def clean_last_name(self):
        last_name = self.cleaned_data.get("last_name")
        if not last_name.replace(" ", "").isalpha():
            raise forms.ValidationError("Last name can only contain letters.")
        return last_name.strip()

    def clean_email(self):
        email = self.cleaned_data.get("email").lower().strip()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            raise forms.ValidationError("Please enter a valid email address.")
        return email


class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.RadioSelect(attrs={"class": "hidden peer"}),
            "comment": forms.Textarea(
                attrs={
                    "class": "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-700",
                    "rows": 4,
                    "placeholder": "Only verified buyers can review. Thank you, for sharing your thoughts about this product...",
                }
            ),
        }
