from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from .models import SupportMessage


def homepage(request):
    return render(request, "core/homepage.html")


def privacy_view(request):
    template_name = "policy/privacy.html"
    return render(request, template_name)


def terms_view(request):
    template_name = "policy/terms-conditions.html"
    return render(request, template_name)


def cookie_view(request):
    template_name = "policy/cookies.html"
    return render(request, template_name)


def content_view(request):
    template_name = "policy/contents.html"
    return render(request, template_name)


def about(request):
    """
    View for the About page
    """
    context = {
        "title": "About Inspirational Guidance",
        "meta_description": "Inspirational Guidance provides self-help guides and teach practical life skills",
    }
    return render(request, "core/about.html", context)


def contact(request):
    """
    View for the contact page
    """
    context = {
        "title": "Contact Inspirational Guidance",
        "meta_description": "We provide self-help guides and teach practical life skills",
    }
    return render(request, "core/contact.html", context)


def support_view(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save to the database only (admin area)
            SupportMessage.objects.create(
                name=form.cleaned_data["name"],
                email=form.cleaned_data["email"],
                subject=form.cleaned_data["subject"],
                message=form.cleaned_data["message"],
            )

            messages.success(
                request, "Thank you for your message. We'll respond within 24 hours."
            )
            return redirect("support")
    else:
        form = ContactForm()

    return render(request, "core/support.html", {"form": form})
