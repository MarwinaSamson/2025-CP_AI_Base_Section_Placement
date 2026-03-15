from django.shortcuts import render, get_object_or_404
from enrollment_app.models import Student
from coordinator_app.models import AcademicPerformance
from datetime import date


def _age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _build_grade_data(student):
    """
    Returns a list ordered by grade level (G7->G10), each entry:
    {
      'grade_level': GradeLevel,
      'school_year': SchoolYear,
      'subjects_list': [
        {
          'subject': Subject,
          'q1': Decimal|None, 'q2': ..., 'q3': ..., 'q4': ..., 'final': ...,
          'final_rating': Decimal|None,
          'status': 'Passed' | 'Failed' | None,
        }, ...
      ],
      'general_average': Decimal|None,
      'promotion_status': 'Promoted' | 'Failed' | 'Incomplete' | None,
      'q1_available': bool,
      'q2_available': bool,
      'q3_available': bool,
      'q4_available': bool,
      'final_available': bool,
      'q1_average': Decimal|None,
      'q2_average': Decimal|None,
      'q3_average': Decimal|None,
      'q4_average': Decimal|None,
    }
    """
    from decimal import Decimal

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

            if final_rating is not None:
                status = 'Passed' if final_rating >= 75 else 'Failed'
            else:
                status = None

            if final_rating is not None:
                final_ratings.append(final_rating)

            subjects_list.append({
                **subj_data,
                'final_rating': final_rating,
                'status': status,
            })

        # General Average for this grade level
        if final_ratings:
            general_average = round(sum(final_ratings) / len(final_ratings), 2)
            all_passed = all(
                s['final_rating'] is not None and s['final_rating'] >= 75
                for s in subjects_list if s['final_rating'] is not None
            )
            has_incomplete = any(s['final_rating'] is None for s in subjects_list)

            if has_incomplete:
                promotion_status = 'Incomplete'
            elif all_passed and general_average >= 75:
                promotion_status = 'Promoted'
            else:
                promotion_status = 'Failed'
        else:
            general_average = None
            promotion_status = None

        # Per-quarter availability: only True when ALL subjects have that quarter's grade
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
            # Quarter availability flags
            'q1_available':     q1_avg is not None,
            'q2_available':     q2_avg is not None,
            'q3_available':     q3_avg is not None,
            'q4_available':     q4_avg is not None,
            'final_available':  general_average is not None,
            # Quarter averages
            'q1_average':       q1_avg,
            'q2_average':       q2_avg,
            'q3_average':       q3_avg,
            'q4_average':       q4_avg,
        })

    return result


def student_details(request, lrn):
    student = get_object_or_404(
        Student.objects.select_related(
            'school_year',
            'student_data',
            'family_data',
            'family_data__father',
            'family_data__mother',
            'family_data__other_guardian',
            'program_selection',
        ),
        lrn=lrn
    )

    sd = getattr(student, 'student_data', None)
    fd = getattr(student, 'family_data', None)
    ps = getattr(student, 'program_selection', None)

    student_age = _age(sd.date_of_birth) if sd else None

    enroll_list = []
    if sd and sd.enrolling_as:
        enroll_list = [e.replace('_', ' ').title() for e in sd.enrolling_as]

    context = {
        'student':           student,
        'sd':                sd,
        'fd':                fd,
        'ps':                ps,
        'student_age':       student_age,
        'enroll_str':        ', '.join(enroll_list) if enroll_list else 'N/A',
        'sy_label':          student.school_year.year_label if student.school_year else 'N/A',
        'grade_levels_data': _build_grade_data(student),
    }

    if request.GET.get('partial') == '1':
        return render(request, 'coordinator_app/coor_studentdetails_partial.html', context)

    return render(request, 'coordinator_app/coor-studentdetails.html', context)