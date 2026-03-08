from django.shortcuts import render, get_object_or_404
from admin_app.decorators import admin_required
from enrollment_app.models import Student
from datetime import date


def _age(dob):
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


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

    # Back URL: if came from masterlist, go back there
    back_url = request.GET.get('back', '')

    context = {
        'student':     student,
        'sd':          sd,
        'fd':          fd,
        'ps':          ps,
        'student_age': student_age,
        'enroll_str':  ', '.join(enroll_list) if enroll_list else 'N/A',
        'sy_label':    student.school_year.year_label if student.school_year else 'N/A',
        'back_url':    back_url,
    }

    if request.GET.get('partial') == '1':
        return render(request, 'admin_app/studentDetails_partial.html', context)

    return render(request, 'admin_app/studentDetails.html', context)