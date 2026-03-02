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

# Grade thresholds per program: (min_grade, max_grade)
# Median is calculated as (min + max) / 2
# Above median: auto-approve | min to median: manual review | below min: auto-reject
PROGRAM_GRADE_THRESHOLDS = {
    'STE': (87, 97),
    'SPFL': (84, 93),
    'SPTVE': (84, 93),
    'REGULAR_TOP5': (85, 90),
    'REGULAR_HETERO': (75, 84),
}


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

        # Determine track for REGULAR program
        # Priority: 1) Student's choice (stored in regular_track), 2) AI recommendation, 3) HETERO fallback
        target_track = None
        if program_code == 'REGULAR':
            # First, use student's chosen track if available
            target_track = getattr(instance, 'regular_track', None)
            if target_track:
                target_track = target_track.upper()

            # If no track specified, try AI recommendation
            if not target_track:
                target_track = _get_ai_recommended_track(student)

            # Final fallback to HETERO
            if not target_track:
                target_track = 'HETERO'

        # Check grade threshold before auto-approval
        grade_result = _check_grade_threshold(student, program_code, target_track)

        if grade_result == 'auto_reject':
            # Grade below program minimum — auto-reject
            instance.admin_approved = False
            instance.admin_rejected = True
            instance.rejected_by = 'AI Assistant'
            instance.rejected_at = timezone.now()
            instance.rejection_reason = f'Auto-rejected: Overall average below minimum threshold for {program_code}'
            instance.admin_notes = f'AI Auto-Reject: Grade average below program minimum range'
            instance.save()
            student.enrollment_status = 'rejected'
            student.save()
            return

        if grade_result == 'manual_review':
            # Grade in lower half of range — needs coordinator review
            instance.admin_approved = False
            instance.admin_notes = f'AI flagged for manual review: Grade average in lower range for {program_code}'
            instance.save()
            student.enrollment_status = 'under_review'
            student.save()
            return

        # grade_result is 'auto_approve' or None — proceed with auto-approval and section assignment
        # Auto-assign to section
        section = _get_next_available_section(program_code, instance.school_year, target_track)
        if section:
            instance.assigned_section = section
            instance.section_assigned_at = timezone.now()

            # Update section capacity using database count (not incrementing)
            section.update_current_students_count()

        instance.save()

        # Update Student enrollment status
        student.enrollment_status = 'approved'
        student.save()


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
    required_fields = {
        'last_name': student_data.last_name,
        'first_name': student_data.first_name,
        'gender': student_data.gender,
        'date_of_birth': student_data.date_of_birth,
    }

    if not all(required_fields.values()):
        return False

    # Check family data exists
    if not hasattr(student, 'family_data'):
        return False

    family_data = student.family_data

    # Check that guardian is present (required)
    has_official_guardian = False

    if family_data.official_guardian_type == 'father' and family_data.father:
        has_official_guardian = True
    elif family_data.official_guardian_type == 'mother' and family_data.mother:
        has_official_guardian = True
    elif family_data.official_guardian_type == 'other' and family_data.other_guardian:
        has_official_guardian = True

    if not has_official_guardian:
        return False

    # Check academic data exists
    if not hasattr(student, 'academic_data'):
        return False

    return True


def _has_report_card(student):
    """
    Check if report card document exists.
    This is the CRITICAL document required for auto-approval.

    Checks TWO locations:
    1. AcademicData.report_card (legacy field)
    2. StudentDocumentSubmission linked to "Report Card" DocumentRequirement
    """
    try:
        # Method 1: Check AcademicData model (legacy)
        if hasattr(student, 'academic_data'):
            academic_data = student.academic_data
            # Check if report_card field has a file
            if academic_data.report_card and academic_data.report_card.name:
                return True

        # Method 2: Check StudentDocumentSubmission for Report Card document
        from enrollment_app.models import StudentDocumentSubmission
        from admin_app.models import DocumentRequirement

        # Find "Report Card" document requirement
        report_card_requirements = DocumentRequirement.objects.filter(
            name__icontains='report card',
            is_active=True
        )

        if report_card_requirements.exists():
            # Check if student has submitted any report card document
            submission = StudentDocumentSubmission.objects.filter(
                student=student,
                requirement__in=report_card_requirements,
                document_file__isnull=False
            ).exclude(document_file='').first()

            if submission and submission.document_file:
                return True

        return False

    except Exception:
        # If any error, be conservative and return False
        return False


def _check_grade_threshold(student, program_code, target_track=None):
    """
    Check student's average grade against program thresholds.

    Returns:
        'auto_approve' - grade >= median (upper half of range)
        'manual_review' - grade >= min but < median (lower half)
        'auto_reject' - grade < min (below range)
        None - no threshold defined or no grades available (skip check)
    """
    try:
        academic_data = student.academic_data
        grades = [
            academic_data.mathematics, academic_data.english,
            academic_data.science, academic_data.filipino,
            academic_data.araling_panlipunan, academic_data.edukasyon_sa_pagpapakatao,
            academic_data.edukasyon_pangkabuhayan, academic_data.mapeh
        ]
        valid = [float(g) for g in grades if g is not None]
        if not valid:
            return None
        average = sum(valid) / len(valid)
    except Exception:
        return None

    # Determine threshold key
    if program_code == 'REGULAR' and target_track:
        key = f'REGULAR_{target_track}'
    else:
        key = program_code

    threshold = PROGRAM_GRADE_THRESHOLDS.get(key)
    if not threshold:
        return None

    min_grade, max_grade = threshold
    median = (min_grade + max_grade) / 2

    if average >= median:
        return 'auto_approve'
    elif average >= min_grade:
        return 'manual_review'
    else:
        return 'auto_reject'


