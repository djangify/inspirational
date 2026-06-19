from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0016_sitesettings_sidebar_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="active_theme",
            field=models.CharField(
                choices=[
                    ("classic", "Classic — default site design"),
                    ("editorial", "Editorial — warm tones, serif headings, magazine layout"),
                    ("minimal", "Minimal — clean black & white, Substack-style"),
                    ("spotlight", "Spotlight — featured products over a clean minimal feed"),
                ],
                default="classic",
                help_text=(
                    "Choose the visual theme for the blog and shop. "
                    "Classic uses your default design. Changes apply immediately."
                ),
                max_length=20,
                verbose_name="Site Theme",
            ),
        ),
    ]
