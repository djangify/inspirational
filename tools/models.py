import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from inspirational.storage import secure_storage
from inspirational.utils import custom_slugify


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


# ── ALIVE List Builder ──────────────────────────────────────────────────────

class AliveListItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alive_list_items",
    )
    item_text = models.CharField(max_length=300)
    category = models.CharField(max_length=100, blank=True)
    is_living_it = models.BooleanField(default=False)
    order = models.PositiveSmallIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created"]

    def __str__(self):
        return f"{self.user} — {self.item_text[:60]}"


# ── Hosted Tools (upload-an-HTML-artifact) ──────────────────────────────────

# Slugs already used by hand-built tool pages in tools/urls.py. An uploaded
# tool may not claim one of these, or it would shadow the existing page.
RESERVED_TOOL_SLUGS = {
    "",
    "calming-game",
    "tap-to-calm",
    "experiment-results",
    "an-alive-list-builder",
    "live-it-list-builder",
}


def validate_html(value):
    """Only allow .html / .htm uploads (a Claude artifact is a single HTML file)."""
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in [".html", ".htm"]:
        raise ValidationError(
            "Only .html files are allowed. Upload the single HTML file Claude gives you."
        )


class HostedTool(models.Model):
    """
    A self-contained HTML 'artifact' (e.g. a Claude-generated interactive tool)
    uploaded by the site owner and served live at /tools/<slug>/.

    The file is stored with secure_storage so it is NOT reachable directly on
    the web. It is only ever served through the sandboxed iframe view
    (see tools/views.py tool_raw), which keeps the artifact's JavaScript
    isolated from the site's own origin (cookies, session, DOM).

    Note: the sandbox uses an opaque origin (no allow-same-origin), so an
    uploaded tool CANNOT call back to this site's logged-in endpoints. Keep
    all state in memory inside the artifact.
    """

    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text="Used in the public URL: /tools/<slug>/ . Leave blank to auto-fill from the title.",
    )
    description = models.TextField(
        blank=True,
        help_text="Optional short caption shown above the tool on its public page.",
    )
    html_file = models.FileField(
        upload_to="hosted_tools/",
        storage=secure_storage,
        validators=[validate_html],
        help_text="Upload the single .html file. Hit save and it goes live at the URL above.",
    )
    published = models.BooleanField(
        default=True,
        help_text="Untick to take the tool offline without deleting it.",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "Hosted Tool"
        verbose_name_plural = "Hosted Tools"

    def __str__(self):
        return self.title

    def clean(self):
        # No per-site quota — unlimited hosted tools.
        # Guard only against colliding with a hand-built tool URL.
        slug = self.slug or custom_slugify(self.title)
        if slug in RESERVED_TOOL_SLUGS:
            raise ValidationError(
                {"slug": f"'{slug}' is reserved by a built-in tool page. Choose a different title or slug."}
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = custom_slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("tools:hosted_tool_detail", kwargs={"slug": self.slug})

    def get_raw_url(self):
        return reverse("tools:hosted_tool_raw", kwargs={"slug": self.slug})
