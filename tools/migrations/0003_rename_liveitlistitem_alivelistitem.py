import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0002_liveitlistitem'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='LiveItListItem',
            new_name='AliveListItem',
        ),
        migrations.AlterField(
            model_name='alivelistitem',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='alive_list_items',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
