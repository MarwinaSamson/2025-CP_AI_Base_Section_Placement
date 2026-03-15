from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
import json
import logging
import traceback

from enrollment_app.models import ProgramSelection
from admin_app.models import Section, SchoolYear
from coordinator_app.models import Qualified_for_ste, AIAssistantPreference
from admin_app.models import Program

logger = logging.getLogger(__name__)

STE_PROGRAMS = ['STE']

@login_required
def enrollment_management(request):
    """
    Unified enrollment management view with dynamic content loading.
    This replaces the old section_assignment view.
    """
    # ── Step 1: Resolve user profile ─────────────────────────────────────────
    try:
        user_profile = getattr(request.user, 'profile', None)
        logger.debug(
            "[enrollment_management] STEP 1 – user=%s | has_profile=%s",
            request.user.username,
            user_profile is not None,
        )
    except Exception:
        logger.error(
            "[enrollment_management] STEP 1 FAILED – could not read user.profile\n%s",
            traceback.format_exc(),
        )
        user_profile = None

    # ── Step 2: Resolve program code / name ──────────────────────────────────
    try:
        program_code = user_profile.program.code if user_profile and user_profile.program else None
        program_name = user_profile.program.name if user_profile and user_profile.program else None
        logger.debug(
            "[enrollment_management] STEP 2 – program_code=%s | program_name=%s",
            program_code,
            program_name,
        )
    except Exception:
        logger.error(
            "[enrollment_management] STEP 2 FAILED – could not read program code/name\n%s",
            traceback.format_exc(),
        )
        program_code = None
        program_name = None

    # ── Step 3: Resolve display info ─────────────────────────────────────────
    try:
        user_full_name = request.user.get_full_name() or request.user.username
        user_type      = f"{program_code} Coordinator" if program_code else "Coordinator"
        user_photo     = user_profile.photo.url if user_profile and user_profile.photo else None
        name_parts     = user_full_name.split()
        user_initials  = ''.join(part[0].upper() for part in name_parts[:2]) if name_parts else "CO"
        logger.debug(
            "[enrollment_management] STEP 3 – user_full_name=%s | user_type=%s | has_photo=%s",
            user_full_name,
            user_type,
            user_photo is not None,
        )
    except Exception:
        logger.error(
            "[enrollment_management] STEP 3 FAILED – could not resolve display info\n%s",
            traceback.format_exc(),
        )
        user_full_name = request.user.username
        user_type      = "Coordinator"
        user_photo     = None
        user_initials  = "CO"

    students_payload = []
    sections_payload = []

    if program_code:
        # ── Step 4: Fetch active school year ─────────────────────────────────
        try:
            active_sy = (
                SchoolYear.objects.filter(is_active=True).order_by('-start_date').first()
                or SchoolYear.objects.order_by('-start_date').first()
            )
            logger.debug(
                "[enrollment_management] STEP 4 – active_sy=%s",
                active_sy,
            )
        except Exception:
            logger.error(
                "[enrollment_management] STEP 4 FAILED – could not fetch SchoolYear\n%s",
                traceback.format_exc(),
            )
            active_sy = None

        # ── Step 5: Fetch sections ────────────────────────────────────────────
        try:
            active_grade = request.session.get('active_grade_code')
            logger.debug(
                "[enrollment_management] STEP 5 – active_grade=%s",
                active_grade,
            )

            sections_qs = Section.objects.filter(program__code=program_code)
            if active_sy:
                sections_qs = sections_qs.filter(school_year=active_sy)
            if active_grade and active_grade != 'all':
                sections_qs = sections_qs.filter(grade_level__code=active_grade)

            for section in sections_qs:
                section.update_current_students_count()

            sections_payload = [
                {
                    'id':       str(section.id),
                    'name':     section.name,
                    'capacity': section.max_students,
                    'current':  section.current_students,
                }
                for section in sections_qs
            ]
            logger.debug(
                "[enrollment_management] STEP 5 – sections_count=%d",
                len(sections_payload),
            )
        except Exception:
            logger.error(
                "[enrollment_management] STEP 5 FAILED – could not fetch/process sections\n%s",
                traceback.format_exc(),
            )
            sections_payload = []

        # ── Step 6: Fetch program selections ─────────────────────────────────
        try:
            selections = (
                ProgramSelection.objects
                .select_related('student', 'student__student_data')
                .filter(selected_program_code=program_code)
            )
            if active_grade:
                selections = selections.filter(assigned_section__grade_level__code=active_grade)

            selection_count = selections.count()
            logger.debug(
                "[enrollment_management] STEP 6 – selections_count=%d",
                selection_count,
            )
        except Exception:
            logger.error(
                "[enrollment_management] STEP 6 FAILED – could not fetch ProgramSelections\n%s",
                traceback.format_exc(),
            )
            selections = ProgramSelection.objects.none()

        # ── Step 7: Build score map (STE program only) ───────────────────────
        try:
            lrns = [sel.student.lrn for sel in selections]
            is_ste_program = program_code in STE_PROGRAMS

            if is_ste_program:
                score_map = {
                    rec.student_lrn: rec
                    for rec in Qualified_for_ste.objects.filter(student_lrn__in=lrns)
                }
                logger.debug(
                    "[enrollment_management] STEP 7 – STE program (%s) | lrns_count=%d | score_map_count=%d",
                    program_code,
                    len(lrns),
                    len(score_map),
                )
            else:
                score_map = {}
                logger.debug(
                    "[enrollment_management] STEP 7 – Non-STE program (%s), score map skipped",
                    program_code,
                )
        except Exception:
            logger.error(
                "[enrollment_management] STEP 7 FAILED – could not build score map\n%s",
                traceback.format_exc(),
            )
            score_map = {}
            lrns = []
            is_ste_program = False

        # ── Step 8: Build students payload ───────────────────────────────────
        try:
            for i, sel in enumerate(selections):
                try:
                    student      = sel.student
                    student_data = getattr(student, 'student_data', None)

                    parts = [
                        getattr(student_data, 'last_name',   '') or '',
                        getattr(student_data, 'first_name',  '') or '',
                        getattr(student_data, 'middle_name', '') or '',
                    ]
                    display_name = ', '.join(
                        [parts[0], ' '.join(parts[1:]).strip()]
                    ).strip(', ')

                    # Only look up scores for STE program
                    scores          = score_map.get(student.lrn) if is_ste_program else None
                    exam_score      = float(scores.exam_score)      if scores and scores.exam_score      else 0
                    interview_score = float(scores.interview_score)  if scores and scores.interview_score else 0

                    # Build flag message for manual review flagged students
                    flag_message = None
                    if student.enrollee_type == 'transferee':
                        flag_message = f'⚠️ Transferee: Requires manual review - Please verify previous school and document requirements'
                    elif sel.admin_notes and 'flagged for manual review' in sel.admin_notes.lower():
                        flag_message = f'⚠️ Flagged: {sel.admin_notes}'

                    students_payload.append({
                        'name':              display_name or student.lrn,
                        'lrn':               student.lrn,
                        'exam':              exam_score,       # always 0 for non-STE
                        'interview':         interview_score,  # always 0 for non-STE
                        'has_scores':        is_ste_program,   # tells frontend whether to show score columns
                        'finalSection':      sel.assigned_section.id if sel.assigned_section else None,
                        'admin_approved':    sel.admin_approved,
                        'approved_by':       sel.approved_by or '',
                        'approved_at':       sel.approved_at.isoformat() if sel.approved_at else None,
                        'enrollment_status': student.enrollment_status or '',
                        'flag_message':      flag_message,  # NEW: Flag for manual review (transferee or min grades)
                    })
                except Exception:
                    logger.error(
                        "[enrollment_management] STEP 8 FAILED on row %d (lrn=%s)\n%s",
                        i,
                        getattr(getattr(sel, 'student', None), 'lrn', 'unknown'),
                        traceback.format_exc(),
                    )
                    # Skip the bad record and continue — don't crash the whole page

            logger.debug(
                "[enrollment_management] STEP 8 – students_payload_count=%d | is_ste_program=%s",
                len(students_payload),
                is_ste_program,
            )
        except Exception:
            logger.error(
                "[enrollment_management] STEP 8 FAILED – outer loop error\n%s",
                traceback.format_exc(),
            )
            students_payload = []

    # ── Step 9: Check AI preference ──────────────────────────────────────────
    ai_enabled = False
    if program_code:
        try:
            program  = user_profile.program
            ai_pref  = AIAssistantPreference.objects.filter(
                user=request.user,
                program=program,
                ai_enabled=True,
            ).first()
            ai_enabled = ai_pref is not None
            logger.debug(
                "[enrollment_management] STEP 9 – ai_enabled=%s",
                ai_enabled,
            )
        except Exception:
            logger.error(
                "[enrollment_management] STEP 9 FAILED – could not read AIAssistantPreference\n%s",
                traceback.format_exc(),
            )
            ai_enabled = False

    # ── Step 10: Render ───────────────────────────────────────────────────────
    try:
        context = {
            'program_code':   program_code,
            'program_name':   program_name,
            'students_json':  json.dumps(students_payload),
            'sections_json':  json.dumps(sections_payload),
            'user_full_name': user_full_name,
            'user_type':      user_type,
            'user_photo':     user_photo,
            'user_initials':  user_initials,
            'ai_enabled':     ai_enabled,
            'is_ste_program': is_ste_program if program_code else False,  # pass to template/JS
        }
        logger.info(
            "[enrollment_management] STEP 10 – rendering for user=%s program=%s students=%d sections=%d is_ste=%s",
            request.user.username,
            program_code,
            len(students_payload),
            len(sections_payload),
            is_ste_program if program_code else False,
        )
        return render(request, 'coordinator_app/enrollment_management.html', context)

    except Exception:
        logger.error(
            "[enrollment_management] STEP 10 FAILED – render error\n%s",
            traceback.format_exc(),
        )
        raise
 
