# Generated migration for SystemSettings and HeaderLogo models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0002_contentmanagement'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('setting_type', models.CharField(
                    choices=[
                        ('header', 'Header Settings'),
                        ('announcement', 'Announcement'),
                        ('services', 'Services'),
                        ('contact', 'Contact Information'),
                        ('members', 'Members/Staff'),
                        ('footer', 'Footer Settings'),
                    ],
                    help_text='Type of setting',
                    max_length=50
                )),
                ('key', models.CharField(
                    help_text='Unique key for this setting',
                    max_length=100,
                    unique=True
                )),
                ('value', models.TextField(
                    blank=True,
                    help_text='The setting value (can be JSON)',
                    null=True
                )),
                ('description', models.TextField(
                    blank=True,
                    help_text='Description of this setting',
                    null=True
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    help_text='When this setting was created'
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    help_text='When this setting was last updated'
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Whether this setting is active'
                )),
                ('updated_by', models.ForeignKey(
                    blank=True,
                    help_text='User who last updated this setting',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='system_settings_updates',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'System Setting',
                'verbose_name_plural': 'System Settings',
                'db_table': 'system_settings',
                'ordering': ['setting_type', 'key'],
            },
        ),
        migrations.CreateModel(
            name='HeaderLogo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('logo_type', models.CharField(
                    choices=[
                        ('school', 'School Logo'),
                        ('region', 'Region IX Logo'),
                        ('peninsula', 'Zamboanga Peninsula'),
                        ('matatag', 'Matatag Logo'),
                    ],
                    help_text='Type of logo',
                    max_length=50,
                    unique=True
                )),
                ('image', models.ImageField(
                    help_text='Logo image file',
                    upload_to='logos/'
                )),
                ('alt_text', models.CharField(
                    help_text='Alternative text for the logo',
                    max_length=255
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='Whether this logo is currently displayed'
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True,
                    help_text='When this logo was uploaded'
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True,
                    help_text='When this logo was last updated'
                )),
                ('uploaded_by', models.ForeignKey(
                    blank=True,
                    help_text='User who uploaded this logo',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='uploaded_logos',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'verbose_name': 'Header Logo',
                'verbose_name_plural': 'Header Logos',
                'db_table': 'header_logo',
                'ordering': ['logo_type'],
            },
        ),
        migrations.AddConstraint(
            model_name='systemsettings',
            constraint=models.UniqueConstraint(
                fields=['setting_type', 'key'],
                name='unique_setting_type_key'
            ),
        ),
        migrations.AddIndex(
            model_name='systemsettings',
            index=models.Index(fields=['setting_type'], name='system_settings_setting_type_idx'),
        ),
        migrations.AddIndex(
            model_name='systemsettings',
            index=models.Index(fields=['key'], name='system_settings_key_idx'),
        ),
        migrations.AddIndex(
            model_name='systemsettings',
            index=models.Index(fields=['is_active'], name='system_settings_is_active_idx'),
        ),
    ]
