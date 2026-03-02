from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
import json

from enrollment_app.models import ProgramSelection
from admin_app.models import Section, SchoolYear
from coordinator_app.models import Qualified_for_ste, AIAssistantPreference
from admin_app.models import Program


@login_required
def enrollment_management(request):
    """
    Unified enrollment management view with dynamic content loading.
    This replaces the old section_assignment view.
    """
    user_profile = getattr(request.user, 'profile', None)
    program_code = user_profile.program.code if user_profile and user_profile.program else None
    program_name = user_profile.program.name if user_profile and user_profile.program else None

    user_full_name = request.user.get_full_name() or request.user.username
    user_type = f"{program_code} Coordinator" if program_code else "Coordinator"
    user_photo = user_profile.photo.url if user_profile and user_profile.photo else None

    name_parts = user_full_name.split()
    user_initials = ''.join(part[0].upper() for part in name_parts[:2]) if name_parts else "CO"

    students_payload = []
    sections_payload = []

    if program_code:
        # Get active school year
        active_sy = (
            SchoolYear.objects.filter(is_active=True).order_by('-start_date').first()
            or SchoolYear.objects.order_by('-start_date').first()
        )

        # Get sections for this program
        active_grade = request.session.get('active_grade_level_code')
        sections_qs = Section.objects.filter(program__code=program_code)
        if active_sy:
            sections_qs = sections_qs.filter(school_year=active_sy)
        if active_grade:
            sections_qs = sections_qs.filter(grade_level__code=active_grade)

        # Update counts
        for section in sections_qs:
            section.update_current_students_count()

        sections_payload = [
            {
                'id': str(section.id),
                'name': section.name,
                'capacity': section.max_students,
                'current': section.current_students,
            }
            for section in sections_qs
        ]

        # Get all program selections
        selections = (
                ProgramSelection.objects
                .select_related('student', 'student__student_data')
                .filter(selected_program_code=program_code)
            )
        if active_grade:
            selections = selections.filter(student__grade_level__code=active_grade)
            
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
            display_name = ', '.join(
                [name_parts[0], ' '.join(name_parts[1:]).strip()]
            ).strip(', ')

            scores = score_map.get(student.lrn)
            exam_score = float(scores.exam_score) if scores and scores.exam_score else 0
            interview_score = float(scores.interview_score) if scores and scores.interview_score else 0

            students_payload.append({
                'name': display_name or student.lrn,
                'lrn': student.lrn,
                'exam': exam_score,
                'interview': interview_score,
                'finalSection': sel.assigned_section.id if sel.assigned_section else None,
                'admin_approved': sel.admin_approved,
                'approved_by': sel.approved_by or '',
                'approved_at': sel.approved_at.isoformat() if sel.approved_at else None,
                'enrollment_status': student.enrollment_status or '',
            })

    # Check if AI is enabled
    ai_enabled = False
    if program_code:
        try:
            program = user_profile.program
            ai_pref = AIAssistantPreference.objects.filter(
                user=request.user,
                program=program,
                ai_enabled=True
            ).first()
            ai_enabled = ai_pref is not None
        except Exception:
            ai_enabled = False

    context = {
        'program_code': program_code,
        'program_name': program_name,
        'students_json': json.dumps(students_payload),
        'sections_json': json.dumps(sections_payload),
        'user_full_name': user_full_name,
        'user_type': user_type,
        'user_photo': user_photo,
        'user_initials': user_initials,
        'ai_enabled': ai_enabled,
        
    }

    return render(request, 'coordinator_app/enrollment_management.html', context)


