from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0012_coupon_and_order_coupon_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="SiteSettings",
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
                    "google_analytics_id",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Enter your GA4 Measurement ID (e.g. G-XXXXXXXXXX). Overrides the hardcoded ID in base.html.",
                        max_length=30,
                        verbose_name="Google Analytics GA4 ID",
                    ),
                ),
                (
                    "google_search_console_verification",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Enter the content value from the GSC meta tag verification (not the full tag — just the code string). Overrides the hardcoded value in base.html.",
                        max_length=255,
                        verbose_name="Google Search Console Verification Code",
                    ),
                ),
                (
                    "og_image",
                    models.ImageField(
                        blank=True,
                        help_text="Default social sharing image (1200×630 px recommended).",
                        null=True,
                        upload_to="site/og/",
                        verbose_name="Default OG Image",
                    ),
                ),
                (
                    "facebook_app_id",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Optional Facebook App ID for OG tags.",
                        max_length=50,
                        verbose_name="Facebook App ID",
                    ),
                ),
                (
                    "currency_code",
                    models.CharField(
                        choices=[
                            ("AUD", "Australian Dollar (A$)"),
                            ("CAD", "Canadian Dollar (CA$)"),
                            ("EUR", "Euro (€)"),
                            ("GBP", "British Pound (£)"),
                            ("USD", "US Dollar ($)"),
                        ],
                        default="USD",
                        help_text="Currency code for Stripe payments (e.g. USD, GBP, EUR).",
                        max_length=3,
                        verbose_name="Currency Code",
                    ),
                ),
                (
                    "currency_symbol",
                    models.CharField(
                        default="$",
                        help_text="Symbol displayed before prices (e.g. $, £, €).",
                        max_length=5,
                        verbose_name="Currency Symbol",
                    ),
                ),
            ],
            options={
                "verbose_name": "Site Settings",
                "verbose_name_plural": "Site Settings",
            },
        ),
    ]
