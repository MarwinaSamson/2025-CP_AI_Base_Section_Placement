"""
admin_app/views/reports_views.py
"""
import csv
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Q

from admin_app.models import SchoolYear, UserProfile, Section, GradeLevel, Program
from enrollment_app.models import (
    Student, StudentEnrollment, ProgramSelection,
    StudentAcademicYearStatus, StudentData,
    StudentDocumentSubmission,
)


@login_required
def reports(request):
    active_sy = SchoolYear.objects.filter(is_active=True).first()
    all_sy    = SchoolYear.objects.all().order_by('-year_label')
    programs  = Program.objects.all().order_by('code')
    grades    = GradeLevel.objects.all().order_by('code')
    return render(request, 'admin_app/reports.html', {
        'active_page':       'reports',
        'active_sy':         active_sy,
        'active_school_year': active_sy,  # ← base.html reads this
        'all_sy':            all_sy,
        'programs':          programs,
        'grades':            grades,
    })


@login_required
@require_http_methods(["GET"])
def reports_header_data(request):
    active_sy = SchoolYear.objects.filter(is_active=True).first()
    try:
        user_profile = UserProfile.objects.select_related(
            'program', 'position', 'department'
        ).get(user=request.user)
    except UserProfile.DoesNotExist:
        user_profile = None

    user      = request.user
    full_name = f"{user.first_name} {user.last_name}".strip() or user.username
    initials  = ''.join([n[0].upper() for n in full_name.split()[:2]]) or 'A'
    role      = user_profile.get_user_type_display() if user_profile else 'Admin'
    photo_url = user_profile.photo.url if user_profile and user_profile.photo else None

    return JsonResponse({
        'school_year': active_sy.year_label if active_sy else 'No Active Year',
        'full_name':   full_name,
        'role':        role,
        'initials':    initials,
        'photo_url':   photo_url,
    })


