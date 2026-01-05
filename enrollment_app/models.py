"""
Enrollment App Models
Handles student enrollment, family data, survey responses, and academic records
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


# ===================================================================
# CORE STUDENT MODEL
# ===================================================================
class Student(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    lrn = models.CharField(max_length=12, primary_key=True, verbose_name="LRN Number")
    email = models.EmailField(null=True, blank=True, help_text="Guardian's email address for contact")
    
    # Link to school year for tracking enrollment by school year
    school_year = models.ForeignKey(
        'admin_app.SchoolYear',
        on_delete=models.CASCADE,
        related_name='students',
        null=True,
        blank=True,
        help_text="School year this student enrolled in"
    )
    
    enrollment_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    is_locked = models.BooleanField(default=False, help_text="Prevents multiple submissions")
    
    # Form completion tracking
    student_data_completed = models.BooleanField(default=False)
    student_data_completed_at = models.DateTimeField(null=True, blank=True)
    
    family_data_completed = models.BooleanField(default=False)
    family_data_completed_at = models.DateTimeField(null=True, blank=True)
    
    survey_completed = models.BooleanField(default=False)
    survey_completed_at = models.DateTimeField(null=True, blank=True)
    
    academic_data_completed = models.BooleanField(default=False)
    academic_data_completed_at = models.DateTimeField(null=True, blank=True)
    
    program_selected = models.BooleanField(default=False)
    program_selected_at = models.DateTimeField(null=True, blank=True)
    
    is_lis_verified = models.BooleanField(
        default=False,
        help_text="Indicates if the student's LRN was verified against LIS"
    )
    lis_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the LRN was verified"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'students'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['enrollment_status']),
            models.Index(fields=['school_year']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"LRN: {self.lrn} - {self.enrollment_status}"
    
    @property
    def is_complete(self):
        """Check if all forms are completed"""
        return all([
            self.student_data_completed,
            self.family_data_completed,
            self.survey_completed,
            self.academic_data_completed,
            self.program_selected
        ])

# ===================================================================
# STUDENT DATA MODEL
# ===================================================================
class StudentData(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]
    
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='student_data'
    )
    
    # Basic Information
    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    place_of_birth = models.CharField(max_length=255, blank=True, null=True)
    
    religion = models.CharField(max_length=100, blank=True, null=True)
    dialect_spoken = models.CharField(max_length=100, blank=True, null=True)
    ethnic_tribe = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    # Enrollment Type (stored as JSON array)
    enrolling_as = models.JSONField(
        default=list,
        help_text='Array of enrollment types: ["new", "transferee", "old"]'
    )
    
    # PWD/SPED Information
    is_sped = models.BooleanField(default=False)
    sped_details = models.TextField(blank=True, null=True)
    
    # Working Student Information
    is_working_student = models.BooleanField(default=False)
    working_details = models.TextField(blank=True, null=True)
    
    # Previous School Information
    last_school_attended = models.CharField(max_length=255, blank=True, null=True)
    previous_grade_section = models.CharField(max_length=50, blank=True, null=True)
    last_school_year = models.CharField(max_length=20, blank=True, null=True)
    
    # File Upload
    student_photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_data'
        indexes = [
            models.Index(fields=['last_name']),
            models.Index(fields=['date_of_birth']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Return full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate age from date of birth"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

class Parent(models.Model):
    """
    Stores parent information (Father or Mother).
    ONE parent record can be linked to MULTIPLE students (siblings).
    This prevents data duplication.
    """
    
    PARENT_TYPE_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
    ]
    
    # Name
    family_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Parent Type
    parent_type = models.CharField(
        max_length=10,
        choices=PARENT_TYPE_CHOICES,
        help_text="Is this person a father or mother"
    )
    
    # Personal Information
    date_of_birth = models.DateField()
    occupation = models.CharField(max_length=255)
    
    # Contact Information
    address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'parents'
        indexes = [
            models.Index(fields=['family_name', 'first_name', 'date_of_birth']),
            models.Index(fields=['contact_number']),
            models.Index(fields=['parent_type']),
        ]
        # Prevent duplicate parent records
        unique_together = [
            ['family_name', 'first_name', 'date_of_birth', 'parent_type']
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.family_name} ({self.get_parent_type_display()})"
    
    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.family_name}"
        return f"{self.first_name} {self.family_name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def get_children(self):
        """Get all students who have this person as a parent"""
        if self.parent_type == 'father':
            return FamilyData.objects.filter(father=self)
        else:
            return FamilyData.objects.filter(mother=self)


# ===================================================================
# MODEL 2: GUARDIAN (Only for "Other" guardians)
# ===================================================================
class Guardian(models.Model):
    """
    Stores guardian information ONLY when guardian is NOT father/mother.
    ONE guardian record can be linked to MULTIPLE students.
    Example: Grandmother raising 3 grandchildren.
    """
    
    # Name
    family_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Personal Information
    date_of_birth = models.DateField()
    occupation = models.CharField(max_length=255)
    
    # Contact Information
    address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    
    # Relationship to student
    relationship_to_student = models.CharField(
        max_length=100,
        help_text="Relationship to student (e.g., Grandmother, Uncle, Aunt)"
    )
    
    # File Upload
    photo = models.ImageField(upload_to='guardian_photos/', blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'guardians'
        indexes = [
            models.Index(fields=['family_name', 'first_name', 'date_of_birth']),
            models.Index(fields=['contact_number']),
        ]
        unique_together = [
            ['family_name', 'first_name', 'date_of_birth', 'relationship_to_student']
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.family_name} ({self.relationship_to_student})"
    
    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.family_name}"
        return f"{self.first_name} {self.family_name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def get_wards(self):
        """Get all students under this guardian's care"""
        return FamilyData.objects.filter(other_guardian=self)


