from django.shortcuts import render, get_object_or_404
from enrollment_app.models import Student
from datetime import date


def _age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


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

    # Compute age from date_of_birth on StudentData
    student_age = _age(sd.date_of_birth) if sd else None

    # enrolling_as is a JSONField list e.g. ['new'], ['transferee']
    enroll_list = []
    if sd and sd.enrolling_as:
        enroll_list = [e.replace('_', ' ').title() for e in sd.enrolling_as]

    context = {
        'student':     student,
        'sd':          sd,
        'fd':          fd,
        'ps':          ps,
        'student_age': student_age,
        'enroll_str':  ', '.join(enroll_list) if enroll_list else 'N/A',
        'sy_label':    student.school_year.year_label if student.school_year else 'N/A',
    }

    if request.GET.get('partial') == '1':
        return render(request, 'coordinator_app/coor_studentdetails_partial.html', context)

    return render(request, 'coordinator_app/coor-studentdetails.html', context)