def _get_next_available_section(program_code, school_year, target_track=None):
    """
    Get next available section using sequential fill strategy.

    Strategy:
    1. Get all sections for program, ordered by creation (oldest first)
    2. For REGULAR program: filter by target_track (TOP5 or HETERO)
    3. Sequential fill: Previous sections must be full before using next section
    4. Return first section with available space (respecting sequential order)

    Args:
        program_code: Program code (e.g., 'STE', 'REGULAR')
        school_year: SchoolYear instance
        target_track: For REGULAR program, specify 'TOP5' or 'HETERO'
    """

    # Get active school year if not provided
    if not school_year:
        school_year = (
            SchoolYear.objects.filter(is_active=True).order_by('-start_date').first()
            or SchoolYear.objects.order_by('-start_date').first()
        )

    if not school_year:
        return None

    # Build query filters
    filters = {
        'program__code': program_code,
        'school_year': school_year
    }

    # For REGULAR program, filter by track
    if program_code == 'REGULAR' and target_track:
        filters['regular_track'] = target_track

    # Get sections for this program, ordered by creation (sequential fill: oldest first)
    sections = Section.objects.filter(**filters).order_by('created_at')

    # Sequential fill: Check each section in order
    for section in sections:
        actual_count = section.get_actual_count()

        if actual_count < section.max_students:
            # Found a section with space
            return section
        # This section is full, continue to next section

    # All sections full or no sections exist
    # For REGULAR program, try alternative track
    if program_code == 'REGULAR' and target_track:
        alternative_track = 'TOP5' if target_track == 'HETERO' else 'HETERO'
        filters['regular_track'] = alternative_track
        sections = Section.objects.filter(**filters).order_by('created_at')

        for section in sections:
            actual_count = section.get_actual_count()
            if actual_count < section.max_students:
                return section

    return None


def _get_ai_recommended_track(student):
    """
    Get AI recommendation for REGULAR program track (TOP5 vs HETERO).

    Returns: 'TOP5' or 'HETERO' based on ML model prediction
    """
    try:
        from TRAINING_ARC.placement_recommender import PlacementRecommender

        # Load recommender
        recommender = PlacementRecommender(model_path='TRAINING_ARC/models')
        if not recommender.load_model():
            return None

        # Prepare student data for prediction
        student_features = _prepare_student_features(student)
        if student_features is None:
            return None

        # Get recommendations
        recommendations = recommender.recommend(student_features, top_n=5)

        # Find REGULAR track recommendation (Top-5 or Hetero)
        for rec in recommendations:
            if rec['placement'] == 'Top-5 Regular':
                return 'TOP5'
            elif rec['placement'] == 'Hetero':
                return 'HETERO'

        # Fallback to HETERO if no clear recommendation
        return 'HETERO'

    except Exception:
        # Fallback: assign to HETERO if recommendation fails
        return 'HETERO'


def _prepare_student_features(student):
    """
    Prepare student features for ML model prediction.
    Extract survey answers, academic data, etc.

    Returns: pandas DataFrame with student features or None if data missing
    """
    try:
        import pandas as pd

        # Get survey data
        if not hasattr(student, 'survey_data') or not student.survey_data:
            return None

        survey = student.survey_data

        # Extract subject enjoyment from enjoyed_subjects list
        enjoyed_subjects = survey.enjoyed_subjects or []
        difficulty_areas = survey.difficulty_areas or []

        # Build feature dictionary based on actual SurveyData model fields
        features = {
            'enjoy_math': 1 if 'Math' in enjoyed_subjects else 0,
            'enjoy_science': 1 if 'Science' in enjoyed_subjects else 0,
            'enjoy_english': 1 if 'English' in enjoyed_subjects else 0,
            'enjoy_filipino': 1 if 'Filipino' in enjoyed_subjects else 0,
            'enjoy_arpan': 1 if 'ARPAN' in enjoyed_subjects else 0,
            'enjoy_mapeh': 1 if 'MAPEH' in enjoyed_subjects else 0,
            'enjoy_tle': 1 if 'TLE' in enjoyed_subjects else 0,
            'difficulty_reading': 1 if 'Reading' in difficulty_areas else 0,
            'difficulty_writing': 1 if 'Writing' in difficulty_areas else 0,
            'difficulty_math': 1 if 'Math' in difficulty_areas else 0,
            'difficulty_focusing': 1 if 'Focusing' in difficulty_areas else 0,
            'difficulty_social_interaction': 1 if 'Social Interaction' in difficulty_areas else 0,
            'award_highest_honors': 1 if getattr(survey, 'extra_support', '') == 'Highest Honors' else 0,
            'award_high_honors': 1 if getattr(survey, 'extra_support', '') == 'High Honors' else 0,
            'award_with_honors': 1 if getattr(survey, 'extra_support', '') == 'With Honors' else 0,
            'sped_learner': 1 if 'SPED' in difficulty_areas else 0,
            'working_student': 1 if getattr(survey, 'survey_responses_json', {}).get('working_student') else 0,
        }

        # Create DataFrame
        df = pd.DataFrame([features])
        return df

    except Exception:
        return None