# ===================================================================
# MODEL 3: FAMILY DATA (Links Student to Parents/Guardian)
# ===================================================================
class FamilyData(models.Model):
    """
    Links a student to their parents and designates official guardian.
    This is the "junction table" that connects everything together.
    DOES NOT store parent details - only references to Parent records.
    """
    
    OFFICIAL_GUARDIAN_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('other', 'Other Guardian'),
    ]
    
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='family_data'
    )
    
    # ===================================================================
    # PARENT REFERENCES (Foreign Keys - Shared across siblings)
    # ===================================================================
    father = models.ForeignKey(
        Parent,
        on_delete=models.RESTRICT,
        related_name='students_as_father',
        limit_choices_to={'parent_type': 'father'},
        help_text="Reference to father's record in Parent table"
    )
    
    mother = models.ForeignKey(
        Parent,
        on_delete=models.RESTRICT,
        related_name='students_as_mother',
        limit_choices_to={'parent_type': 'mother'},
        help_text="Reference to mother's record in Parent table"
    )
    
    # ===================================================================
    # OFFICIAL GUARDIAN DESIGNATION
    # ===================================================================
    official_guardian_type = models.CharField(
        max_length=10,
        choices=OFFICIAL_GUARDIAN_CHOICES,
        help_text="Who is the student's official guardian"
    )
    
    # Link to Guardian (ONLY when official_guardian_type is 'other')
    other_guardian = models.ForeignKey(
        Guardian,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name='students_as_guardian',
        help_text="Other guardian reference (only when type is 'other')"
    )
    
    # Parent Photo Upload
    parent_photo = models.ImageField(
        upload_to='parent_photos/', 
        blank=True, 
        null=True,
        help_text="Photo of the official guardian"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'family_data'
        indexes = [
            models.Index(fields=['official_guardian_type']),
            models.Index(fields=['father']),
            models.Index(fields=['mother']),
            models.Index(fields=['other_guardian']),
        ]
    
    def __str__(self):
        return f"Family Data - {self.student.lrn} (Guardian: {self.get_official_guardian_type_display()})"
    
    # ===================================================================
    # HELPER PROPERTIES
    # ===================================================================
    
    @property
    def official_guardian_name(self):
        """Return the name of the official guardian"""
        if self.official_guardian_type == 'father':
            return self.father.full_name
        elif self.official_guardian_type == 'mother':
            return self.mother.full_name
        elif self.official_guardian_type == 'other' and self.other_guardian:
            return self.other_guardian.full_name
        return "Not Set"
    
    @property
    def official_guardian_contact(self):
        """Return the contact number of the official guardian"""
        if self.official_guardian_type == 'father':
            return self.father.contact_number
        elif self.official_guardian_type == 'mother':
            return self.mother.contact_number
        elif self.official_guardian_type == 'other' and self.other_guardian:
            return self.other_guardian.contact_number
        return "N/A"
    
    @property
    def official_guardian_email(self):
        """Return the email of the official guardian"""
        if self.official_guardian_type == 'father':
            return self.father.email or "N/A"
        elif self.official_guardian_type == 'mother':
            return self.mother.email or "N/A"
        elif self.official_guardian_type == 'other' and self.other_guardian:
            return self.other_guardian.email or "N/A"
        return "N/A"
    
    def get_siblings(self):
        """Get all students who share the same parents"""
        from django.db.models import Q
        
        siblings = FamilyData.objects.filter(
            Q(father=self.father) | Q(mother=self.mother)
        ).exclude(student=self.student)
        
        return siblings
    
    def clean(self):
        """Validate guardian relationships"""
        
        if self.official_guardian_type == 'other' and not self.other_guardian:
            raise ValidationError({
                'other_guardian': 'Other guardian must be specified when guardian type is "other".'
            })
        
        if self.official_guardian_type != 'other' and self.other_guardian:
            raise ValidationError({
                'other_guardian': 'Other guardian should only be set when guardian type is "other".'
            })
        
        if self.father and self.father.parent_type != 'father':
            raise ValidationError({
                'father': 'Selected parent must have parent_type="father".'
            })
        
        if self.mother and self.mother.parent_type != 'mother':
            raise ValidationError({
                'mother': 'Selected parent must have parent_type="mother".'
            })

# ===================================================================
# SURVEY DATA MODEL
# ===================================================================
class SurveyData(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='survey_data'
    )
    
    # Section A: Student Information (Optional)
    student_name = models.CharField(max_length=255, blank=True, null=True)
    age = models.IntegerField(null=True, blank=True)
    current_grade_section = models.CharField(max_length=50, blank=True, null=True)
    residence_barangay = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=50, blank=True, null=True)
    
    # Section B: Student Profile
    learning_style = models.CharField(max_length=50, blank=True, null=True)
    study_hours = models.CharField(max_length=50, blank=True, null=True)
    study_environment = models.CharField(max_length=50, blank=True, null=True)
    schoolwork_support = models.CharField(max_length=50, blank=True, null=True)
    
    # Section C: Interests & Motivation
    enjoyed_subjects = models.JSONField(
        default=list,
        help_text='Array of subjects: ["Math", "Science", ...]'
    )
    interested_program = models.CharField(max_length=50, blank=True, null=True)
    program_motivation = models.CharField(max_length=50, blank=True, null=True)
    enjoyed_activities = models.JSONField(
        default=list,
        help_text='Array of activities'
    )
    enjoyed_activities_other = models.TextField(blank=True, null=True)
    
    # Section D: Behavioral & Study Habits
    assignments_on_time = models.CharField(max_length=50, blank=True, null=True)
    handle_difficult_lessons = models.CharField(max_length=50, blank=True, null=True)
    
    # Section E: Technology Access
    device_availability = models.CharField(max_length=50, blank=True, null=True)
    internet_access = models.CharField(max_length=50, blank=True, null=True)
    
    # Section F: Attendance & Responsibility
    absences = models.CharField(max_length=50, blank=True, null=True)
    absence_reason = models.CharField(max_length=100, blank=True, null=True)
    participation = models.CharField(max_length=50, blank=True, null=True)
    
    # Section G: Learning Support & Special Needs
    difficulty_areas = models.JSONField(
        default=list,
        help_text='Array of difficulty areas'
    )
    extra_support = models.CharField(max_length=10, blank=True, null=True)
    
    # Section H: Environmental Factors
    quiet_place = models.CharField(max_length=50, blank=True, null=True)
    distance_from_school = models.CharField(max_length=50, blank=True, null=True)
    travel_difficulty = models.CharField(max_length=50, blank=True, null=True)
    
    # Full survey backup
    survey_responses_json = models.JSONField(
        default=dict,
        help_text='Complete survey responses as backup'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'survey_data'
        indexes = [
            models.Index(fields=['interested_program']),
        ]
    
    def __str__(self):
        return f"Survey - {self.student.lrn}"

# ===================================================================
# ACADEMIC DATA MODEL
# ===================================================================
class AcademicData(models.Model):
    DOST_RESULT_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('not_taken', 'Not Taken'),
    ]
    
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='academic_data'
    )
    
    # DOST Exam
    dost_exam_result = models.CharField(
        max_length=20,
        choices=DOST_RESULT_CHOICES,
        null=True,
        blank=True
    )
    
    # Grade 6 Subjects
    mathematics = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    araling_panlipunan = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    english = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    edukasyon_sa_pagpapakatao = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    science = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    edukasyon_pangkabuhayan = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    filipino = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    mapeh = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # File Upload
    report_card = models.FileField(upload_to='report_cards/', blank=True, null=True)
    
    # Working Student & PWD (cached from student_data)
    is_working_student = models.BooleanField(default=False)
    working_type = models.TextField(blank=True, null=True)
    is_pwd = models.BooleanField(default=False)
    disability_type = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'academic_data'
        indexes = [
            models.Index(fields=['dost_exam_result']),
        ]
    
    def __str__(self):
        return f"Academic Data - {self.student.lrn} (Avg: {self.overall_average})"
    
    @property
    def overall_average(self):
        """Calculate overall average of all subjects"""
        subjects = [
            self.mathematics,
            self.araling_panlipunan,
            self.english,
            self.edukasyon_sa_pagpapakatao,
            self.science,
            self.edukasyon_pangkabuhayan,
            self.filipino,
            self.mapeh
        ]
        
        # Filter out None values
        valid_subjects = [s for s in subjects if s is not None]
        
        if not valid_subjects:
            return 0
        
        return round(sum(valid_subjects) / len(valid_subjects), 2)

