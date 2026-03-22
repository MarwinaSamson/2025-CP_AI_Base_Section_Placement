from django.shortcuts import render, get_object_or_404
from enrollment_app.models import (
    Student, StudentEnrollment, StudentAcademicYearStatus, ProgramSelection
)
from coordinator_app.models import AcademicPerformance, ProbationRecord
from admin_app.models import GradeLevel
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from datetime import date
from django.db.models import Case, When, IntegerField


def _age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _build_grade_data(student):
    """
    Returns a list ordered by grade level (G7->G10), each entry with
    quarter availability flags, averages, and promotion status.
    """
    performances = (
        AcademicPerformance.objects
        .filter(student=student)
        .select_related('subject', 'grade_level', 'school_year')
        .order_by('grade_level__code', 'subject__name', 'quarter')
    )

    grade_data = {}
    q_field = {1: 'q1', 2: 'q2', 3: 'q3', 4: 'q4', 5: 'final'}

    for perf in performances:
        gl_id = perf.grade_level_id
        if gl_id not in grade_data:
            grade_data[gl_id] = {
                'grade_level': perf.grade_level,
                'school_year': perf.school_year,
                'program_code': perf.program.code if perf.program else '',
                'subjects': {},
            }
        subj_id = perf.subject_id
        if subj_id not in grade_data[gl_id]['subjects']:
            grade_data[gl_id]['subjects'][subj_id] = {
                'subject': perf.subject,
                'q1': None, 'q2': None, 'q3': None, 'q4': None, 'final': None,
            }
        field = q_field.get(perf.quarter)
        if field:
            grade_data[gl_id]['subjects'][subj_id][field] = perf.grade

    result = []
    for gl_id, data in sorted(grade_data.items(), key=lambda x: x[1]['grade_level'].code):
        subjects_list = []
        final_ratings = []

        for subj_data in sorted(data['subjects'].values(), key=lambda x: x['subject'].name):
            q_grades = [subj_data[f'q{i}'] for i in range(1, 5) if subj_data[f'q{i}'] is not None]

            if subj_data['final'] is not None:
                final_rating = subj_data['final']
            elif q_grades:
                final_rating = round(sum(q_grades) / len(q_grades), 2)
            else:
                final_rating = None

            # Determine status with STE probation threshold logic
            subject_obj = subj_data['subject']
            # Get program code from grade_data context
            section_program = data.get('program_code', '')
            is_ste_threshold = (
                getattr(subject_obj, 'is_threshold_subject', False)
                and section_program == 'STE'
            )

            if final_rating is not None:
                if is_ste_threshold:
                    if final_rating >= 83:
                        status = 'Passed'
                    elif final_rating >= 75:
                        status = 'Probation Risk'
                    else:
                        status = 'Failed'
                else:
                    status = 'Passed' if final_rating >= 75 else 'Failed'
            else:
                status = None

            # Per-quarter status for STE threshold subjects
            quarter_statuses = {}
            for q_num in range(1, 5):
                q_grade = subj_data.get(f'q{q_num}')
                if q_grade is not None:
                    if is_ste_threshold:
                        if q_grade >= 83:
                            quarter_statuses[f'q{q_num}_status'] = 'Passed'
                        elif q_grade >= 75:
                            quarter_statuses[f'q{q_num}_status'] = 'Probation Risk'
                        else:
                            quarter_statuses[f'q{q_num}_status'] = 'Failed'
                    else:
                        quarter_statuses[f'q{q_num}_status'] = 'Passed' if q_grade >= 75 else 'Failed'
                else:
                    quarter_statuses[f'q{q_num}_status'] = None

            if final_rating is not None:
                final_ratings.append(final_rating)

            subjects_list.append({
                **subj_data,
                'final_rating': final_rating,
                'status': status,
                'is_ste_threshold': is_ste_threshold,
                **quarter_statuses,
            })

        if final_ratings:
            general_average = round(sum(final_ratings) / len(final_ratings), 2)
            has_incomplete = any(s['final_rating'] is None for s in subjects_list)
            all_passed = all(
                s['final_rating'] is not None and s['final_rating'] >= 75
                for s in subjects_list if s['final_rating'] is not None
            )
            if has_incomplete:
                promotion_status = 'Incomplete'
            elif all_passed and general_average >= 75:
                promotion_status = 'Promoted'
            else:
                promotion_status = 'Failed'
        else:
            general_average = None
            promotion_status = None

        def q_avg(q_key):
            grades = [s[q_key] for s in subjects_list if s[q_key] is not None]
            if len(grades) == len(subjects_list) and len(grades) > 0:
                return round(sum(grades) / len(grades), 2)
            return None

        q1_avg = q_avg('q1')
        q2_avg = q_avg('q2')
        q3_avg = q_avg('q3')
        q4_avg = q_avg('q4')

        result.append({
            'grade_level':      data['grade_level'],
            'school_year':      data['school_year'],
            'subjects_list':    subjects_list,
            'general_average':  general_average,
            'promotion_status': promotion_status,
            'q1_available':     q1_avg is not None,
            'q2_available':     q2_avg is not None,
            'q3_available':     q3_avg is not None,
            'q4_available':     q4_avg is not None,
            'final_available':  general_average is not None,
            'q1_average':       q1_avg,
            'q2_average':       q2_avg,
            'q3_average':       q3_avg,
            'q4_average':       q4_avg,
        })

    return result


