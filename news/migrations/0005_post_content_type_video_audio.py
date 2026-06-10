# Generated manually — adds content_type, video_url, audio_url, audio_file to news.Post

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
import news.models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0004_add_content_updated_to_post'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='content_type',
            field=models.CharField(
                choices=[
                    ('article', 'Article'),
                    ('bite', 'Bite — short quick-read'),
                    ('video', 'Video'),
                    ('audio', 'Audio / Podcast'),
                ],
                default='article',
                help_text='Article = long-form post, Bite = short quick-read, Video = video embed, Audio = podcast/audio embed.',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='post',
            name='video_url',
            field=models.URLField(
                blank=True,
                help_text='YouTube, Vimeo, or any video platform page URL — converted to an embed automatically.',
                null=True,
                verbose_name='Video URL',
            ),
        ),
        migrations.AddField(
            model_name='post',
            name='audio_url',
            field=models.URLField(
                blank=True,
                help_text='SoundCloud, Spotify, Buzzsprout, Anchor etc. — paste the public page URL.',
                null=True,
                verbose_name='Audio URL',
            ),
        ),
        migrations.AddField(
            model_name='post',
            name='audio_file',
            field=models.FileField(
                blank=True,
                help_text='Upload an MP3 or other audio file directly (max ~50 MB).',
                null=True,
                upload_to='news/audio/',
                validators=[news.models.validate_audio_file],
                verbose_name='Audio File (Upload)',
            ),
        ),
    ]
