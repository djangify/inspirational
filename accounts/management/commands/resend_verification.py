from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from accounts.models import EmailVerificationToken


class Command(BaseCommand):
    help = "Resend verification email to a user"

    def add_arguments(self, parser):
        parser.add_argument("email", type=str)

    def handle(self, *args, **kwargs):
        email = kwargs["email"]
        try:
            user = User.objects.get(email=email)

            # Get or create the token
            token_obj, created = EmailVerificationToken.objects.get_or_create(user=user)
            token = token_obj.token

            link = f"{settings.SITE_URL}{reverse('accounts:verify_email', kwargs={'token': token})}"
            subject = "Verify your email"
            message = (
                f"Please verify your account by clicking the following link:\n\n{link}"
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            self.stdout.write(self.style.SUCCESS(f"Verification email sent to {email}"))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"No user with email: {email}"))
