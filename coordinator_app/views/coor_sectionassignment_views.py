from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import json

from enrollment_app.models import ProgramSelection
from coordinator_app.models import Qualified_for_ste


@login_required
def section_assignment(request):
    """Section assignment dashboard scoped to the coordinator's program."""

    program_code = None
    if hasattr(request.user, 'profile') and request.user.profile.program:
        program_code = request.user.profile.program.code

    students_payload = []

    if program_code:
        selections = (
            ProgramSelection.objects
            .select_related('student', 'student__student_data')
            .filter(selected_program_code=program_code)
        )

        lrns = [sel.student.lrn for sel in selections]
        score_map = {
            rec.student_lrn: rec
            for rec in Qualified_for_ste.objects.filter(student_lrn__in=lrns)
        }

        for sel in selections:
            student = sel.student
            student_data = getattr(student, 'student_data', None)
            name_parts = [
                getattr(student_data, 'last_name', ''),
                getattr(student_data, 'first_name', ''),
                getattr(student_data, 'middle_name', '') or ''
            ]
            display_name = ', '.join([name_parts[0], ' '.join(name_parts[1:]).strip()]).strip(', ')

            scores = score_map.get(student.lrn)
            exam_score = float(scores.exam_score) if scores and scores.exam_score is not None else 0
            interview_score = float(scores.interview_score) if scores and scores.interview_score is not None else 0

            students_payload.append({
                'name': display_name or student.lrn,
                'lrn': student.lrn,
                'exam': exam_score,
                'interview': interview_score,
                'aiSuggestion': sel.assigned_section or program_code,
            })

    context = {
        'program_code': program_code,
        'students_json': json.dumps(students_payload),
    }

    return render(request, 'coordinator_app/sectionAssignment.html', context)