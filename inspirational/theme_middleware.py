"""
inspirational/theme_middleware.py

Reads the active theme from SiteSettings on each request and stores it
in a thread-local so ThemeLoader can access it without a DB hit inside
the loader itself. SiteSettings is a singleton so the query is tiny;
errors fall back to 'classic' silently.
"""

from inspirational.theme_loader import set_current_theme


class ThemeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_theme(self._resolve_theme())
        return self.get_response(request)

    @staticmethod
    def _resolve_theme() -> str:
        try:
            from shop.models import SiteSettings
            s = SiteSettings.objects.only("active_theme").first()
            return s.active_theme if s else "classic"
        except Exception:
            return "classic"
