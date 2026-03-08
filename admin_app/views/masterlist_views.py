from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from admin_app.decorators import admin_required
from admin_app.models import Section
from enrollment_app.models import ProgramSelection, Student, StudentData, AcademicData


@admin_required
def masterlist(request):
    """
    General masterlist landing — redirects to sections.
    """
    return render(request, 'admin_app/masterlist.html', {})


@admin_required
def masterlist_by_section(request, section_id):
    """
    Masterlist for a specific section.
    Fetches all approved students assigned to this section.
    """
    section = get_object_or_404(
        Section.objects.select_related('program', 'adviser', 'grade_level', 'school_year'),
        pk=section_id
    )

    # Get all approved program selections for this section
    program_selections = ProgramSelection.objects.filter(
        assigned_section=section,
        admin_approved=True,
    ).select_related('student')

    # Build enriched student list
    students = []
    for ps in program_selections:
        student = ps.student
        try:
            student_data = student.student_data
        except Exception:
            student_data = None

        try:
            academic_data = student.academic_data
        except Exception:
            academic_data = None

        students.append({
            'lrn': student.lrn,
            'student_data': student_data,
            'program_selection': ps,
            'academic_data': academic_data,
            'get_enrollee_type_display': student.get_enrollee_type_display() if student.enrollee_type else '—',
        })

    # Sort alphabetically by last name
    students.sort(key=lambda x: x['student_data'].last_name.lower() if x['student_data'] else '')

    context = {
        'section': section,
        'students': students,
    }
    return render(request, 'admin_app/masterlist.html', context)