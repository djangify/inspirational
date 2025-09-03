from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator


class WritingGoal(models.Model):
    """Model to store user's personal writing goals"""

    FREQUENCY_CHOICES = [
        ("daily", "Day"),
        ("weekly", "Week"),
        ("monthly", "Month"),
    ]

    TYPE_CHOICES = [
        ("time", "Minutes per session"),
        ("words", "Words per session"),
        ("sessions", "Number of sessions"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="writing_goals"
    )
    goal_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default="time",
        help_text="Used for tracking writing progress",
    )

    goal_label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional custom label (e.g., Read 10 pages, Drink water)",
    )

    target_value = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Target value (e.g., 30 minutes, 10 sessions, 1000 words)",
    )

    frequency = models.CharField(
        max_length=10, choices=FREQUENCY_CHOICES, default="daily"
    )
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(
        null=True, blank=True, help_text="Leave blank for ongoing goals"
    )
    active = models.BooleanField(default=True)
    notes = models.TextField(
        blank=True, help_text="Why did you set this goal? What are you working towards?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        label = self.goal_label or self.get_goal_type_display()
        return f"{label} goal for {self.user.username}: {self.target_value} per {self.frequency}"

    def is_current(self):
        """Check if the goal is current (not past end_date)"""
        today = timezone.now().date()
        if self.end_date:
            return today <= self.end_date
        return True

    def days_remaining(self):
        """Number of days remaining for the goal, or None if ongoing"""
        if not self.end_date:
            return None
        today = timezone.now().date()
        if today > self.end_date:
            return 0
        return (self.end_date - today).days

    def progress_percentage(self):
        """Calculate accurate progress based on goal frequency and target value."""
        if not self.active or not self.is_current():
            return 0

        today = timezone.now().date()
        end = self.end_date if (self.end_date and self.end_date < today) else today
        start = self.start_date

        # Number of periods (days/weeks/months) in range
        if self.frequency == "daily":
            total_periods = (end - start).days + 1
        elif self.frequency == "weekly":
            total_periods = ((end - start).days // 7) + 1
        elif self.frequency == "monthly":
            total_periods = ((end.year - start.year) * 12 + end.month - start.month) + 1
        else:
            total_periods = 1

        expected_total = self.target_value * max(total_periods, 0)

        # Only sessions that belong to THIS goal
        sessions = self.sessions.filter(date__gte=start)
        if self.end_date:
            sessions = sessions.filter(date__lte=self.end_date)

        if self.goal_type == "time":
            actual_total = (
                sessions.aggregate(models.Sum("minutes_spent"))["minutes_spent__sum"]
                or 0
            )
        elif self.goal_type == "words":
            actual_total = (
                sessions.aggregate(models.Sum("word_count"))["word_count__sum"] or 0
            )
        elif self.goal_type == "sessions":
            actual_total = sessions.count()
        else:
            actual_total = 0

        if not expected_total:
            return 0

        pct = int((actual_total / expected_total) * 100)
        return max(0, min(pct, 100))


class WritingSession(models.Model):
    """Model to track individual writing sessions"""

    MOOD_CHOICES = [
        ("very_negative", "Very Difficult"),
        ("negative", "Difficult"),
        ("neutral", "Neutral"),
        ("positive", "Enjoyable"),
        ("very_positive", "Very Enjoyable"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="writing_sessions"
    )
    goal = models.ForeignKey(
        "WritingGoal",
        on_delete=models.CASCADE,
        related_name="sessions",
        help_text="Which goal is this session for?",
    )
    date = models.DateField(default=timezone.now)
    minutes_spent = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text="How many minutes did you spend on your goal?",
    )
    word_count = models.PositiveIntegerField(
        default=0, help_text="Approximately how many words did you write? (Optional)"
    )
    prompt_used = models.TextField(blank=True, null=True)
    mood = models.CharField(
        max_length=15,
        choices=MOOD_CHOICES,
        default="neutral",
        help_text="How was your writing session?",
    )

    notes = models.TextField(
        blank=True, help_text="What did you write about? How did it go?"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"Writing session on {self.date} by {self.user.username} ({self.minutes_spent} minutes)"
