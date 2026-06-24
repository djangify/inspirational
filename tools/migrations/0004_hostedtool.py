import inspirational.storage
import tools.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0003_rename_liveitlistitem_alivelistitem'),
    ]

    operations = [
        migrations.CreateModel(
            name='HostedTool',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(blank=True, help_text='Used in the public URL: /tools/<slug>/ . Leave blank to auto-fill from the title.', max_length=200, unique=True)),
                ('description', models.TextField(blank=True, help_text='Optional short caption shown above the tool on its public page.')),
                ('html_file', models.FileField(help_text='Upload the single .html file. Hit save and it goes live at the URL above.', storage=inspirational.storage.SecureFileStorage(), upload_to='hosted_tools/', validators=[tools.models.validate_html])),
                ('published', models.BooleanField(default=True, help_text='Untick to take the tool offline without deleting it.')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Hosted Tool',
                'verbose_name_plural': 'Hosted Tools',
                'ordering': ['title'],
            },
        ),
    ]
