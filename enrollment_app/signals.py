"""
Enrollment App Signals
Handles automatic enrollment approval and section assignment when AI is enabled
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from enrollment_app.models import ProgramSelection, Student
from admin_app.models import Section, SchoolYear
from coordinator_app.models import AIAssistantPreference


@receiver(post_save, sender=ProgramSelection)
def auto_process_enrollment(sender, instance, created, **kwargs):
    """
    Automatically approve and assign section if AI Assistant is enabled.
    
    Runs when a new ProgramSelection is created.
    
    Validation:
    - Student not already assigned elsewhere
    - All required enrollment data complete
    - Report card document exists
    
    Assignment Strategy:
    - Fill sections sequentially by creation order
    - Move to next section when current is full
    """
    
    # Only process new program selections
    if not created:
        return
    
    # Check if already approved or assigned
    if instance.admin_approved or instance.assigned_section:
        return
    
    program_code = instance.selected_program_code
    
    # Check if AI Assistant is enabled for this program
    # Get any coordinator with AI enabled for this program
    try:
        from admin_app.models import Program
        program = Program.objects.get(code=program_code)
        
        ai_pref = AIAssistantPreference.objects.filter(
            program=program,
            ai_enabled=True
        ).first()
        
        if not ai_pref:
            return  # AI disabled for this program, skip automation
    except Exception:
        return  # Program not found or error, skip automation
    
    # Start validation
    student = instance.student
    
    # 1. Check for duplicate enrollments
    if _has_duplicate_enrollment(student, instance):
        return
    
    # 2. Validate all required fields are complete
    if not _is_enrollment_complete(student):
        return
    
    # 3. Validate report card exists
    if not _has_report_card(student):
        return
    
    # All validations passed - proceed with auto-approval and assignment
    with transaction.atomic():
        # Auto-approve
        instance.admin_approved = True
        instance.approved_by = 'AI Assistant'
        instance.approved_at = timezone.now()
        instance.admin_notes = 'Auto-approved by AI Assistant - all validation criteria met'
        
        # Auto-assign to section
        section = _get_next_available_section(program_code, instance.school_year)
        if section:
            instance.assigned_section = str(section.id)
            instance.section_assigned_at = timezone.now()
            
            # Update section capacity using database count (not incrementing)
            section.update_current_students_count()
        
        instance.save()


def _has_duplicate_enrollment(student, current_selection):
    """Check if student is already enrolled in another program/section"""
    existing = ProgramSelection.objects.filter(
        student=student,
        admin_approved=True
    ).exclude(pk=current_selection.pk).exists()
    
    return existing


def _is_enrollment_complete(student):
    """Validate all required enrollment forms are complete"""
    
    # Check Student model completion flags
    if not all([
        student.student_data_completed,
        student.family_data_completed,
        student.survey_completed,
        student.academic_data_completed,
        student.program_selected
    ]):
        return False
    
    # Verify actual data exists
    if not hasattr(student, 'student_data'):
        return False
    
    student_data = student.student_data
    
    # Check required student data fields
    required_fields = [
        student_data.last_name,
        student_data.first_name,
        student_data.gender,
        student_data.date_of_birth,
    ]
    
    if not all(required_fields):
        return False
    
    # Check family data exists
    if not hasattr(student, 'family_data'):
        return False
    
    family_data = student.family_data
    
    # Check required parent fields (father or mother)
    has_father = all([
        family_data.father_family_name,
        family_data.father_first_name,
        family_data.father_dob,
        family_data.father_occupation,
        family_data.father_contact_number
    ])
    
    has_mother = all([
        family_data.mother_family_name,
        family_data.mother_first_name,
        family_data.mother_dob,
        family_data.mother_occupation,
        family_data.mother_contact_number
    ])
    
    if not (has_father or has_mother):
        return False
    
    # Check academic data exists
    if not hasattr(student, 'academic_data'):
        return False
    
    return True


def _has_report_card(student):
    """
    Check if report card document exists.
    This is the CRITICAL document required for auto-approval.
    """
    try:
        # Report card is stored in AcademicData model
        if hasattr(student, 'academic_data'):
            academic_data = student.academic_data
            # Check if report_card field has a file
            if academic_data.report_card and academic_data.report_card.name:
                return True
        
        return False
        
    except Exception:
        # If any error, be conservative
        return False


def _get_next_available_section(program_code, school_year):
    """
    Get next available section using sequential fill strategy.
    
    Strategy:
    1. Get all sections for program, ordered by creation (oldest first)
    2. Sequential fill: Previous sections must be full before using next section
    3. Return first section with available space (respecting sequential order)
    """
    
    # Get active school year if not provided
    if not school_year:
        school_year = (
            SchoolYear.objects.filter(is_active=True).order_by('-start_date').first()
            or SchoolYear.objects.order_by('-start_date').first()
        )
    
    if not school_year:
        return None
    
    # Get sections for this program, ordered by creation (sequential fill: oldest first)
    sections = Section.objects.filter(
        program__code=program_code,
        school_year=school_year
    ).order_by('created_at')
    
    # Sequential fill: Check each section in order
    for section in sections:
        actual_count = section.get_actual_count()
        
        if actual_count < section.max_students:
            # Found a section with space
            return section
        # This section is full, continue to next section
    
    # All sections full or no sections exist
    return None
