from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0019_onetimeoffer_self_authored"),
    ]

    operations = [
        migrations.AddField(
            model_name="onetimeoffer",
            name="included_products",
            field=models.ManyToManyField(
                blank=True,
                help_text=(
                    "Tick the products this offer includes. On purchase the buyer gets "
                    "each product's download and its existing AI coach — no need to "
                    "re-upload anything."
                ),
                related_name="in_one_time_offers",
                to="shop.product",
            ),
        ),
    ]
