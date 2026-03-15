from django.db import transaction
from django.utils import timezone

from enrollment_app.models import (
    Student, StudentEnrollment, StudentDocumentSubmission, ProgramSelection
)
from admin_app.models import GradeLevel


@transaction.atomic
def create_transferee_enrollment(student_lrn: str, new_school_year, grade_level: GradeLevel, last_school_attended: str, documents=None, selected_program_code: str = None):
    """
    Create a StudentEnrollment for a transferee.

    - Validates presence of last_school_attended.
    - Creates StudentEnrollment with enrollee_type='transferee'.
    - Creates/updates ProgramSelection with requires_program_selection=False.
    - Accepts a list of document dicts to create StudentDocumentSubmission rows (optional).

    Args:
        student_lrn: LRN of the student
        new_school_year: SchoolYear instance
        grade_level: GradeLevel instance for intended enrollment
        last_school_attended: str
        documents: optional list of dicts with keys: requirement (DocumentRequirement), document_file, file_name, file_size, file_format

    Returns:
        StudentEnrollment

    Raises:
        Student.DoesNotExist
        ValueError for validation failures
    """
    student = Student.objects.get(lrn=student_lrn)

    if not last_school_attended:
        raise ValueError('last_school_attended is required for transferees')

    # Idempotent: return existing enrollment if present
    enrollment, created = StudentEnrollment.objects.get_or_create(
        student=student,
        school_year=new_school_year,
        defaults={
            'grade_level': grade_level,
            'enrollee_type': 'transferee',
            'enrollment_status': 'under_review',
            'student_data_completed': False,
            'family_data_completed': False,
            'survey_completed': False,
            'academic_data_completed': False,
            'program_selected': True,
            'program_selected_at': timezone.now(),
            'documents_completed': False,
            'is_locked': False,
        }
    )

    # FORCE UPDATE for existing enrollments — important because _save_old_student_to_db
    # may have created it with enrollee_type='continuing' and enrollment_status='submitted'
    if not created:
        enrollment.grade_level = grade_level
        enrollment.enrollee_type = 'transferee'
        enrollment.enrollment_status = 'under_review'
        enrollment.program_selected = True
        enrollment.program_selected_at = timezone.now()
        enrollment.save(update_fields=['grade_level', 'enrollee_type', 'enrollment_status', 'program_selected', 'program_selected_at'])
        print(f"✓ Updated existing enrollment for {student_lrn}: enrollee_type='transferee', status='under_review'")

    # Ensure ProgramSelection exists and is coordinator-managed
    ps, ps_created = ProgramSelection.objects.get_or_create(
        student=student,
        school_year=new_school_year,
        defaults={
            'requires_program_selection': False,
            'selected_program_code': selected_program_code or None,
            'selection_reason': f'Transferee enrollment for {new_school_year.year_label}. Program: {selected_program_code or "Pending"}. Coordinator to assign section.'
        }
    )

    # Always update ProgramSelection to ensure flags are set correctly
    ps.requires_program_selection = False
    if selected_program_code:
        ps.selected_program_code = selected_program_code
        ps.selection_reason = f'Suggested program {selected_program_code} for transferee ({new_school_year.year_label}).'
    else:
        ps.selected_program_code = None
        ps.selection_reason = f'Transferee enrollment for {new_school_year.year_label}. Coordinator to assign.'
    ps.save()
    
    status = "created" if ps_created else "updated"
    print(f"✓ ProgramSelection {status} for {student_lrn}: program_code={ps.selected_program_code}")

    # Create document submissions if provided
    created_submissions = []
    if documents:
        for doc in documents:
            submission = StudentDocumentSubmission.objects.create(
                student=student,
                requirement=doc['requirement'],
                school_year=new_school_year,
                document_file=doc.get('document_file', ''),
                file_name=doc.get('file_name', ''),
                file_size=doc.get('file_size', 0),
                file_format=doc.get('file_format', ''),
                status=doc.get('status', 'pending'),
            )
            created_submissions.append(submission)

    return enrollment
