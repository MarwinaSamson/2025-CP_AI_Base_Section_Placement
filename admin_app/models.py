from django.db import models
from django.utils import timezone
import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Position(models.Model):
    """
    Model to store teaching positions/ranks in the school system.
    Examples: Teacher I, Teacher II, Master Teacher I, etc.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Position name (e.g., Teacher I, Master Teacher I)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description of this position"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date when this position was added"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date when this position was last updated"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this position is currently active"
    )

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
        """Validate the model before saving"""
        if self.name:
            self.name = self.name.strip()
        
        if not self.name:
            raise ValidationError({'name': 'Position name cannot be empty or just whitespace.'})

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_user_count(self):
        """Returns the number of users assigned to this position"""
        return self.userprofile_set.count()

    def can_delete(self):
        """Check if this position can be deleted"""
        return self.get_user_count() == 0

    def get_formatted_date(self):
        """Returns formatted creation date"""
        return self.created_at.strftime('%b %d, %Y')


class Department(models.Model):
    """
    Model to store school departments.
    Examples: English Department, Science Department, Mathematics Department, etc.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Department name (e.g., English Department, Science Department)"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description of this department"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date when this department was added"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date when this department was last updated"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this department is currently active"
    )

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
        """Validate the model before saving"""
        if self.name:
            self.name = self.name.strip()
        
        if not self.name:
            raise ValidationError({'name': 'Department name cannot be empty or just whitespace.'})

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_user_count(self):
        """Returns the number of users assigned to this department"""
        return self.userprofile_set.count()

    def can_delete(self):
        """Check if this department can be deleted"""
        return self.get_user_count() == 0

    def get_formatted_date(self):
        """Returns formatted creation date"""
        return self.created_at.strftime('%b %d, %Y')


class Program(models.Model):
    """
    Model to store school programs.
    Examples: STE, STEM, SPFL, SPTVE, TOP 5, HETERO
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Program code (e.g., STE, STEM, SPFL)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Full program name"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description of this program"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this program is currently active"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date when this program was added"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date when this program was last updated"
    )

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
        """Validate the model before saving"""
        if self.code:
            self.code = self.code.strip().upper()  # Normalize to uppercase
        
        if not self.code:
            raise ValidationError({'code': 'Program code cannot be empty or just whitespace.'})
        
        if self.name:
            self.name = self.name.strip()
        
        if not self.name:
            raise ValidationError({'name': 'Program name cannot be empty or just whitespace.'})

    def save(self, *args, **kwargs):
        """Override save to ensure validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_user_count(self):
        """Returns the number of users assigned to this program"""
        return self.userprofile_set.count()

    def can_delete(self):
        """Check if this program can be deleted"""
        return self.get_user_count() == 0

    def get_formatted_date(self):
        """Returns formatted creation date"""
        return self.created_at.strftime('%b %d, %Y')


class Teacher(models.Model):
    """
    Stores teacher records. A teacher may advise one section (is_adviser) and
    can teach multiple sections as a subject teacher.
    """
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)

    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers',
        help_text="Teacher's position/rank"
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers',
        help_text="Teacher's department"
    )

    address = models.TextField(blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True)

    is_adviser = models.BooleanField(
        default=False,
        help_text="Set to true when assigned as a section adviser (one section max)."
    )

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
        parts = [self.first_name or '', self.middle_name or '', self.last_name or '']
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


class ActivityLog(models.Model):
    """
    Model to track all activities in the admin system
    """
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
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs',
        help_text="User who performed the action"
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    description = models.TextField(
        help_text="Detailed description of the action"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="Browser user agent"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action was performed"
    )
    
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
        """Returns formatted date"""
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
        """Returns formatted time"""
        return self.created_at.strftime('%I:%M %p')


# Update your UserProfile class - add these fields and methods:
class UserProfile(models.Model):
    USER_TYPE_CHOICES = [
        ('admin', 'Admin'),
        ('coordinator', 'Coordinator'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    user_type = models.CharField(
        max_length=20, 
        choices=USER_TYPE_CHOICES
    )
    
    # ForeignKey relationships to other models
    program = models.ForeignKey(
        Program,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='userprofile_set',
        help_text="User's program"
    )
    
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='userprofile_set',
        help_text="User's position/rank"
    )
    
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='userprofile_set',
        help_text="User's department"
    )
    
    # NEW FIELDS - Add these:
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Employee ID number"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the profile was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the profile was last updated"
    )
    
    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
    
    def get_program_name(self):
        """Returns the program code or 'N/A' if not set"""
        return self.program.code if self.program else 'N/A'
    
    def get_position_name(self):
        """Returns the position name or 'N/A' if not set"""
        return self.position.name if self.position else 'N/A'
    
    def get_department_name(self):
        """Returns the department name or 'N/A' if not set"""
        return self.department.name if self.department else 'N/A'
    
    def get_access_badges(self):
        """Returns list of access types"""
        badges = []
        if self.user_type == 'admin':
            badges.append('Admin')
        if self.user_type == 'coordinator':
            badges.append('Coordinator')
        return badges
    
    def get_last_login_formatted(self):
        """Returns formatted last login"""
        if not self.user.last_login:
            return 'Never'
        
        today = timezone.now().date()
        yesterday = today - datetime.timedelta(days=1)
        login_date = self.user.last_login.date()
        
        if login_date == today:
            return f"Today, {self.user.last_login.strftime('%I:%M %p')}"
        elif login_date == yesterday:
            return f"Yesterday, {self.user.last_login.strftime('%I:%M %p')}"
        else:
            days_ago = (today - login_date).days
            if days_ago < 7:
                return f'{days_ago} days ago'
            else:
                return self.user.last_login.strftime('%b %d, %Y')
    
    def get_date_joined_formatted(self):
        """Returns formatted date joined"""
        return self.user.date_joined.strftime('%b %d, %Y')
    
    class Meta:
        db_table = 'user_profile'


class SystemSettings(models.Model):
    """
    Model to store system-wide settings and content for the landing page
    """
    SETTING_TYPE_CHOICES = [
        ('header_logo_school', 'Header - School Logo'),
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
    
    setting_type = models.CharField(
        max_length=50,
        choices=SETTING_TYPE_CHOICES,
        unique=True,
        help_text="Type of setting"
    )
    setting_value = models.TextField(
        blank=True,
        null=True,
        help_text="Setting value (text, HTML, or JSON)"
    )
    image = models.ImageField(
        upload_to='system_settings/',
        blank=True,
        null=True,
        help_text="Image file for logo/image settings"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_settings',
        help_text="User who last updated this setting"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this setting was last updated"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this setting was created"
    )
    
    class Meta:
        ordering = ['setting_type']
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
        db_table = 'system_settings'
        indexes = [
            models.Index(fields=['setting_type']),
        ]
    
    def __str__(self):
        return f"{self.get_setting_type_display()}"
    
    def get_formatted_date(self):
        """Returns formatted update date"""
        return self.updated_at.strftime('%b %d, %Y at %I:%M %p')


class StaffMember(models.Model):
    """
    Model to store staff/member information for landing page
    """
    name = models.CharField(
        max_length=200,
        help_text="Staff member name"
    )
    position = models.CharField(
        max_length=200,
        help_text="Staff member position/title"
    )
    photo = models.ImageField(
        upload_to='staff_members/',
        blank=True,
        null=True,
        help_text="Staff member photo"
    )
    display_order = models.IntegerField(
        default=0,
        help_text="Order in which to display (lower numbers first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this staff member is currently displayed"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )
    
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