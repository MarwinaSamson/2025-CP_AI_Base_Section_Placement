from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class SectionMasterlist(models.Model):
    """
    Stores uploaded section masterlist PDFs per program/section.
    """
    program = models.ForeignKey(
        'admin_app.Program',
        on_delete=models.CASCADE,
        related_name='section_masterlists',
        help_text="Program for which masterlist is uploaded"
    )
    section = models.CharField(
        max_length=100,
        help_text="Section name or code"
    )
    file = models.FileField(
        upload_to='section_masterlists/',
        help_text="PDF file of the section masterlist"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_masterlists',
        help_text="Coordinator who uploaded the masterlist"
    )
    upload_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when masterlist was uploaded"
    )
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


# Create your models here.

class Qualified_for_ste(models.Model):
    """
    Model to store students who are qualified for STE (Science, Technology, Engineering) program.
    Tracks exam scores, interview scores, and qualification status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('qualified', 'Qualified'),
        ('not_qualified', 'Not Qualified'),
        ('waitlisted', 'Waitlisted'),
    ]
    
    # Reference to student using LRN
    student_lrn = models.CharField(
        max_length=12,
        verbose_name="Student LRN",
        help_text="Learner Reference Number of the student"
    )
    
    # Scores
    exam_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Exam score (0-100)"
    )
    
    interview_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Interview score (0-100)"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current qualification status"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when record was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when record was last updated"
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ste_qualifications',
        help_text="User who last updated this record"
    )
    
    # Additional fields
    remarks = models.TextField(
        blank=True,
        null=True,
        help_text="Additional remarks or notes"
    )
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Qualified for STE'
        verbose_name_plural = 'Qualified for STE'
        db_table = 'qualified_for_ste'
        indexes = [
            models.Index(fields=['student_lrn']),
            models.Index(fields=['status']),
            models.Index(fields=['-updated_at']),
        ]
    
    def __str__(self):
        return f"{self.student_lrn} - {self.get_status_display()}"
    
    def get_total_score(self):
        """Calculate total score (exam + interview)"""
        return self.exam_score + self.interview_score
    
    def get_average_score(self):
        """Calculate average score"""
        return (self.exam_score + self.interview_score) / 2


class CoordinatorGeneratedReport(models.Model):
    """
    Stores generated reports from the coordinator reports module.
    Auto-deleted after 30 days to keep the database clean.
    """
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

    report_name = models.CharField(
        max_length=255,
        help_text="Display name of the report"
    )
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPE_CHOICES,
        help_text="Type of report generated"
    )
    file_format = models.CharField(
        max_length=10,
        choices=FILE_FORMAT_CHOICES,
        help_text="File format (PDF, Excel, Word)"
    )
    file = models.FileField(
        upload_to='coordinator_reports/',
        help_text="Generated report file"
    )
    file_size = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Human-readable file size"
    )
    program_code = models.CharField(
        max_length=20,
        help_text="Program code (STE, REGULAR, etc.)"
    )
    filter_used = models.CharField(
        max_length=100,
        blank=True,
        default='All',
        help_text="Filter applied when generating"
    )
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coordinator_reports',
        help_text="Coordinator who generated the report"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the report was generated"
    )

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
        """Return human-readable file size."""
        if self.file and self.file.storage.exists(self.file.name):
            size = self.file.size
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return self.file_size or 'N/A'


class AIAssistantPreference(models.Model):
    """
    Stores AI Assistant preferences per coordinator per program.
    Controls whether auto-approval and auto-assignment is enabled.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_preferences',
        help_text="Coordinator user"
    )
    
    program = models.ForeignKey(
        'admin_app.Program',
        on_delete=models.CASCADE,
        related_name='ai_preferences',
        help_text="Program for which AI preference is set"
    )
    
    ai_enabled = models.BooleanField(
        default=True,
        help_text="Whether AI assistant is enabled for this coordinator in this program"
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when preference was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when preference was last updated"
    )
    
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


