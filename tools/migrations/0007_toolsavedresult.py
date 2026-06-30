# Generated manually 2026-06-30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0006_hostedtool_link_text_hostedtool_link_url'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ToolSavedResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tool_slug', models.SlugField(help_text='Slug of the HostedTool that created this result.', max_length=200)),
                ('tool_title', models.CharField(blank=True, help_text='Human-readable tool name, captured at save time.', max_length=200)),
                ('label', models.CharField(help_text="Short name for this result, e.g. 'My top 3 values'.", max_length=300)),
                ('data', models.JSONField(default=dict, help_text='Arbitrary JSON payload from the tool.')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tool_saved_results',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]
