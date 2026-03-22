"""
admin_app/models.py — FULLY UPDATED
"""

from django.db import models
from django.utils import timezone
import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


# ===================================================================
# GRADE LEVEL
# ===================================================================
class GradeLevel(models.Model):
    """Represents a grade level (Grade 7, Grade 8, Grade 9, Grade 10)."""
    code = models.CharField(
        max_length=10, unique=True,
        help_text="Short code (e.g. G7, G8, G9, G10)"
    )
    name = models.CharField(
        max_length=50, unique=True,
        help_text="Full name (e.g. Grade 7, Grade 8)"
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        db_table = 'grade_level'
        verbose_name = 'Grade Level'
        verbose_name_plural = 'Grade Levels'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name


# ===================================================================
# POSITION
# ===================================================================
class Position(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'
        db_table = 'position'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError({'name': 'Position name cannot be empty or just whitespace.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_user_count(self):
        return self.userprofile_set.count()

    def can_delete(self):
        return self.get_user_count() == 0

    def get_formatted_date(self):
        return self.created_at.strftime('%b %d, %Y')


# ===================================================================
# DEPARTMENT
# ===================================================================
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        db_table = 'department'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError({'name': 'Department name cannot be empty or just whitespace.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_user_count(self):
        return self.userprofile_set.count()

    def can_delete(self):
        return self.get_user_count() == 0

    def get_formatted_date(self):
        return self.created_at.strftime('%b %d, %Y')


# ===================================================================
# PROGRAM
# ===================================================================
class Program(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'
        db_table = 'program'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        if self.code:
            self.code = self.code.strip().upper()
        if not self.code:
            raise ValidationError({'code': 'Program code cannot be empty or just whitespace.'})
        if self.name:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError({'name': 'Program name cannot be empty or just whitespace.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_user_count(self):
        return self.userprofile_set.count()

    def can_delete(self):
        return self.get_user_count() == 0

    def get_formatted_date(self):
        return self.created_at.strftime('%b %d, %Y')


# ===================================================================
# TEACHER
# ===================================================================
class Teacher(models.Model):
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)

    position = models.ForeignKey(
        Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='teachers'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='teachers'
    )

    address = models.TextField(blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True)

    is_adviser = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Teacher'
        verbose_name_plural = 'Teachers'
        db_table = 'teacher'
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['email']),
            models.Index(fields=['is_adviser']),
        ]

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        parts = [self.first_name or '',
                 self.middle_name or '', self.last_name or '']
        return ' '.join(p for p in parts if p).strip()

    def clean(self):
        if self.first_name:
            self.first_name = self.first_name.strip()
        if self.middle_name:
            self.middle_name = self.middle_name.strip()
        if self.last_name:
            self.last_name = self.last_name.strip()
        if self.email:
            self.email = self.email.strip().lower()
        if not self.first_name:
            raise ValidationError({'first_name': 'First name is required.'})
        if not self.last_name:
            raise ValidationError({'last_name': 'Last name is required.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ===================================================================
# SUBJECT
# ===================================================================
class Subject(models.Model):
    """
    Subject is scoped to Program only (not GradeLevel).
    Math in Grade 7 STE and Math in Grade 9 STE are the same Subject row.
    The grade dimension is carried by AcademicPerformance.grade_level.
    """
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_threshold_subject = models.BooleanField(
        default=False,
        help_text=(
            "STE only — if True, student must score >= 83 in this subject "
            "to avoid probation. Applies to Math, Science, English, Research "
            "and any future STE specialized subjects."
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['program__code', 'name']
        unique_together = [('program', 'code')]
        db_table = 'subject'
        indexes = [
            models.Index(fields=['program', 'code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.program.code})"

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if self.code:
            self.code = self.code.strip().upper()
        if not self.name:
            raise ValidationError({'name': 'Subject name is required.'})
        if not self.code:
            raise ValidationError({'code': 'Subject code is required.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ===================================================================
# SECTION — UPDATED
# ===================================================================
class Section(models.Model):
    """
    CHANGES:
      - Added grade_level FK so sections are properly scoped:
        "STE Grade 7 Einstein" vs "STE Grade 9 Einstein" are distinct records.
      - unique_together now includes grade_level.
      - update_current_students_count() and get_actual_count() simplified
        because ProgramSelection.assigned_section is now a real FK.
      - __str__ includes grade level label.
    """

    school_year = models.ForeignKey(
        'SchoolYear',
        on_delete=models.CASCADE,
        related_name='sections',
        null=True, blank=True,
    )
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name='sections'
    )

    grade_level = models.ForeignKey(
        GradeLevel,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sections',
        help_text="Grade level this section handles (e.g. Grade 7, Grade 8)"
    )

    name = models.CharField(max_length=100)
    regular_track = models.CharField(
        max_length=20, blank=True, null=True,
        help_text="For Regular program sections: TOP5 or HETERO"
    )
    adviser = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='advisory_sections',
    )
    building = models.CharField(max_length=50, blank=True, null=True)
    room = models.CharField(max_length=50, blank=True, null=True)
    max_students = models.PositiveIntegerField(default=40)
    current_students = models.PositiveIntegerField(default=0)
    masterlist_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['school_year', 'program__code', 'grade_level__code', 'created_at']
        unique_together = [('school_year', 'program', 'grade_level', 'name')]
        db_table = 'section'
        indexes = [
            models.Index(fields=['school_year', 'program', 'name']),
            models.Index(fields=['school_year']),
            models.Index(fields=['adviser']),
            models.Index(fields=['grade_level']),
        ]

    def __str__(self):
        year_label = self.school_year.year_label if self.school_year else 'No Year'
        grade_label = self.grade_level.name if self.grade_level else 'No Grade'
        track_info = f" ({self.regular_track})" if self.regular_track else ""
        return f"{year_label} - {grade_label} - {self.program.code}{track_info} - {self.name}"

    def update_current_students_count(self):
        """Recount enrolled students using the real FK — no string coercion needed."""
        from enrollment_app.models import ProgramSelection
        actual_count = ProgramSelection.objects.filter(
            assigned_section=self,
            admin_approved=True
        ).count()
        self.current_students = actual_count
        self.save(update_fields=['current_students'])
        return actual_count

    def get_actual_count(self):
        from enrollment_app.models import ProgramSelection
        return ProgramSelection.objects.filter(
            assigned_section=self,
            admin_approved=True
        ).count()

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError({'name': 'Section name is required.'})
        if self.max_students <= 0:
            raise ValidationError({'max_students': 'Maximum students must be positive.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ===================================================================
# ACTIVITY LOG
# ===================================================================
class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('user_added', 'User Added'),
        ('user_updated', 'User Updated'),
        ('user_deleted', 'User Deleted'),
        ('permission_changed', 'Permission Changed'),
        ('position_added', 'Position Added'),
        ('position_updated', 'Position Updated'),
        ('position_deleted', 'Position Deleted'),
        ('department_added', 'Department Added'),
        ('department_updated', 'Department Updated'),
        ('department_deleted', 'Department Deleted'),
        ('program_added', 'Program Added'),
        ('program_updated', 'Program Updated'),
        ('program_deleted', 'Program Deleted'),
        ('content_updated', 'Content Updated'),
        ('settings_changed', 'Settings Changed'),
    ]

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='activity_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        db_table = 'activity_log'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['action']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        user_name = self.user.get_full_name() if self.user else 'System'
        return f"{user_name} - {self.get_action_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def get_formatted_date(self):
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
            return self.created_at.strftime('%b %d, %Y')

    def get_formatted_time(self):
        return self.created_at.strftime('%I:%M %p')


# ===================================================================
# USER PROFILE
# ===================================================================
class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('coordinator', 'Coordinator'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)

    program = models.ForeignKey(
        Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='userprofile_set'
    )
    position = models.ForeignKey(
        Position, on_delete=models.SET_NULL, null=True, blank=True, related_name='userprofile_set'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='userprofile_set'
    )

    employee_id = models.CharField(max_length=50, unique=True)
    photo = models.ImageField(upload_to='user_profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profile'

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"

    def get_user_type_display(self):
        return {'admin': 'Admin', 'coordinator': 'Coordinator'}.get(self.user_type, self.user_type)

    def get_program_name(self):
        return self.program.code if self.program else 'N/A'

    def get_position_name(self):
        return self.position.name if self.position else 'N/A'

    def get_department_name(self):
        return self.department.name if self.department else 'N/A'

    def get_access_badges(self):
        return ['Admin'] if self.user_type == 'admin' else ['Coordinator']

    def get_last_login_formatted(self):
        if not self.user.last_login:
            return 'Never'
        today = timezone.now().date()
        yesterday = today - datetime.timedelta(days=1)
        login_date = self.user.last_login.date()
        if login_date == today:
            return f"Today, {self.user.last_login.strftime('%I:%M %p')}"
        elif login_date == yesterday:
            return f"Yesterday, {self.user.last_login.strftime('%I:%M %p')}"
        days_ago = (today - login_date).days
        if days_ago < 7:
            return f'{days_ago} days ago'
        return self.user.last_login.strftime('%b %d, %Y')

    def get_date_joined_formatted(self):
        return self.user.date_joined.strftime('%b %d, %Y')


# ===================================================================
# SYSTEM SETTINGS
# ===================================================================
class SystemSettings(models.Model):
    SETTING_TYPE_CHOICES = [
        ('header_logo_school', 'Header - School Logo'),
        ('carousel_slide_1_image', 'Carousel - Slide 1 Image'),
        ('carousel_slide_1_title', 'Carousel - Slide 1 Title'),
        ('carousel_slide_1_caption', 'Carousel - Slide 1 Caption'),
        ('carousel_slide_2_image', 'Carousel - Slide 2 Image'),
        ('carousel_slide_2_title', 'Carousel - Slide 2 Title'),
        ('carousel_slide_2_caption', 'Carousel - Slide 2 Caption'),
        ('carousel_slide_3_image', 'Carousel - Slide 3 Image'),
        ('carousel_slide_3_title', 'Carousel - Slide 3 Title'),
        ('carousel_slide_3_caption', 'Carousel - Slide 3 Caption'),
        ('partner_logo_1', 'Partner - Logo 1'),
        ('partner_logo_1_name', 'Partner - Logo 1 Name'),
        ('partner_logo_2', 'Partner - Logo 2'),
        ('partner_logo_2_name', 'Partner - Logo 2 Name'),
        ('partner_logo_3', 'Partner - Logo 3'),
        ('partner_logo_3_name', 'Partner - Logo 3 Name'),
        ('header_logo_region', 'Header - Region IX Logo'),
        ('header_logo_peninsula', 'Header - Zamboanga Peninsula Logo'),
        ('header_logo_matatag', 'Header - Matatag Logo'),
        ('header_caption', 'Header - Caption'),
        ('announcement_image', 'Announcement - Image'),
        ('announcement_caption', 'Announcement - Caption'),
        ('contact_address', 'Contact - Address'),
        ('contact_phone', 'Contact - Phone'),
        ('contact_email', 'Contact - Email'),
        ('contact_facebook', 'Contact - Facebook'),
        ('contact_hours', 'Contact - Operating Hours'),
        ('footer_copyright', 'Footer - Copyright'),
        ('footer_links', 'Footer - Links (JSON)'),
        ('footer_social', 'Footer - Social Media (JSON)'),
    ]

    setting_type = models.CharField(max_length=50, choices=SETTING_TYPE_CHOICES, unique=True)
    setting_value = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='system_settings/', blank=True, null=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_settings'
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['setting_type']
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        db_table = 'system_settings'
        indexes = [models.Index(fields=['setting_type'])]

    def __str__(self):
        return f"{self.get_setting_type_display()}"

    def get_formatted_date(self):
        return self.updated_at.strftime('%b %d, %Y at %I:%M %p')


# ===================================================================
# STAFF MEMBER
# ===================================================================
class StaffMember(models.Model):
    name = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='staff_members/', blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'name']
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'
        db_table = 'staff_member'
        indexes = [
            models.Index(fields=['display_order']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} - {self.position}"


# ===================================================================
# BUILDING
# ===================================================================
class Building(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# ===================================================================
# ROOM
# ===================================================================
class Room(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=50)

    class Meta:
        unique_together = ('building', 'room_number')

    def __str__(self):
        return f"{self.room_number} in {self.building.name}"


# ===================================================================
# SCHOOL YEAR
# ===================================================================
class SchoolYear(models.Model):
    year_label = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    enrollment_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year_label']
        db_table = 'school_year'
        indexes = [
            models.Index(fields=['year_label']),
            models.Index(fields=['is_active']),
            models.Index(fields=['enrollment_open']),
        ]

    def __str__(self):
        return self.year_label

    def clean(self):
        if self.year_label:
            self.year_label = self.year_label.strip()
        if not self.year_label:
            raise ValidationError({'year_label': 'School year label is required.'})
        if self.start_date >= self.end_date:
            raise ValidationError({'end_date': 'End date must be after start date.'})
        if self.is_active:
            SchoolYear.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_total_students(self):
        from enrollment_app.models import Student
        return Student.objects.filter(school_year=self).count()

    def get_sections_count(self):
        return self.sections.count()

    @classmethod
    def get_active_school_year(cls):
        return cls.objects.filter(is_active=True).first()

    def get_formatted_dates(self):
        return f"{self.start_date.strftime('%b %d, %Y')} - {self.end_date.strftime('%b %d, %Y')}"


# ===================================================================
# DOCUMENT REQUIREMENT — UPDATED
# ===================================================================
class DocumentRequirement(models.Model):
    """
    CHANGES:
      - applies_to  : controls which enrollee type sees this requirement.
      - grade_level : optional FK — when set, only students enrolling into
                      that specific grade level see this requirement.
                      NULL means "applies to all grade levels".

    Usage in views:
        from django.db.models import Q
        requirements = DocumentRequirement.objects.filter(
            school_year=active_school_year,
            is_active=True,
        ).filter(
            Q(applies_to='all') | Q(applies_to=student.enrollee_type)
        ).filter(
            Q(grade_level__isnull=True) | Q(grade_level=student.grade_level)
        )

    Examples:
      - 'PSA Birth Certificate'  → grade_level=NULL  (all grades, new + transferee)
      - 'SF9 / Form 138 Gr 6'   → grade_level=G7,   applies_to='new'
      - 'SF9 / Form 138 Gr 7'   → grade_level=G8,   applies_to='transferee'
      - 'SF9 / Form 138 Gr 8'   → grade_level=G9,   applies_to='transferee'
      - 'SF9 / Form 138 Gr 9'   → grade_level=G10,  applies_to='transferee'

    - Continuing students never go through the document upload step
      — their docs carry over automatically.
    """

    REQUIREMENT_TYPE_CHOICES = [
        ('mandatory', 'Mandatory'),
        ('optional', 'Optional'),
        ('conditional', 'Conditional'),
    ]

    APPLIES_TO_CHOICES = [
        ('all', 'All Enrollee Types'),
        ('new', 'New Students Only'),
        ('transferee', 'Transferees Only'),
        ('continuing', 'Continuing Students Only'),
        ('returnee', 'Returnees Only'),
    ]

    school_year = models.ForeignKey(
        SchoolYear,
        on_delete=models.CASCADE,
        related_name='document_requirements',
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    requirement_type = models.CharField(
        max_length=20, choices=REQUIREMENT_TYPE_CHOICES, default='mandatory'
    )

    applies_to = models.CharField(
        max_length=20,
        choices=APPLIES_TO_CHOICES,
        default='all',
        help_text=(
            "Which enrollee type must submit this document. "
            "'All' covers new students and transferees. "
            "Continuing students never go through the document upload step "
            "— their docs carry over automatically."
        )
    )

    grade_level = models.ForeignKey(
        'GradeLevel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_requirements',
        help_text=(
            "If set, only students enrolling into this grade level see this requirement. "
            "Leave blank (NULL) for requirements that apply to all grade levels. "
            "Example: 'SF9 Gr 6 card' → set to Grade 7 (incoming Grade 7 students submit their Gr 6 card)."
        )
    )

    file_format = models.CharField(
        max_length=100, default='pdf,jpg,jpeg,png',
        help_text="Allowed file formats (comma-separated)"
    )
    max_file_size_mb = models.DecimalField(
        max_digits=5, decimal_places=2, default=5.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(50.0)],
    )
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_document_requirements',
    )

    class Meta:
        ordering = ['school_year', 'order', 'name']
        verbose_name = 'Document Requirement'
        verbose_name_plural = 'Document Requirements'
        db_table = 'document_requirement'
        unique_together = [('school_year', 'name')]
        indexes = [
            models.Index(fields=['school_year', 'is_active']),
            models.Index(fields=['requirement_type']),
            models.Index(fields=['order']),
            models.Index(fields=['applies_to']),
            models.Index(fields=['grade_level']),
        ]

    def __str__(self):
        year_label = self.school_year.year_label if self.school_year else 'No Year'
        return f"{year_label} - {self.name} ({self.get_requirement_type_display()})"

    def get_allowed_extensions(self):
        return [ext.strip() for ext in self.file_format.split(',')]

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError({'name': 'Document name is required.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


# ===================================================================
# LIS STUDENT (Learning Information System)
# ===================================================================
class LISStudent(models.Model):
    """LIS Student data for LRN verification."""
    lrn = models.CharField(max_length=12, primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField()
    last_school = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'lis_students'

    def __str__(self):
        return f"{self.lrn} - {self.last_name}"
    
    
    # for request move student
class ProgramMoveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    # Programs that require DOST exam — cannot be moved INTO unless student has it
    DOST_REQUIRED_PROGRAMS = ['STE']

    # Move eligibility matrix: from_program -> list of allowed target programs
    ALLOWED_MOVES = {
        'STE':     ['SPFL', 'REGULAR', 'SPTVE', 'OHSP', 'SNED'],
        'SPFL':    ['SPTVE', 'REGULAR', 'OHSP', 'SNED'],
        'SPTVE':   ['SPFL', 'REGULAR', 'OHSP', 'SNED'],
        'OHSP':    ['REGULAR', 'SPFL', 'SPTVE', 'SNED'],
        'SNED':    ['REGULAR', 'SPFL', 'SPTVE', 'OHSP'],
        'REGULAR': [],  # REGULAR (both TOP5 and HETERO) cannot move to specialized programs
    }

    # TOP5 override — these can move to non-STE specialized programs
    REGULAR_TOP5_ALLOWED = ['SPFL', 'SPTVE', 'OHSP', 'SNED']

    student = models.ForeignKey(
        'enrollment_app.Student',
        on_delete=models.CASCADE,
        related_name='move_requests'
    )
    from_program_code = models.CharField(max_length=20)
    to_program_code = models.CharField(max_length=20)
    from_section = models.ForeignKey(
        'admin_app.Section',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='move_requests_from'
    )
    reason = models.TextField()
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='submitted_move_requests'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_move_requests'
    )
    review_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.lrn}: {self.from_program_code} → {self.to_program_code} [{self.status}]"

    @classmethod
    def check_eligibility(cls, from_program_code, to_program_code, student=None):
        """
        Returns (is_eligible: bool, reason: str)
        Checks business rules for program transfer eligibility.
        """
        from_code = from_program_code.upper()
        to_code = to_program_code.upper()

        if from_code == to_code:
            return False, "Student is already in this program."

        # STE requires DOST exam — no one can move into STE
        if to_code in cls.DOST_REQUIRED_PROGRAMS:
            return False, (
                "Cannot move to STE. STE requires a passing DOST entrance exam "
                "which cannot be waived via program transfer."
            )

        # Check if from_program is REGULAR
        if from_code == 'REGULAR':
            # Check if student is TOP5 — TOP5 can move to non-STE specialized programs
            is_top5 = False
            if student:
                try:
                    ps = student.program_selection
                    if ps.assigned_section and hasattr(ps.assigned_section, 'regular_track'):
                        is_top5 = ps.assigned_section.regular_track == 'TOP5'
                except Exception:
                    pass

            if is_top5:
                if to_code in cls.REGULAR_TOP5_ALLOWED:
                    return True, ""
                return False, (
                    f"REGULAR TOP5 students can only move to: "
                    f"{', '.join(cls.REGULAR_TOP5_ALLOWED)}."
                )
            else:
                # HETERO — cannot move to any specialized program
                return False, (
                    "REGULAR (Hetero) students cannot transfer to specialized programs. "
                    "Specialized programs require qualifications that cannot be satisfied "
                    "through a transfer request."
                )

        # All other programs — check the allowed moves matrix
        allowed = cls.ALLOWED_MOVES.get(from_code, [])
        if to_code in allowed:
            return True, ""

        return False, (
            f"Transfer from {from_code} to {to_code} is not permitted. "
            f"Allowed destinations from {from_code}: "
            f"{', '.join(allowed) if allowed else 'None'}."
        )