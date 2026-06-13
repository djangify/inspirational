# Generated manually — relabels the default format back to "Writing" and adds
# a separate "Lil & Lol" format option. Choices-only change (no DB data change);
# existing "article" posts simply display as "Writing".

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0008_tags"),
    ]

    operations = [
        migrations.AlterField(
            model_name="post",
            name="content_type",
            field=models.CharField(
                choices=[
                    ("article", "Writing"),
                    ("lillol", "Lil & Lol"),
                    ("bite", "Bites — short quick-read"),
                    ("video", "Video"),
                    ("audio", "Audio / Podcast"),
                ],
                default="article",
                help_text="The FORMAT of the post: Writing = standard post (default), Lil & Lol = short and playful, Bites = short quick-read, Video = video embed, Audio = podcast/audio embed. Use Tags below for TOPICS like Choices or Updates.",
                max_length=10,
            ),
        ),
    ]