@login_required
def generate_report(request):
    if request.method == 'POST':
        return JsonResponse({'status': 'success', 'message': 'Report generated'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY STATS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["GET"])
def reports_summary(request):
    sy_label = request.GET.get('school_year')
    sy = (
        SchoolYear.objects.filter(year_label=sy_label).first()
        if sy_label else
        SchoolYear.objects.filter(is_active=True).first()
    )
    if not sy:
        return JsonResponse({'error': 'No school year found'}, status=400)

    total_enrolled = StudentEnrollment.objects.filter(
        school_year=sy, enrollment_status='approved',
    ).count()

    total_sections = Section.objects.filter(school_year=sy).count()

    program_dist = (
        ProgramSelection.objects
        .filter(school_year=sy, admin_approved=True)
        .values('selected_program_code')
        .annotate(count=Count('student'))
        .order_by('-count')
    )

    promoted = StudentAcademicYearStatus.objects.filter(
        school_year=sy, final_status='promoted',
    ).count()

    retained = StudentAcademicYearStatus.objects.filter(
        school_year=sy, final_status='retained',
    ).count()

    pending_enrollment = ProgramSelection.objects.filter(
        school_year=sy, admin_approved=False, admin_rejected=False,
    ).count()

    return JsonResponse({
        'school_year':            sy.year_label,
        'total_enrolled':         total_enrolled,
        'total_sections':         total_sections,
        'promoted':               promoted,
        'retained':               retained,
        'pending_enrollment':     pending_enrollment,
        'program_distribution':   list(program_dist),
    })


# ─────────────────────────────────────────────────────────────────────────────
# PREVIEW
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["GET"])
def get_report_preview(request):
    report_type  = request.GET.get('type')
    sy_label     = request.GET.get('school_year')
    program_code = request.GET.get('program', 'all')
    grade_code   = request.GET.get('grade', 'all')

    sy = (
        SchoolYear.objects.filter(year_label=sy_label).first()
        if sy_label else
        SchoolYear.objects.filter(is_active=True).first()
    )
    if not sy:
        return JsonResponse({'error': 'No school year found'}, status=400)

    try:
        if report_type == 'enrolled':
            qs = ProgramSelection.objects.filter(school_year=sy, admin_approved=True)
            if program_code != 'all':
                qs = qs.filter(selected_program_code=program_code)
            return JsonResponse({'count': qs.count(), 'label': 'enrolled students'})

        elif report_type == 'sections':
            qs = Section.objects.filter(school_year=sy)
            if program_code != 'all':
                qs = qs.filter(program__code=program_code)
            return JsonResponse({'count': qs.count(), 'label': 'sections'})

        elif report_type == 'promotion':
            qs = StudentAcademicYearStatus.objects.filter(school_year=sy)
            return JsonResponse({
                'count':    qs.count(),
                'promoted': qs.filter(final_status='promoted').count(),
                'retained': qs.filter(final_status='retained').count(),
                'pending':  qs.filter(final_status='pending').count(),
                'label':    'students with academic status',
            })

        elif report_type == 'pending':
            qs = ProgramSelection.objects.filter(
                school_year=sy, admin_approved=False, admin_rejected=False,
            )
            return JsonResponse({'count': qs.count(), 'label': 'pending enrollments'})

        elif report_type == 'masterlist':
            sections = Section.objects.filter(school_year=sy)
            if program_code != 'all':
                sections = sections.filter(program__code=program_code)
            students = ProgramSelection.objects.filter(
                school_year=sy, admin_approved=True,
                assigned_section__in=sections,
            ).count()
            return JsonResponse({
                'count':    students,
                'sections': sections.count(),
                'label':    'students across sections',
            })

        elif report_type == 'transferees':
            qs = StudentEnrollment.objects.filter(
                school_year=sy, enrollee_type='transferee',
            )
            return JsonResponse({'count': qs.count(), 'label': 'transferee students'})

        elif report_type == 'probation':
            try:
                from coordinator_app.models import ProbationRecord
                qs = ProbationRecord.objects.filter(school_year=sy, is_active=True)
                return JsonResponse({'count': qs.count(), 'label': 'students on probation'})
            except Exception:
                return JsonResponse({'count': 0, 'label': 'students on probation'})

        elif report_type == 'ai_vs_manual':
            approved_qs = ProgramSelection.objects.filter(
                school_year=sy, admin_approved=True,
            )
            ai_count     = approved_qs.filter(approved_by__icontains='AI').count()
            manual_count = approved_qs.exclude(approved_by__icontains='AI').count()
            return JsonResponse({
                'count':  approved_qs.count(),
                'ai':     ai_count,
                'manual': manual_count,
                'label':  'approved enrollments',
            })

        elif report_type == 'no_section':
            qs = ProgramSelection.objects.filter(
                school_year=sy, admin_approved=True, assigned_section__isnull=True,
            )
            if program_code != 'all':
                qs = qs.filter(selected_program_code=program_code)
            return JsonResponse({'count': qs.count(), 'label': 'students without section'})

        elif report_type == 'documents':
            missing = (
                StudentEnrollment.objects
                .filter(school_year=sy, enrollment_status='approved', documents_completed=False)
                .count()
            )
            complete = (
                StudentEnrollment.objects
                .filter(school_year=sy, enrollment_status='approved', documents_completed=True)
                .count()
            )
            return JsonResponse({
                'count':    missing + complete,
                'complete': complete,
                'missing':  missing,
                'label':    'students (document status)',
            })

        elif report_type == 'activity_log':
            try:
                from coordinator_app.models import CoordinatorActivityLog
                qs = CoordinatorActivityLog.objects.filter(
                    created_at__year=sy.start_date.year
                ) if hasattr(sy, 'start_date') and sy.start_date else CoordinatorActivityLog.objects.all()
                return JsonResponse({'count': qs.count(), 'label': 'activity log entries'})
            except Exception:
                return JsonResponse({'count': 0, 'label': 'activity log entries'})

        elif report_type == 'enrollee_type':
            breakdown = (
                StudentEnrollment.objects
                .filter(school_year=sy)
                .values('enrollee_type')
                .annotate(count=Count('id'))
                .order_by('enrollee_type')
            )
            return JsonResponse({
                'count':     StudentEnrollment.objects.filter(school_year=sy).count(),
                'breakdown': list(breakdown),
                'label':     'total enrollments',
            })

        elif report_type == 'move_requests':
            try:
                from admin_app.models import ProgramMoveRequest
                qs = ProgramMoveRequest.objects.filter(
                    student__enrollments__school_year=sy
                ).distinct()
                return JsonResponse({
                    'count':    qs.count(),
                    'approved': qs.filter(status='approved').count(),
                    'rejected': qs.filter(status='rejected').count(),
                    'pending':  qs.filter(status='pending').count(),
                    'label':    'program move requests',
                })
            except Exception:
                return JsonResponse({'count': 0, 'label': 'program move requests'})

        return JsonResponse({'error': 'Unknown report type'}, status=400)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_sy(sy_label):
    return (
        SchoolYear.objects.filter(year_label=sy_label).first()
        if sy_label else
        SchoolYear.objects.filter(is_active=True).first()
    )

