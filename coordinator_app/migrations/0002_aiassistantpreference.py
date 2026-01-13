# Generated migration for AIAssistantPreference model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0011_documentrequirement'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('coordinator_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AIAssistantPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ai_enabled', models.BooleanField(default=True, help_text='Whether AI assistant is enabled for this coordinator in this program')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Date and time when preference was created')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Date and time when preference was last updated')),
                ('program', models.ForeignKey(help_text='Program for which AI preference is set', on_delete=django.db.models.deletion.CASCADE, related_name='ai_preferences', to='admin_app.program')),
                ('user', models.ForeignKey(help_text='Coordinator user', on_delete=django.db.models.deletion.CASCADE, related_name='ai_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ai_assistant_preference',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddIndex(
            model_name='aiassistantpreference',
            index=models.Index(fields=['user', 'program'], name='ai_assista_user_id_program_9a3f5e_idx'),
        ),
        migrations.AddIndex(
            model_name='aiassistantpreference',
            index=models.Index(fields=['user'], name='ai_assista_user_id_1b2c3d_idx'),
        ),
        migrations.AddIndex(
            model_name='aiassistantpreference',
            index=models.Index(fields=['program'], name='ai_assista_program_4e5f6g_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='aiassistantpreference',
            unique_together={('user', 'program')},
        ),
    ]