def _build_progression_data(student):
    """
    Builds a G7 -> G8 -> G9 -> G10 progression timeline.

    Each node contains:
      - grade_level        : GradeLevel instance
      - school_year        : SchoolYear from StudentEnrollment
      - enrollment_status  : from StudentEnrollment
      - enrollee_type      : new / continuing / transferee
      - section_name       : from ProgramSelection or StudentAcademicYearStatus
      - program_code       : from ProgramSelection
      - regular_track      : from ProgramSelection
      - adviser_name       : from Section.adviser
      - overall_grade      : from StudentAcademicYearStatus
      - final_status       : promoted / retained / etc.
      - remarks            : from StudentAcademicYearStatus
      - has_data           : True if any enrollment record exists for this grade
      - is_current         : True for the most recent enrollment
    """
    

    grade_order = Case(
        When(code='G7', then=1),
        When(code='G8', then=2),
        When(code='G9', then=3),
        When(code='G10', then=4),
        default=5,
        output_field=IntegerField()
    )
    all_grade_levels = GradeLevel.objects.filter(
        code__in=['G7', 'G8', 'G9', 'G10']
    ).annotate(sort_order=grade_order).order_by('sort_order')

    enrollments = (
        StudentEnrollment.objects
        .filter(student=student)
        .select_related('school_year', 'grade_level')
        .order_by('school_year__year_label')
    )
    enrollment_map = {e.grade_level_id: e for e in enrollments if e.grade_level_id}

    statuses = (
        StudentAcademicYearStatus.objects
        .filter(student=student)
        .select_related('school_year', 'grade_level', 'section', 'section__adviser', 'recorded_by')
    )
    status_map = {s.grade_level_id: s for s in statuses if s.grade_level_id}

    try:
        ps = student.program_selection
    except Exception:
        ps = None

    latest_enrollment = enrollments.last()
    current_gl_id = latest_enrollment.grade_level_id if latest_enrollment else None

    progression = []
    for gl in all_grade_levels:
        enrollment = enrollment_map.get(gl.id)
        acad_status = status_map.get(gl.id)
        is_current = (gl.id == current_gl_id)

        section_name = None
        adviser_name = None
        program_code = None
        regular_track = None

        # Pull section info from academic year status (historical grades)
        if acad_status and acad_status.section:
            section_name = acad_status.section.name
            if acad_status.section.adviser:
                adviser_name = acad_status.section.adviser.get_full_name()

        # For the current grade, also pull from ProgramSelection
        if is_current and ps:
            if ps.assigned_section:
                section_name = section_name or ps.assigned_section.name
                if not adviser_name and ps.assigned_section.adviser:
                    adviser_name = ps.assigned_section.adviser.get_full_name()
            program_code = ps.selected_program_code
            regular_track = ps.regular_track

        progression.append({
            'grade_level':       gl,
            'school_year':       enrollment.school_year if enrollment else None,
            'enrollment_status': enrollment.enrollment_status if enrollment else None,
            'enrollee_type':     enrollment.enrollee_type if enrollment else None,
            'section_name':      section_name,
            'program_code':      program_code,
            'regular_track':     regular_track,
            'adviser_name':      adviser_name,
            'overall_grade':     acad_status.overall_grade if acad_status else None,
            'final_status':      acad_status.final_status if acad_status else None,
            'remarks':           acad_status.remarks if acad_status else None,
            'has_data':          enrollment is not None,
            'is_current':        is_current,
        })

    return progression


