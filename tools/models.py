from django.db import models


# ── Experiment: The 1000 True Fans ───────────────────────────────────────────

MILESTONE_CHOICES = [
    ("30", "30 Days"),
    ("60", "60 Days"),
    ("90", "90 Days"),
]


class ExperimentWeek(models.Model):
    week_date = models.DateField(
        unique=True,
        help_text="The Monday this week starts",
    )
    week_number = models.PositiveIntegerField()
    is_milestone = models.BooleanField(default=False)
    milestone_label = models.CharField(max_length=50, blank=True, null=True)

    # Activity metrics
    blog_posts_rewritten = models.PositiveIntegerField(default=0)
    pinterest_pins = models.PositiveIntegerField(default=0)
    youtube_audio = models.PositiveIntegerField(default=0)
    substack_posts = models.PositiveIntegerField(default=0)
    emails_added = models.PositiveIntegerField(default=0)
    ga4_sessions = models.PositiveIntegerField(null=True, blank=True)

    # Reflections
    what_i_did = models.TextField(blank=True)
    what_i_noticed = models.TextField(blank=True)
    what_changed = models.TextField(blank=True)
    went_well_wednesday = models.TextField(blank=True)

    # Revenue
    revenue_this_week = models.DecimalField(
        max_digits=8, decimal_places=2, default=0
    )
    transactions = models.PositiveIntegerField(default=0)
    email_list_total = models.PositiveIntegerField(null=True, blank=True)

    is_published = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-week_date"]

    def __str__(self):
        return f"Week {self.week_number} — {self.week_date}"


class ExperimentGoal(models.Model):
    milestone = models.CharField(max_length=2, choices=MILESTONE_CHOICES)
    goal_text = models.CharField(max_length=200)
    is_achieved = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["milestone", "order"]

    def __str__(self):
        return f"[{self.get_milestone_display()}] {self.goal_text}"


class MilestoneReflection(models.Model):
    milestone = models.CharField(
        max_length=2, choices=MILESTONE_CHOICES, unique=True
    )
    reflection_text = models.TextField()
    published_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_milestone_display()} Reflection"
