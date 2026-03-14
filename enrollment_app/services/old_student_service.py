# enrollment_app/services/old_student_service.py
"""
Service functions for handling old student (continuing) enrollment logic.

Key operations:
  - Check if old student can continue
  - Create continuation enrollment
  - Promote students to next year
  - Get prior academic status
"""

from django.db import transaction
from django.utils import timezone
from enrollment_app.models import (
    Student, StudentEnrollment, StudentAcademicYearStatus, StudentDocumentSubmission
)
from admin_app.models import GradeLevel, SchoolYear


def can_student_continue(student_lrn: str) -> bool:
    """
    Check if a student can re-enroll as a continuing student.
    Returns True only if the student's latest academic status was 'promoted'.
    
    Args:
        student_lrn: The student's LRN
        
    Returns:
        bool: True if student was promoted last year, False otherwise
    """
    try:
        latest_status = StudentAcademicYearStatus.objects.filter(
            student__lrn=student_lrn
        ).latest('school_year__year_label')
        
        return latest_status.final_status == 'promoted'
    except StudentAcademicYearStatus.DoesNotExist:
        # No prior academic record exists
        return False


def get_student_promotion_status(student_lrn: str):
    """
    Get the most recent academic year status for a student.
    
    Args:
        student_lrn: The student's LRN
        
    Returns:
        StudentAcademicYearStatus or None
    """
    try:
        return StudentAcademicYearStatus.objects.filter(
            student__lrn=student_lrn
        ).latest('school_year__year_label')
    except StudentAcademicYearStatus.DoesNotExist:
        return None


def get_next_grade_level(current_grade_level):
    """
    Get the next grade level after the given one.
    Grade 7 → 8, Grade 8 → 9, Grade 9 → 10, Grade 10 → None (graduates)
    
    Args:
        current_grade_level: GradeLevel instance
        
    Returns:
        GradeLevel instance or None if student graduates
    """
    grade_order = {
        'Grade 7': 'Grade 8',
        'Grade 8': 'Grade 9',
        'Grade 9': 'Grade 10',
        'Grade 10': None,
    }
    
    next_grade_name = grade_order.get(current_grade_level.name)
    if next_grade_name:
        return GradeLevel.objects.get(name=next_grade_name)
    return None


@transaction.atomic
def create_continuation_enrollment(student_lrn: str, new_school_year) -> StudentEnrollment:
    """
    Create a new StudentEnrollment for a continuing student entering next year.
    
    Pre-condition: Student must have passed previous year (can_student_continue == True)
    
    Process:
      1. Validate student can continue
      2. Get prior grade level
      3. Create new StudentEnrollment for next grade
      4. Carry over documents
      5. Set documents_completed=True
      
    Args:
        student_lrn: The student's LRN
        new_school_year: SchoolYear instance for the new enrollment
        
    Returns:
        StudentEnrollment: The newly created enrollment
        
    Raises:
        Student.DoesNotExist: If student not found
        ValueError: If student cannot continue (did not pass)
    """
    # Validate student exists
    student = Student.objects.get(lrn=student_lrn)
    
    # Validate can continue
    if not can_student_continue(student_lrn):
        raise ValueError(
            f"Student {student_lrn} cannot re-enroll as continuing. "
            "Did not pass previous year."
        )
    
    # Get latest academic status to determine next grade
    prior_status = get_student_promotion_status(student_lrn)
    if not prior_status or not prior_status.grade_level:
        raise ValueError(
            f"Cannot determine previous grade level for student {student_lrn}"
        )
    
    # Determine next grade
    next_grade = get_next_grade_level(prior_status.grade_level)
    if not next_grade:
        raise ValueError(
            f"Student {student_lrn} has completed Grade 10. Cannot continue enrollment."
        )
    
    # Create new StudentEnrollment
    enrollment = StudentEnrollment.objects.create(
        student=student,
        school_year=new_school_year,
        grade_level=next_grade,
        enrollee_type='continuing',
        enrollment_status='draft'
    )
    
    # Carry over documents from previous year
    StudentDocumentSubmission.carry_over_for_student(student, new_school_year)
    
    # Mark documents as completed
    enrollment.documents_completed = True
    enrollment.documents_completed_at = timezone.now()
    enrollment.save()
    
    return enrollment


