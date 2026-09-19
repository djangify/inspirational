from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
    email = forms.EmailField(label="Email")
    subject = forms.CharField(label="Subject", max_length=150)
    message = forms.CharField(label="Message", widget=forms.Textarea)


class HeroNewsletterForm(forms.Form):
    first_name = forms.CharField(label="First name", max_length=100)
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Your email address"}),
    )
    # Honeypot: real visitors never see or fill this field.
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""
