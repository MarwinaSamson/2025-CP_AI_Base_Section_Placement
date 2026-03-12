from django.shortcuts import render, get_object_or_404
from admin_app.decorators import admin_required
from enrollment_app.models import Student
from coordinator_app.models import AcademicPerformance
from decimal import Decimal
from datetime import date


def _age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _build_grade_data(student):
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
                final_ratings.append(final_rating)
            else:
                status = None

            subjects_list.append({**subj_data, 'final_rating': final_rating, 'status': status})

        if final_ratings:
            general_average = round(sum(final_ratings) / len(final_ratings), 2)
            has_incomplete = any(s['final_rating'] is None for s in subjects_list)
            all_passed = all(
                s['final_rating'] >= 75
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

        result.append({
            'grade_level': data['grade_level'],
            'school_year': data['school_year'],
            'subjects_list': subjects_list,
            'general_average': general_average,
            'promotion_status': promotion_status,
        })

    return result


@admin_required
def student_details(request, lrn):
    student = get_object_or_404(
        Student.objects.select_related(
            'school_year',
            'student_data',
            'academic_data',
            'family_data',
            'family_data__father',
            'family_data__mother',
            'family_data__other_guardian',
            'program_selection',
            'program_selection__assigned_section',
            'program_selection__assigned_section__program',
            'program_selection__assigned_section__grade_level',
        ),
        lrn=lrn
    )

    sd = getattr(student, 'student_data', None)
    fd = getattr(student, 'family_data', None)
    ps = getattr(student, 'program_selection', None)

    student_age = _age(sd.date_of_birth) if sd and getattr(sd, 'date_of_birth', None) else None

    enroll_list = []
    if sd and getattr(sd, 'enrolling_as', None):
        enroll_list = [e.replace('_', ' ').title() for e in sd.enrolling_as]

    back_url = request.GET.get('back', '')

    context = {
        'student':           student,
        'sd':                sd,
        'fd':                fd,
        'ps':                ps,
        'student_age':       student_age,
        'enroll_str':        ', '.join(enroll_list) if enroll_list else 'N/A',
        'sy_label':          student.school_year.year_label if student.school_year else 'N/A',
        'back_url':          back_url,
        'grade_levels_data': _build_grade_data(student),
    }

    if request.GET.get('partial') == '1':
        return render(request, 'admin_app/studentDetails_partial.html', context)

    return render(request, 'admin_app/studentDetails.html', context)