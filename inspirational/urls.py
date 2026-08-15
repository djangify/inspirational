from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from inspirational.sitemaps import (
    StaticViewSitemap,
    ShopCategorySitemap,
    ShopProductSitemap,
    NewsSitemap,
    PromptCategorySitemap,
    NewsCategorySitemap,
)
from core.views import robots_txt, oauth_authorization_server_metadata
from mcp_server import views as mcp_views
from mcp_server.sidebar import install_sidebar_link
from accounts import admin_stats

sitemaps = {
    "static": StaticViewSitemap,
    "shop_categories": ShopCategorySitemap,
    "shop_products": ShopProductSitemap,
    "news": NewsSitemap,
    "news_categories": NewsCategorySitemap,
    "prompt_categories": PromptCategorySitemap,
}

urlpatterns = [
    # OAuth Authorization Server metadata (RFC 8414) for the Claude MCP connector.
    path(
        ".well-known/oauth-authorization-server",
        oauth_authorization_server_metadata,
        name="oauth_as_metadata",
    ),
    # Owner-only Connect-to-Claude pages. Mounted BEFORE the admin include so
    # these admin/-prefixed paths resolve ahead of the admin catch-all.
    path("admin/connect-claude/", mcp_views.connect_claude, name="admin_connect_claude"),
    path("admin/claude-connections/", mcp_views.claude_connections, name="admin_claude_connections"),
    path("admin/email-list-stats/", admin_stats.email_list_stats, name="admin_email_list_stats"),
    path("admin/", admin.site.urls),
    # OAuth 2.1 Authorization Server for the MCP connector: /o/authorize,
    # /o/token, /o/introspect, /o/revoke_token.
    path("o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    path("", include("core.urls", namespace="core")),
    path("shop/", include("shop.urls", namespace="shop")),
    path("guides/", include("bots.urls", namespace="bots")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("prompt/", include("prompt.urls")),
    path("tools/", include("tools.urls", namespace="tools")),
    # PWA: manifest, service worker (must be at site root for full scope), offline fallback.
    # These MUST come before the news "" catch-all include below — its <slug:slug>/
    # pattern would otherwise swallow /offline/ and return 404.
    path(
        "manifest.webmanifest",
        TemplateView.as_view(
            template_name="pwa/manifest.webmanifest",
            content_type="application/manifest+json",
        ),
        name="manifest",
    ),
    path(
        "sw.js",
        TemplateView.as_view(
            template_name="pwa/sw.js",
            content_type="application/javascript",
        ),
        name="service_worker",
    ),
    path(
        "offline/",
        TemplateView.as_view(template_name="pwa/offline.html"),
        name="offline",
    ),
    path("", include("news.urls", namespace="news")),
    # Sitemap and robots.txt
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = "core.views.handler404"
handler500 = "core.views.handler500"
handler403 = "core.views.handler403"

# ---- ADMINITA DJANGO DASHBOARD ----
admin.site.site_header = "Inspirational Guidance"
admin.site.site_title = "Inspirational Guidance"
admin.site.index_title = "Welcome to Your Site"

# Add the superuser-only "Claude connector" links to the admin sidebar.
install_sidebar_link()

# Add the superuser-only "Email list stats" link to the admin sidebar.
admin_stats.install_sidebar_link()
