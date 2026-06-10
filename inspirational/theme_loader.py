"""
inspirational/theme_loader.py

Custom Django template loader that prepends the active theme's directory
to the template search path on every request. Falls back to normal
template resolution for any file the theme doesn't override.

Thread-safe: the active theme name is stored in threading.local so
concurrent requests each see the correct theme.
"""

import os
import threading
from django.template.loaders.filesystem import Loader as FilesystemLoader
from django.conf import settings

_theme_local = threading.local()


def set_current_theme(theme_name: str) -> None:
    _theme_local.name = theme_name


def get_current_theme() -> str:
    return getattr(_theme_local, "name", "classic")


class ThemeLoader(FilesystemLoader):
    """
    Checks templates/themes/<active_theme>/ before the global templates/ dir.
    When theme is 'classic' (default) no override dir is added — standard
    app template resolution runs as normal.
    Only blog (news) and shop templates are provided per theme, so all other
    pages fall through to their default templates unaffected.
    """

    def get_dirs(self):
        theme = get_current_theme()
        if not theme or theme == "classic":
            return []
        theme_dir = os.path.join(settings.BASE_DIR, "templates", "themes", theme)
        if os.path.isdir(theme_dir):
            return [theme_dir]
        return []
