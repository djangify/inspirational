# Generated manually — adds sidebar_heading and sidebar_product_count to SiteSettings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0015_sitesettings_active_theme'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='sidebar_heading',
            field=models.CharField(
                blank=True,
                default='Featured Products',
                help_text='Heading shown above the products sidebar on blog pages.',
                max_length=100,
                verbose_name='Blog Sidebar Heading',
            ),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='sidebar_product_count',
            field=models.PositiveSmallIntegerField(
                default=5,
                help_text='Number of featured products to show in the blog sidebar.',
                verbose_name='Blog Sidebar Product Count',
            ),
        ),
    ]
