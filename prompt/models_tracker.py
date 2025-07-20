from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator


class WritingGoal(models.Model):
    """Model to store user's personal writing goals"""

    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    ]

    TYPE_CHOICES = [
        ("time", "Minutes per session"),
        ("words", "Words per session"),
        ("sessions", "Number of sessions"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="writing_goals"
    )
    goal_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="time")
    target_value = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Target value (minutes, words, or sessions)",
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
        return f"{self.get_goal_type_display()} goal for {self.user.username}: {self.target_value} per {self.frequency}"

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
        """Calculate progress towards goal based on tracked sessions"""
        if not self.active or not self.is_current():
            return 0

        # Get all related sessions within the goal period
        sessions = WritingSession.objects.filter(
            user=self.user, date__gte=self.start_date
        )

        if self.end_date:
            sessions = sessions.filter(date__lte=self.end_date)

        # Calculate progress based on goal type
        if self.goal_type == "time":
            total_minutes = (
                sessions.aggregate(models.Sum("minutes_spent"))["minutes_spent__sum"]
                or 0
            )
            return min(int((total_minutes / self.target_value) * 100), 100)
        elif self.goal_type == "words":
            total_words = (
                sessions.aggregate(models.Sum("word_count"))["word_count__sum"] or 0
            )
            return min(int((total_words / self.target_value) * 100), 100)
        elif self.goal_type == "sessions":
            session_count = sessions.count()
            return min(int((session_count / self.target_value) * 100), 100)

        return 0


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
    date = models.DateField(default=timezone.now)
    minutes_spent = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="How many minutes did you spend writing?",
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
