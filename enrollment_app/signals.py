"""
Enrollment App Signals
Handles automatic enrollment approval and section assignment when AI is enabled
"""


from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import transaction

from enrollment_app.models import ProgramSelection, Student, StudentEnrollment
from admin_app.models import Section, SchoolYear, GradeLevel
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


@receiver(post_save, sender=StudentEnrollment)
def auto_set_grade7_for_new(sender, instance, created, **kwargs):
    """
    Auto-set grade_level to G7 when enrollee_type='new' and grade_level is None.
    Safe: only new records, skips if manually set.
    """
    if (created and 
        instance.enrollee_type == 'new' and 
        instance.grade_level is None and
        instance.school_year):
        
        try:
            grade7 = GradeLevel.objects.get(code='G7')
            instance.grade_level = grade7
            instance.save(update_fields=['grade_level'])
            print(f"[SIGNAL] Auto-set Grade 7 for new enrollment {instance.student.lrn}")
        except GradeLevel.DoesNotExist:
            print(f"[SIGNAL] No G7 GradeLevel found for {instance.school_year}")


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
    import sys

    # Only process new program selections
    if not created:
        print(f"[SIGNAL] Skipping - not a new creation", file=sys.stderr)
        return

    # Check if already approved or assigned
    if instance.admin_approved or instance.assigned_section:
        print(f"[SIGNAL] Skipping - already approved/assigned", file=sys.stderr)
        return

    # Skip continuing students — they are handled by _auto_process_continuing_student()
    # which has its own probation/retention checks
    try:
        from enrollment_app.models import StudentEnrollment
        se = StudentEnrollment.objects.filter(
            student=instance.student,
            school_year=instance.school_year,
        ).first()
        if se and se.enrollee_type == 'continuing':
            print(f"[SIGNAL] Skipping - continuing student handled separately", file=sys.stderr)
            return
    except Exception:
        pass

    program_code = instance.selected_program_code
    print(f"[SIGNAL] Processing ProgramSelection for {instance.student.lrn}, program={program_code}", file=sys.stderr)

    # Check if AI Assistant is enabled for this program
    try:
        from admin_app.models import Program
        program = Program.objects.get(code=program_code)

        ai_pref = AIAssistantPreference.objects.filter(
            program=program,
            ai_enabled=True
        ).first()

        if not ai_pref:
            print(f"[SIGNAL] Skipping - AI not enabled for {program_code}", file=sys.stderr)
            return

    except Exception as e:
        print(f"[SIGNAL] Skipping - error checking AI: {str(e)}", file=sys.stderr)
        return

    # Start validation
    student = instance.student
    print(f"[SIGNAL] Validating student data...", file=sys.stderr)

    # 1. Check for duplicate enrollments
    if _has_duplicate_enrollment(student, instance):
        print(f"[SIGNAL] Skipping - duplicate enrollment found", file=sys.stderr)
        return

    # 2. Validate all required fields are complete
    if not _is_enrollment_complete(student, instance.school_year):
        print(f"[SIGNAL] Skipping - enrollment incomplete", file=sys.stderr)
        return

    # 3. Validate report card exists
    if not _has_report_card(student):
        print(f"[SIGNAL] Skipping - no report card", file=sys.stderr)
        return

    print(f"[SIGNAL] All validations passed - proceeding with AI processing", file=sys.stderr)

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
            
            # Update StudentEnrollment status (not deprecated Student field)
            if instance.school_year:
                enrollment = StudentEnrollment.objects.filter(
                    student=student,
                    school_year=instance.school_year
                ).first()
                if enrollment:
                    enrollment.enrollment_status = 'rejected'
                    enrollment.save()
            return

        if grade_result == 'manual_review':
            # Grade in lower half of range — needs coordinator review
            instance.admin_approved = False
            instance.admin_notes = f'AI flagged for manual review: Grade average in lower range for {program_code}'
            instance.save()
            
            # Update StudentEnrollment status (not deprecated Student field)
            if instance.school_year:
                enrollment = StudentEnrollment.objects.filter(
                    student=student,
                    school_year=instance.school_year
                ).first()
                if enrollment:
                    enrollment.enrollment_status = 'under_review'
                    enrollment.save()
            return

        # grade_result is 'auto_approve' or None — proceed with auto-approval and section assignment
        # Auto-assign to section
        # Get grade level from StudentEnrollment
        enrollment_grade = None
        try:
            from enrollment_app.models import StudentEnrollment
            se = StudentEnrollment.objects.filter(
                student=instance.student,
                school_year=instance.school_year,
            ).first()
            if se:
                enrollment_grade = se.grade_level
        except Exception:
            pass

        section = _get_next_available_section(program_code, instance.school_year, target_track, grade_level=enrollment_grade)
        if section:
            instance.assigned_section = section
            instance.section_assigned_at = timezone.now()

            # Update section capacity using database count (not incrementing)
            section.update_current_students_count()

        instance.save()

        # Update StudentEnrollment enrollment status (not deprecated Student field)
        if instance.school_year:
            enrollment = StudentEnrollment.objects.filter(
                student=student,
                school_year=instance.school_year
            ).first()
            if enrollment:
                enrollment.enrollment_status = 'approved'
                enrollment.save()


