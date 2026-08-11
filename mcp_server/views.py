"""Owner-only "Connect to Claude" admin pages.

Shows the site owner everything they need to add this site to Claude as a
custom connector: the connector URL, the OAuth Client ID, and — once, right
after generating — the Client Secret.

This is the UI equivalent of the ``mcp_create_client`` management command, so
the owner never has to touch the CLI. django-oauth-toolkit hashes the client
secret on save and it cannot be recovered afterwards, so the secret is only ever
shown on the same response that generated it. If it's lost, click "Generate a
new secret" to roll a fresh one.

Owner-only (superuser).
"""

from functools import wraps

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

# Keep these in lock-step with accounts/management/commands/mcp_create_client.py
APP_NAME = "Claude (MCP connector)"
DEFAULT_REDIRECT = "https://claude.ai/api/mcp/auth_callback"


def owner_required(view):
    """Allow only logged-in superusers (the site owner). Staff redirect to login."""

    @wraps(view)
    @staff_member_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404()
        return view(request, *args, **kwargs)

    return _wrapped


def _get_app():
    """Return the existing Claude OAuth Application, or None."""
    from oauth2_provider.models import get_application_model

    App = get_application_model()
    return App.objects.filter(name=APP_NAME).first()


def _owner():
    """First active superuser — the site owner the client belongs to."""
    from django.contrib.auth import get_user_model

    return (
        get_user_model()
        .objects.filter(is_superuser=True, is_active=True)
        .order_by("pk")
        .first()
    )


def _connection_status(app):
    """Work out whether Claude is currently connected to this site.

    "Connected" means Claude still holds credentials it can use to reach the
    sidecar: either a live (unexpired) access token, or a non-revoked refresh
    token still inside its expiry window.
    """
    status = {
        "connected": False,
        "last_authorized": None,
        "access_expires": None,
        "last_active": None,
    }
    if app is None:
        return status

    from datetime import timedelta

    from django.utils import timezone
    from oauth2_provider.models import (
        get_access_token_model,
        get_refresh_token_model,
    )
    from oauth2_provider.settings import oauth2_settings

    AccessToken = get_access_token_model()
    RefreshToken = get_refresh_token_model()
    now = timezone.now()

    live_access = (
        AccessToken.objects.filter(application=app, expires__gt=now)
        .order_by("-expires")
        .first()
    )

    newest_refresh = (
        RefreshToken.objects.filter(application=app, revoked__isnull=True)
        .order_by("-created")
        .first()
    )
    refresh_ok = False
    if newest_refresh is not None:
        ttl = oauth2_settings.REFRESH_TOKEN_EXPIRE_SECONDS
        refresh_ok = ttl is None or newest_refresh.created > now - timedelta(seconds=ttl)

    status["connected"] = bool(live_access) or refresh_ok

    dates = [t.created for t in (live_access, newest_refresh) if t is not None]
    if dates:
        status["last_authorized"] = max(dates)
    if live_access is not None:
        status["access_expires"] = live_access.expires

    from .models import MCPCallLog

    last_call = (
        MCPCallLog.objects.filter(client_id=app.client_id)
        .order_by("-created")
        .first()
    )
    if last_call is not None:
        status["last_active"] = last_call.created

    return status


def _disconnect(app):
    """Revoke every token/grant Claude holds for this site.

    Forces Claude to re-authorize on its next request. The client credentials
    (Client ID/Secret) are left intact, so reconnecting is just clicking
    "Connect" again in Claude — no need to re-enter anything.
    """
    if app is None:
        return
    from oauth2_provider.models import (
        get_access_token_model,
        get_grant_model,
        get_refresh_token_model,
    )

    get_refresh_token_model().objects.filter(application=app).delete()
    get_access_token_model().objects.filter(application=app).delete()
    get_grant_model().objects.filter(application=app).delete()


@owner_required
@require_http_methods(["GET", "POST"])
def connect_claude(request):
    """Render the Connect-to-Claude page; create/reset the client on POST."""
    from oauth2_provider.generators import generate_client_secret
    from oauth2_provider.models import get_application_model

    App = get_application_model()
    app = _get_app()
    new_secret = None
    error = None
    disconnected = False

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "disconnect":
            _disconnect(app)
            disconnected = True
        elif action in ("generate", "reset"):
            owner = _owner()
            if owner is None:
                error = "No active site-owner account was found on this site."
            else:
                # Capture the plaintext BEFORE save; DOT hashes it on save.
                new_secret = generate_client_secret()
                if app is None:
                    app = App(
                        name=APP_NAME,
                        user=owner,
                        client_type=App.CLIENT_CONFIDENTIAL,
                        authorization_grant_type=App.GRANT_AUTHORIZATION_CODE,
                        redirect_uris=DEFAULT_REDIRECT,
                        client_secret=new_secret,
                    )
                else:
                    app.client_secret = new_secret
                    app.redirect_uris = DEFAULT_REDIRECT
                    app.client_type = App.CLIENT_CONFIDENTIAL
                    app.authorization_grant_type = App.GRANT_AUTHORIZATION_CODE
                    app.user = owner
                app.save()
        else:
            return redirect(reverse("admin_connect_claude"))

    mcp_url = request.build_absolute_uri("/mcp")
    status = _connection_status(app)
    connections_url = reverse("admin_claude_connections")

    context = {
        **admin.site.each_context(request),
        "title": "Connect to Claude",
        "app": app,
        "client_id": app.client_id if app else None,
        "new_secret": new_secret,
        "mcp_url": mcp_url,
        "redirect_uri": DEFAULT_REDIRECT,
        "error": error,
        "status": status,
        "disconnected": disconnected,
        "connections_url": connections_url,
    }
    return render(request, "admin/mcp/connect_claude.html", context)


@owner_required
@require_http_methods(["GET"])
def claude_connections(request):
    """Read-only overview of everything connected to this site via Claude/MCP."""
    from django.utils import timezone
    from oauth2_provider.models import (
        get_access_token_model,
        get_application_model,
        get_grant_model,
        get_id_token_model,
        get_refresh_token_model,
    )

    now = timezone.now()
    App = get_application_model()
    AccessToken = get_access_token_model()
    RefreshToken = get_refresh_token_model()

    connectors = []
    for a in App.objects.order_by("name", "created"):
        connectors.append(
            {
                "name": a.name or "(unnamed connector)",
                "client_id": a.client_id,
                "created": a.created,
                "status": _connection_status(a),
                "live_sessions": AccessToken.objects.filter(
                    application=a, expires__gt=now
                ).count(),
            }
        )

    sessions = []
    for t in (
        AccessToken.objects.filter(expires__gt=now)
        .select_related("application", "user")
        .order_by("-expires")
    ):
        user = t.user if t.user_id else None
        sessions.append(
            {
                "connector": t.application.name if t.application_id else "—",
                "user": getattr(user, "email", "") or getattr(user, "username", "")
                if user is not None
                else "",
                "created": t.created,
                "expires": t.expires,
            }
        )

    housekeeping = {
        "refresh": RefreshToken.objects.filter(revoked__isnull=True).count(),
        "grants": get_grant_model().objects.count(),
        "id_tokens": get_id_token_model().objects.count(),
    }

    context = {
        **admin.site.each_context(request),
        "title": "Claude connections",
        "connectors": connectors,
        "sessions": sessions,
        "housekeeping": housekeeping,
        "connect_url": reverse("admin_connect_claude"),
        "generated": now,
    }
    return render(request, "admin/mcp/claude_connections.html", context)
