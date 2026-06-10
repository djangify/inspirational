from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0011_orderbump"),
    ]

    operations = [
        migrations.CreateModel(
            name="Coupon",
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
                ("code", models.CharField(max_length=50, unique=True)),
                (
                    "discount_type",
                    models.CharField(
                        choices=[
                            ("percentage", "Percentage"),
                            ("fixed", "Fixed Amount"),
                        ],
                        default="percentage",
                        max_length=20,
                    ),
                ),
                (
                    "discount_value",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Percentage (e.g. 10 for 10%) or fixed amount in dollars (e.g. 5.00)",
                        max_digits=10,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("valid_from", models.DateTimeField(blank=True, null=True)),
                ("valid_to", models.DateTimeField(blank=True, null=True)),
                (
                    "usage_limit",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Leave blank for unlimited uses.",
                        null=True,
                    ),
                ),
                ("times_used", models.PositiveIntegerField(default=0)),
                (
                    "minimum_order_pence",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Minimum order value in cents required to use this coupon. 0 = no minimum.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Coupon",
                "verbose_name_plural": "Coupons",
                "ordering": ["-id"],
            },
        ),
        migrations.AddField(
            model_name="order",
            name="coupon_code",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AddField(
            model_name="order",
            name="coupon_discount_pence",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
