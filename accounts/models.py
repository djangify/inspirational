# accounts/models.py
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
