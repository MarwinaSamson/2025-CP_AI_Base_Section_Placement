from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from admin_app.models import SystemSettings, StaffMember, Program, Section
from enrollment_app.models import ProgramSelection
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

def landing_page(request):
    """
    Landing page with dynamic content from SystemSettings
    """
    # Fetch all settings
    try:
        settings_qs = SystemSettings.objects.all()
        settings = {}
        for setting in settings_qs:
            settings[setting.setting_type] = {
                'value': setting.setting_value,
                'image_url': setting.image.url if setting.image else None
            }
    except Exception as e:
        settings = {}

    # Fetch active staff members
    try:
        staff_members = StaffMember.objects.filter(is_active=True).order_by('display_order', 'name')
    except Exception:
        staff_members = []

    # Fetch programs with their sections for the Section Assignment dropdown
    try:
        programs_with_sections = []
        active_programs = Program.objects.filter(is_active=True).order_by('code')
        for prog in active_programs:
            sections = Section.objects.filter(program=prog, masterlist_published=True).order_by('name')
            if not sections.exists():
                continue

            # REGULAR program: group sections by regular_track (TOP5 / HETERO)
            if prog.code == 'REGULAR':
                top5_sections = sections.filter(regular_track='TOP5').order_by('name')
                hetero_sections = sections.filter(regular_track='HETERO').order_by('name')
                programs_with_sections.append({
                    'program': prog,
                    'has_tracks': True,
                    'tracks': [
                        {'name': 'TOP 5', 'sections': top5_sections},
                        {'name': 'HETERO', 'sections': hetero_sections},
                    ],
                })
            else:
                programs_with_sections.append({
                    'program': prog,
                    'has_tracks': False,
                    'sections': sections,
                })
    except Exception:
        programs_with_sections = []

    # Helper function to get setting value safely
    def get_setting(key, default=''):
        return settings.get(key, {}).get('value', default)

    def get_setting_image(key):
        return settings.get(key, {}).get('image_url', None)

    context = {
        # Header
        'header_logo_school': get_setting_image('header_logo_school'),
        'header_logo_region': get_setting_image('header_logo_region'),
        'header_logo_peninsula': get_setting_image('header_logo_peninsula'),
        'header_logo_matatag': get_setting_image('header_logo_matatag'),
        'header_caption': get_setting('header_caption', '''
            <h2 class="text-2xl font-bold mb-4">Welcome to Excellence in Education</h2>
            <p class="text-lg">Empowering students to achieve their dreams through quality education and innovative programs</p>
        '''),

        # Announcements
        'announcement_image': get_setting_image('announcement_image'),
        'announcement_caption': get_setting('announcement_caption', 'Stay updated with our latest announcements'),

        # Contact Information
        'contact_address': get_setting('contact_address', 'R.T. Lim Boulevard Zamboanga City, Philippines'),
        'contact_phone': get_setting('contact_phone', '+63 61 0086516'),
        'contact_email': get_setting('contact_email', 'nationalhighschoolwest@gmail.com'),
        'contact_facebook': get_setting('contact_facebook', 'https://web.facebook.com/znhs.west'),
        'contact_hours': get_setting('contact_hours', '''Monday to Friday: 7:00 AM - 5:00 PM
Saturday: 7:00 AM - 5:00 PM
Sunday: Closed'''),

        # Footer
        'footer_copyright': get_setting('footer_copyright', '© 2025 Zamboanga National High School West. All rights reserved.'),

        # Staff Members
        'staff_members': staff_members,

        # Programs with sections for Section Assignment
        'programs_with_sections': programs_with_sections,
    }

    return render(request, 'enrollment_app/landing.html', context)

def get_section_students(request, section_id):
    """
    Public API endpoint to get the student list for a given section.
    Used by the landing page Section Assignment modal.
    """
    section = get_object_or_404(
        Section.objects.select_related('program', 'adviser'),
        id=section_id,
        masterlist_published=True
    )

    program_selections = ProgramSelection.objects.filter(
        assigned_section=str(section_id),
        admin_approved=True
    ).select_related(
        'student',
        'student__student_data',
        'student__academic_data'
    ).order_by('student__student_data__last_name', 'student__student_data__first_name')

    students = []
    for idx, ps in enumerate(program_selections, 1):
        student = ps.student
        student_info = getattr(student, 'student_data', None)
        if student_info:
            students.append({
                'number': idx,
                'lrn': student.lrn,
                'last_name': student_info.last_name,
                'first_name': student_info.first_name,
                'middle_name': student_info.middle_name or '',
                'gender': student_info.gender or '',
            })

    return JsonResponse({
        'section_name': section.name,
        'program_name': section.program.name,
        'program_code': section.program.code,
        'adviser': f"{section.adviser.first_name} {section.adviser.last_name}" if section.adviser else 'Not assigned',
        'total_students': len(students),
        'max_students': section.max_students,
        'students': students,
    })


def download_section_masterlist(request, section_id):
    """
    Public endpoint to download the section masterlist as PDF.
    """
    section = get_object_or_404(
        Section.objects.select_related('program', 'adviser'),
        id=section_id,
        masterlist_published=True
    )

    program_selections = ProgramSelection.objects.filter(
        assigned_section=str(section_id),
        admin_approved=True
    ).select_related(
        'student',
        'student__student_data',
    ).order_by('student__student_data__last_name', 'student__student_data__first_name')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{section.program.code}_{section.name}_Masterlist.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph(f"<b>{section.program.code} - {section.name} Student Masterlist</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))

    adviser_name = f"{section.adviser.first_name} {section.adviser.last_name}" if section.adviser else 'Not assigned'
    info = Paragraph(f"Program: {section.program.name} | Adviser: {adviser_name}", styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 0.3 * inch))

    data = [['#', 'LRN', 'Last Name', 'First Name', 'M.I.', 'Gender']]

    for idx, ps in enumerate(program_selections, 1):
        student = ps.student
        student_info = getattr(student, 'student_data', None)
        if student_info:
            data.append([
                str(idx),
                student.lrn,
                student_info.last_name,
                student_info.first_name,
                student_info.middle_name[0] if student_info.middle_name else '',
                (student_info.gender or '').capitalize(),
            ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#991B1B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))

    elements.append(table)
    doc.build(elements)
    return response


def clear_session(request):
    request.session.clear()
    return redirect('enrollment_app:landing')
