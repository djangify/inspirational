from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bots", "0006_botproduct_model_max_tokens"),
    ]

    operations = [
        migrations.AlterField(
            model_name="botproduct",
            name="model",
            field=models.CharField(
                choices=[
                    ("claude-haiku-4-5-20251001", "Haiku 4.5 — recommended"),
                    ("claude-sonnet-4-5", "Sonnet — more capable"),
                ],
                default="claude-haiku-4-5-20251001",
                help_text="Which Claude model this coach uses. Haiku keeps running costs down and is well suited to answering from a workbook PDF.",
                max_length=64,
            ),
        ),
    ]
