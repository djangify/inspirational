from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0009_merge_20260320_1253"),
    ]

    operations = [
        migrations.CreateModel(
            name="ShopSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("show_digital_withdrawal_consent", models.BooleanField(default=False, help_text="Show the EU/UK digital withdrawal consent checkbox at checkout.")),
                ("digital_withdrawal_consent_text", models.CharField(
                    default=(
                        "I understand and agree that by completing this purchase I am requesting "
                        "immediate access to digital content, and I therefore waive my right to "
                        "withdraw from this contract under the EU/UK Consumer Rights Act "
                        "(14-day cooling-off period)."
                    ),
                    max_length=500,
                )),
            ],
            options={
                "verbose_name": "Shop Settings",
                "verbose_name_plural": "Shop Settings",
            },
        ),
    ]