# ===================================================================
# PROGRAM SELECTION MODEL
# Note: Program master data is managed in admin_app
# ===================================================================
# ============================================================
# 7. PROGRAM SELECTION MODEL
# ============================================================
# Note: Program model is in admin_app, not here

class ProgramSelection(models.Model):
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='program_selection'
    )
    
    # Link to school year for tracking program selection by year
    school_year = models.ForeignKey(
        'admin_app.SchoolYear',
        on_delete=models.CASCADE,
        related_name='program_selections',
        null=True,
        blank=True,
        help_text="School year this program selection belongs to"
    )
    
    # Student's Selected Program (stored as code, e.g., "STE", "SPFL")
    # Program details come from admin_app.Program model
    selected_program_code = models.CharField(
        max_length=20,
        help_text="Program code selected by student (e.g., STE, SPFL, TOP5)"
    )
    program_description = models.TextField(
        help_text="Description shown during selection"
    )
    selection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Why student chose this program"
    )
    
    # Admin Review & Approval
    admin_approved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    approved_by = models.CharField(max_length=255, blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Final Section Assignment
    assigned_section = models.CharField(max_length=50, blank=True, null=True)
    section_assigned_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'program_selection'
        indexes = [
            models.Index(fields=['selected_program_code']),
            models.Index(fields=['school_year']),
            models.Index(fields=['admin_approved']),
            models.Index(fields=['assigned_section']),
        ]
    
    def __str__(self):
        year_label = self.school_year.year_label if self.school_year else 'No Year'
        return f"{self.student.lrn} - {self.selected_program_code} ({year_label})"

# ===================================================================
# ENROLLMENT STATUS LOG MODEL (Audit Trail)
# ===================================================================
class EnrollmentStatusLog(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='status_logs'
    )
    
    old_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        null=True,
        blank=True
    )
    new_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    changed_by = models.CharField(max_length=255, blank=True, null=True)
    change_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'enrollment_status_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'new_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.student.lrn}: {self.old_status} → {self.new_status}"