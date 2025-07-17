from django.shortcuts import render


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
