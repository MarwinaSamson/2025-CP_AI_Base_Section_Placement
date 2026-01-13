from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

from enrollment_app.models import ProgramSelection
from coordinator_app.models import Qualified_for_ste


@login_required
def section_assignment(request):
    """Section assignment dashboard scoped to the coordinator's program."""
    
    user_profile = getattr(request.user, 'profile', None)
    program_code = user_profile.program.code if user_profile and user_profile.program else None
    program_name = user_profile.program.name if user_profile and user_profile.program else None

    # Get user info for header
    user_full_name = request.user.get_full_name() or request.user.username
    user_type = f"{program_code} Coordinator" if program_code else "Coordinator"
    
    # FIX: Change profile_picture to photo
    user_photo = user_profile.photo.url if user_profile and user_profile.photo else None
    
    # Generate initials
    name_parts = user_full_name.split()
    user_initials = ''.join([part[0].upper() for part in name_parts[:2]]) if name_parts else 'CO'

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
        'program_name': program_name,
        'students_json': json.dumps(students_payload),
        'user_full_name': user_full_name,
        'user_type': user_type,
        'user_photo': user_photo,
        'user_initials': user_initials,
    }

    return render(request, 'coordinator_app/sectionAssignment.html', context)


@login_required
@require_http_methods(["POST"])
def export_assignments_pdf(request):
    """Export section assignments as PDF"""
    
    user_profile = getattr(request.user, 'profile', None)
    program_code = user_profile.program.code if user_profile and user_profile.program else "N/A"
    
    try:
        data = json.loads(request.body)
        students = data.get('students', [])
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#991b1b'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        # Title
        title = Paragraph(f"Section Assignments - {program_code}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3*inch))
        
        # Table data
        table_data = [['Student Name', 'LRN', 'Exam Score', 'Interview Score', 'Final Section']]
        
        for student in students:
            table_data.append([
                student.get('name', ''),
                student.get('lrn', ''),
                f"{student.get('exam', 0)}%",
                f"{student.get('interview', 0)}%",
                student.get('finalSection', '-')
            ])
        
        # Create table
        table = Table(table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#991b1b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="section_assignments_{program_code}.pdf"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def export_assignments_docx(request):
    """Export section assignments as DOCX"""
    
    user_profile = getattr(request.user, 'profile', None)
    program_code = user_profile.program.code if user_profile and user_profile.program else "N/A"
    
    try:
        data = json.loads(request.body)
        students = data.get('students', [])
        
        doc = Document()
        
        # Title
        title = doc.add_heading(f'Section Assignments - {program_code}', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.runs[0].font.color.rgb = RGBColor(153, 27, 27)
        
        doc.add_paragraph()
        
        # Table
        table = doc.add_table(rows=1, cols=5)
        table.style = 'Light Grid Accent 1'
        
        # Header
        header_cells = table.rows[0].cells
        headers = ['Student Name', 'LRN', 'Exam Score', 'Interview Score', 'Final Section']
        for i, header in enumerate(headers):
            cell = header_cells[i]
            cell.text = header
            cell.paragraphs[0].runs[0].font.bold = True
            cell.paragraphs[0].runs[0].font.size = Pt(11)
            cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Data rows
        for student in students:
            row_cells = table.add_row().cells
            row_cells[0].text = student.get('name', '')
            row_cells[1].text = student.get('lrn', '')
            row_cells[2].text = f"{student.get('exam', 0)}%"
            row_cells[3].text = f"{student.get('interview', 0)}%"
            row_cells[4].text = student.get('finalSection', '-')
            
            for cell in row_cells:
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="section_assignments_{program_code}.docx"'
        return response
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)