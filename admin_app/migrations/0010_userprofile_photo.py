# Generated migration for UserProfile photo field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0009_schoolyear_alter_section_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='photo',
            field=models.ImageField(blank=True, help_text='User profile photo', null=True, upload_to='user_profiles/'),
        ),
    ]
