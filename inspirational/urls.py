from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from inspirational.sitemaps import (
    ShopCategorySitemap,
    ShopProductSitemap,
    NewsSitemap,
    PromptCategorySitemap,
    NewsCategorySitemap,
)
from core.views import robots_txt

sitemaps = {
    "shop_categories": ShopCategorySitemap,
    "shop_products": ShopProductSitemap,
    "news": NewsSitemap,
    "news_categories": NewsCategorySitemap,
    "prompt_categories": PromptCategorySitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls", namespace="core")),
    path("shop/", include("shop.urls", namespace="shop")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("prompt/", include("prompt.urls")),
    path("tools/", include("tools.urls", namespace="tools")),
    path("", include("news.urls", namespace="news")),
    # Sitemap and robots.txt
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
