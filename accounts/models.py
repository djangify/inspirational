# accounts/models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from prompt.models import WritingPrompt
import uuid
from datetime import timedelta


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    verified = models.BooleanField(default=False)
    bio = models.TextField(max_length=500, blank=True)
    is_subscribed = models.BooleanField(default=True)
    mailerlite_id = models.CharField(max_length=255, blank=True, null=True)
    oto_seen_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the one-time offer was first shown to this user. Set once; ensures the offer is strictly one-time.",
    )

    favourite_prompts = models.ManyToManyField(
        WritingPrompt, blank=True, related_name="favorited_by"
    )
    favourite_products = models.ManyToManyField(
        "shop.Product", blank=True, related_name="favorited_by"
    )

    def __str__(self):
        return f"{self.user.username}'s profile"


# Create a UserProfile automatically when a User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Check if profile exists before trying to save it
    # This fixes the "User has no profile" error for existing users
    try:
        instance.profile.save()
    except User.profile.RelatedObjectDoesNotExist:
        # Create a profile for existing users who don't have one
        UserProfile.objects.create(user=instance)


class EmailVerificationToken(models.Model):
    """Model for email verification tokens"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        # Token expires after 24 hours
        return self.created_at >= timezone.now() - timedelta(hours=24)

    def __str__(self):
        return f"Verification for {self.user.username}"


class MemberResource(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    file = models.FileField(upload_to="member_resources/")
    thumbnail = models.ImageField(upload_to="member_resources/thumbnails/")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title


class EmailListStatsSnapshot(models.Model):
    """
    Cached snapshot of the site's MailerLite list stats (read-only reporting).

    We never call MailerLite on a normal admin page load. Instead the last result
    from ``accounts.list_stats.get_list_stats()`` is stored here with a timestamp
    and reused for up to ``REFRESH_EVERY`` (12h), plus an explicit "Refresh now"
    button. Persisting to the DB — rather than a per-process cache — keeps the
    snapshot shared across worker processes and restarts, so the 12-hour refresh
    (and MailerLite's rate limits) are actually honoured.

    Singleton: only ever one row.
    """

    REFRESH_EVERY = timedelta(hours=12)

    provider = models.CharField(max_length=20, blank=True, default="")
    subscribers_total = models.PositiveIntegerField(null=True, blank=True)
    new_last_30d = models.PositiveIntegerField(null=True, blank=True)
    growth_pct = models.FloatField(null=True, blank=True)
    ok = models.BooleanField(default=False)
    error = models.CharField(max_length=100, blank=True, default="")
    fetched_at = models.DateTimeField(null=True, blank=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Email List Stats Snapshot"
        verbose_name_plural = "Email List Stats Snapshot"

    def __str__(self):
        return f"Email list stats ({self.provider or 'not configured'})"

    def save(self, *args, **kwargs):
        # Enforce singleton: fold any accidental second insert onto the first row.
        if not self.pk:
            existing = EmailListStatsSnapshot.objects.first()
            if existing:
                self.pk = existing.pk
        super().save(*args, **kwargs)

    def is_stale(self, current_provider):
        """True if we should re-fetch: never fetched, provider changed, or old."""
        if self.fetched_at is None:
            return True
        if (self.provider or "") != (current_provider or ""):
            return True
        return timezone.now() - self.fetched_at >= self.REFRESH_EVERY

    def as_dict(self):
        """The same normalised shape accounts.list_stats.get_list_stats() returns."""
        return {
            "provider": self.provider,
            "subscribers_total": self.subscribers_total,
            "new_last_30d": self.new_last_30d,
            "growth_pct": self.growth_pct,
            "fetched_at": self.fetched_at,
            "ok": self.ok,
            "error": self.error,
        }

    @classmethod
    def refresh(cls):
        """Fetch live stats now and persist them onto the single row."""
        from .list_stats import get_list_stats

        data = get_list_stats()
        obj = cls.objects.first() or cls()
        obj.provider = data["provider"]
        obj.subscribers_total = data["subscribers_total"]
        obj.new_last_30d = data["new_last_30d"]
        obj.growth_pct = data["growth_pct"]
        obj.ok = data["ok"]
        obj.error = data["error"]
        obj.fetched_at = data["fetched_at"]
        obj.save()
        return obj

    @classmethod
    def get(cls, force=False):
        """
        Return the current snapshot, refreshing from MailerLite only when it is
        missing, stale (older than ``REFRESH_EVERY``), the provider changed, or
        ``force=True`` (the "Refresh now" button).
        """
        current_provider = "mailerlite" if getattr(settings, "MAILERLITE_API_KEY", "") else ""
        obj = cls.objects.first()
        if force or obj is None or obj.is_stale(current_provider):
            obj = cls.refresh()
        return obj


class SupportRequest(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="support_requests"
    )
    subject = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    handled = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Support Request"
        verbose_name_plural = "Support Requests"

    def __str__(self):
        return f"Support from {self.user.email}: {self.subject or '(no subject)'}"