def _has_duplicate_enrollment(student, current_selection):
    """Check if student is already enrolled in another program/section"""
    existing = ProgramSelection.objects.filter(
        student=student,
        admin_approved=True
    ).exclude(pk=current_selection.pk).exists()

    return existing


def _is_enrollment_complete(student, school_year=None):
    """
    Validate all required enrollment forms are complete.
    Checks StudentEnrollment if school_year provided, otherwise falls back to Student model.
    """
    
    # Check StudentEnrollment if school_year is provided
    if school_year:
        enrollment = StudentEnrollment.objects.filter(
            student=student,
            school_year=school_year
        ).first()
        if not enrollment:
            return False
        
        # Check StudentEnrollment completion flags
        if not all([
            enrollment.student_data_completed,
            enrollment.family_data_completed,
            enrollment.survey_completed,
            enrollment.academic_data_completed,
            enrollment.program_selected
        ]):
            return False
    else:
        # Fallback to Student model (backward compat)
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
                         OR if student is a transferee (always requires curator review)
        'auto_reject' - grade < min (below range)
        None - no threshold defined or no grades available (skip check)
    """
    # TRANSFEREE CHECK: Always flag for manual review (coordinator verification needed)
    try:
        student_data = getattr(student, 'student_data', None)
        if student_data and 'transferee' in (student_data.enrolling_as or []):
            # Transferee students always require manual review regardless of grade
            return 'manual_review'
    except Exception:
        pass  # If error checking transferee status, continue with grade threshold check
    
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


def _get_next_available_section(program_code, school_year, target_track=None, grade_level=None):
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

    # CRITICAL: Always filter by grade_level if provided
    # Without this, sections from wrong grades/years can be assigned
    if grade_level:
        filters['grade_level'] = grade_level

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
        from TRAINING_ARC.placement_recommender_hybrid import HybridPlacementRecommender

        # Load recommender (Hybrid: Ridge + XGBoost)
        recommender = HybridPlacementRecommender(model_path='TRAINING_ARC/models/hybrid')
        if not recommender.load_model():
            print(f"[SIGNALS] ✗ Failed to load Hybrid recommender")
            return None

        print(f"[SIGNALS] ✓ HYBRID MODEL LOADED for track assignment (Ridge + XGBoost)")

        # Prepare student data for prediction
        student_features = _prepare_student_features(student)
        if student_features is None:
            return None

        # Get recommendations
        recommendations = recommender.recommend(student_features, top_n=5)

        # Find REGULAR track recommendation (Top-5 or Hetero)
        for rec in recommendations:
            if rec['placement'] == 'Top-5 Regular':
                print(f"[SIGNALS] → Recommending TOP5 for {student.id}")
                return 'TOP5'
            elif rec['placement'] == 'Hetero':
                print(f"[SIGNALS] → Recommending HETERO for {student.id}")
                return 'HETERO'

        # Fallback to HETERO if no clear recommendation
        print(f"[SIGNALS] → Fallback to HETERO for {student.id}")
        return 'HETERO'

    except Exception as e:
        # Fallback: assign to HETERO if recommendation fails
        # (Enhanced error handling for debugging)
        print(f"[SIGNALS] ✗ Hybrid recommendation error: {e}")
        return 'HETERO'


def _prepare_student_features(student):
    """
    Prepare student features for ML model prediction.
    Extract survey answers, academic data, and demographic info.

    Returns: pandas DataFrame with all required features for Hybrid recommender
    """
    try:
        import pandas as pd
        import numpy as np
        from enrollment_app.models import AcademicData

        # Initialize feature dictionary with defaults (NaN for missing)
        features = {}

        # ── ACADEMIC DATA (Grade 6 subjects) ──
        academic = None
        try:
            academic = student.academic_data.filter(school_year__isnull=False).first()
        except:
            academic = None

        # Map AcademicData fields to feature names
        academic_fields = {
            'mathematics': 'grade_math',
            'science': 'grade_science',
            'english': 'grade_english',
            'filipino': 'grade_filipino',
            'araling_panlipunan': 'grade_arpan',
            'edukasyon_sa_pagpapakatao': 'grade_esp',
            'edukasyon_pangkabuhayan': 'average_grade_tle',
            'mapeh': 'grade_mapeh',
        }

        for db_field, feature_name in academic_fields.items():
            if academic and hasattr(academic, db_field):
                val = getattr(academic, db_field, None)
                features[feature_name] = float(val) if val else np.nan
            else:
                features[feature_name] = np.nan

        # grade_6_final_average will be computed from the 8 subject grades
        g6_subjects = ['grade_math', 'grade_science', 'grade_english', 'grade_filipino',
                       'grade_arpan', 'grade_esp', 'average_grade_tle', 'grade_mapeh']
        g6_vals = [features.get(f, np.nan) for f in g6_subjects]
        g6_avg = np.nanmean([v for v in g6_vals if not np.isnan(v)]) if any(not np.isnan(v) for v in g6_vals) else np.nan
        features['grade_6_final_average'] = round(g6_avg, 2) if not np.isnan(g6_avg) else np.nan

        # ── DEMOGRAPHIC ──
        features['age'] = student.age if hasattr(student, 'age') else np.nan
        features['gender'] = 1 if getattr(student, 'gender', '').lower() in ['male', 'm'] else 0

        # ── SURVEY DATA ──
        if hasattr(student, 'survey_data') and student.survey_data:
            survey = student.survey_data
            enjoyed_subjects = survey.enjoyed_subjects or []
            difficulty_areas = survey.difficulty_areas or []

            # Subject enjoyment
            features['enjoy_math'] = 1 if 'Math' in enjoyed_subjects else 0
            features['enjoy_science'] = 1 if 'Science' in enjoyed_subjects else 0
            features['enjoy_english'] = 1 if 'English' in enjoyed_subjects else 0
            features['enjoy_filipino'] = 1 if 'Filipino' in enjoyed_subjects else 0
            features['enjoy_arpan'] = 1 if 'ARPAN' in enjoyed_subjects else 0
            features['enjoy_mapeh'] = 1 if 'MAPEH' in enjoyed_subjects else 0
            features['enjoy_tle'] = 1 if 'TLE' in enjoyed_subjects else 0

            # Academic difficulties
            features['difficulty_reading'] = 1 if 'Reading' in difficulty_areas else 0
            features['difficulty_writing'] = 1 if 'Writing' in difficulty_areas else 0
            features['difficulty_math'] = 1 if 'Math' in difficulty_areas else 0
            features['difficulty_focusing'] = 1 if 'Focusing' in difficulty_areas else 0
            features['difficulty_social_interaction'] = 1 if 'Social Interaction' in difficulty_areas else 0

            # Awards
            features['award_highest_honors'] = 1 if getattr(survey, 'extra_support', '') == 'Highest Honors' else 0
            features['award_high_honors'] = 1 if getattr(survey, 'extra_support', '') == 'High Honors' else 0
            features['award_with_honors'] = 1 if getattr(survey, 'extra_support', '') == 'With Honors' else 0

            # Other survey fields
            features['sped_learner'] = 1 if 'SPED' in difficulty_areas else 0
            features['working_student'] = 1 if getattr(survey, 'survey_responses_json', {}).get('working_student') else 0

            # Survey responses with defaults
            survey_json = getattr(survey, 'survey_responses_json', {}) or {}
            features['learning_style'] = survey_json.get('learning_style', 2)
            features['study_hours_daily'] = survey_json.get('study_hours_daily', 2)
            features['support_person'] = survey_json.get('support_person', 1)
            features['assignment_completion'] = survey_json.get('assignment_completion', 2)
            features['handle_difficulty'] = survey_json.get('handle_difficulty', 2)
            features['motivation_level'] = survey_json.get('motivation_level', 2)
            features['foreign_language_interest'] = survey_json.get('foreign_language_interest', 2)
            features['device_availability'] = survey_json.get('device_availability', 2)
            features['internet_access'] = survey_json.get('internet_access', 2)
            features['school_participation'] = survey_json.get('school_participation', 2)
            features['distance_from_school'] = survey_json.get('distance_from_school', 2)
            
            # Boolean fields
            features['enjoy_science_experiments'] = survey_json.get('enjoy_science_experiments', 0)
            features['enjoy_reading'] = survey_json.get('enjoy_reading', 0)
            features['enjoy_handson_activities'] = survey_json.get('enjoy_handson_activities', 0)
            features['enjoy_sports'] = survey_json.get('enjoy_sports', 0)
            features['enjoy_arts'] = survey_json.get('enjoy_arts', 0)
            features['enjoy_language_related_activities'] = survey_json.get('enjoy_language_related_activities', 0)
            features['competition_participation'] = survey_json.get('competition_participation', 0)
            features['family_income_help'] = survey_json.get('family_income_help', 0)
            features['received_awards'] = 1 if any([
                features.get('award_highest_honors'),
                features.get('award_high_honors'),
                features.get('award_with_honors')
            ]) else 0
            features['extra_support_recommended'] = survey_json.get('extra_support_recommended', 0)
            features['quiet_study_place'] = survey_json.get('quiet_study_place', 0)
            features['travel_difficulty'] = survey_json.get('travel_difficulty', 0)
            
            # Others
            features['absences_count'] = survey_json.get('absences_count', 0)
        else:
            # Set defaults if no survey data
            default_fields = [
                'learning_style', 'study_hours_daily', 'support_person', 'assignment_completion',
                'handle_difficulty', 'motivation_level', 'foreign_language_interest',
                'device_availability', 'internet_access', 'school_participation', 'distance_from_school',
                'enjoy_science_experiments', 'enjoy_reading', 'enjoy_handson_activities', 'enjoy_sports',
                'enjoy_arts', 'enjoy_language_related_activities', 'competition_participation',
                'family_income_help', 'extra_support_recommended', 'quiet_study_place', 'travel_difficulty',
                'absences_count'
            ]
            for field in default_fields:
                if field not in features:
                    features[field] = np.nan

        # All other non-academic fields default to NaN if not set
        all_non_academic = [
            'age', 'gender', 'learning_style', 'study_hours_daily', 'support_person',
            'assignment_completion', 'handle_difficulty', 'enjoy_math', 'enjoy_science',
            'enjoy_english', 'enjoy_filipino', 'enjoy_arpan', 'enjoy_mapeh', 'enjoy_tle',
            'motivation_level', 'enjoy_science_experiments', 'enjoy_reading',
            'enjoy_handson_activities', 'enjoy_sports', 'enjoy_arts',
            'enjoy_language_related_activities', 'foreign_language_interest',
            'competition_participation', 'device_availability', 'internet_access',
            'absences_count', 'family_income_help', 'school_participation',
            'received_awards', 'award_highest_honors', 'award_high_honors',
            'award_with_honors', 'award_best_science', 'award_best_math',
            'award_best_english', 'award_conduct', 'achiever_award',
            'difficulty_reading', 'difficulty_writing', 'difficulty_math',
            'difficulty_focusing', 'difficulty_social_interaction',
            'extra_support_recommended', 'quiet_study_place',
            'distance_from_school', 'travel_difficulty', 'has_valid_preference'
        ]

        for field in all_non_academic:
            if field not in features:
                features[field] = np.nan

        # Create DataFrame with single row
        df = pd.DataFrame([features])
        return df

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
    
    

@receiver(post_save, sender=SchoolYear)
def auto_generate_statuses_on_new_sy(sender, instance, created, **kwargs):
    """
    When a new school year is activated, auto-generate StudentAcademicYearStatus
    records for all approved students from the PREVIOUS school year.
    Only runs when is_active transitions to True.
    """
    if not instance.is_active:
        return

    # Find the previous school year (most recent inactive one)
    previous_sy = (
        SchoolYear.objects.filter(is_active=False)
        .exclude(pk=instance.pk)
        .order_by('-year_label')
        .first()
    )

    if not previous_sy:
        print(f"[SIGNAL] No previous school year found, skipping status generation.")
        return

    print(
        f"[SIGNAL] New SY activated: {instance.year_label}. "
        f"Generating statuses for {previous_sy.year_label}..."
    )

    # Run the management command logic inline
    try:
        from django.core.management import call_command
        call_command(
            'generate_academic_statuses',
            school_year=previous_sy.year_label,
        )
        print(f"[SIGNAL] Status generation complete for {previous_sy.year_label}")
    except Exception as e:
        import traceback
        print(f"[SIGNAL] Error generating statuses: {e}")
        traceback.print_exc()
        
def _auto_process_continuing_student(student, school_year):
    """
    Auto-process continuing student enrollment if AI is enabled for their program.
    Handles probation check and retention grade check (SPFL/SPTVE/STE).
    """
    import sys

    try:
        from enrollment_app.models import ProgramSelection, StudentEnrollment
        from admin_app.models import Program, Section
        from coordinator_app.models import (
            AIAssistantPreference, ProbationRecord, AcademicPerformance
        )
        from django.utils import timezone

        # Get ProgramSelection
        try:
            ps = ProgramSelection.objects.get(student=student)
        except ProgramSelection.DoesNotExist:
            print(f"[AI-CONTINUING] No ProgramSelection for {student.lrn}", file=sys.stderr)
            return

        # Skip if already approved
        if ps.admin_approved:
            print(f"[AI-CONTINUING] Already approved, skipping {student.lrn}", file=sys.stderr)
            return

        program_code = ps.selected_program_code
        if not program_code:
            print(f"[AI-CONTINUING] No program code for {student.lrn}", file=sys.stderr)
            return

        # ── PROBATION CHECK (BEFORE AI check) ────────────────────────────────
        # Must run before the AI gate so probation students aren't blocked
        # by "AI not enabled for STE" when they should be processed as REGULAR.
        from coordinator_app.models import ProbationRecord as _PR
        early_probation = _PR.get_active_for_student(student)
        if early_probation:
            print(
                f"[AI-CONTINUING] {student.lrn} ON PROBATION — "
                f"overriding {program_code} → REGULAR TOP5 before AI check",
                file=sys.stderr
            )
            program_code = 'REGULAR'
            ps.selected_program_code = 'REGULAR'
            ps.regular_track = 'TOP5'
            ps.save(update_fields=['selected_program_code', 'regular_track'])

        # Check if AI is enabled for this program (after probation override)
        try:
            program = Program.objects.get(code=program_code)
            ai_pref = AIAssistantPreference.objects.filter(
                program=program,
                ai_enabled=True,
            ).first()
            if not ai_pref:
                print(
                    f"[AI-CONTINUING] AI not enabled for {program_code}, "
                    f"skipping {student.lrn}",
                    file=sys.stderr
                )
                return
        except Program.DoesNotExist:
            print(f"[AI-CONTINUING] Program {program_code} not found", file=sys.stderr)
            return

        print(
            f"[AI-CONTINUING] Processing {student.lrn} | program={program_code}",
            file=sys.stderr
        )

        # Get StudentEnrollment for new school year
        enrollment = StudentEnrollment.objects.filter(
            student=student,
            school_year=school_year,
        ).first()

        if not enrollment or not enrollment.grade_level:
            print(
                f"[AI-CONTINUING] No enrollment/grade_level for "
                f"{student.lrn} in {school_year}",
                file=sys.stderr
            )
            return

        target_grade = enrollment.grade_level

        # Probation already handled above before AI check
        probation = early_probation

        # ── RETENTION GRADE CHECK (SPFL, SPTVE, STE) ─────────────────────────
        RETENTION_PROGRAMS  = ['SPFL', 'SPTVE', 'STE']
        RETENTION_THRESHOLD = 83

        if program_code in RETENTION_PROGRAMS and not probation:
            # Get previous school year from academic status
            prev_academic_status = student.academic_year_statuses.order_by(
                '-school_year__year_label'
            ).select_related('school_year').first()

            prev_sy = prev_academic_status.school_year if prev_academic_status else None

            if prev_sy:
                # Helper to get final grade for a subject keyword
                def get_final_grade(subject_keyword):
                    for quarter in [5, 4]:
                        perf = AcademicPerformance.objects.filter(
                            student=student,
                            school_year=prev_sy,
                            quarter=quarter,
                            subject__name__icontains=subject_keyword,
                        ).first()
                        if perf:
                            return float(perf.grade)
                    return None

                math_grade    = get_final_grade('Math')
                science_grade = get_final_grade('Science')

                print(
                    f"[AI-CONTINUING] Retention check {student.lrn}: "
                    f"Math={math_grade} Science={science_grade} "
                    f"threshold={RETENTION_THRESHOLD}",
                    file=sys.stderr
                )

                # No grades found — flag for manual review to be safe
                if math_grade is None and science_grade is None:
                    print(
                        f"[AI-CONTINUING] No Math/Science grades found for "
                        f"{student.lrn} — flagging for manual review",
                        file=sys.stderr
                    )
                    with transaction.atomic():
                        enrollment.enrollment_status = 'under_review'
                        enrollment.save()
                        ps.admin_notes = (
                            'AI flagged for manual review: '
                            'No Math/Science final grades found for retention check.'
                        )
                        ps.save()
                    return

                # Check if failed retention threshold
                failed_retention = False
                fail_reason      = ''

                if math_grade is not None and math_grade < RETENTION_THRESHOLD:
                    failed_retention = True
                    fail_reason = (
                        f'Math final grade {math_grade} is below '
                        f'retention threshold {RETENTION_THRESHOLD}.'
                    )
                elif science_grade is not None and science_grade < RETENTION_THRESHOLD:
                    failed_retention = True
                    fail_reason = (
                        f'Science final grade {science_grade} is below '
                        f'retention threshold {RETENTION_THRESHOLD}.'
                    )

                if failed_retention:
                    print(
                        f"[AI-CONTINUING] {student.lrn} FAILED RETENTION: "
                        f"{fail_reason} → moving to REGULAR",
                        file=sys.stderr
                    )
                    program_code = 'REGULAR'
                    try:
                        program = Program.objects.get(code='REGULAR')
                    except Program.DoesNotExist:
                        print(
                            f"[AI-CONTINUING] REGULAR program not found!",
                            file=sys.stderr
                        )
                        return

                    ps.selected_program_code = 'REGULAR'

                    # Create ProbationRecord for audit trail
                    original_program = ps.selected_program_code
                    try:
                        ProbationRecord.objects.get_or_create(
                            student=student,
                            school_year=prev_sy,
                            grade_level=enrollment.grade_level,
                            defaults={
                                'previous_program': original_program,
                                'moved_to_program': 'REGULAR',
                                'reason':           fail_reason,
                                'is_active':        True,
                            }
                        )
                        print(
                            f"[AI-CONTINUING] ProbationRecord created for {student.lrn}",
                            file=sys.stderr
                        )
                    except Exception as e:
                        print(
                            f"[AI-CONTINUING] Could not create ProbationRecord: {e}",
                            file=sys.stderr
                        )

        # ── DETERMINE TRACK FOR REGULAR PROGRAM ───────────────────────────────
        # If probation forced TOP5, honour that — don't override with prev section track
        if probation and program_code == 'REGULAR':
            target_track = 'TOP5'
            print(f"[AI-CONTINUING] Probation override: using TOP5 track", file=sys.stderr)
        else:
            target_track = ps.regular_track or None
            if program_code == 'REGULAR' and not target_track:
                # Keep same track from previous year's section
                try:
                    prev_status = student.academic_year_statuses.order_by(
                        '-school_year__year_label'
                    ).select_related('section').first()
                    if prev_status and prev_status.section:
                        target_track = getattr(
                            prev_status.section, 'regular_track', None
                        )
                except Exception:
                    pass
                if not target_track:
                    target_track = 'HETERO'

        print(
            f"[AI-CONTINUING] Finding section: program={program_code} "
            f"grade={target_grade.code if target_grade else 'NONE'} track={target_track}",
            file=sys.stderr
        )
        # Debug: show all sections being searched
        from admin_app.models import Section as Sec
        debug_sections = Sec.objects.filter(
            program__code=program_code,
            school_year=school_year,
        )
        print(f"[AI-CONTINUING] Sections found (before grade filter): {list(debug_sections.values('name', 'grade_level__name', 'school_year__year_label'))}", file=sys.stderr)

        # ── FIND AVAILABLE SECTION ────────────────────────────────────────────
        section_filters = {
            'program__code': program_code,
            'school_year':   school_year,
            'grade_level':   target_grade,
        }
        if program_code == 'REGULAR' and target_track:
            section_filters['regular_track'] = target_track

        available_section = None
        for section in Section.objects.filter(**section_filters).order_by('created_at'):
            if section.get_actual_count() < section.max_students:
                available_section = section
                break

        # For REGULAR: try alternative track if primary is full
        if not available_section and program_code == 'REGULAR' and target_track:
            alt_track = 'TOP5' if target_track == 'HETERO' else 'HETERO'
            alt_filters = dict(section_filters)
            alt_filters['regular_track'] = alt_track
            for section in Section.objects.filter(**alt_filters).order_by('created_at'):
                if section.get_actual_count() < section.max_students:
                    available_section = section
                    target_track      = alt_track
                    break

        # No section available — leave as submitted for coordinator
        if not available_section:
            print(
                f"[AI-CONTINUING] No available section for {student.lrn} "
                f"in {program_code} {target_grade.code}. "
                f"Leaving for manual assignment.",
                file=sys.stderr
            )
            # Still save the program change if probation/retention moved them
            if ps.selected_program_code != ps.__class__.objects.get(
                student=student
            ).selected_program_code:
                ps.save()
            return

        print(
            f"[AI-CONTINUING] ✅ Assigning {student.lrn} → {available_section.name}",
            file=sys.stderr
        )

        # ── APPROVE AND ASSIGN ────────────────────────────────────────────────
        with transaction.atomic():
            ps.admin_approved      = True
            ps.approved_by         = 'AI Assistant'
            ps.approved_at         = timezone.now()
            ps.assigned_section    = available_section
            ps.section_assigned_at = timezone.now()
            if target_track:
                ps.regular_track = target_track

            # Build admin notes explaining what happened
            notes_parts = ['Auto-approved by AI Assistant — continuing student, previously promoted.']
            if probation:
                notes_parts.append(
                    f'Probation detected: moved from '
                    f'{probation.previous_program} to REGULAR.'
                )
            if 'failed_retention' in dir() and failed_retention:
                notes_parts.append(f'Retention check failed: {fail_reason}')
            ps.admin_notes = ' '.join(notes_parts)
            ps.save()

            # Update section count
            available_section.update_current_students_count()

            # Update StudentEnrollment status
            enrollment.enrollment_status = 'approved'
            enrollment.save()

            # Log activity
            from coordinator_app.models import CoordinatorActivityLog
            sd           = getattr(student, 'student_data', None)
            student_name = sd.full_name if sd else student.lrn

            CoordinatorActivityLog.log(
                user=ai_pref.user,
                action='student_approved',
                description=(
                    f'AI auto-approved continuing student {student_name} '
                    f'and assigned to {available_section.name}'
                    + (f' [Probation: moved to REGULAR]' if probation else '')
                    + (f' [Retention fail: moved to REGULAR]'
                       if 'failed_retention' in dir() and failed_retention else '')
                ),
                category='enrollment',
                program=program,
                student_lrn=student.lrn,
                student_name=student_name,
                section_name=available_section.name,
                metadata={
                    'track':          target_track,
                    'grade_level':    target_grade.code,
                    'auto_processed': True,
                    'enrollee_type':  'continuing',
                    'probation':      bool(probation),
                    'retention_fail': 'failed_retention' in dir() and failed_retention,
                },
            )

            print(
                f"[AI-CONTINUING] ✅ DONE: {student.lrn} → "
                f"{available_section.name} ({program_code})",
                file=sys.stderr
            )

    except Exception as e:
        import traceback
        print(f"[AI-CONTINUING] ERROR for {student.lrn}: {e}", file=sys.stderr)
        traceback.print_exc()
