from django.urls import path
from django.views.generic import TemplateView
from .views import homepage, support_view

app_name = "core"

urlpatterns = [
    path("", homepage, name="homepage"),
    path("support/", support_view, name="support"),
    # Static template pages using TemplateView
    path("about/", TemplateView.as_view(template_name="core/about.html"), name="about"),
    # Policy pages from templates/policy/
    path(
        "policy/privacy/",
        TemplateView.as_view(template_name="policy/privacy.html"),
        name="privacy_policy",
    ),
    path(
        "policy/cookies/",
        TemplateView.as_view(template_name="policy/cookies.html"),
        name="cookie_policy",
    ),
    path(
        "policy/contents/",
        TemplateView.as_view(template_name="policy/content_policy.html"),
        name="content_policy",
    ),
    path(
        "policy/terms-conditions/",
        TemplateView.as_view(template_name="policy/terms-conditions.html"),
        name="terms_conditions",
    ),
    path(
        "policy/affiliate/",
        TemplateView.as_view(template_name="policy/affiliate_disclosure.html"),
        name="affiliate_disclosure",
    ),
    path(
        "policy/ai-disclaimer/",
        TemplateView.as_view(template_name="policy/ai_disclaimer.html"),
        name="ai_disclaimer",
    ),
]
