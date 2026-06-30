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
    link_text = models.CharField(
        "URL name",
        max_length=120,
        blank=True,
        help_text=(
            "Optional. The clickable label for a link button shown at the top "
            "AND bottom of the tool's page (e.g. 'Back to the shop', "
            "'Get the full guide'). Leave blank to hide the link."
        ),
    )
    link_url = models.URLField(
        "URL link",
        max_length=500,
        blank=True,
        help_text="Where the link button points. Only shown if both fields are filled.",
    )
    html_file = models.FileField(
        upload_to="hosted_tools/",
        storage=secure_storage,
        validators=[validate_html],
        help_text="Upload the single .html file. Hit save and it goes live at the URL above.",
    )
    ACCESS_FREE = "free"
    ACCESS_PAID = "paid"
    ACCESS_CHOICES = [
        (ACCESS_FREE, "Free — anyone can use it"),
        (ACCESS_PAID, "Paid — only buyers can use it"),
    ]
    access = models.CharField(
        max_length=10,
        choices=ACCESS_CHOICES,
        default=ACCESS_FREE,
        help_text=(
            "Free tools are public at /tools/<slug>/. Paid tools are unlocked "
            "only by buying a linked shop product (attach this tool to a Product "
            "in the shop, then it appears in the buyer's downloads area)."
        ),
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

    @property
    def has_link(self):
        """True when both the link name and link URL are set (show the button)."""
        return bool(self.link_text and self.link_url)

    # -- Selling a tool ------------------------------------------------------
    # access == "paid" gates the tool: its public page is only reachable by
    # someone who has purchased the linked shop product (or by staff). The link
    # itself is made on the shop side (Product.hosted_tool, reverse accessor
    # `self.product`). Free tools stay public for everyone.

    @property
    def linked_product(self):
        """The shop Product selling this tool, or None if it isn't linked."""
        try:
            return self.product
        except Exception:
            return None

    @property
    def requires_purchase(self):
        """True if this tool is marked Paid and must be unlocked by a purchase."""
        return self.access == self.ACCESS_PAID

    def user_has_access(self, user):
        """
        Can `user` view this tool? Free tools: always. Sold tools: only the
        buyer (a completed order for the linked product) or staff.
        """
        if not self.requires_purchase:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        # Local import avoids a circular import at module load time.
        from shop.models import OrderItem
        return OrderItem.objects.filter(
            order__user=user,
            order__status="completed",
            product__hosted_tool=self,
        ).exists()


# ── Tool saved results ────────────────────────────────────────────────────────

class ToolSavedResult(models.Model):
    """
    Generic JSON store for results that an uploaded HTML tool wants to
    persist to the user's dashboard (e.g. top 3 core values + compass text).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tool_saved_results",
    )
    tool_slug = models.SlugField(
        max_length=200,
        help_text="Slug of the HostedTool that created this result.",
    )
    tool_title = models.CharField(
        max_length=200,
        blank=True,
        help_text="Human-readable tool name, captured at save time.",
    )
    label = models.CharField(
        max_length=300,
        help_text="Short name for this result, e.g. 'My top 3 values'.",
    )
    data = models.JSONField(
        default=dict,
        help_text="Arbitrary JSON payload from the tool.",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user} — {self.tool_slug} — {self.label[:60]}"
