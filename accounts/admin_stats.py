"""Owner-only "Email list stats" admin page.

A read-only snapshot of the MailerLite list — total subscribers, pulled live from
MailerLite (see ``accounts.list_stats``). Figures are cached in the DB for up to
12 hours; "Refresh now" forces a fresh fetch (POST -> redirect, so a browser
reload never re-fetches). Everything fails soft: no key, or a MailerLite outage,
shows a calm message rather than a stack trace. Nothing here writes to MailerLite.

Owner-only (superuser).
"""

from functools import wraps

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse

from .list_stats import PROVIDER_DASHBOARD, PROVIDER_LABEL


def install_sidebar_link():
    """Add an owner-only "Email list stats" link to the admin sidebar.

    Injects the link into the ``app_list`` the admin builds for every page, so
    the active theme (Adminita) renders it in its own style. Safe to call once at
    startup; calling it again is a no-op.
    """
    site = admin.site
    if getattr(site, "_email_stats_sidebar_patched", False):
        return
    site._email_stats_sidebar_patched = True

    original_get_app_list = site.get_app_list

    def get_app_list(request, app_label=None):
        app_list = list(original_get_app_list(request, app_label))
        try:
            if app_label is None and getattr(request, "user", None) and request.user.is_superuser:
                app_list.append(
                    {
                        "name": "Email list",
                        "app_label": "email_list",
                        "app_url": reverse("admin_email_list_stats"),
                        "has_module_perms": True,
                        "models": [
                            {
                                "name": "Email list stats",
                                "object_name": "email_list_stats",
                                "admin_url": reverse("admin_email_list_stats"),
                                "view_only": True,
                            }
                        ],
                    }
                )
        except NoReverseMatch:
            pass
        except Exception:
            # The sidebar link is cosmetic — never let it break the admin.
            pass
        return app_list

    site.get_app_list = get_app_list


def owner_required(view):
    """Allow only logged-in superusers (the site owner). Staff redirect to login."""

    @wraps(view)
    @staff_member_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise Http404()
        return view(request, *args, **kwargs)

    return _wrapped


@owner_required
def email_list_stats(request):
    from .models import EmailListStatsSnapshot

    # Manual "Refresh now": force a live re-fetch, then redirect (PRG pattern).
    if request.method == "POST" and request.POST.get("action") == "refresh":
        try:
            EmailListStatsSnapshot.get(force=True)
        except Exception:
            # A refresh failure is captured in the snapshot's ok/error; if even
            # that write fails, just fall through to the normal render.
            pass
        return redirect("admin_email_list_stats")

    try:
        stats = EmailListStatsSnapshot.get().as_dict()
    except Exception:
        # Belt-and-braces: the page must render even if the cache layer errors.
        stats = {
            "provider": "",
            "subscribers_total": None,
            "new_last_30d": None,
            "growth_pct": None,
            "fetched_at": None,
            "ok": False,
            "error": "fetch_failed",
        }

    context = {
        **admin.site.each_context(request),
        "title": "Email list stats",
        "stats": stats,
        "provider_label": PROVIDER_LABEL,
        "dashboard_url": PROVIDER_DASHBOARD,
        "not_configured": stats.get("error") == "not_configured" or not stats.get("provider"),
    }
    return render(request, "admin/email_list_stats.html", context)
