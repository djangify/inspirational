from django.urls import path
from django.views.generic import TemplateView
from .views import (
    homepage,
    support_view,
    quietly_you_page,
    my_turn_now_page,
    diane_corriette_page,
)

app_name = "core"

urlpatterns = [
    path("", homepage, name="homepage"),
    path("support/", support_view, name="support"),
    path("quietly-you/", quietly_you_page, name="quietly"),
    path("my-turn-now/", my_turn_now_page, name="myturn"),
    path("diane-corriette/", diane_corriette_page, name="diane_corriette"),
    path(
        "personal-development/",
        TemplateView.as_view(template_name="core/personal-development.html"),
        name="about",
    ),
    # Cluster pages
    path(
        "pause-emotional-resilience",
        TemplateView.as_view(template_name="core/pause-emotional-resilience.html"),
        name="emotional_resilience",
    ),
    path(
        "build-self-confidence",
        TemplateView.as_view(template_name="core/build-self-confidence.html"),
        name="build_self_confidence",
    ),
    path(
        "live-with-purpose",
        TemplateView.as_view(template_name="core/live-with-purpose.html"),
        name="live_with_purpose",
    ),
    path(
        "empowered-living",
        TemplateView.as_view(template_name="core/empowered-living.html"),
        name="empowered_living",
    ),
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
        TemplateView.as_view(template_name="policy/affiliate.html"),
        name="affiliate",
    ),
    path(
        "policy/ai-disclaimer/",
        TemplateView.as_view(template_name="policy/ai_disclaimer.html"),
        name="ai_disclaimer",
    ),
]
handler404 = "core.views.handler404"
handler500 = "core.views.handler500"
handler403 = "core.views.handler403"
