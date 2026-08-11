"""Add a "Claude connector" section to the admin sidebar (superusers only).

Rather than hard-coding theme HTML, we inject two links into the ``app_list``
the admin builds for every page, so the active theme (Adminita) renders them in
its own style — exactly like the built-in app sections. Safe to call once at
startup; calling it again is a no-op.
"""

from django.contrib import admin
from django.urls import NoReverseMatch, reverse


def install_sidebar_link():
    site = admin.site
    if getattr(site, "_mcp_sidebar_patched", False):
        return
    site._mcp_sidebar_patched = True

    original_get_app_list = site.get_app_list

    def get_app_list(request, app_label=None):
        app_list = list(original_get_app_list(request, app_label))

        # Only the site owner (superuser) needs the connector controls, and only
        # on the full sidebar (app_label is None), not per-app pages.
        try:
            if app_label is None and getattr(request, "user", None) and request.user.is_superuser:
                models = []
                try:
                    models.append(
                        {
                            "name": "Connect to Claude",
                            "object_name": "connect_claude",
                            "admin_url": reverse("admin_connect_claude"),
                            "view_only": True,
                        }
                    )
                    models.append(
                        {
                            "name": "Claude connections",
                            "object_name": "claude_connections",
                            "admin_url": reverse("admin_claude_connections"),
                            "view_only": True,
                        }
                    )
                except NoReverseMatch:
                    models = []
                if models:
                    app_list.append(
                        {
                            "name": "Claude connector",
                            "app_label": "mcp_connector",
                            "app_url": reverse("admin_connect_claude"),
                            "has_module_perms": True,
                            "models": models,
                        }
                    )
        except Exception:
            # The sidebar link is cosmetic — never let it break the admin.
            pass

        return app_list

    site.get_app_list = get_app_list
