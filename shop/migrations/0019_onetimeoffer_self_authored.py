from django.db import migrations, models
import django.db.models.deletion
import inspirational.storage
import tinymce.models


class Migration(migrations.Migration):
    """
    Rebuild OneTimeOffer for the self-authored design: the offer now carries its
    own title/price/file/image/copy and links to a hidden, auto-managed Product
    (no product picker). The original table held no real data, so we drop and
    recreate it cleanly rather than reconcile column-by-column.
    """

    dependencies = [
        ("shop", "0018_onetimeoffer"),
    ]

    operations = [
        migrations.DeleteModel(name="OneTimeOffer"),
        migrations.CreateModel(
            name="OneTimeOffer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=False,
                        help_text="Tick to show the one-time offer to eligible users on their next login.",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        default="",
                        help_text="Name of what they're buying (shown as the item title).",
                        max_length=200,
                    ),
                ),
                (
                    "price_pence",
                    models.PositiveIntegerField(
                        default=700,
                        help_text="Price they pay, in pence (e.g. 700 = £7.00).",
                    ),
                ),
                (
                    "compare_at_pence",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Optional 'normal' price in pence, shown with a line through it for contrast.",
                        null=True,
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        blank=True,
                        help_text="The downloadable file (PDF or ZIP) the buyer receives. Upload it here.",
                        null=True,
                        storage=inspirational.storage.SecureFileStorage(),
                        upload_to="products/files/",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        help_text="Optional image shown alongside the offer.",
                        null=True,
                        storage=inspirational.storage.PublicMediaStorage(),
                        upload_to="products/images/",
                    ),
                ),
                (
                    "download_limit",
                    models.PositiveIntegerField(
                        default=5,
                        help_text="How many times the buyer can download the file.",
                    ),
                ),
                (
                    "headline",
                    models.CharField(
                        default="A one-time offer, just for you", max_length=200
                    ),
                ),
                (
                    "subheadline",
                    models.CharField(blank=True, default="", max_length=300),
                ),
                (
                    "body",
                    tinymce.models.HTMLField(
                        blank=True, help_text="Sales pitch shown under the headline."
                    ),
                ),
                (
                    "button_text",
                    models.CharField(
                        default="Yes, add this to my account", max_length=80
                    ),
                ),
                (
                    "decline_text",
                    models.CharField(
                        default="No thanks, take me to my dashboard", max_length=80
                    ),
                ),
                (
                    "show_timer",
                    models.BooleanField(
                        default=False,
                        help_text="Show a countdown timer on the offer page.",
                    ),
                ),
                (
                    "timer_minutes",
                    models.PositiveIntegerField(
                        default=15,
                        help_text="Countdown length in minutes (visual urgency only).",
                    ),
                ),
                (
                    "product",
                    models.OneToOneField(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="one_time_offer",
                        to="shop.product",
                    ),
                ),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "One-Time Offer",
                "verbose_name_plural": "One-Time Offer",
            },
        ),
    ]
