"""
coordinator_app/models.py — FULLY UPDATED
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from enrollment_app.models import Student
from admin_app.models import Section, Program, Subject, GradeLevel, SchoolYear


# ===================================================================
# SECTION MASTERLIST
# ===================================================================
class SectionMasterlist(models.Model):
    program = models.ForeignKey(
        'admin_app.Program',
        on_delete=models.CASCADE,
        related_name='section_masterlists',
    )
    section = models.CharField(max_length=100)
    file = models.FileField(upload_to='section_masterlists/')
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='uploaded_masterlists',
    )
    upload_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-upload_date']
        db_table = 'section_masterlist'
        indexes = [
            models.Index(fields=['program']),
            models.Index(fields=['section']),
            models.Index(fields=['-upload_date']),
        ]

    def __str__(self):
        return f"{self.program} - {self.section} Masterlist ({self.upload_date:%Y-%m-%d})"


# ===================================================================
# ACADEMIC PERFORMANCE — UPDATED
# ===================================================================
class AcademicPerformance(models.Model):
    """
    CHANGES:
      - Added school_year FK — distinguishes Grade 7 Q1 Math in SY 2023-2024
        from the same in SY 2024-2025.
      - Removed ambiguous `average` field — a single quarter record has nothing
        to average. Use get_annual_average() instead.
      - unique_together updated to include school_year.
      - get_annual_average() helper computes across all 4 quarters for a
        given student + subject + grade_level + school_year.

    Subject is still scoped to Program only (not GradeLevel).
    Math in Grade 7 STE and Math in Grade 9 STE are the same Subject row.
    The grade dimension is carried by this model's grade_level FK.
    """

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='academic_performances'
    )
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name='academic_performances'
    )
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name='academic_performances'
    )
    grade_level = models.ForeignKey(
        GradeLevel, on_delete=models.CASCADE, related_name='academic_performances'
    )

    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name='academic_performances',
        null=True, blank=True,
        help_text="School year this performance record belongs to"
    )

    subject = models.ForeignKey(
        Subject, on_delete=models.CASCADE, related_name='academic_performances'
    )
    quarter = models.PositiveSmallIntegerField(
        choices=[(i, f'Quarter {i}') for i in range(1, 5)],
    )
    grade = models.DecimalField(max_digits=5, decimal_places=2)

    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'school_year', 'grade_level', 'subject', 'quarter')
        ordering = ['student', 'grade_level', 'school_year', 'quarter', 'subject']
        db_table = 'academic_performance'
        indexes = [
            models.Index(fields=['student']),
            models.Index(fields=['section']),
            models.Index(fields=['program']),
            models.Index(fields=['grade_level']),
            models.Index(fields=['quarter']),
            models.Index(fields=['school_year']),
        ]

    def __str__(self):
        sy = self.school_year.year_label if self.school_year else 'No Year'
        return (
            f"{self.student.lrn} | {sy} | {self.grade_level.name} "
            f"| {self.subject.code} | Q{self.quarter}: {self.grade}"
        )

    def clean(self):
        if self.grade is not None and (self.grade < 0 or self.grade > 100):
            raise ValidationError({'grade': 'Grade must be between 0 and 100.'})
        if self.quarter not in [1, 2, 3, 4]:
            raise ValidationError({'quarter': 'Quarter must be 1, 2, 3, or 4.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_annual_average(self):
        """
        Computes the annual average across all quarters for this student + subject
        within the same school year and grade level.
        Returns a rounded Decimal or None if no records found.
        """
        records = AcademicPerformance.objects.filter(
            student=self.student,
            subject=self.subject,
            grade_level=self.grade_level,
            school_year=self.school_year,
        ).exclude(grade__isnull=True)

        grades = list(records.values_list('grade', flat=True))
        if not grades:
            return None
        return round(sum(grades) / len(grades), 2)


# ===================================================================
# QUALIFIED FOR STE — UPDATED
# ===================================================================
class Qualified_for_ste(models.Model):
    """
    CHANGES:
      - Added grade_level FK — a Grade 9 STE transferee can sit the exam
        separately from a Grade 7 new student.
      - Added school_year FK — ties the qualification to an enrollment cycle.
      - Added unique_together (student_lrn, grade_level, school_year) —
        prevents duplicate qualification records for the same student
        in the same grade and year.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('qualified', 'Qualified'),
        ('not_qualified', 'Not Qualified'),
        ('waitlisted', 'Waitlisted'),
    ]

    student_lrn = models.CharField(max_length=12, verbose_name="Student LRN")

    exam_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    interview_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    grade_level = models.ForeignKey(
        GradeLevel,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ste_qualifications',
        help_text="Grade level this qualification is for (e.g. Grade 7 or Grade 9 transferee)"
    )
    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='ste_qualifications',
        help_text="School year this qualification belongs to"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ste_qualifications',
    )

    remarks = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Qualified for STE'
        verbose_name_plural = 'Qualified for STE'
        db_table = 'qualified_for_ste'
        unique_together = [('student_lrn', 'grade_level', 'school_year')]
        indexes = [
            models.Index(fields=['student_lrn']),
            models.Index(fields=['status']),
            models.Index(fields=['-updated_at']),
            models.Index(fields=['grade_level']),
            models.Index(fields=['school_year']),
        ]

    def __str__(self):
        grade = self.grade_level.name if self.grade_level else 'Unknown Grade'
        sy = self.school_year.year_label if self.school_year else 'Unknown Year'
        return f"{self.student_lrn} | {grade} | {sy} - {self.get_status_display()}"

    def get_total_score(self):
        return self.exam_score + self.interview_score

    def get_average_score(self):
        return (self.exam_score + self.interview_score) / 2