@transaction.atomic
def promote_students_to_next_year(from_school_year, to_school_year):
    """
    End-of-year batch operation: promote all students who passed to next year.
    
    Creates StudentEnrollment records for next grade for all students with
    final_status='promoted' in the current year.
    
    Args:
        from_school_year: SchoolYear instance for current year
        to_school_year: SchoolYear instance for next year
        
    Returns:
        tuple: (promoted_enrollments list, count)
    """
    # Get all students who were promoted this year
    promoted_statuses = StudentAcademicYearStatus.objects.filter(
        school_year=from_school_year,
        final_status='promoted'
    ).select_related('student', 'grade_level')
    
    promoted_enrollments = []
    
    for status in promoted_statuses:
        try:
            enrollment = create_continuation_enrollment(
                student_lrn=status.student.lrn,
                new_school_year=to_school_year
            )
            promoted_enrollments.append(enrollment)
        except (Student.DoesNotExist, ValueError, GradeLevel.DoesNotExist) as e:
            # Log error and continue with next student
            print(f"Error promoting student {status.student.lrn}: {e}")
            continue
    
    return promoted_enrollments, len(promoted_enrollments)


def get_student_enrollment_history(student_lrn: str):
    """
    Get all enrollments for a student across school years.
    
    Args:
        student_lrn: The student's LRN
        
    Returns:
        QuerySet of StudentEnrollment objects (ordered by year descending)
    """
    return StudentEnrollment.objects.filter(
        student__lrn=student_lrn
    ).select_related('school_year', 'grade_level').order_by('-school_year__year_label')


def get_prior_section_preference(student_lrn: str):
    """
    Get the section the student was in during their most recent prior year.
    Useful for re-assigning continuing students to the same section.
    
    Args:
        student_lrn: The student's LRN
        
    Returns:
        Section instance or None
    """
    from admin_app.models import Section
    
    prior_enrollment = StudentEnrollment.objects.filter(
        student__lrn=student_lrn
    ).exclude(enrollment_status='draft').order_by('-school_year__year_label').first()
    
    if not prior_enrollment:
        return None
    
    # Try to find the section assignment through ProgramSelection
    from enrollment_app.models import ProgramSelection
    try:
        program_sel = ProgramSelection.objects.get(student__lrn=student_lrn)
        return program_sel.assigned_section
    except ProgramSelection.DoesNotExist:
        return None


@transaction.atomic
def finalize_academic_year(school_year):
    """
    End-of-year operation: create StudentAcademicYearStatus for all enrolled students.
    
    For each student enrolled in the given school year:
      1. Compute overall grade from AcademicPerformance records
      2. Determine final_status (promoted if grade >= 75, else retained)
      3. Create StudentAcademicYearStatus record
      
    Args:
        school_year: SchoolYear instance
        
    Returns:
        list: Created StudentAcademicYearStatus instances
    """
    from coordinator_app.models import AcademicPerformance
    from decimal import Decimal
    
    enrollments = StudentEnrollment.objects.filter(
        school_year=school_year,
        enrollment_status='approved'
    ).select_related('student', 'grade_level', 'school_year')
    
    created_statuses = []
    
    for enrollment in enrollments:
        # Get all academic performance records for this student/year/grade
        perf_records = AcademicPerformance.objects.filter(
            student=enrollment.student,
            school_year=school_year,
            grade_level=enrollment.grade_level,
            quarter=5  # Final grade only
        )
        
        # Compute overall grade
        grades = [p.grade for p in perf_records if p.grade is not None]
        overall_grade = (
            sum(grades) / len(grades) if grades 
            else None
        )
        
        # Determine final status
        if overall_grade is None:
            final_status = 'pending'
        elif overall_grade >= Decimal('75'):
            final_status = 'promoted'
        else:
            final_status = 'retained'
        
        # Get section from ProgramSelection if available
        from enrollment_app.models import ProgramSelection
        section = None
        try:
            prog_sel = ProgramSelection.objects.get(student=enrollment.student)
            section = prog_sel.assigned_section
        except ProgramSelection.DoesNotExist:
            pass
        
        # Create status record
        status = StudentAcademicYearStatus.objects.create(
            student=enrollment.student,
            school_year=enrollment.school_year,
            grade_level=enrollment.grade_level,
            section=section,
            final_status=final_status,
            overall_grade=overall_grade,
            remarks=f"Academic year {school_year.year_label} finalized."
        )
        
        created_statuses.append(status)
    
    return created_statuses
