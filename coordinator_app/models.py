from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


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
