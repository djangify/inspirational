from django.shortcuts import render
from django.db.models import Sum, Max

from .models import ExperimentWeek, ExperimentGoal, MilestoneReflection


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
