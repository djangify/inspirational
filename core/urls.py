from django.urls import path
from .views import homepage
from .views import support_view
from . import views

app_name = "core"

urlpatterns = [
    path("", homepage, name="homepage"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("support/", support_view, name="support"),
    path("policy/privacy/", views.privacy_view, name="privacy_policy"),
    path("policy/cookies/", views.cookie_view, name="cookie_policy"),
    path("policy/contents/", views.content_view, name="content_policy"),
    path("policy/terms-conditions/", views.terms_view, name="terms_conditions"),
]
