from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
import json

from admin_app.decorators import admin_required
from admin_app.models import ProgramMoveRequest, Program, SchoolYear, Section
from enrollment_app.models import Student, ProgramSelection, EnrollmentStatusLog


@admin_required
def get_pending_move_requests(request):
    """Returns pending move requests count + list for admin bell notification."""
    pending = ProgramMoveRequest.objects.filter(status='pending').select_related(
        'student__student_data', 'requested_by'
    )

    items = []
    for mr in pending:
        student_name = (
            mr.student.student_data.full_name
            if hasattr(mr.student, 'student_data') and mr.student.student_data
            else mr.student.lrn
        )
        items.append({
            'id': mr.id,
            'student_lrn': mr.student.lrn,
            'student_name': student_name,
            'from_program': mr.from_program_code,
            'to_program': mr.to_program_code,
            'reason': mr.reason,
            'requested_by': mr.requested_by.get_full_name() if mr.requested_by else 'Unknown',
            'created_at': mr.created_at.strftime('%b %d, %Y'),
        })

    return JsonResponse({'count': len(items), 'requests': items})


@admin_required
@require_http_methods(["POST"])
def review_move_request(request, move_request_id):
    """
    Admin approves or rejects a move request.
    On approval: moves student to new program, clears old section,
    and auto-places in new program section if available.
    Admin manually picks target section.
    """
    try:
        with transaction.atomic():
            data = json.loads(request.body)
            action = data.get('action')  # 'approve' or 'reject'
            review_notes = data.get('review_notes', '')
            target_section_id = data.get('target_section_id')  # required for approve

            if action not in ('approve', 'reject'):
                return JsonResponse({'success': False, 'error': 'Invalid action.'}, status=400)

            move_request = ProgramMoveRequest.objects.select_related(
                'student', 'from_section'
            ).get(id=move_request_id, status='pending')

            if action == 'reject':
                move_request.status = 'rejected'
                move_request.reviewed_by = request.user
                move_request.review_notes = review_notes
                move_request.reviewed_at = timezone.now()
                move_request.save()
                return JsonResponse({'success': True, 'message': 'Move request rejected.'})

            # --- APPROVE ---
            if not target_section_id:
                return JsonResponse({
                    'success': False,
                    'error': 'Target section is required to approve a move request.'
                }, status=400)

            target_section = Section.objects.select_related('program').get(id=target_section_id)

            # Verify section belongs to the target program
            if target_section.program.code.upper() != move_request.to_program_code.upper():
                return JsonResponse({
                    'success': False,
                    'error': f'Selected section belongs to {target_section.program.code}, '
                             f'not {move_request.to_program_code}.'
                }, status=400)

            # Check section capacity
            if target_section.get_actual_count() >= target_section.max_students:
                return JsonResponse({
                    'success': False,
                    'error': f'Section {target_section.name} is full '
                             f'({target_section.max_students}/{target_section.max_students}).'
                }, status=400)

            student = move_request.student
            program_selection = ProgramSelection.objects.get(student=student)

            # Remove from old section
            old_section = program_selection.assigned_section
            old_program_code = program_selection.selected_program_code

            # Update program selection
            program_selection.selected_program_code = move_request.to_program_code
            program_selection.assigned_section = target_section
            program_selection.section_assigned_at = timezone.now()
            program_selection.admin_approved = True
            program_selection.admin_notes = (
                f'[PROGRAM MOVE] From {old_program_code} to {move_request.to_program_code}. '
                f'Admin: {review_notes}'
            )
            program_selection.save()

            # Update section counts
            if old_section:
                old_section.update_current_students_count()
            target_section.update_current_students_count()

            # Log status change
            EnrollmentStatusLog.objects.create(
                student=student,
                old_status=student.enrollment_status,
                new_status='approved',
                changed_by=request.user.get_full_name() or request.user.username,
                change_reason=(
                    f'Program moved from {old_program_code} to {move_request.to_program_code} '
                    f'by admin. Section: {target_section.name}'
                )
            )

            # Mark move request as approved
            move_request.status = 'approved'
            move_request.reviewed_by = request.user
            move_request.review_notes = review_notes
            move_request.reviewed_at = timezone.now()
            move_request.save()

            student_name = (
                student.student_data.full_name
                if hasattr(student, 'student_data') and student.student_data
                else student.lrn
            )

            return JsonResponse({
                'success': True,
                'message': (
                    f'{student_name} has been moved from {old_program_code} '
                    f'to {move_request.to_program_code} and placed in {target_section.name}.'
                ),
                'student_name': student_name,
                'new_program': move_request.to_program_code,
                'new_section': target_section.name,
            })

    except ProgramMoveRequest.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Move request not found or already reviewed.'}, status=404)
    except Section.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Target section not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@admin_required
def get_sections_for_program(request):
    """Returns sections available for a given program code (for admin move modal)."""
    program_code = request.GET.get('program_code', '').upper()
    if not program_code:
        return JsonResponse({'success': False, 'error': 'Program code required.'}, status=400)

    school_year = SchoolYear.objects.filter(is_active=True).first()
    sections = Section.objects.filter(
        program__code=program_code,
        school_year=school_year
    ).order_by('name')

    data = []
    for s in sections:
        actual = s.get_actual_count()
        data.append({
            'id': s.id,
            'name': s.name,
            'current': actual,
            'max': s.max_students,
            'available': s.max_students - actual,
            'is_full': actual >= s.max_students,
            'regular_track': getattr(s, 'regular_track', '') or '',
        })

    return JsonResponse({'success': True, 'sections': data})