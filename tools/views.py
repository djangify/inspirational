import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Max
from django.views.decorators.http import require_POST

from .models import ExperimentWeek, ExperimentGoal, MilestoneReflection, LiveItListItem


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


def live_it_list_builder(request):
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
            item = LiveItListItem.objects.create(
                user=request.user,
                item_text=item_text,
                category=category,
            )
            return JsonResponse({"status": "ok", "item_id": item.id})

        elif action == "delete_item":
            item_id = data.get("item_id")
            item = get_object_or_404(LiveItListItem, id=item_id, user=request.user)
            item.delete()
            return JsonResponse({"status": "ok"})

        elif action == "toggle_living_it":
            item_id = data.get("item_id")
            item = get_object_or_404(LiveItListItem, id=item_id, user=request.user)
            item.is_living_it = not item.is_living_it
            item.save(update_fields=["is_living_it", "updated"])
            return JsonResponse({"status": "ok", "is_living_it": item.is_living_it})

        return JsonResponse({"error": "Unknown action"}, status=400)

    # GET
    existing_items = []
    if request.user.is_authenticated:
        existing_items = list(
            LiveItListItem.objects.filter(user=request.user).values(
                "id", "item_text", "category", "is_living_it", "order"
            )
        )

    return render(request, "tools/live_it_list_builder.html", {
        "existing_items_json": json.dumps(existing_items),
        "user_authenticated": request.user.is_authenticated,
    })
