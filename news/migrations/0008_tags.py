# Generated manually — adds a Tag model + Post.tags (topics), seeds the
# "Choices" and "Updates" tags, migrates any posts that briefly used those
# as content_type, and reverts content_type back to format-only choices.

import django.db.models.deletion
from django.db import migrations, models
from django.utils.text import slugify


def seed_tags_and_migrate(apps, schema_editor):
    Post = apps.get_model("news", "Post")
    Tag = apps.get_model("news", "Tag")

    topics = {"choices": "Choices", "updates": "Updates"}
    for slug, name in topics.items():
        tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
        # Move any post that used the old content_type onto the matching tag.
        for post in Post.objects.filter(content_type=slug):
            post.tags.add(tag)
            post.content_type = "article"
            post.save()


def remove_seeded_tags(apps, schema_editor):
    Tag = apps.get_model("news", "Tag")
    Tag.objects.filter(slug__in=["choices", "updates"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("news", "0007_alter_post_content_type_sections"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
                (
                    "slug",
                    models.SlugField(
                        max_length=50,
                        unique=True,
                        help_text="Used in the blog URL (e.g. ?type=choices). Auto-filled from the name.",
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="post",
            name="tags",
            field=models.ManyToManyField(
                blank=True,
                related_name="posts",
                to="news.tag",
                help_text="Topics this post belongs to (e.g. Choices, Updates). A post can have more than one, and they work alongside the format above.",
            ),
        ),
        migrations.AlterField(
            model_name="post",
            name="content_type",
            field=models.CharField(
                choices=[
                    ("article", "Lil & Lol"),
                    ("bite", "Bites — short quick-read"),
                    ("video", "Video"),
                    ("audio", "Audio / Podcast"),
                ],
                default="article",
                help_text="The FORMAT of the post: Lil & Lol = standard post, Bites = short quick-read, Video = video embed, Audio = podcast/audio embed. Use Tags below for TOPICS like Choices or Updates.",
                max_length=10,
            ),
        ),
        migrations.RunPython(seed_tags_and_migrate, remove_seeded_tags),
    ]
