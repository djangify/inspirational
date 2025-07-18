from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(label="Name", max_length=100)
    email = forms.EmailField(label="Email")
    subject = forms.CharField(label="Subject", max_length=150)
    message = forms.CharField(label="Message", widget=forms.Textarea)
