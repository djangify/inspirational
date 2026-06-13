# Generated manually — updates content_type section choices
# (relabels article -> "Lil & Lol", renames bite label, adds "choices" and "updates")

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0006_alter_post_slug_max_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='content_type',
            field=models.CharField(
                choices=[
                    ('article', 'Lil & Lol'),
                    ('bite', 'Bites — short quick-read'),
                    ('choices', 'Choices — intentional living'),
                    ('updates', 'Updates — site news'),
                    ('video', 'Video'),
                    ('audio', 'Audio / Podcast'),
                ],
                default='article',
                help_text='Lil & Lol = standard post, Bites = short quick-read, Choices = intentional living, Updates = site news, Video = video embed, Audio = podcast/audio embed.',
                max_length=10,
            ),
        ),
    ]
