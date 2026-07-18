from django.urls import path
from django.views.generic import TemplateView, RedirectView
from .views import (
    homepage,
    support_view,
    quietly_you_page,
    my_turn_now_page,
    diane_corriette_page,
    category_hub,
    public_freebie_download,
)

app_name = "core"

urlpatterns = [
    path("", homepage, name="homepage"),
    path("support/", support_view, name="support"),
    path(
        "quietly-you/",
        RedirectView.as_view(pattern_name="core:get_out_of_a_rut", permanent=True),
        name="quietly",
    ),
    path("my-turn-now/", my_turn_now_page, name="myturn"),
    path("diane-corriette/", diane_corriette_page, name="diane_corriette"),
    path(
        "personal-development/",
        RedirectView.as_view(pattern_name="core:diane_corriette", permanent=True),
        name="about",
    ),
    # Cluster pages
    path(
        "how-to-get-out-of-a-rut",
        TemplateView.as_view(template_name="core/how-to-get-out-of-a-rut.html"),
        name="get_out_of_a_rut",
    ),
    # Old cluster pages — consolidated into "how-to-get-out-of-a-rut".
    # 301-redirect the old URLs so inbound links and SEO are preserved. The URL
    # names are kept so existing {% url %} references keep resolving.
    path(
        "pause-emotional-resilience",
        RedirectView.as_view(pattern_name="core:get_out_of_a_rut", permanent=True),
        name="emotional_resilience",
    ),
    path(
        "build-self-confidence",
        RedirectView.as_view(pattern_name="core:get_out_of_a_rut", permanent=True),
        name="build_self_confidence",
    ),
    path(
        "live-with-purpose",
        RedirectView.as_view(pattern_name="core:get_out_of_a_rut", permanent=True),
        name="live_with_purpose",
    ),
    path(
        "empowered-living",
        RedirectView.as_view(pattern_name="core:get_out_of_a_rut", permanent=True),
        name="empowered_living",
    ),
    path(
        "self-authorship",
        RedirectView.as_view(pattern_name="core:get_out_of_a_rut", permanent=True),
        name="self_authorship",
    ),
    path(
        "journaling-personal-growth",
        RedirectView.as_view(pattern_name="core:get_out_of_a_rut", permanent=True),
        name="journaling",
    ),
    path(
        "personal-development-resources",
        TemplateView.as_view(template_name="core/personal-development-resources.html"),
        name="personal_development_resources",
    ),
    # Public streaming download for the free lead-magnet PDFs on that page.
    # Serves whitelisted files from member_resources/ without login, so the
    # files stay put and the rest of member_resources stays gated.
    path(
        "free-resources/download/<str:filename>",
        public_freebie_download,
        name="freebie_download",
    ),
    # Social link-hub — shared from social bios (utm_medium=linkhub). Keep it live.
    path(
        "purpose/",
        TemplateView.as_view(template_name="core/purpose-links.html"),
        name="linkhub",
    ),
    # Deleted page — 301-redirect to the consolidated pillar page.
    path(
        "develop-self-reliance/",
        RedirectView.as_view(pattern_name="core:get_out_of_a_rut", permanent=True),
        name="develop_self_reliance",
    ),
    path("category/", category_hub, name="category"),
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