def student_details(request, lrn):
    student = get_object_or_404(
        Student.objects.select_related(
            'student_data',
            'family_data',
            'family_data__father',
            'family_data__mother',
            'family_data__other_guardian',
            'program_selection',
            'program_selection__assigned_section',
            'program_selection__assigned_section__adviser',
        ),
        lrn=lrn
    )

    sd = getattr(student, 'student_data', None)
    fd = getattr(student, 'family_data', None)
    ps = getattr(student, 'program_selection', None)

    student_age = _age(sd.date_of_birth) if sd else None

    enroll_list = []
    if sd and sd.enrolling_as:
        raw = sd.enrolling_as
        if isinstance(raw, list):
            enroll_list = [e.replace('_', ' ').title() for e in raw]
        elif isinstance(raw, str):
            enroll_list = [raw.replace('_', ' ').title()]

    # Get latest enrollment for school year / status display
    latest_enrollment = (
        StudentEnrollment.objects
        .filter(student=student)
        .select_related('school_year', 'grade_level')
        .order_by('-school_year__year_label')
        .first()
    )

    # Get all probation records for this student (active and inactive)
    probation_records = ProbationRecord.objects.filter(
        student=student
    ).select_related('school_year', 'grade_level', 'reinstated_by').order_by('-flagged_at')

    # Build a map of grade_level_id -> probation record for easy template lookup
    probation_map = {}
    for rec in probation_records:
        if rec.grade_level_id:
            probation_map[rec.grade_level_id] = rec

    context = {
        'student':           student,
        'sd':                sd,
        'fd':                fd,
        'ps':                ps,
        'student_age':       student_age,
        'enroll_str':        ', '.join(enroll_list) if enroll_list else 'N/A',
        'sy_label':          latest_enrollment.school_year.year_label if latest_enrollment and latest_enrollment.school_year else 'N/A',
        'enroll_status':     latest_enrollment.enrollment_status if latest_enrollment else 'N/A',
        'enrollee_type':     latest_enrollment.get_enrollee_type_display() if latest_enrollment else 'N/A',
        'grade_levels_data': _build_grade_data(student),
        'progression':       _build_progression_data(student),
        'latest_enrollment': latest_enrollment,
        'probation_records': probation_records,
        'probation_map':     probation_map,
    }

    if request.GET.get('partial') == '1':
        return render(request, 'coordinator_app/coor_studentdetails_partial.html', context)

    return render(request, 'coordinator_app/coor-studentdetails.html', context)


@login_required
@require_http_methods(["POST"])
def lift_probation(request, lrn):
    """Lift an active probation record for a student."""
    try:
        data = json.loads(request.body)
        reason = (data.get('reason') or '').strip()

        if not reason:
            return JsonResponse({'success': False, 'error': 'Reason is required.'}, status=400)

        student = get_object_or_404(Student, lrn=lrn)

        probation = ProbationRecord.objects.filter(
            student=student,
            is_active=True,
        ).order_by('-flagged_at').first()

        if not probation:
            return JsonResponse({
                'success': False,
                'error': 'No active probation record found for this student.'
            }, status=404)

        # Reinstate — marks is_active=False, records who lifted it
        probation.reinstate(reinstated_by_user=request.user, reason=reason)

        lifted_by = request.user.get_full_name() or request.user.username

        return JsonResponse({
            'success': True,
            'message': f'Probation successfully lifted by {lifted_by}.',
            'lifted_by': lifted_by,
            'lifted_at': probation.reinstated_at.strftime('%B %d, %Y at %I:%M %p'),
            'reason': reason,
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)