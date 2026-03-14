# Generated migration for StudentEnrollment and StudentAcademicYearStatus

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('admin_app', '0001_initial'),  # Adjust to match your latest admin_app migration
        ('enrollment_app', '0012_rename_program_sel_assigne_c4a54f_idx_program_sel_assigne_ffbd3e_idx_and_more'),  # Fixed: changed from 0019_latest to actual last migration
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Create StudentEnrollment table
        migrations.CreateModel(
            name='StudentEnrollment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrollee_type', models.CharField(
                    choices=[
                        ('new', 'New (Incoming Grade 7)'),
                        ('continuing', 'Continuing (Old Student — Same School)'),
                        ('transferee', 'Transferee (From Another School)'),
                        ('returnee', 'Returnee'),
                    ],
                    default='new',
                    help_text='Drives which enrollment steps are required',
                    max_length=20,
                )),
                ('enrollment_status', models.CharField(
                    choices=[
                        ('draft', 'Draft'),
                        ('submitted', 'Submitted'),
                        ('under_review', 'Under Review'),
                        ('approved', 'Approved'),
                        ('rejected', 'Rejected'),
                    ],
                    default='draft',
                    max_length=20,
                )),
                ('student_data_completed', models.BooleanField(default=False)),
                ('student_data_completed_at', models.DateTimeField(blank=True, null=True)),
                ('family_data_completed', models.BooleanField(default=False)),
                ('family_data_completed_at', models.DateTimeField(blank=True, null=True)),
                ('survey_completed', models.BooleanField(default=False)),
                ('survey_completed_at', models.DateTimeField(blank=True, null=True)),
                ('academic_data_completed', models.BooleanField(default=False)),
                ('academic_data_completed_at', models.DateTimeField(blank=True, null=True)),
                ('program_selected', models.BooleanField(default=False)),
                ('program_selected_at', models.DateTimeField(blank=True, null=True)),
                ('documents_completed', models.BooleanField(default=False)),
                ('documents_completed_at', models.DateTimeField(blank=True, null=True)),
                ('is_locked', models.BooleanField(default=False, help_text='Prevents duplicate submissions')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('grade_level', models.ForeignKey(
                    blank=True,
                    help_text='Grade level the student is enrolled in',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='enrollments',
                    to='admin_app.gradelevel',
                )),
                ('school_year', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_enrollments',
                    to='admin_app.schoolyear',
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='enrollments',
                    to='enrollment_app.student',
                )),
            ],
            options={
                'db_table': 'student_enrollment',
            },
        ),

        # Create StudentAcademicYearStatus table
        migrations.CreateModel(
            name='StudentAcademicYearStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('final_status', models.CharField(
                    choices=[
                        ('promoted', 'Promoted to Next Grade'),
                        ('retained', 'Retained in Same Grade'),
                        ('transferred', 'Transferred Out'),
                        ('graduated', 'Graduated'),
                        ('dropped_out', 'Dropped Out'),
                        ('pending', 'Pending Final Assessment'),
                    ],
                    help_text='Final academic outcome for the year (promoted/retained/graduated/etc.)',
                    max_length=20,
                )),
                ('overall_grade', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    help_text='Average grade for the entire school year',
                    max_digits=5,
                    null=True,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(100),
                    ],
                )),
                ('remarks', models.TextField(
                    blank=True,
                    help_text="Optional remarks about student performance (e.g., 'Excellent in Math', 'Needs support')",
                    null=True,
                )),
                ('recorded_at', models.DateTimeField(
                    auto_now_add=True,
                    help_text='When the final status was recorded',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('grade_level', models.ForeignKey(
                    blank=True,
                    help_text='Grade level the student was in during this school year',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='academic_statuses',
                    to='admin_app.gradelevel',
                )),
                ('recorded_by', models.ForeignKey(
                    blank=True,
                    help_text='Section adviser (Teacher) who finalized this status',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='recorded_student_statuses',
                    to='admin_app.teacher',
                )),
                ('school_year', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_academic_statuses',
                    to='admin_app.schoolyear',
                )),
                ('section', models.ForeignKey(
                    blank=True,
                    help_text='Section the student was assigned to',
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='academic_statuses',
                    to='admin_app.section',
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='academic_year_statuses',
                    to='enrollment_app.student',
                )),
            ],
            options={
                'db_table': 'student_academic_year_status',
            },
        ),

        # Add unique constraints
        migrations.AddConstraint(
            model_name='studentenrollment',
            constraint=models.UniqueConstraint(
                fields=['student', 'school_year'],
                name='unique_student_enrollment_per_year',
            ),
        ),
        migrations.AddConstraint(
            model_name='studentacademicyearstatus',
            constraint=models.UniqueConstraint(
                fields=['student', 'school_year'],
                name='unique_academic_status_per_year',
            ),
        ),

        # Add indexes
        migrations.AddIndex(
            model_name='studentenrollment',
            index=models.Index(
                fields=['student', 'school_year'],
                name='student_enrollment_student_school_year_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='studentenrollment',
            index=models.Index(
                fields=['school_year', 'enrollment_status'],
                name='student_enrollment_school_status_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='studentenrollment',
            index=models.Index(fields=['grade_level'], name='student_enrollment_grade_idx'),
        ),
        migrations.AddIndex(
            model_name='studentenrollment',
            index=models.Index(fields=['enrollee_type'], name='student_enrollment_type_idx'),
        ),
        migrations.AddIndex(
            model_name='studentenrollment',
            index=models.Index(
                fields=['enrollment_status'],
                name='student_enrollment_status_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='studentacademicyearstatus',
            index=models.Index(
                fields=['student', 'school_year'],
                name='academic_status_student_year_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='studentacademicyearstatus',
            index=models.Index(
                fields=['school_year', 'final_status'],
                name='academic_status_year_status_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='studentacademicyearstatus',
            index=models.Index(
                fields=['final_status'],
                name='academic_status_status_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='studentacademicyearstatus',
            index=models.Index(
                fields=['recorded_by'],
                name='academic_status_adviser_idx',
            ),
        ),
    ]
