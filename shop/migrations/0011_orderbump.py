from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0010_shopsettings"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrderBump",
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
                    "headline",
                    models.CharField(
                        default="Special One-Time Offer!",
                        help_text="Bold headline shown on the bump box.",
                        max_length=200,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Short pitch for why the customer should add this.",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Display order if multiple bumps are active.",
                    ),
                ),
                (
                    "bump_product",
                    models.ForeignKey(
                        help_text="The product being offered as the bump add-on.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="order_bumps",
                        to="shop.product",
                    ),
                ),
                (
                    "trigger_product",
                    models.ForeignKey(
                        blank=True,
                        help_text="Only show this bump when this product is in the cart. Leave blank to always show.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="order_bump_triggers",
                        to="shop.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "Order Bump",
                "verbose_name_plural": "Order Bumps",
                "ordering": ["order"],
            },
        ),
    ]
