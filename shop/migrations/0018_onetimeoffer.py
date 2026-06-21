from django.db import migrations, models
import django.db.models.deletion
import inspirational.storage
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0017_alter_sitesettings_active_theme"),
    ]

    operations = [
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
                    "offer_price_pence",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Special one-time price in pence (e.g. 700 for £7.00). Leave blank to use the product's current price.",
                        null=True,
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
                    "image",
                    models.ImageField(
                        blank=True,
                        help_text="Optional image shown alongside the offer.",
                        null=True,
                        storage=inspirational.storage.PublicMediaStorage(),
                        upload_to="shop/offer/",
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
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.ForeignKey(
                        help_text="The product offered. Must be published, active, and have a downloadable file.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="one_time_offers",
                        to="shop.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "One-Time Offer",
                "verbose_name_plural": "One-Time Offer",
            },
        ),
    ]
