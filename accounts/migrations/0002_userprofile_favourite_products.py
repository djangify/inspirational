# Generated by Django 5.2.4 on 2025-07-19 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('shop', '0003_alter_productimage_options_productimage_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='favourite_products',
            field=models.ManyToManyField(blank=True, related_name='favorited_by', to='shop.product'),
        ),
    ]