@login_required
@require_http_methods(["GET"])
def get_manual_mode_content(request):
    """
    API endpoint to fetch Manual mode content HTML.
    Returns only the content portion (not the full page).
    """
    try:
        # Debug: Print to console
        print("DEBUG: get_manual_mode_content called")

        # Render the manual mode partial template
        html = render_to_string(
            'coordinator_app/partials/manual_mode_content.html',
            {},
            request=request
        )

        print(f"DEBUG: Successfully rendered manual mode content, length: {len(html)}")
        return HttpResponse(html, content_type='text/html')
    except Exception as e:
        import traceback
        print(f"ERROR in get_manual_mode_content: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_ai_mode_content(request):
    """
    API endpoint to fetch AI mode content HTML.
    Returns only the content portion (not the full page).
    """
    try:
        # Debug: Print to console
        print("DEBUG: get_ai_mode_content called")

        # Query students flagged for manual review by AI
        user_profile = getattr(request.user, 'profile', None)
        program_code = user_profile.program.code if user_profile and user_profile.program else None
        if program_code:
            under_review_students = ProgramSelection.objects.filter(
                selected_program_code=program_code,
                admin_approved=False,
                admin_rejected=False,
                student__enrollment_status='under_review',
            ).select_related('student', 'student__student_data', 'student__academic_data')
            under_review_count = under_review_students.count()
        else:
            under_review_students = ProgramSelection.objects.none()
            under_review_count = 0

        # Render the AI mode partial template
        html = render_to_string(
            'coordinator_app/partials/ai_mode_content.html',
            {
                'under_review_students': under_review_students,
                'under_review_count': under_review_count,
            },
            request=request
        )

        print(f"DEBUG: Successfully rendered AI mode content, length: {len(html)}")
        return HttpResponse(html, content_type='text/html')
    except Exception as e:
        import traceback
        print(f"ERROR in get_ai_mode_content: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def refresh_enrollment_data(request):
    """
    API endpoint to refresh enrollment data without page reload.
    Returns updated students and sections data as JSON.
    """
    try:
        user_profile = getattr(request.user, 'profile', None)
        program_code = user_profile.program.code if user_profile and user_profile.program else None

        if not program_code:
            return JsonResponse({'error': 'No program assigned'}, status=400)

        students_payload = []
        sections_payload = []

        # Get active school year
        active_sy = (
            SchoolYear.objects.filter(is_active=True).order_by('-start_date').first()
            or SchoolYear.objects.order_by('-start_date').first()
        )

        # Get sections
        active_grade = request.session.get('active_grade_level_code')
        sections_qs = Section.objects.filter(program__code=program_code)
        if active_sy:
            sections_qs = sections_qs.filter(school_year=active_sy)
        if active_grade:
            sections_qs = sections_qs.filter(grade_level__code=active_grade)

        for section in sections_qs:
            section.update_current_students_count()

        sections_payload = [
            {
                'id': str(section.id),
                'name': section.name,
                'capacity': section.max_students,
                'current': section.current_students,
            }
            for section in sections_qs
        ]

        # Get students
        selections = (
            ProgramSelection.objects
            .select_related('student', 'student__student_data')
            .filter(selected_program_code=program_code)
        )
        if active_grade:
            selections = selections.filter(student__grade_level__code=active_grade)
            
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
            display_name = ', '.join(
                [name_parts[0], ' '.join(name_parts[1:]).strip()]
            ).strip(', ')

            scores = score_map.get(student.lrn)
            exam_score = float(scores.exam_score) if scores and scores.exam_score else 0
            interview_score = float(scores.interview_score) if scores and scores.interview_score else 0

            students_payload.append({
                'name': display_name or student.lrn,
                'lrn': student.lrn,
                'exam': exam_score,
                'interview': interview_score,
                'finalSection': sel.assigned_section.id if sel.assigned_section else None,
                'admin_approved': sel.admin_approved,
                'approved_by': sel.approved_by or '',
                'approved_at': sel.approved_at.isoformat() if sel.approved_at else None,
            })

        return JsonResponse({
            'success': True,
            'students': students_payload,
            'sections': sections_payload
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def toggle_ai_mode(request):
    """
    API endpoint to toggle AI mode on/off for the coordinator's program.
    Updates AIAssistantPreference in database.
    """
    try:
        data = json.loads(request.body)
        ai_enabled = data.get('ai_enabled', False)

        # Get coordinator's program
        user_profile = getattr(request.user, 'profile', None)
        if not user_profile or not user_profile.program:
            return JsonResponse({'error': 'No program assigned'}, status=400)

        program = user_profile.program

        # Update or create AI preference
        ai_pref, created = AIAssistantPreference.objects.update_or_create(
            user=request.user,
            program=program,
            defaults={'ai_enabled': ai_enabled}
        )

        return JsonResponse({
            'success': True,
            'ai_enabled': ai_enabled,
            'message': f"AI mode {'enabled' if ai_enabled else 'disabled'} successfully"
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)
