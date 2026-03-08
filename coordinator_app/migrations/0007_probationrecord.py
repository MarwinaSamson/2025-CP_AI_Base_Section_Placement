"""
Creates the probation_record table used to track students who are
moved from a special program (SPFL / SPTVE / STE) to Regular because
they fell below the academic retention threshold.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0017_seed_grade_levels'),
        ('coordinator_app', '0006_academicperformance_qualified_for_ste_grade_level_and_more'),
        ('enrollment_app', '0012_rename_program_sel_assigne_c4a54f_idx_program_sel_assigne_ffbd3e_idx_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ProbationRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_program', models.CharField(
                    max_length=20,
                    help_text='Program the student was in before probation (e.g. SPFL, SPTVE, STE).',
                )),
                ('moved_to_program', models.CharField(
                    max_length=20,
                    default='REGULAR',
                    help_text='Program they are reassigned to — almost always REGULAR.',
                )),
                ('reason', models.TextField(
                    help_text='Human-readable explanation of why probation was triggered.',
                )),
                ('is_active', models.BooleanField(
                    default=True,
                    help_text='True while probation is enforced. Set to False when reinstated.',
                )),
                ('reinstated_at', models.DateTimeField(null=True, blank=True)),
                ('reinstatement_reason', models.TextField(blank=True, null=True)),
                ('flagged_at', models.DateTimeField(auto_now_add=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='probation_records',
                    to='enrollment_app.student',
                    help_text='Student who is on academic probation.',
                )),
                ('school_year', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='probation_records',
                    to='admin_app.schoolyear',
                    help_text='School year in which the probation was assessed.',
                )),
                ('grade_level', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='probation_records',
                    to='admin_app.gradelevel',
                    help_text='Grade level where the student failed the retention threshold.',
                )),
                ('flagged_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='flagged_probations',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('reinstated_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reinstated_probations',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Probation Record',
                'verbose_name_plural': 'Probation Records',
                'db_table': 'probation_record',
                'ordering': ['-flagged_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='probationrecord',
            constraint=models.UniqueConstraint(
                fields=['student', 'school_year', 'grade_level'],
                name='unique_probation_per_student_grade_year',
            ),
        ),
        migrations.AddIndex(
            model_name='probationrecord',
            index=models.Index(fields=['student'], name='probation_student_idx'),
        ),
        migrations.AddIndex(
            model_name='probationrecord',
            index=models.Index(fields=['school_year'], name='probation_school_year_idx'),
        ),
        migrations.AddIndex(
            model_name='probationrecord',
            index=models.Index(fields=['grade_level'], name='probation_grade_level_idx'),
        ),
        migrations.AddIndex(
            model_name='probationrecord',
            index=models.Index(fields=['is_active'], name='probation_is_active_idx'),
        ),
        migrations.AddIndex(
            model_name='probationrecord',
            index=models.Index(fields=['-flagged_at'], name='probation_flagged_at_idx'),
        ),
    ]