@login_required
@require_http_methods(["GET"])
def get_manual_mode_content(request):
    """
    API endpoint to fetch Manual mode content HTML + data.
    Returns HTML content and refreshed student/sections data for JS to use.
    """
    try:
        print("DEBUG: get_manual_mode_content called")

        # Rebuild student and section data (same as main page)
        user_profile = getattr(request.user, 'profile', None)
        program_code = user_profile.program.code if user_profile and user_profile.program else None
        
        students_payload = []
        sections_payload = []
        
        if program_code:
            # Get active school year
            from admin_app.models import SchoolYear
            active_sy = SchoolYear.objects.filter(is_active=True).first() or SchoolYear.objects.order_by('-start_date').first()
            
            # Get sections
            active_grade = request.session.get('active_grade_code')
            sections_qs = Section.objects.filter(program__code=program_code)
            if active_sy:
                sections_qs = sections_qs.filter(school_year=active_sy)
            if active_grade and active_grade != 'all':
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
            
            # Get selections
            selections = (
                ProgramSelection.objects
                .select_related('student', 'student__student_data')
                .filter(selected_program_code=program_code)
            )
            if active_grade:
                selections = selections.filter(assigned_section__grade_level__code=active_grade)
            
            # Build students payload
            lrns = [sel.student.lrn for sel in selections]
            is_ste_program = program_code in STE_PROGRAMS
            
            if is_ste_program:
                score_map = {
                    rec.student_lrn: rec
                    for rec in Qualified_for_ste.objects.filter(student_lrn__in=lrns)
                }
            else:
                score_map = {}
            
            for sel in selections:
                try:
                    student = sel.student
                    student_data = getattr(student, 'student_data', None)
                    
                    parts = [
                        getattr(student_data, 'last_name', '') or '',
                        getattr(student_data, 'first_name', '') or '',
                        getattr(student_data, 'middle_name', '') or '',
                    ]
                    display_name = ', '.join(
                        [parts[0], ' '.join(parts[1:]).strip()]
                    ).strip(', ')
                    
                    scores = score_map.get(student.lrn) if is_ste_program else None
                    exam_score = float(scores.exam_score) if scores and scores.exam_score else 0
                    interview_score = float(scores.interview_score) if scores and scores.interview_score else 0
                    
                    flag_message = None
                    if student.enrollee_type == 'transferee':
                        flag_message = f'⚠️ Transferee: Requires manual review'
                    elif sel.admin_notes and 'flagged for manual review' in sel.admin_notes.lower():
                        flag_message = f'⚠️ Flagged: {sel.admin_notes}'
                    
                    students_payload.append({
                        'name': display_name or student.lrn,
                        'lrn': student.lrn,
                        'exam': exam_score,
                        'interview': interview_score,
                        'has_scores': is_ste_program,
                        'finalSection': str(sel.assigned_section.id) if sel.assigned_section else None,
                        'admin_approved': sel.admin_approved,
                        'approved_by': sel.approved_by or '',
                        'approved_at': sel.approved_at.isoformat() if sel.approved_at else None,
                        'enrollment_status': student.enrollment_status or '',
                        'flag_message': flag_message,
                    })
                except Exception:
                    logger.error(
                        "[get_manual_mode_content] Failed to process student %s\n%s",
                        getattr(getattr(sel, 'student', None), 'lrn', 'unknown'),
                        traceback.format_exc(),
                    )
                    continue
        
        # Render the manual mode partial template
        html = render_to_string(
            'coordinator_app/partials/manual_mode_content.html',
            {},
            request=request
        )
        
        print(f"DEBUG: get_manual_mode_content rendered successfully")
        
        # Return JSON with both HTML and refreshed data
        return JsonResponse({
            'html': html,
            'students': students_payload,
            'sections': sections_payload,
            'program_code': program_code,
        })
    except Exception as e:
        import traceback
        print(f"ERROR in get_manual_mode_content: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def get_ai_mode_content(request):
    """
    API endpoint to fetch AI mode content HTML + data.
    Returns HTML content and refreshed student/sections data for JS to use.
    """
    try:
        print("DEBUG: get_ai_mode_content called")

        # Rebuild student and section data (same as main page)
        user_profile = getattr(request.user, 'profile', None)
        program_code = user_profile.program.code if user_profile and user_profile.program else None
        
        students_payload = []
        sections_payload = []
        
        if program_code:
            # Get active school year
            from admin_app.models import SchoolYear
            active_sy = SchoolYear.objects.filter(is_active=True).first() or SchoolYear.objects.order_by('-start_date').first()
            
            # Get sections
            active_grade = request.session.get('active_grade_code')
            sections_qs = Section.objects.filter(program__code=program_code)
            if active_sy:
                sections_qs = sections_qs.filter(school_year=active_sy)
            if active_grade and active_grade != 'all':
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
            
            # Get selections
            selections = (
                ProgramSelection.objects
                .select_related('student', 'student__student_data')
                .filter(selected_program_code=program_code)
            )
            if active_grade:
                selections = selections.filter(assigned_section__grade_level__code=active_grade)
            
            # Build students payload
            lrns = [sel.student.lrn for sel in selections]
            is_ste_program = program_code in STE_PROGRAMS
            
            if is_ste_program:
                score_map = {
                    rec.student_lrn: rec
                    for rec in Qualified_for_ste.objects.filter(student_lrn__in=lrns)
                }
            else:
                score_map = {}
            
            for sel in selections:
                try:
                    student = sel.student
                    student_data = getattr(student, 'student_data', None)
                    
                    parts = [
                        getattr(student_data, 'last_name', '') or '',
                        getattr(student_data, 'first_name', '') or '',
                        getattr(student_data, 'middle_name', '') or '',
                    ]
                    display_name = ', '.join(
                        [parts[0], ' '.join(parts[1:]).strip()]
                    ).strip(', ')
                    
                    scores = score_map.get(student.lrn) if is_ste_program else None
                    exam_score = float(scores.exam_score) if scores and scores.exam_score else 0
                    interview_score = float(scores.interview_score) if scores and scores.interview_score else 0
                    
                    flag_message = None
                    if student.enrollee_type == 'transferee':
                        flag_message = f'⚠️ Transferee: Requires manual review'
                    elif sel.admin_notes and 'flagged for manual review' in sel.admin_notes.lower():
                        flag_message = f'⚠️ Flagged: {sel.admin_notes}'
                    
                    students_payload.append({
                        'name': display_name or student.lrn,
                        'lrn': student.lrn,
                        'exam': exam_score,
                        'interview': interview_score,
                        'has_scores': is_ste_program,
                        'finalSection': str(sel.assigned_section.id) if sel.assigned_section else None,
                        'admin_approved': sel.admin_approved,
                        'approved_by': sel.approved_by or '',
                        'approved_at': sel.approved_at.isoformat() if sel.approved_at else None,
                        'enrollment_status': student.enrollment_status or '',
                        'flag_message': flag_message,
                    })
                except Exception:
                    logger.error(
                        "[get_ai_mode_content] Failed to process student %s\n%s",
                        getattr(getattr(sel, 'student', None), 'lrn', 'unknown'),
                        traceback.format_exc(),
                    )
                    continue
            
            # Query students flagged for manual review
            if active_sy:
                from enrollment_app.models import StudentEnrollment
                under_review_enrollments = StudentEnrollment.objects.filter(
                    student__program_selection__selected_program_code=program_code,
                    school_year=active_sy,
                    enrollment_status='under_review',
                ).select_related('student', 'student__student_data')
                
                under_review_students = ProgramSelection.objects.filter(
                    student__in=[e.student for e in under_review_enrollments]
                ).select_related('student', 'student__student_data')
                
                under_review_count = under_review_students.count()
            else:
                under_review_students = ProgramSelection.objects.none()
                under_review_count = 0
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
        
        print(f"DEBUG: get_ai_mode_content rendered successfully")
        
        # Return JSON with both HTML and refreshed data
        return JsonResponse({
            'html': html,
            'students': students_payload,
            'sections': sections_payload,
            'program_code': program_code,
        })
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
        active_grade = request.session.get('active_grade_code')
        sections_qs = Section.objects.filter(program__code=program_code)
        if active_sy:
            sections_qs = sections_qs.filter(school_year=active_sy)
        if active_grade and active_grade != 'all':
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
            selections = selections.filter(assigned_section__grade_level__code=active_grade)
            
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
