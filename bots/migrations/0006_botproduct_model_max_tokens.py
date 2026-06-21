from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bots", "0005_alter_botproduct_access_days_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="botproduct",
            name="model",
            field=models.CharField(
                choices=[
                    ("claude-haiku-4-5-20251001", "Haiku 4.5 — cheaper, recommended"),
                    ("claude-sonnet-4-5", "Sonnet — more capable, ~3x cost"),
                ],
                default="claude-haiku-4-5-20251001",
                help_text="Which Claude model this coach uses. Haiku is ~3x cheaper and fine for answering from a workbook PDF.",
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name="botproduct",
            name="max_tokens",
            field=models.PositiveIntegerField(
                default=1000,
                help_text="Maximum length of each reply, in tokens. Lower = shorter, cheaper answers.",
            ),
        ),
    ]
