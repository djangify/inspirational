from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_supportrequest"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="oto_seen_at",
            field=models.DateTimeField(
                blank=True,
                help_text="When the one-time offer was first shown to this user. Set once; ensures the offer is strictly one-time.",
                null=True,
            ),
        ),
    ]
