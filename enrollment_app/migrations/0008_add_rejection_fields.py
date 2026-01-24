# Generated migration for adding rejection fields to ProgramSelection

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment_app', '0007_studentdata_age_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='programselection',
            name='admin_rejected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='programselection',
            name='rejected_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='programselection',
            name='rejected_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='programselection',
            name='rejection_reason',
            field=models.TextField(blank=True, null=True),
        ),
    ]
