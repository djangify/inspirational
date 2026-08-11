from django.contrib import admin

from .models import MCPCallLog


@admin.register(MCPCallLog)
class MCPCallLogAdmin(admin.ModelAdmin):
    list_display = ("created", "tool", "ok", "owner", "client_id", "duration_ms")
    list_filter = ("tool", "ok")
    search_fields = ("tool", "client_id", "args_summary", "error")
    date_hierarchy = "created"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# Hide the raw django-oauth-toolkit models from the admin sidebar.
#
# Out of the box DOT registers five sections — Applications, Access tokens,
# Refresh tokens, Grants and ID tokens. Those are OAuth internals that the site
# owner never needs to hand-edit. The owner-facing "Connect to Claude" and
# "Claude connections" pages present the same information in plain language, so
# we unregister the raw admin here. Removing the registration also drops the
# CRUD URLs, so tokens can't be edited by mistake.
#
# oauth2_provider is listed before mcp_server in INSTALLED_APPS, so its admin is
# already registered by the time this module is imported during autodiscover.
# Each unregister is guarded so a DOT upgrade that drops a model can't break the
# admin.
def _hide_oauth_admin():
    try:
        from oauth2_provider.models import (
            get_access_token_model,
            get_application_model,
            get_grant_model,
            get_id_token_model,
            get_refresh_token_model,
        )
    except Exception:
        return

    for getter in (
        get_application_model,
        get_access_token_model,
        get_refresh_token_model,
        get_grant_model,
        get_id_token_model,
    ):
        try:
            admin.site.unregister(getter())
        except Exception:
            # Not registered (or already unregistered) — nothing to do.
            pass


_hide_oauth_admin()
