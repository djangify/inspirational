from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum, Count
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models_tracker import WritingGoal, WritingSession
from .forms_tracker import WritingGoalForm, WritingSessionForm

import calendar
from datetime import datetime, timedelta
import json


@login_required
def writing_progress(request):
    """
    Main view for the writing progress tracker section
    """
    if request.method == "POST":
        form = WritingSessionForm(request.POST, user=request.user)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            return redirect("prompt:writing_progress")

    else:
        form = WritingSessionForm(user=request.user)
    # Get active writing goals
    active_goals = WritingGoal.objects.filter(user=request.user, active=True)

    # Get current month's writing sessions
    today = timezone.now().date()
    first_day = today.replace(day=1)
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    current_month_sessions = WritingSession.objects.filter(
        user=request.user, date__range=(first_day, last_day)
    ).order_by("-date")

    # Calculate basic stats
    total_minutes = (
        current_month_sessions.aggregate(Sum("minutes_spent"))["minutes_spent__sum"]
        or 0
    )
    total_words = (
        current_month_sessions.aggregate(Sum("word_count"))["word_count__sum"] or 0
    )
    total_sessions = current_month_sessions.count()

    # Prepare calendar data
    calendar_data = {}
    for session in current_month_sessions:
        date_str = session.date.strftime("%Y-%m-%d")
        minutes = session.minutes_spent or 0
        words = session.word_count or 0

        if date_str not in calendar_data:
            calendar_data[date_str] = {
                "minutes": minutes,
                "words": words,
                "count": 1,
            }
        else:
            calendar_data[date_str]["minutes"] += minutes
            calendar_data[date_str]["words"] += words
            calendar_data[date_str]["count"] += 1

    # New goal form
    goal_form = WritingGoalForm()

    # Get recent sessions for display
    recent_sessions = WritingSession.objects.filter(user=request.user).order_by(
        "-date"
    )[:5]
    session_form = WritingSessionForm(user=request.user)
    context = {
        "active_goals": active_goals,
        "session_form": session_form,
        "goal_form": goal_form,
        "recent_sessions": recent_sessions,
        "calendar_data": json.dumps(calendar_data),
        "current_month": today.strftime("%B %Y"),
        "stats": {
            "total_minutes": total_minutes,
            "total_words": total_words,
            "total_sessions": total_sessions,
            "avg_minutes": round(total_minutes / total_sessions)
            if total_sessions
            else 0,
            "avg_words": round(total_words / total_sessions) if total_sessions else 0,
        },
    }

    return render(request, "prompt/writing_progress.html", context)


@login_required
def session_list(request):
    """Display all writing sessions with pagination"""
    sessions = WritingSession.objects.filter(user=request.user).order_by("-date")

    # Handle filtering
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")
    mood = request.GET.get("mood")

    if date_from:
        try:
            date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
            sessions = sessions.filter(date__gte=date_from)
        except ValueError:
            pass

    if date_to:
        try:
            date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
            sessions = sessions.filter(date__lte=date_to)
        except ValueError:
            pass

    if mood and mood != "all":
        sessions = sessions.filter(mood=mood)

    # Pagination
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Calculate stats for the filtered sessions
    total_sessions = sessions.count()
    total_minutes = sessions.aggregate(Sum("minutes_spent"))["minutes_spent__sum"] or 0
    total_words = sessions.aggregate(Sum("word_count"))["word_count__sum"] or 0

    context = {
        "page_obj": page_obj,
        "total_sessions": total_sessions,
        "total_minutes": total_minutes,
        "total_words": total_words,
        "avg_minutes": round(total_minutes / total_sessions) if total_sessions else 0,
        "avg_words": round(total_words / total_sessions) if total_sessions else 0,
        # Keep current filters in context for form
        "date_from": date_from,
        "date_to": date_to,
        "mood": mood or "all",
    }

    return render(request, "prompt/session_list.html", context)


@login_required
@require_POST
def add_goal(request):
    """Handle adding a new writing goal"""
    form = WritingGoalForm(request.POST)
    if form.is_valid():
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        messages.success(request, "New goal added successfully!")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

    return redirect("prompt:writing_progress")


@login_required
def edit_goal(request, goal_id):
    """Handle editing an existing goal"""
    goal = get_object_or_404(WritingGoal, id=goal_id, user=request.user)

    if request.method == "POST":
        form = WritingGoalForm(request.POST, instance=goal)
        if form.is_valid():
            form.save()
            messages.success(request, "Goal updated successfully!")
            return redirect("prompt:writing_progress")
    else:
        form = WritingGoalForm(instance=goal)

    return render(
        request,
        "prompt/edit_goal.html",
        {
            "form": form,
            "goal": goal,
        },
    )


@login_required
def delete_goal(request, goal_id):
    """Handle deleting a goal"""
    goal = get_object_or_404(WritingGoal, id=goal_id, user=request.user)

    if request.method == "POST":
        goal.delete()
        messages.success(request, "Goal deleted successfully!")
        return redirect("prompt:writing_progress")

    return render(request, "prompt/confirm_delete_goal.html", {"goal": goal})


