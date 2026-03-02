"""
enrollment_app/models.py — FULLY UPDATED
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

    ENROLLEE_TYPE_CHOICES = [
        ('new', 'New (Incoming Grade 7)'),
        ('continuing', 'Continuing (Old Student — Same School)'),
        ('transferee', 'Transferee (From Another School)'),
        ('returnee', 'Returnee'),
    ]

    lrn = models.CharField(max_length=12, primary_key=True, verbose_name="LRN Number")
    email = models.EmailField(null=True, blank=True, help_text="Guardian's email address for contact")

    school_year = models.ForeignKey(
        'admin_app.SchoolYear',
        on_delete=models.CASCADE,
        related_name='students',
        null=True, blank=True,
        help_text="School year this student enrolled in"
    )

    grade_level = models.ForeignKey(
        'admin_app.GradeLevel',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='students',
        help_text="Grade level the student is enrolling INTO (e.g. Grade 7, Grade 8)"
    )

    enrollee_type = models.CharField(
        max_length=20,
        choices=ENROLLEE_TYPE_CHOICES,
        null=True, blank=True,
        help_text="Drives which steps are required and whether documents carry over"
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

    documents_completed = models.BooleanField(
        default=False,
        help_text=(
            "True when all required documents are submitted or confirmed. "
            "Auto-set to True for continuing students when documents are "
            "carried over from the previous school year."
        )
    )
    documents_completed_at = models.DateTimeField(null=True, blank=True)

    is_lis_verified = models.BooleanField(default=False)
    lis_verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['enrollment_status']),
            models.Index(fields=['school_year']),
            models.Index(fields=['created_at']),
            models.Index(fields=['grade_level']),
            models.Index(fields=['enrollee_type']),
        ]

    def __str__(self):
        return f"LRN: {self.lrn} - {self.enrollment_status}"

    @property
    def required_steps(self):
        """
        Returns a list of booleans for each step required by this enrollee type.
        All must be True for is_complete to return True.

        NEW STUDENT:
            student_data + family_data + survey + academic_data (OCR)
            + documents + program_selected (AI recommendation)

        CONTINUING (e.g. Grade 7 -> Grade 8, same school):
            student_data + family_data only.
            Documents carry over automatically via carry_over_for_student()
            which sets documents_completed=True — no upload step shown.
            No survey, no OCR, no AI recommendation.
            Coordinator assigns section directly.

        TRANSFEREE (from another school):
            student_data + family_data + documents.
            Must submit fresh documents; no prior records exist.
            No survey, no OCR, no AI recommendation.
            Coordinator assigns section directly.

        RETURNEE:
            Treated same as continuing.
        """
        base = [
            self.student_data_completed,
            self.family_data_completed,
        ]

        if self.enrollee_type == 'new':
            return base + [
                self.survey_completed,
                self.academic_data_completed,
                self.documents_completed,
                self.program_selected,
            ]
        elif self.enrollee_type == 'continuing':
            return base
        elif self.enrollee_type == 'transferee':
            return base + [
                self.documents_completed,
            ]
        elif self.enrollee_type == 'returnee':
            return base

        # Fallback: enrollee_type not yet set — require everything
        return base

    @property
    def is_complete(self):
        return all(self.required_steps)


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

    last_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField(blank=True, null=True, help_text="Auto-computed from date of birth")
    place_of_birth = models.CharField(max_length=255, blank=True, null=True)

    religion = models.CharField(max_length=100, blank=True, null=True)
    dialect_spoken = models.CharField(max_length=100, blank=True, null=True)
    ethnic_tribe = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    enrolling_as = models.JSONField(
        default=list,
        help_text='Array of enrollment types: ["new", "transferee", "old"]'
    )

    is_sped = models.BooleanField(default=False)
    sped_details = models.TextField(blank=True, null=True)

    is_working_student = models.BooleanField(default=False)
    working_details = models.TextField(blank=True, null=True)

    last_school_attended = models.CharField(max_length=255, blank=True, null=True)
    previous_grade_section = models.CharField(max_length=50, blank=True, null=True)
    last_school_year = models.CharField(max_length=20, blank=True, null=True)

    student_photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    agreed_to_terms = models.BooleanField(default=False)

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
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    def _calculate_age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    def save(self, *args, **kwargs):
        calculated_age = self._calculate_age()
        if calculated_age is not None:
            self.age = calculated_age
        super().save(*args, **kwargs)


# ===================================================================
# PARENT MODEL
# ===================================================================
class Parent(models.Model):
    PARENT_TYPE_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
    ]

    family_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)

    parent_type = models.CharField(max_length=10, choices=PARENT_TYPE_CHOICES)

    date_of_birth = models.DateField()
    occupation = models.CharField(max_length=255)

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
        if self.parent_type == 'father':
            return FamilyData.objects.filter(father=self)
        return FamilyData.objects.filter(mother=self)


# ===================================================================
# GUARDIAN MODEL
# ===================================================================
class Guardian(models.Model):
    family_name = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)

    date_of_birth = models.DateField()
    occupation = models.CharField(max_length=255)

    address = models.TextField(blank=True, null=True)
    contact_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)

    relationship_to_student = models.CharField(
        max_length=100,
        help_text="e.g. Grandmother, Uncle, Aunt"
    )

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
        return FamilyData.objects.filter(other_guardian=self)


# ===================================================================
# FAMILY DATA MODEL
# ===================================================================
class FamilyData(models.Model):
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

    father = models.ForeignKey(
        Parent,
        on_delete=models.RESTRICT,
        null=True, blank=True,
        related_name='students_as_father',
        limit_choices_to={'parent_type': 'father'},
    )

    mother = models.ForeignKey(
        Parent,
        on_delete=models.RESTRICT,
        null=True, blank=True,
        related_name='students_as_mother',
        limit_choices_to={'parent_type': 'mother'},
    )

    official_guardian_type = models.CharField(
        max_length=10,
        choices=OFFICIAL_GUARDIAN_CHOICES,
        null=True, blank=True,
    )

    other_guardian = models.ForeignKey(
        Guardian,
        on_delete=models.RESTRICT,
        null=True, blank=True,
        related_name='students_as_guardian',
    )

    parent_photo = models.ImageField(upload_to='parent_photos/', blank=True, null=True)

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

    @property
    def official_guardian_name(self):
        if self.official_guardian_type == 'father' and self.father:
            return self.father.full_name
        elif self.official_guardian_type == 'mother' and self.mother:
            return self.mother.full_name
        elif self.official_guardian_type == 'other' and self.other_guardian:
            return self.other_guardian.full_name
        return "Not Set"

    @property
    def official_guardian_contact(self):
        if self.official_guardian_type == 'father' and self.father:
            return self.father.contact_number
        elif self.official_guardian_type == 'mother' and self.mother:
            return self.mother.contact_number
        elif self.official_guardian_type == 'other' and self.other_guardian:
            return self.other_guardian.contact_number
        return "N/A"

    @property
    def official_guardian_email(self):
        if self.official_guardian_type == 'father' and self.father:
            return self.father.email or "N/A"
        elif self.official_guardian_type == 'mother' and self.mother:
            return self.mother.email or "N/A"
        elif self.official_guardian_type == 'other' and self.other_guardian:
            return self.other_guardian.email or "N/A"
        return "N/A"

    def get_siblings(self):
        from django.db.models import Q
        return FamilyData.objects.filter(
            Q(father=self.father) | Q(mother=self.mother)
        ).exclude(student=self.student)

    def clean(self):
        if self.official_guardian_type == 'other' and not self.other_guardian:
            raise ValidationError({
                'other_guardian': 'Other guardian must be specified when guardian type is "other".'
            })
        if self.official_guardian_type != 'other' and self.other_guardian:
            raise ValidationError({
                'other_guardian': 'Other guardian should only be set when guardian type is "other".'
            })
        if self.father and self.father.parent_type != 'father':
            raise ValidationError({'father': 'Selected parent must have parent_type="father".'})
        if self.mother and self.mother.parent_type != 'mother':
            raise ValidationError({'mother': 'Selected parent must have parent_type="mother".'})


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

    student_name = models.CharField(max_length=255, blank=True, null=True)
    age = models.IntegerField(null=True, blank=True)
    current_grade_section = models.CharField(max_length=50, blank=True, null=True)
    residence_barangay = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=50, blank=True, null=True)

    learning_style = models.CharField(max_length=50, blank=True, null=True)
    study_hours = models.CharField(max_length=50, blank=True, null=True)
    study_environment = models.CharField(max_length=50, blank=True, null=True)
    schoolwork_support = models.CharField(max_length=50, blank=True, null=True)

    enjoyed_subjects = models.JSONField(default=list)
    interested_program = models.CharField(max_length=50, blank=True, null=True)
    program_motivation = models.CharField(max_length=50, blank=True, null=True)
    enjoyed_activities = models.JSONField(default=list)
    enjoyed_activities_other = models.TextField(blank=True, null=True)

    assignments_on_time = models.CharField(max_length=50, blank=True, null=True)
    handle_difficult_lessons = models.CharField(max_length=50, blank=True, null=True)

    device_availability = models.CharField(max_length=50, blank=True, null=True)
    internet_access = models.CharField(max_length=50, blank=True, null=True)

    absences = models.CharField(max_length=50, blank=True, null=True)
    absence_reason = models.CharField(max_length=100, blank=True, null=True)
    participation = models.CharField(max_length=50, blank=True, null=True)

    difficulty_areas = models.JSONField(default=list)
    extra_support = models.CharField(max_length=10, blank=True, null=True)

    quiet_place = models.CharField(max_length=50, blank=True, null=True)
    distance_from_school = models.CharField(max_length=50, blank=True, null=True)
    travel_difficulty = models.CharField(max_length=50, blank=True, null=True)

    survey_responses_json = models.JSONField(default=dict)

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
    """
    Only created for NEW students — OCR + grade entry step.
    overall_average is persisted (not a @property) and computed in save().
    report_card_grade_level tracks which year's card was submitted.
    """

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

    # Persisted average — computed and saved in save(), NOT a @property
    overall_average = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Auto-computed average of all submitted subjects, saved on each update."
    )

    report_card_grade_level = models.ForeignKey(
        'admin_app.GradeLevel',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='submitted_report_cards',
        help_text=(
            "Grade level of the submitted report card. "
            "Grade 7 enrollee submits Grade 6 card; Grade 8 enrollee submits Grade 7 card, etc."
        )
    )

    dost_exam_result = models.CharField(
        max_length=20, choices=DOST_RESULT_CHOICES, null=True, blank=True
    )

    mathematics = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    araling_panlipunan = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    english = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    edukasyon_sa_pagpapakatao = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    science = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    edukasyon_pangkabuhayan = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    filipino = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    mapeh = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])

    report_card = models.FileField(upload_to='report_cards/', blank=True, null=True)

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
            models.Index(fields=['report_card_grade_level']),
        ]

    def __str__(self):
        return f"Academic Data - {self.student.lrn} (Avg: {self.overall_average})"

    def clean(self):
        """Block academic data creation for non-new students."""
        if self.student.enrollee_type and self.student.enrollee_type != 'new':
            raise ValidationError(
                "Academic data with OCR is only required for new students. "
                f"This student is enrolled as '{self.student.get_enrollee_type_display()}'."
            )

    def _compute_average(self):
        subjects = [
            self.mathematics, self.araling_panlipunan, self.english,
            self.edukasyon_sa_pagpapakatao, self.science,
            self.edukasyon_pangkabuhayan, self.filipino, self.mapeh,
        ]
        valid = [s for s in subjects if s is not None]
        return round(sum(valid) / len(valid), 2) if valid else None

    def save(self, *args, **kwargs):
        self.overall_average = self._compute_average()
        super().save(*args, **kwargs)


# ===================================================================
# PROGRAM SELECTION MODEL
# ===================================================================
class ProgramSelection(models.Model):
    """
    requires_program_selection = True  → new students only (AI recommendation flow)
    requires_program_selection = False → continuing & transferee (coordinator assigns directly)
    selected_program_code is nullable because continuing/transferee don't self-select.
    """

    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='program_selection'
    )

    school_year = models.ForeignKey(
        'admin_app.SchoolYear',
        on_delete=models.CASCADE,
        related_name='program_selections',
        null=True, blank=True,
    )

    requires_program_selection = models.BooleanField(
        default=True,
        help_text=(
            "True for new students — they go through AI recommendation and pick "
            "a program themselves. False for continuing and transferee students — "
            "the coordinator assigns their section and program directly."
        )
    )

    # Nullable: continuing/transferee don't self-select a program
    selected_program_code = models.CharField(max_length=20, blank=True, null=True)
    regular_track = models.CharField(max_length=10, blank=True, null=True)
    program_description = models.TextField(blank=True, null=True)
    selection_reason = models.TextField(blank=True, null=True)

    admin_approved = models.BooleanField(default=False)
    admin_rejected = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    approved_by = models.CharField(max_length=255, blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.CharField(max_length=255, blank=True, null=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)

    # Proper FK — was a raw CharField before
    assigned_section = models.ForeignKey(
        'admin_app.Section',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='enrolled_students',
        help_text="Final section assigned to this student after approval"
    )
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
            models.Index(fields=['requires_program_selection']),
        ]

    def __str__(self):
        year_label = self.school_year.year_label if self.school_year else 'No Year'
        return f"{self.student.lrn} - {self.selected_program_code or 'Pending'} ({year_label})"


# ===================================================================
# ENROLLMENT STATUS LOG
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
        Student, on_delete=models.CASCADE, related_name='status_logs'
    )
    old_status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
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


# ===================================================================
# STUDENT DOCUMENT SUBMISSION
# ===================================================================
class StudentDocumentSubmission(models.Model):
    """
    school_year FK          — ties submission to an enrollment cycle.
    is_carried_over         — True when copied from a prior year for a continuing student.
    carried_over_from       — self-referential FK to the original submission (audit trail).
    unique_together updated — (student, requirement, school_year) allows same doc across years.

    CARRYOVER FLOW (continuing students):
        Call StudentDocumentSubmission.carry_over_for_student(student, new_school_year).
        Copies all approved submissions from the most recent prior year.
        Sets student.documents_completed = True automatically.
        Student sees "On file — update if needed" instead of upload prompt.

    UPDATE FLOW (continuing student replaces a carried-over doc):
        Call submission.update_file(new_file, file_name, file_size, file_format).
        Flips is_carried_over=False, resets status to 'pending' for re-review.
        carried_over_from is preserved for audit history.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resubmit', 'Resubmit Required'),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='document_submissions'
    )

    requirement = models.ForeignKey(
        'admin_app.DocumentRequirement',
        on_delete=models.CASCADE,
        related_name='student_submissions'
    )

    school_year = models.ForeignKey(
        'admin_app.SchoolYear',
        on_delete=models.CASCADE,
        related_name='document_submissions',
        null=True, blank=True,
        help_text="The enrollment cycle this submission belongs to."
    )

    is_carried_over = models.BooleanField(
        default=False,
        help_text=(
            "True when this submission was automatically copied from a previous "
            "school year for a continuing student. The student may update it "
            "but is not required to re-upload."
        )
    )

    carried_over_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='carryover_copies',
        help_text=(
            "Points to the original submission this was copied from. "
            "Preserved even after the student uploads a new file."
        )
    )

    document_file = models.FileField(upload_to='student_documents/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    file_format = models.CharField(max_length=10)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_document_submissions',
    )
    review_notes = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_document_submissions'
        ordering = ['-submitted_at']
        unique_together = [('student', 'requirement', 'school_year')]
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['requirement', 'status']),
            models.Index(fields=['submitted_at']),
            models.Index(fields=['status']),
            models.Index(fields=['school_year']),
            models.Index(fields=['is_carried_over']),
        ]

    def __str__(self):
        tag = " [carried over]" if self.is_carried_over else ""
        return f"{self.student.lrn} - {self.requirement.name} ({self.status}){tag}"

    def clean(self):
        if self.document_file:
            max_size_bytes = self.requirement.max_file_size_mb * 1024 * 1024
            if self.document_file.size > max_size_bytes:
                raise ValidationError(
                    f"File size exceeds the maximum of {self.requirement.max_file_size_mb}MB."
                )
            allowed = self.requirement.get_allowed_extensions()
            if self.file_format.lower() not in allowed:
                raise ValidationError(
                    f"'.{self.file_format}' is not allowed. Allowed: {', '.join(allowed)}"
                )

    @classmethod
    def carry_over_for_student(cls, student, new_school_year):
        """
        Call this when a continuing student starts a new enrollment cycle.
        Finds all approved submissions from the most recent prior school year
        and creates copies in new_school_year with is_carried_over=True.
        Sets student.documents_completed = True immediately.
        Idempotent — safe to call multiple times.

        Usage:
            StudentDocumentSubmission.carry_over_for_student(
                student=student,
                new_school_year=active_school_year,
            )
        """
        prior_submissions = (
            cls.objects
            .filter(student=student, status='approved')
            .exclude(school_year=new_school_year)
            .select_related('school_year', 'requirement')
            .order_by('-school_year__year_label')
        )

        # Keep only the latest approved submission per requirement
        seen = set()
        to_carry = []
        for sub in prior_submissions:
            if sub.requirement_id not in seen:
                seen.add(sub.requirement_id)
                to_carry.append(sub)

        carried = []
        for original in to_carry:
            if cls.objects.filter(
                student=student,
                requirement=original.requirement,
                school_year=new_school_year,
            ).exists():
                continue

            prior_year = (
                original.school_year.year_label
                if original.school_year else 'prior year'
            )
            new_sub = cls.objects.create(
                student=student,
                requirement=original.requirement,
                school_year=new_school_year,
                document_file=original.document_file,
                file_name=original.file_name,
                file_size=original.file_size,
                file_format=original.file_format,
                status='approved',
                is_carried_over=True,
                carried_over_from=original,
                review_notes=f"Carried over from {prior_year}.",
            )
            carried.append(new_sub)

        if to_carry:
            student.documents_completed = True
            student.documents_completed_at = timezone.now()
            student.save(update_fields=['documents_completed', 'documents_completed_at'])

        return carried

    def update_file(self, new_file, file_name, file_size, file_format):
        """
        Call this when a continuing student replaces a carried-over document.
        Swaps the file, flips is_carried_over=False, resets status to 'pending'.
        carried_over_from is preserved for audit history.

        Usage:
            submission.update_file(
                new_file=request.FILES['document'],
                file_name=original_filename,
                file_size=file_bytes,
                file_format=extension,
            )
        """
        prior_year = (
            self.carried_over_from.school_year.year_label
            if self.carried_over_from and self.carried_over_from.school_year
            else None
        )
        self.document_file = new_file
        self.file_name = file_name
        self.file_size = file_size
        self.file_format = file_format
        self.is_carried_over = False
        self.status = 'pending'
        self.reviewed_by = None
        self.reviewed_at = None
        self.review_notes = (
            "Document updated by student."
            + (f" Previously carried over from {prior_year}." if prior_year else "")
        )
        self.save()