# ===================================================================
# COORDINATOR GENERATED REPORT
# ===================================================================
class CoordinatorGeneratedReport(models.Model):
    REPORT_TYPE_CHOICES = [
        ('enrollment', 'Enrollment Report'),
        ('academic', 'Academic Performance Report'),
        ('sections', 'Section Assignment Report'),
        ('custom', 'Custom Report'),
    ]
    FILE_FORMAT_CHOICES = [
        ('PDF', 'PDF Document'),
        ('Excel', 'Excel Spreadsheet'),
        ('Word', 'Word Document'),
    ]

    report_name = models.CharField(max_length=255)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    file_format = models.CharField(max_length=10, choices=FILE_FORMAT_CHOICES)
    file = models.FileField(upload_to='coordinator_reports/')
    file_size = models.CharField(max_length=20, blank=True, default='')
    program_code = models.CharField(max_length=20)
    filter_used = models.CharField(max_length=100, blank=True, default='All')
    generated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coordinator_reports',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coor_generated_report'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['program_code']),
            models.Index(fields=['generated_by']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.report_name} ({self.created_at:%Y-%m-%d %H:%M})"

    def get_file_size_display(self):
        if self.file and self.file.storage.exists(self.file.name):
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return self.file_size or 'N/A'


# ===================================================================
# AI ASSISTANT PREFERENCE
# ===================================================================
class AIAssistantPreference(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='ai_preferences'
    )
    program = models.ForeignKey(
        'admin_app.Program', on_delete=models.CASCADE, related_name='ai_preferences'
    )
    ai_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_assistant_preference'
        ordering = ['-updated_at']
        unique_together = [('user', 'program')]
        indexes = [
            models.Index(fields=['user', 'program']),
            models.Index(fields=['user']),
            models.Index(fields=['program']),
        ]

    def __str__(self):
        status = "Enabled" if self.ai_enabled else "Disabled"
        return f"{self.user.username} - {self.program.code} - AI {status}"


