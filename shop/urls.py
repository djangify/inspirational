# stream/urls.py
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from . import views
# from django.contrib.sitemaps.views import sitemap
# from .sitemaps import (
#     StaticViewSitemap,
#     NewsSitemap,
#     PageSitemap,
#     ShopCategorySitemap,
#     ShopProductSitemap,

# )
from django.views.generic import TemplateView

# sitemaps = {
#     "static": StaticViewSitemap,
#     "news": NewsSitemap,
#     "pages": PageSitemap,
#     "shop_categories": ShopCategorySitemap,
#     "shop_products": ShopProductSitemap,

# }

urlpatterns = [
    path("", include("pages.urls")),
    path("admin/", admin.site.urls),
    path("ckeditor/", include("ckeditor_uploader.urls")),
    path("profiles/", include("profiles.urls", namespace="profiles")),
    path("courses/", include("courses.urls", namespace="courses")),
    path("news/", include("news.urls", namespace="news")),
    path("shop/", include("shop.urls", namespace="shop")),
    path("policy/privacy/", views.privacy_view, name="privacy_policy"),
    path("policy/cookies/", views.cookie_view, name="cookie_policy"),
    path("policy/contents/", views.content_view, name="content_policy"),
    path("policy/terms-conditions/", views.terms_view, name="terms_conditions"),
    # path(
    #     "sitemap.xml",
    #     sitemap,
    #     {"sitemaps": sitemaps},
    #     name="django.contrib.sitemaps.views",
    # ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
