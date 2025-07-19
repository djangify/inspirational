from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = "Send a test email to confirm email delivery"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)

    def handle(self, *args, **kwargs):
        email = kwargs["email"]
        subject = "Test Email from Inspirational Guidance"
        message = "This is a test email to confirm your email delivery is working."
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
            self.stdout.write(self.style.SUCCESS(f"Test email sent to {email}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error sending email: {e}"))
