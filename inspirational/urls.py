from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from inspirational.sitemaps import (
    ShopCategorySitemap,
    ShopProductSitemap,
    NewsSitemap,
    PromptCategorySitemap,
)

sitemaps = {
    "shop_categories": ShopCategorySitemap,
    "shop_products": ShopProductSitemap,
    "news": NewsSitemap,
    "prompt_categories": PromptCategorySitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("shop/", include("shop.urls", namespace="shop")),
    path("news/", include("news.urls", namespace="news")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("prompt/", include("prompt.urls")),
    path("tools/", include("tools.urls", namespace="tools")),
    # Sitemap and robots.txt
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
