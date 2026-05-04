from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Delete unverified accounts older than 3 days"

    def handle(self, *args, **kwargs):
        cutoff = timezone.now() - timedelta(days=3)
        old_unverified = User.objects.filter(
            is_active=False,
            date_joined__lt=cutoff,
            is_staff=False,
            is_superuser=False,
        )
        count = old_unverified.count()
        old_unverified.delete()
        self.stdout.write(f"Deleted {count} unverified accounts.")
