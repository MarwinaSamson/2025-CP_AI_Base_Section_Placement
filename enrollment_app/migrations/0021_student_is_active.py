# Generated migration to add is_active field to Student

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('enrollment_app', '0020_studentenrollment_studentacademicyearstatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='is_active',
            field=models.BooleanField(
                default=True,
                help_text='False if student has graduated, dropped out, or is otherwise inactive'
            ),
        ),
    ]