class CoordinatorActivityLog(models.Model):
    """
    Comprehensive activity logging for all coordinator actions.
    Tracks enrollments, approvals, rejections, section assignments, report generation, etc.
    """
    
    # Action Categories with Icons
    ACTION_CHOICES = [
        # Enrollment Actions
        ('student_approved', 'Student Approved'),
        ('student_rejected', 'Student Rejected'),
        ('student_reverted', 'Enrollment Reverted'),
        ('batch_approved', 'Batch Approval'),
        ('batch_rejected', 'Batch Rejection'),
        
        # Section Actions
        ('section_assigned', 'Section Assigned'),
        ('section_transferred', 'Section Transfer'),
        ('section_created', 'Section Created'),
        ('section_updated', 'Section Updated'),
        ('masterlist_published', 'Masterlist Published'),
        ('masterlist_unpublished', 'Masterlist Unpublished'),
        
        # Student Management
        ('student_edited', 'Student Info Edited'),
        ('student_viewed', 'Student Profile Viewed'),
        ('grades_uploaded', 'Grades Uploaded'),
        ('results_uploaded', 'Results Uploaded'),
        
        # Report Actions
        ('report_generated', 'Report Generated'),
        ('report_downloaded', 'Report Downloaded'),
        ('template_downloaded', 'Template Downloaded'),
        
        # AI Actions
        ('ai_recommendation_applied', 'AI Recommendation Applied'),
        ('ai_recommendation_rejected', 'AI Recommendation Rejected'),
        
        # Other Actions
        ('login', 'Coordinator Login'),
        ('logout', 'Coordinator Logout'),
        ('settings_changed', 'Settings Changed'),
        ('masterlist_uploaded', 'Masterlist Uploaded'),
    ]
    
    # Action Category for filtering/icons
    CATEGORY_CHOICES = [
        ('enrollment', 'Enrollment'),
        ('section', 'Section'),
        ('student', 'Student'),
        ('report', 'Report'),
        ('ai', 'AI'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='coordinator_activity_logs',
        help_text="Coordinator who performed the action"
    )
    
    program = models.ForeignKey(
        'admin_app.Program',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='coordinator_activity_logs',
        help_text="Program context for the action"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='system',
        help_text="Category of the action for filtering"
    )
    
    description = models.TextField(
        help_text="Detailed description of the action"
    )
    
    # Related entities (optional)
    student_lrn = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="LRN of the student involved (if applicable)"
    )
    
    student_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Name of the student involved (if applicable)"
    )
    
    section_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Section involved (if applicable)"
    )
    
    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata about the action (JSON)"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the coordinator"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action was performed"
    )
    
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
        """Returns formatted date for display."""
        import datetime
        today = timezone.now().date()
        yesterday = today - datetime.timedelta(days=1)
        log_date = self.created_at.date()
        
        if log_date == today:
            return 'Today'
        elif log_date == yesterday:
            return 'Yesterday'
        else:
            days_ago = (today - log_date).days
            if days_ago < 7:
                return f'{days_ago} days ago'
            else:
                return self.created_at.strftime('%b %d, %Y')
    
    def get_formatted_time(self):
        """Returns formatted time for display."""
        return self.created_at.strftime('%I:%M %p')
    
    def get_icon_class(self):
        """Returns Font Awesome icon class based on action category."""
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
        """Returns color class based on action type."""
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
        else:
            return 'text-gray-600 bg-gray-100'
    
    @classmethod
    def log(cls, user, action, description, category='system', program=None, 
            student_lrn=None, student_name=None, section_name=None, 
            metadata=None, ip_address=None):
        """
        Convenience method to create a log entry.
        
        Usage:
            CoordinatorActivityLog.log(
                user=request.user,
                action='student_approved',
                description=f'Approved enrollment for {student_name}',
                category='enrollment',
                program=program,
                student_lrn=lrn,
                student_name=student_name
            )
        """
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
            ip_address=ip_address
        )