@login_required
def toggle_goal_active(request, goal_id):
    """Toggle the active status of a goal"""
    goal = get_object_or_404(WritingGoal, id=goal_id, user=request.user)

    goal.active = not goal.active
    goal.save()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "status": "success",
                "active": goal.active,
            }
        )

    if goal.active:
        messages.success(request, f"Goal '{goal}' has been activated.")
    else:
        messages.info(request, f"Goal '{goal}' has been deactivated.")

    return redirect("prompt:writing_progress")


@login_required
def edit_session(request, session_id):
    """Handle editing an existing writing session"""
    session = get_object_or_404(WritingSession, id=session_id, user=request.user)

    if request.method == "POST":
        form = WritingSessionForm(request.POST, instance=session, user=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Session updated successfully!")

            if "return_to_list" in request.POST:
                return redirect("prompt:session_list")
            return redirect("prompt:writing_progress")
    else:
        form = WritingSessionForm(instance=session, user=request.user)

    return render(
        request,
        "prompt/edit_session.html",
        {
            "form": form,
            "session": session,
        },
    )


@login_required
def delete_session(request, session_id):
    """Handle deleting a writing session"""
    session = get_object_or_404(WritingSession, id=session_id, user=request.user)

    if request.method == "POST":
        session.delete()
        messages.success(request, "Your session deleted successfully!")

        # Check where to redirect
        if request.GET.get("from") == "list":
            return redirect("prompt:session_list")
        return redirect("prompt:writing_progress")

    return render(request, "prompt/confirm_delete_session.html", {"session": session})


@login_required
def stats_view(request):
    """Display detailed writing statistics"""
    # Time period selection
    period = request.GET.get("period", "month")
    today = timezone.now().date()

    if period == "week":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        title = (
            f"This Week ({start_date.strftime('%d %b')} - {end_date.strftime('%d %b')})"
        )
    elif period == "month":
        start_date = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = today.replace(day=last_day)
        title = f"This Month ({today.strftime('%B %Y')})"
    elif period == "year":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
        title = f"This Year ({today.year})"
    elif period == "all":
        # Get the date of the first session
        first_session = (
            WritingSession.objects.filter(user=request.user).order_by("date").first()
        )
        start_date = first_session.date if first_session else today
        end_date = today
        title = f"All Time ({start_date.strftime('%d %b %Y')} - {today.strftime('%d %b %Y')})"
    else:
        # Custom date range
        try:
            start_date = datetime.strptime(
                request.GET.get("start_date", ""), "%Y-%m-%d"
            ).date()
            end_date = datetime.strptime(
                request.GET.get("end_date", ""), "%Y-%m-%d"
            ).date()
            title = f"Custom ({start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')})"
        except ValueError:
            # Default to this month if invalid dates
            start_date = today.replace(day=1)
            last_day = calendar.monthrange(today.year, today.month)[1]
            end_date = today.replace(day=last_day)
            title = f"This Month ({today.strftime('%B %Y')})"

    # Get sessions for the selected period
    sessions = WritingSession.objects.filter(
        user=request.user, date__range=(start_date, end_date)
    )

    # Basic stats
    total_sessions = sessions.count()
    total_minutes = sessions.aggregate(Sum("minutes_spent"))["minutes_spent__sum"] or 0
    total_words = sessions.aggregate(Sum("word_count"))["word_count__sum"] or 0

    # Mood distribution
    mood_counts = dict(sessions.values_list("mood").annotate(count=Count("mood")))

    # Day of week distribution
    day_counts = {}
    for i in range(7):
        day_name = calendar.day_name[i]
        day_counts[day_name] = 0

    for session in sessions:
        day_name = calendar.day_name[session.date.weekday()]
        day_counts[day_name] += 1

    # Time trend data (for charts)
    time_data = {}
    for session in sessions:
        date_str = session.date.strftime("%Y-%m-%d")
        if date_str in time_data:
            time_data[date_str]["minutes"] += session.minutes_spent
            time_data[date_str]["words"] += session.word_count
            time_data[date_str]["count"] += 1
        else:
            time_data[date_str] = {
                "date": date_str,
                "minutes": session.minutes_spent,
                "words": session.word_count,
                "count": 1,
            }

    # Convert to list for template
    time_series = list(time_data.values())
    time_series.sort(key=lambda x: x["date"])

    context = {
        "period": period,
        "title": title,
        "start_date": start_date,
        "end_date": end_date,
        "stats": {
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "total_words": total_words,
            "avg_minutes": round(total_minutes / total_sessions)
            if total_sessions
            else 0,
            "avg_words": round(total_words / total_sessions) if total_sessions else 0,
        },
        "mood_counts": mood_counts,
        "day_counts": day_counts,
        "time_series": json.dumps(time_series),
    }

    return render(request, "prompt/components/stats.html", context)
