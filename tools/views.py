import json

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Max
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from .models import (
    ExperimentWeek,
    ExperimentGoal,
    MilestoneReflection,
    AliveListItem,
    HostedTool,
)


def experiment_results(request):
    weeks = ExperimentWeek.objects.filter(is_published=True).order_by("-week_date")

    goals_qs = ExperimentGoal.objects.all()
    goals_by_milestone = {
        "30": goals_qs.filter(milestone="30"),
        "60": goals_qs.filter(milestone="60"),
        "90": goals_qs.filter(milestone="90"),
    }

    reflections = {r.milestone: r for r in MilestoneReflection.objects.all()}

    totals = weeks.aggregate(
        total_revenue=Sum("revenue_this_week"),
        total_true_fans=Sum("transactions"),
        total_posts_rewritten=Sum("blog_posts_rewritten"),
    )

    latest_email_total = weeks.filter(
        email_list_total__isnull=False
    ).values_list("email_list_total", flat=True).first()

    context = {
        "weeks": weeks,
        "goals_by_milestone": goals_by_milestone,
        "reflections": reflections,
        "total_revenue": totals["total_revenue"] or 0,
        "total_true_fans": totals["total_true_fans"] or 0,
        "total_posts_rewritten": totals["total_posts_rewritten"] or 0,
        "latest_email_total": latest_email_total or 0,
    }
    return render(request, "tools/experiment_results.html", context)


def tools_home(request):
    return render(request, "tools/index.html")


def calming_game(request):
    return render(request, "tools/calming_game.html")


def tap_to_calm(request):
    return render(request, "tools/tap_to_calm.html")


def alive_list_builder(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        action = data.get("action")

        if not request.user.is_authenticated:
            return JsonResponse({"requires_login": True}, status=401)

        if action == "save_item":
            item_text = data.get("item_text", "").strip()
            category = data.get("category", "").strip()
            if not item_text:
                return JsonResponse({"error": "item_text required"}, status=400)
            item = AliveListItem.objects.create(
                user=request.user,
                item_text=item_text,
                category=category,
            )
            return JsonResponse({"status": "ok", "item_id": item.id})

        elif action == "delete_item":
            item_id = data.get("item_id")
            item = get_object_or_404(AliveListItem, id=item_id, user=request.user)
            item.delete()
            return JsonResponse({"status": "ok"})

        elif action == "toggle_living_it":
            item_id = data.get("item_id")
            item = get_object_or_404(AliveListItem, id=item_id, user=request.user)
            item.is_living_it = not item.is_living_it
            item.save(update_fields=["is_living_it", "updated"])
            return JsonResponse({"status": "ok", "is_living_it": item.is_living_it})

        return JsonResponse({"error": "Unknown action"}, status=400)

    # GET
    existing_items = []
    if request.user.is_authenticated:
        existing_items = list(
            AliveListItem.objects.filter(user=request.user).values(
                "id", "item_text", "category", "is_living_it", "order"
            )
        )

    return render(request, "tools/alive_list_builder.html", {
        "existing_items_json": json.dumps(existing_items),
        "user_authenticated": request.user.is_authenticated,
    })


# ── Hosted Tools (upload-an-HTML-artifact) ──────────────────────────────────

def _staff_preview(request):
    return request.GET.get("preview") == "1" and request.user.is_staff


def hosted_tool_detail(request, slug):
    """
    Public wrapper page for an uploaded tool. Shows site chrome (nav/footer)
    and embeds the artifact in a sandboxed iframe pointing at the raw view.
    """
    if _staff_preview(request):
        tool = get_object_or_404(HostedTool, slug=slug)
    else:
        tool = get_object_or_404(HostedTool, slug=slug, published=True)
    return render(request, "tools/hosted_tool_detail.html", {"tool": tool})


@xframe_options_sameorigin
def hosted_tool_raw(request, slug):
    """
    Serve the raw artifact HTML so its JavaScript executes.

    Security model:
      - The file lives in secure_storage, so it is not directly web-served;
        this view is the only way to reach it.
      - It is only ever loaded inside the sandboxed iframe on the detail page
        (sandbox WITHOUT allow-same-origin => opaque origin => the artifact
        cannot read this site's cookies, session or DOM).
      - X-Frame-Options: SAMEORIGIN (decorator) lets our own page frame it
        while blocking other sites; frame-ancestors 'self' is the modern
        equivalent / belt-and-braces.
    """
    if _staff_preview(request):
        tool = get_object_or_404(HostedTool, slug=slug)
    else:
        tool = get_object_or_404(HostedTool, slug=slug, published=True)

    if not tool.html_file:
        raise Http404("No file attached to this tool.")

    try:
        with tool.html_file.open("rb") as fh:
            html = fh.read()
    except (FileNotFoundError, ValueError):
        raise Http404("Tool file missing on server.")

    # Inject a tiny height-reporter so the parent page can size the iframe to
    # the content (no inner scroll). Runs inside the sandbox via allow-scripts;
    # only posts a number, so it needs no same-origin access.
    reporter = (
        b"<script>(function(){"
        b"function r(){var h=Math.max("
        b"document.body?document.body.scrollHeight:0,"
        b"document.documentElement?document.documentElement.scrollHeight:0);"
        b"parent.postMessage({__toolHeight:h},'*');}"
        b"window.addEventListener('load',r);"
        b"window.addEventListener('resize',r);"
        b"if(window.ResizeObserver){new ResizeObserver(r).observe(document.documentElement);}"
        b"setTimeout(r,300);setTimeout(r,1200);"
        b"})();</script>"
    )
    if b"</body>" in html:
        head, sep, tail = html.rpartition(b"</body>")
        html = head + reporter + sep + tail
    else:
        html = html + reporter

    response = HttpResponse(html, content_type="text/html; charset=utf-8")
    response["Content-Security-Policy"] = "frame-ancestors 'self'"
    response["X-Content-Type-Options"] = "nosniff"
    return response
