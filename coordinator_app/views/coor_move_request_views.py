from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json

from admin_app.decorators import coordinator_required
from admin_app.models import ProgramMoveRequest, Program, SchoolYear
from enrollment_app.models import Student, ProgramSelection


@coordinator_required
@require_http_methods(["POST"])
def submit_move_request(request, student_id):
    """
    Coordinator submits a program move request for a student.
    Admin must approve before the move takes effect.
    """
    try:
        data = json.loads(request.body)
        to_program_code = data.get('to_program_code', '').upper()
        reason = data.get('reason', '').strip()

        if not to_program_code:
            return JsonResponse({'success': False, 'error': 'Target program is required.'}, status=400)
        if not reason:
            return JsonResponse({'success': False, 'error': 'Reason for move is required.'}, status=400)

        student = Student.objects.select_related(
            'student_data', 'program_selection', 'program_selection__assigned_section'
        ).get(lrn=student_id)

        program_selection = getattr(student, 'program_selection', None)
        if not program_selection:
            return JsonResponse({'success': False, 'error': 'Student has no program selection.'}, status=400)

        from_program_code = program_selection.selected_program_code.upper()

        # Check eligibility
        is_eligible, ineligibility_reason = ProgramMoveRequest.check_eligibility(
            from_program_code, to_program_code, student=student
        )
        if not is_eligible:
            return JsonResponse({'success': False, 'error': ineligibility_reason}, status=400)

        # Check for existing pending request
        existing = ProgramMoveRequest.objects.filter(
            student=student, status='pending'
        ).first()
        if existing:
            return JsonResponse({
                'success': False,
                'error': f'There is already a pending move request for this student '
                         f'({existing.from_program_code} → {existing.to_program_code}). '
                         f'Please wait for admin to review it.'
            }, status=400)

        # Verify target program exists
        if not Program.objects.filter(code=to_program_code).exists():
            return JsonResponse({'success': False, 'error': f'Program {to_program_code} does not exist.'}, status=400)

        # Create the move request
        move_request = ProgramMoveRequest.objects.create(
            student=student,
            from_program_code=from_program_code,
            to_program_code=to_program_code,
            from_section=program_selection.assigned_section,
            reason=reason,
            requested_by=request.user,
            status='pending',
        )

        # Log coordinator activity
        try:
            from coordinator_app.models import CoordinatorActivityLog
            student_name = student.student_data.full_name if hasattr(student, 'student_data') else student.lrn
            user_profile = getattr(request.user, 'profile', None)
            program_obj = user_profile.program if user_profile else None
            CoordinatorActivityLog.log(
                user=request.user,
                action='program_move_requested',
                description=f'Requested program move for {student_name}: {from_program_code} → {to_program_code}. Reason: {reason}',
                category='enrollment',
                program=program_obj,
                student_lrn=student.lrn,
                student_name=student_name,
                metadata={
                    'from_program': from_program_code,
                    'to_program': to_program_code,
                    'move_request_id': move_request.id,
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'message': f'Move request submitted successfully. Admin has been notified.',
            'move_request_id': move_request.id,
        })

    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@coordinator_required
def get_eligible_programs(request, student_id):
    """
    Returns list of programs this student is eligible to move to,
    based on their current program and the eligibility rules.
    """
    try:
        student = Student.objects.select_related(
            'program_selection', 'program_selection__assigned_section'
        ).get(lrn=student_id)

        program_selection = getattr(student, 'program_selection', None)
        if not program_selection:
            return JsonResponse({'success': False, 'error': 'No program selection found.'}, status=400)

        from_code = program_selection.selected_program_code.upper()

        # Get all active programs
        all_programs = Program.objects.all()

        eligible = []
        for prog in all_programs:
            if prog.code.upper() == from_code:
                continue
            is_ok, _ = ProgramMoveRequest.check_eligibility(from_code, prog.code.upper(), student=student)
            if is_ok:
                eligible.append({'code': prog.code, 'name': prog.name})

        return JsonResponse({
            'success': True,
            'current_program': from_code,
            'eligible_programs': eligible,
        })

    except Student.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Student not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)