def _csv_response(filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_http_methods(["GET"])
def export_enrolled_students(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    program_code = request.GET.get('program', 'all')
    grade_code   = request.GET.get('grade', 'all')

    qs = ProgramSelection.objects.filter(
        school_year=sy, admin_approved=True,
    ).select_related(
        'student', 'student__student_data',
        'assigned_section', 'assigned_section__grade_level',
    ).order_by('selected_program_code', 'student__student_data__last_name')

    if program_code != 'all':
        qs = qs.filter(selected_program_code=program_code)
    if grade_code != 'all':
        qs = qs.filter(assigned_section__grade_level__code=grade_code)

    response = _csv_response(f"enrolled_students_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)
    writer.writerow([
        'LRN', 'Last Name', 'First Name', 'Middle Name',
        'Gender', 'Program', 'Track', 'Grade Level',
        'Section', 'Enrollment Type', 'Approved By', 'Approved At',
    ])

    for ps in qs:
        sd  = getattr(ps.student, 'student_data', None)
        sec = ps.assigned_section
        enrollment = StudentEnrollment.objects.filter(
            student=ps.student, school_year=sy,
        ).first()

        writer.writerow([
            ps.student.lrn,
            getattr(sd, 'last_name', '') or '',
            getattr(sd, 'first_name', '') or '',
            getattr(sd, 'middle_name', '') or '',
            getattr(sd, 'gender', '') or '',
            ps.selected_program_code or '',
            ps.regular_track or '',
            sec.grade_level.name if sec and sec.grade_level else '',
            sec.name if sec else 'Not Assigned',
            enrollment.enrollee_type if enrollment else '',
            ps.approved_by or '',
            ps.approved_at.strftime('%Y-%m-%d %H:%M') if ps.approved_at else '',
        ])

    return response


@login_required
@require_http_methods(["GET"])
def export_section_list(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    program_code = request.GET.get('program', 'all')
    grade_code   = request.GET.get('grade', 'all')

    qs = Section.objects.filter(school_year=sy).select_related(
        'program', 'grade_level', 'adviser'
    ).order_by('program__code', 'grade_level__code', 'name')

    if program_code != 'all':
        qs = qs.filter(program__code=program_code)
    if grade_code != 'all':
        qs = qs.filter(grade_level__code=grade_code)

    response = _csv_response(f"sections_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)
    writer.writerow([
        'Section Name', 'Program', 'Track', 'Grade Level',
        'Adviser', 'Max Students', 'Enrolled', 'Available Slots',
    ])

    for section in qs:
        section.update_current_students_count()
        adviser_name = ''
        if section.adviser:
            adviser_name = getattr(section.adviser, 'full_name', str(section.adviser))
        writer.writerow([
            section.name,
            section.program.code if section.program else '',
            section.regular_track or '',
            section.grade_level.name if section.grade_level else '',
            adviser_name,
            section.max_students,
            section.current_students,
            section.max_students - section.current_students,
        ])

    return response


@login_required
@require_http_methods(["GET"])
def export_promotion_status(request):
    sy_label = request.GET.get('school_year')
    sy = (
        SchoolYear.objects.filter(year_label=sy_label).first()
        if sy_label else
        SchoolYear.objects.filter(is_active=False).order_by('-year_label').first()
    )
    if not sy:
        return HttpResponse('No school year found.', status=400)

    program_code  = request.GET.get('program', 'all')
    status_filter = request.GET.get('status', 'all')

    qs = StudentAcademicYearStatus.objects.filter(
        school_year=sy,
    ).select_related(
        'student', 'student__student_data', 'grade_level', 'section',
    ).order_by('final_status', 'student__student_data__last_name')

    if status_filter != 'all':
        qs = qs.filter(final_status=status_filter)
    if program_code != 'all':
        qs = qs.filter(section__program__code=program_code)

    response = _csv_response(f"promotion_status_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)
    writer.writerow([
        'LRN', 'Last Name', 'First Name',
        'Grade Level', 'Section', 'Program',
        'Overall Grade', 'Final Status', 'Remarks',
    ])

    for status in qs:
        sd  = getattr(status.student, 'student_data', None)
        sec = status.section
        writer.writerow([
            status.student.lrn,
            getattr(sd, 'last_name', '') or '',
            getattr(sd, 'first_name', '') or '',
            status.grade_level.name if status.grade_level else '',
            sec.name if sec else '',
            sec.program.code if sec and sec.program else '',
            status.overall_grade or '',
            status.final_status,
            status.remarks or '',
        ])

    return response


@login_required
@require_http_methods(["GET"])
def export_pending_enrollments(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    qs = ProgramSelection.objects.filter(
        school_year=sy, admin_approved=False, admin_rejected=False,
    ).select_related(
        'student', 'student__student_data',
    ).order_by('selected_program_code', 'created_at')

    response = _csv_response(f"pending_enrollments_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)
    writer.writerow([
        'LRN', 'Last Name', 'First Name',
        'Program Applied', 'Track', 'Enrollee Type',
        'Enrollment Status', 'Submitted At', 'Notes',
    ])

    for ps in qs:
        sd = getattr(ps.student, 'student_data', None)
        enrollment = StudentEnrollment.objects.filter(
            student=ps.student, school_year=sy,
        ).first()

        writer.writerow([
            ps.student.lrn,
            getattr(sd, 'last_name', '') or '',
            getattr(sd, 'first_name', '') or '',
            ps.selected_program_code or '',
            ps.regular_track or '',
            enrollment.enrollee_type if enrollment else '',
            enrollment.enrollment_status if enrollment else '',
            ps.created_at.strftime('%Y-%m-%d %H:%M') if ps.created_at else '',
            ps.admin_notes or '',
        ])

    return response


@login_required
@require_http_methods(["GET"])
def export_masterlist(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    program_code = request.GET.get('program', 'all')
    grade_code   = request.GET.get('grade', 'all')

    sections_qs = Section.objects.filter(school_year=sy).select_related(
        'program', 'grade_level', 'adviser'
    ).order_by('program__code', 'grade_level__code', 'name')

    if program_code != 'all':
        sections_qs = sections_qs.filter(program__code=program_code)
    if grade_code != 'all':
        sections_qs = sections_qs.filter(grade_level__code=grade_code)

    response = _csv_response(f"masterlist_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)

    for section in sections_qs:
        adviser_name = ''
        if section.adviser:
            adviser_name = getattr(section.adviser, 'full_name', str(section.adviser))

        writer.writerow([])
        writer.writerow([
            f"SECTION: {section.name}",
            f"Program: {section.program.code if section.program else ''}",
            f"Grade: {section.grade_level.name if section.grade_level else ''}",
            f"Adviser: {adviser_name}",
            f"School Year: {sy.year_label}",
        ])
        writer.writerow([
            '#', 'LRN', 'Last Name', 'First Name', 'Middle Name',
            'Gender', 'Date of Birth', 'Address',
        ])

        students_in_section = ProgramSelection.objects.filter(
            school_year=sy, assigned_section=section, admin_approved=True,
        ).select_related('student', 'student__student_data').order_by(
            'student__student_data__last_name'
        )

        for i, ps in enumerate(students_in_section, 1):
            sd = getattr(ps.student, 'student_data', None)
            writer.writerow([
                i,
                ps.student.lrn,
                getattr(sd, 'last_name', '') or '',
                getattr(sd, 'first_name', '') or '',
                getattr(sd, 'middle_name', '') or '',
                getattr(sd, 'gender', '') or '',
                getattr(sd, 'date_of_birth', '') or '',
                getattr(sd, 'address', '') or '',
            ])

        writer.writerow([f"Total: {students_in_section.count()}"])

    return response


@login_required
@require_http_methods(["GET"])
def export_transferees(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    qs = StudentEnrollment.objects.filter(
        school_year=sy, enrollee_type='transferee',
    ).select_related('student', 'student__student_data', 'grade_level').order_by(
        'student__student_data__last_name'
    )

    response = _csv_response(f"transferees_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)
    writer.writerow([
        'LRN', 'Last Name', 'First Name', 'Middle Name',
        'Gender', 'Grade Level', 'Program Applied',
        'Previous School', 'Enrollment Status',
    ])

    for e in qs:
        sd = getattr(e.student, 'student_data', None)
        ps = ProgramSelection.objects.filter(student=e.student).first()
        writer.writerow([
            e.student.lrn,
            getattr(sd, 'last_name', '') or '',
            getattr(sd, 'first_name', '') or '',
            getattr(sd, 'middle_name', '') or '',
            getattr(sd, 'gender', '') or '',
            e.grade_level.name if e.grade_level else '',
            ps.selected_program_code if ps else '',
            getattr(sd, 'last_school_attended', '') or '',
            e.enrollment_status,
        ])

    return response


@login_required
@require_http_methods(["GET"])
def export_probation_list(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    response = _csv_response(f"probation_list_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)

    try:
        from coordinator_app.models import ProbationRecord

        qs = ProbationRecord.objects.filter(
            school_year=sy,
        ).select_related(
            'student', 'student__student_data', 'grade_level',
        ).order_by('student__student_data__last_name')

        writer.writerow([
            'LRN', 'Last Name', 'First Name',
            'Grade Level', 'Previous Program', 'Moved To',
            'Reason', 'Is Active',
        ])

        for p in qs:
            sd = getattr(p.student, 'student_data', None)
            writer.writerow([
                p.student.lrn,
                getattr(sd, 'last_name', '') or '',
                getattr(sd, 'first_name', '') or '',
                p.grade_level.name if p.grade_level else '',
                p.previous_program or '',
                p.moved_to_program or '',
                p.reason or '',
                'Yes' if p.is_active else 'No',
            ])

    except Exception as e:
        writer.writerow([f'Error: {str(e)}'])

    return response


@login_required
@require_http_methods(["GET"])
def export_ai_vs_manual(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    qs = ProgramSelection.objects.filter(
        school_year=sy, admin_approved=True,
    ).select_related(
        'student', 'student__student_data', 'assigned_section',
    ).order_by('approved_by', 'student__student_data__last_name')

    response = _csv_response(f"ai_vs_manual_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)
    writer.writerow([
        'LRN', 'Last Name', 'First Name',
        'Program', 'Section', 'Approved By',
        'Processing Type', 'Approved At',
    ])

    for ps in qs:
        sd = getattr(ps.student, 'student_data', None)
        processing = 'AI Automated' if (ps.approved_by or '').upper().__contains__('AI') else 'Manual'
        writer.writerow([
            ps.student.lrn,
            getattr(sd, 'last_name', '') or '',
            getattr(sd, 'first_name', '') or '',
            ps.selected_program_code or '',
            ps.assigned_section.name if ps.assigned_section else '',
            ps.approved_by or '',
            processing,
            ps.approved_at.strftime('%Y-%m-%d %H:%M') if ps.approved_at else '',
        ])

    return response


@login_required
@require_http_methods(["GET"])
def export_no_section(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    program_code = request.GET.get('program', 'all')

    qs = ProgramSelection.objects.filter(
        school_year=sy, admin_approved=True, assigned_section__isnull=True,
    ).select_related('student', 'student__student_data')

    if program_code != 'all':
        qs = qs.filter(selected_program_code=program_code)

    qs = qs.order_by('selected_program_code', 'student__student_data__last_name')

    response = _csv_response(f"no_section_assigned_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)
    writer.writerow([
        'LRN', 'Last Name', 'First Name',
        'Program', 'Track', 'Approved By', 'Approved At',
    ])

    for ps in qs:
        sd = getattr(ps.student, 'student_data', None)
        writer.writerow([
            ps.student.lrn,
            getattr(sd, 'last_name', '') or '',
            getattr(sd, 'first_name', '') or '',
            ps.selected_program_code or '',
            ps.regular_track or '',
            ps.approved_by or '',
            ps.approved_at.strftime('%Y-%m-%d %H:%M') if ps.approved_at else '',
        ])

    return response


@login_required
@require_http_methods(["GET"])
def export_document_compliance(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    status_filter = request.GET.get('doc_status', 'all')

    qs = StudentEnrollment.objects.filter(
        school_year=sy,
    ).select_related('student', 'student__student_data')

    if status_filter == 'complete':
        qs = qs.filter(documents_completed=True)
    elif status_filter == 'missing':
        qs = qs.filter(documents_completed=False)

    qs = qs.order_by('student__student_data__last_name')

    response = _csv_response(f"document_compliance_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)
    writer.writerow([
        'LRN', 'Last Name', 'First Name',
        'Enrollee Type', 'Enrollment Status',
        'Documents Complete', 'Program',
    ])

    for e in qs:
        sd = getattr(e.student, 'student_data', None)
        ps = ProgramSelection.objects.filter(student=e.student).first()
        writer.writerow([
            e.student.lrn,
            getattr(sd, 'last_name', '') or '',
            getattr(sd, 'first_name', '') or '',
            e.enrollee_type,
            e.enrollment_status,
            'Yes' if e.documents_completed else 'No',
            ps.selected_program_code if ps else '',
        ])

    return response


@login_required
@require_http_methods(["GET"])
def export_activity_log(request):
    sy = _get_sy(request.GET.get('school_year'))
    category = request.GET.get('category', 'all')

    response = _csv_response(f"activity_log_{sy.year_label.replace('-','_') if sy else 'all'}.csv")
    writer = csv.writer(response)

    try:
        from coordinator_app.models import CoordinatorActivityLog

        qs = CoordinatorActivityLog.objects.select_related(
            'user', 'program',
        ).order_by('-created_at')

        if sy and hasattr(sy, 'start_date') and sy.start_date:
            qs = qs.filter(created_at__year=sy.start_date.year)

        if category != 'all':
            qs = qs.filter(category=category)

        writer.writerow([
            'Date', 'Time', 'User', 'Action',
            'Category', 'Program', 'Student LRN',
            'Student Name', 'Section', 'Description',
        ])

        for log in qs:
            writer.writerow([
                log.created_at.strftime('%Y-%m-%d'),
                log.created_at.strftime('%H:%M:%S'),
                log.user.get_full_name() if log.user else '',
                log.action_display if hasattr(log, 'action_display') else log.action,
                log.category or '',
                log.program.code if log.program else '',
                log.student_lrn or '',
                log.student_name or '',
                log.section_name or '',
                log.description or '',
            ])

    except Exception as e:
        writer.writerow([f'Error: {str(e)}'])

    return response


@login_required
@require_http_methods(["GET"])
def export_enrollee_type_breakdown(request):
    sy = _get_sy(request.GET.get('school_year'))
    if not sy:
        return HttpResponse('No school year found.', status=400)

    qs = StudentEnrollment.objects.filter(
        school_year=sy,
    ).select_related('student', 'student__student_data', 'grade_level')

    enrollee_type = request.GET.get('enrollee_type', 'all')
    if enrollee_type != 'all':
        qs = qs.filter(enrollee_type=enrollee_type)

    qs = qs.order_by('enrollee_type', 'student__student_data__last_name')

    response = _csv_response(f"enrollee_breakdown_{sy.year_label.replace('-','_')}.csv")
    writer = csv.writer(response)
    writer.writerow([
        'LRN', 'Last Name', 'First Name',
        'Enrollee Type', 'Grade Level',
        'Enrollment Status', 'Program',
    ])

    for e in qs:
        sd = getattr(e.student, 'student_data', None)
        ps = ProgramSelection.objects.filter(student=e.student).first()
        writer.writerow([
            e.student.lrn,
            getattr(sd, 'last_name', '') or '',
            getattr(sd, 'first_name', '') or '',
            e.get_enrollee_type_display(),
            e.grade_level.name if e.grade_level else '',
            e.enrollment_status,
            ps.selected_program_code if ps else '',
        ])

    return response


@login_required
@require_http_methods(["GET"])
def export_move_requests(request):
    sy = _get_sy(request.GET.get('school_year'))

    response = _csv_response(f"move_requests_{sy.year_label.replace('-','_') if sy else 'all'}.csv")
    writer = csv.writer(response)

    try:
        from admin_app.models import ProgramMoveRequest

        qs = ProgramMoveRequest.objects.select_related(
            'student', 'student__student_data',
            'requested_by', 'reviewed_by',
        ).order_by('-created_at')

        if sy:
            qs = qs.filter(student__enrollments__school_year=sy).distinct()

        status_filter = request.GET.get('status', 'all')
        if status_filter != 'all':
            qs = qs.filter(status=status_filter)

        writer.writerow([
            'LRN', 'Last Name', 'First Name',
            'From Program', 'To Program',
            'Requested By', 'Status',
            'Reviewed By', 'Reason',
            'Created At', 'Reviewed At',
        ])

        for r in qs:
            sd = getattr(r.student, 'student_data', None)
            writer.writerow([
                r.student.lrn,
                getattr(sd, 'last_name', '') or '',
                getattr(sd, 'first_name', '') or '',
                r.from_program_code or '',
                r.to_program_code or '',
                r.requested_by.get_full_name() if r.requested_by else '',
                r.status,
                r.reviewed_by.get_full_name() if r.reviewed_by else '',
                r.reason or '',
                r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else '',
                r.reviewed_at.strftime('%Y-%m-%d %H:%M') if r.reviewed_at else '',
            ])

    except Exception as e:
        writer.writerow([f'Error: {str(e)}'])

    return response