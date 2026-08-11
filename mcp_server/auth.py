"""Resource-Server auth for the sidecar.

The sidecar does NOT issue tokens. Django (django-oauth-toolkit) is the
Authorization Server; here we only *verify* the bearer token Claude presents and
resolve it to the owning user. FastMCP is given this verifier plus AuthSettings,
so it serves the Protected Resource Metadata document and returns spec-compliant
401s (with a ``WWW-Authenticate`` pointing at that metadata) on its own.

Two token paths, in priority order:

1. **Real OAuth token** — look it up in DOT's AccessToken table (same database),
   check it's unexpired and carries the ``mcp`` scope, and map it to its user.
2. **Dev token** — only when ``MCP_DEV_TOKEN`` is set (local/Inspector testing).
   A constant-time match resolves to the site's single superuser. Leave the env
   var unset in any real deployment and this path is inert.
"""

import hmac
import os

from asgiref.sync import sync_to_async
from mcp.server.auth.provider import AccessToken, TokenVerifier

MCP_SCOPE = "mcp"


def _dev_token() -> str:
    return os.environ.get("MCP_DEV_TOKEN", "").strip()


def _superuser():
    from django.contrib.auth import get_user_model

    return (
        get_user_model()
        .objects.filter(is_superuser=True, is_active=True)
        .order_by("pk")
        .first()
    )


def _verify_sync(token: str) -> AccessToken | None:
    """Synchronous token validation (runs in a worker thread)."""
    if not token:
        return None

    # 1) Real DOT-issued access token.
    from oauth2_provider.models import get_access_token_model

    AccessTokenModel = get_access_token_model()
    dot_token = AccessTokenModel.objects.filter(token=token).select_related("user").first()
    if dot_token is not None:
        if not dot_token.is_valid([MCP_SCOPE]):  # expiry + scope check
            return None
        user = dot_token.user
        if user is None or not user.is_active or not user.is_superuser:
            # v1: one owner. A token not tied to the site owner is refused.
            return None
        return AccessToken(
            token=token,
            client_id=str(getattr(dot_token.application, "client_id", "") or ""),
            scopes=dot_token.scope.split() if dot_token.scope else [],
            expires_at=int(dot_token.expires.timestamp()) if dot_token.expires else None,
            subject=str(user.pk),
        )

    # 2) Dev token fallback (only if explicitly configured).
    expected = _dev_token()
    if expected and hmac.compare_digest(token, expected):
        user = _superuser()
        if user is not None:
            return AccessToken(
                token=token,
                client_id="dev-token",
                scopes=[MCP_SCOPE],
                expires_at=None,
                subject=str(user.pk),
            )

    return None


class DjangoOAuthTokenVerifier(TokenVerifier):
    """Validates bearer tokens against DOT (with an optional dev-token fallback)."""

    async def verify_token(self, token: str) -> AccessToken | None:
        return await sync_to_async(_verify_sync, thread_sensitive=True)(token)
