# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0002_add_poll_fields_and_rename_choice'),
    ]

    operations = [
        migrations.AddField(
            model_name='poll',
            name='is_draft',
            field=models.BooleanField(default=False, help_text='If True, poll is a draft and not visible publicly'),
        ),
        migrations.AddIndex(
            model_name='poll',
            index=models.Index(fields=['is_draft', 'created_by'], name='polls_poll_is_draf_idx'),
        ),
    ]

