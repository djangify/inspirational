from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.services.mailerlite import add_subscriber


class Command(BaseCommand):
    help = "Sync verified, subscribed users who are missing a MailerLite ID"

    def handle(self, *args, **kwargs):
        users = User.objects.filter(
            is_active=True,
            profile__is_subscribed=True,
            profile__mailerlite_id__isnull=True,
        ).exclude(
            is_staff=True
        ).exclude(
            is_superuser=True
        )

        self.stdout.write(f"Found {users.count()} users to sync...")

        synced = 0
        skipped = 0

        for user in users:
            try:
                add_subscriber(user)
                if user.profile.mailerlite_id:
                    synced += 1
                    self.stdout.write(f"  ✓ {user.email}")
                else:
                    skipped += 1
                    self.stdout.write(f"  ✗ {user.email} (no ID returned)")
            except Exception as e:
                skipped += 1
                self.stdout.write(f"  ✗ {user.email} — {e}")

        self.stdout.write(f"\nDone. Synced: {synced}, Failed: {skipped}")
