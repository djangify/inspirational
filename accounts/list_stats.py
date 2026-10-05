# accounts/list_stats.py
"""
Read-only email list statistics for Inspirational Guidance.

The READ counterpart to accounts/services/brevo.py. Where that module
*writes* (adds a verified subscriber), this one only *reads*: it asks Brevo
how the list is doing and returns a single normalised dict the admin panel can
render.

This site uses Brevo exclusively (settings.BREVO_API_KEY /
BREVO_LIST_ID), so there is only one provider reader. Any figure Brevo
does not cheaply expose is left as ``None`` rather than guessed. This layer is
READ-ONLY — it never subscribes, removes, tags or writes anything.

The API key comes from Django settings and is only used in memory to make the
outgoing call. It is never logged or returned.
"""

import logging

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger("accounts.list_stats")

# Short timeout so a slow provider never hangs the admin page.
_TIMEOUT = 10

PROVIDER_LABEL = "Brevo"
PROVIDER_DASHBOARD = "https://app.brevo.com/contact/list"


def get_list_stats() -> dict:
    """
    Fetch Brevo list stats and return a normalised dict::

        {
            "provider":          "brevo",        # or "" when nothing is configured
            "subscribers_total": 1234,           # int or None
            "new_last_30d":      None,           # not available from Brevo
            "growth_pct":        None,
            "fetched_at":        <datetime>,     # tz-aware, always set
            "ok":                True,           # False on any failure
            "error":             "",             # short reason when ok is False
        }

    Never raises: a provider outage, bad key or missing field is caught and
    reported via ``ok=False`` / ``error`` so the admin page can fail soft.
    """
    api_key = (getattr(settings, "BREVO_API_KEY", "") or "").strip()
    group_id = (str(getattr(settings, "BREVO_LIST_ID", "") or "")).strip()

    if not api_key:
        return _result(ok=False, error="not_configured")

    try:
        total = _stats_brevo(api_key, group_id)
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        logger.warning("[list_stats] Brevo HTTP %s: %s", status, e)
        return _result(ok=False, error=_http_error_message(status))
    except requests.RequestException as e:
        logger.warning("[list_stats] Brevo request failed: %s", e)
        return _result(ok=False, error="provider_unreachable")
    except Exception as e:  # noqa: BLE001 — never let the reader crash the panel
        logger.warning("[list_stats] Brevo reader error: %s", e)
        return _result(ok=False, error="fetch_failed")

    return _result(subscribers_total=total, ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _http_error_message(status):
    """A short, plain-language hint (with the code to quote to support)."""
    if status in (401, 403):
        return f"Brevo rejected the API key (HTTP {status}). Check BREVO_API_KEY."
    if status == 404:
        return "Brevo couldn't find that list (HTTP 404). Check BREVO_LIST_ID."
    if status == 429:
        return "Brevo is rate-limiting requests (HTTP 429). Please try again in a few minutes."
    if status and 500 <= status < 600:
        return f"Brevo had a temporary server error (HTTP {status}). Please try again later."
    if status:
        return f"Brevo returned HTTP {status}. Check your API key and list ID."
    return "provider_unreachable"


def _result(subscribers_total=None, new_last_30d=None, growth_pct=None,
            ok=False, error=""):
    """Build the normalised result dict (single shape for success and failure)."""
    return {
        "provider": "" if error == "not_configured" else "brevo",
        "subscribers_total": subscribers_total,
        "new_last_30d": new_last_30d,
        "growth_pct": growth_pct,
        "fetched_at": timezone.now(),
        "ok": bool(ok),
        "error": error or "",
    }


def _as_int(value):
    """Coerce a provider count to int, or None if absent/unparseable."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Provider reader
# ---------------------------------------------------------------------------

def _stats_brevo(api_key, list_id):
    """
    Brevo API v3. https://developers.brevo.com/reference/getlist

    Total: the list's ``totalSubscribers``. Brevo has no simple "created in the
    last 30 days" count, so the panel leaves that figure blank.
    """
    headers = {"api-key": api_key, "Accept": "application/json"}
    resp = requests.get(
        f"https://api.brevo.com/v3/contacts/lists/{int(list_id)}",
        headers=headers, timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return _as_int(resp.json().get("totalSubscribers"))
