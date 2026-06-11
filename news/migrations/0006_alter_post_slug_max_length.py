# Generated manually — widens news.Post.slug (50→200) and news.Category.slug (50→100)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0005_post_content_type_video_audio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='slug',
            field=models.SlugField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='slug',
            field=models.SlugField(max_length=100, unique=True),
        ),
    ]
