from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ProgrammaticPage",
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
                ("keyword", models.CharField(max_length=150)),
                ("slug", models.SlugField(max_length=160, unique=True)),
                (
                    "master_template",
                    models.TextField(
                        help_text="Write your core content once. Use [Topic] as the placeholder — it will be replaced with the keyword when content is generated."
                    ),
                ),
                ("generated_content", models.TextField(blank=True, null=True)),
                ("h1_heading", models.CharField(blank=True, max_length=200)),
                ("meta_title", models.CharField(blank=True, max_length=60)),
                ("meta_description", models.CharField(blank=True, max_length=160)),
                (
                    "cta_text",
                    models.CharField(
                        blank=True,
                        help_text="The pitch line shown at the bottom of the page. Supports [Topic] substitution.",
                        max_length=200,
                    ),
                ),
                (
                    "cta_url",
                    models.URLField(
                        blank=True,
                        help_text="The link the CTA button points to.",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("pending_review", "Pending Review"),
                            ("published", "Published"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("manual", "Manual"),
                            ("csv_import", "CSV Import"),
                        ],
                        default="manual",
                        max_length=20,
                    ),
                ),
                (
                    "noindex",
                    models.BooleanField(
                        default=False,
                        help_text="Tick to hide this page from search engines (adds noindex meta tag).",
                    ),
                ),
                (
                    "publish_date",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        help_text="Set a future date/time to auto-publish. Leave blank to publish manually.",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Programmatic Page",
                "verbose_name_plural": "Programmatic Pages",
                "ordering": ["-created"],
            },
        ),
    ]
