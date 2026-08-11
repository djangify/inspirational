"""Create (or reset) the OAuth client Claude uses for the MCP connector.

This site is its own OAuth Authorization Server, so it needs its own
django-oauth-toolkit Application. Claude's custom-connector "Advanced settings"
take a Client ID + Client Secret, which this command prints.

The client secret is hashed on save and cannot be recovered afterwards, so it is
generated here and printed once. Re-run with --reset to roll a new secret. The
owner-facing "Connect to Claude" admin page does the same thing without the CLI.

    python manage.py mcp_create_client
    python manage.py mcp_create_client --reset
    python manage.py mcp_create_client --redirect-uri https://claude.ai/api/mcp/auth_callback
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

APP_NAME = "Claude (MCP connector)"
DEFAULT_REDIRECT = "https://claude.ai/api/mcp/auth_callback"


class Command(BaseCommand):
    help = "Create/reset the OAuth Application Claude uses for the MCP connector."

    def add_arguments(self, parser):
        parser.add_argument(
            "--redirect-uri",
            default=DEFAULT_REDIRECT,
            help=f"OAuth redirect URI Claude uses (default: {DEFAULT_REDIRECT}).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Roll a new client secret on the existing Application.",
        )

    def handle(self, *args, **options):
        try:
            from oauth2_provider.generators import generate_client_secret
            from oauth2_provider.models import get_application_model
        except ImportError as exc:  # pragma: no cover
            raise CommandError(
                "django-oauth-toolkit is not installed / migrated on this site."
            ) from exc

        App = get_application_model()

        owner = (
            get_user_model()
            .objects.filter(is_superuser=True, is_active=True)
            .order_by("pk")
            .first()
        )
        if owner is None:
            raise CommandError("No active superuser (site owner) found.")

        redirect_uri = options["redirect_uri"]
        app = App.objects.filter(name=APP_NAME).first()

        if app and not options["reset"]:
            self.stdout.write(
                self.style.WARNING(
                    f'An Application named "{APP_NAME}" already exists '
                    f"(client_id: {app.client_id}).\n"
                    "The secret can't be shown again — re-run with --reset to roll a new one."
                )
            )
            return

        # Capture the plaintext BEFORE save; DOT hashes it on save.
        plaintext_secret = generate_client_secret()

        if app:  # --reset
            app.client_secret = plaintext_secret
            app.redirect_uris = redirect_uri
            app.client_type = App.CLIENT_CONFIDENTIAL
            app.authorization_grant_type = App.GRANT_AUTHORIZATION_CODE
            app.user = owner
            app.save()
            action = "reset"
        else:
            app = App(
                name=APP_NAME,
                user=owner,
                client_type=App.CLIENT_CONFIDENTIAL,
                authorization_grant_type=App.GRANT_AUTHORIZATION_CODE,
                redirect_uris=redirect_uri,
                client_secret=plaintext_secret,
            )
            app.save()
            action = "created"

        self.stdout.write(self.style.SUCCESS(f"\nMCP OAuth client {action}.\n"))
        self.stdout.write("Paste these into Claude -> custom connector -> Advanced settings:\n")
        self.stdout.write(f"  CLIENT_ID:     {app.client_id}")
        self.stdout.write(f"  CLIENT_SECRET: {plaintext_secret}")
        self.stdout.write(f"  redirect_uri:  {redirect_uri}")
        self.stdout.write(
            self.style.WARNING(
                "\nStore the secret now — it is hashed and cannot be shown again."
            )
        )
