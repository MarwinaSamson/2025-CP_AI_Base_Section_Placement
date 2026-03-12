from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0001_initial'),
        ('coordinator_app', '0008_remove_probationrecord_unique_probation_per_student_grade_year_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GradeUploadBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quarter', models.PositiveSmallIntegerField(choices=[(1, 'Quarter 1'), (2, 'Quarter 2'), (3, 'Quarter 3'), (4, 'Quarter 4')])),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('original_filename', models.CharField(blank=True, max_length=255)),
                ('status', models.CharField(
                    choices=[('processing', 'Processing'), ('done', 'Done'), ('partial', 'Partial — some rows failed'), ('failed', 'Failed')],
                    default='processing', max_length=20,
                )),
                ('total_rows', models.PositiveIntegerField(default=0)),
                ('rows_saved', models.PositiveIntegerField(default=0)),
                ('rows_failed', models.PositiveIntegerField(default=0)),
                ('error_log', models.TextField(blank=True)),
                ('grade_level', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='grade_upload_batches',
                    to='admin_app.gradelevel',
                )),
                ('program', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='grade_upload_batches',
                    to='admin_app.program',
                )),
                ('school_year', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='grade_upload_batches',
                    to='admin_app.schoolyear',
                )),
                ('section', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='grade_upload_batches',
                    to='admin_app.section',
                )),
                ('uploaded_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='grade_upload_batches',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'db_table': 'grade_upload_batch',
                'ordering': ['-uploaded_at'],
                'indexes': [
                    models.Index(fields=['section', 'quarter'], name='grade_batch_section_q_idx'),
                    models.Index(fields=['-uploaded_at'], name='grade_batch_uploaded_idx'),
                ],
            },
        ),
        migrations.AddField(
            model_name='academicperformance',
            name='upload_batch',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='performances',
                to='coordinator_app.gradeuploadbatch',
                help_text='The upload batch that created or last updated this record',
            ),
        ),
    ]