# ===================================================================
# COORDINATOR ACTIVITY LOG
# ===================================================================
class CoordinatorActivityLog(models.Model):
    ACTION_CHOICES = [
        ('student_approved', 'Student Approved'),
        ('student_rejected', 'Student Rejected'),
        ('student_reverted', 'Enrollment Reverted'),
        ('batch_approved', 'Batch Approval'),
        ('batch_rejected', 'Batch Rejection'),
        ('section_assigned', 'Section Assigned'),
        ('section_transferred', 'Section Transfer'),
        ('section_created', 'Section Created'),
        ('section_updated', 'Section Updated'),
        ('masterlist_published', 'Masterlist Published'),
        ('masterlist_unpublished', 'Masterlist Unpublished'),
        ('student_edited', 'Student Info Edited'),
        ('student_viewed', 'Student Profile Viewed'),
        ('grades_uploaded', 'Grades Uploaded'),
        ('results_uploaded', 'Results Uploaded'),
        ('report_generated', 'Report Generated'),
        ('report_downloaded', 'Report Downloaded'),
        ('template_downloaded', 'Template Downloaded'),
        ('ai_recommendation_applied', 'AI Recommendation Applied'),
        ('ai_recommendation_rejected', 'AI Recommendation Rejected'),
        ('login', 'Coordinator Login'),
        ('logout', 'Coordinator Logout'),
        ('settings_changed', 'Settings Changed'),
        ('masterlist_uploaded', 'Masterlist Uploaded'),
    ]

    CATEGORY_CHOICES = [
        ('enrollment', 'Enrollment'),
        ('section', 'Section'),
        ('student', 'Student'),
        ('report', 'Report'),
        ('ai', 'AI'),
        ('system', 'System'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='coordinator_activity_logs',
    )
    program = models.ForeignKey(
        'admin_app.Program', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='coordinator_activity_logs',
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='system')
    description = models.TextField()
    student_lrn = models.CharField(max_length=20, blank=True, null=True)
    student_name = models.CharField(max_length=255, blank=True, null=True)
    section_name = models.CharField(max_length=100, blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Coordinator Activity Log'
        verbose_name_plural = 'Coordinator Activity Logs'
        db_table = 'coordinator_activity_log'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['category']),
            models.Index(fields=['user']),
            models.Index(fields=['program']),
            models.Index(fields=['student_lrn']),
        ]

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'System'
        return f"{user_name} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def get_formatted_date(self):
        import datetime
        today = timezone.now().date()
        yesterday = today - datetime.timedelta(days=1)
        log_date = self.created_at.date()
        if log_date == today:
            return 'Today'
        elif log_date == yesterday:
            return 'Yesterday'
        days_ago = (today - log_date).days
        if days_ago < 7:
            return f'{days_ago} days ago'
        return self.created_at.strftime('%b %d, %Y')

    def get_formatted_time(self):
        return self.created_at.strftime('%I:%M %p')

    def get_icon_class(self):
        icon_map = {
            'enrollment': 'fa-user-check',
            'section': 'fa-users-cog',
            'student': 'fa-user-edit',
            'report': 'fa-file-alt',
            'ai': 'fa-robot',
            'system': 'fa-cog',
        }
        return icon_map.get(self.category, 'fa-circle')

    def get_color_class(self):
        if 'approved' in self.action or 'created' in self.action:
            return 'text-green-600 bg-green-100'
        elif 'rejected' in self.action:
            return 'text-red-600 bg-red-100'
        elif 'transferred' in self.action or 'assigned' in self.action:
            return 'text-blue-600 bg-blue-100'
        elif 'report' in self.action or 'downloaded' in self.action:
            return 'text-purple-600 bg-purple-100'
        elif 'ai' in self.action:
            return 'text-yellow-600 bg-yellow-100'
        return 'text-gray-600 bg-gray-100'

    @classmethod
    def log(cls, user, action, description, category='system', program=None,
            student_lrn=None, student_name=None, section_name=None,
            metadata=None, ip_address=None):
        return cls.objects.create(
            user=user,
            action=action,
            description=description,
            category=category,
            program=program,
            student_lrn=student_lrn,
            student_name=student_name,
            section_name=section_name,
            metadata=metadata or {},
            ip_address=ip_address,
        )