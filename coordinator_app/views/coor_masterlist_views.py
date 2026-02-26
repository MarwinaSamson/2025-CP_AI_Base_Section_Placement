from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Avg, Count, Q
from admin_app.decorators import coordinator_required
from admin_app.models import Section
from enrollment_app.models import Student, ProgramSelection
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

@coordinator_required
def masterlist_by_section(request, section_id):
    """View to display masterlist for a specific section"""
    try:
        # Get coordinator's profile and program
        user_profile = request.user.profile
        program = user_profile.program
        
        # Get the section (ensure it belongs to coordinator's program)
        section = get_object_or_404(
            Section.objects.select_related('program', 'school_year', 'adviser'),
            id=section_id,
            program=program
        )
        
        # Get students enrolled in this section through ProgramSelection
        program_selections = ProgramSelection.objects.filter(
            assigned_section=str(section_id),
            admin_approved=True
        ).select_related(
            'student',
            'student__student_data',
            'student__academic_data'
        ).order_by('student__student_data__last_name', 'student__student_data__first_name')
        
        # Build student list with all needed data
        students_data = []
        for idx, ps in enumerate(program_selections, 1):
            student = ps.student
            student_info = getattr(student, 'student_data', None)
            academic_info = getattr(student, 'academic_data', None)
            
            if student_info:
                students_data.append({
                    'number': idx,
                    'lrn': student.lrn,
                    'last_name': student_info.last_name,
                    'first_name': student_info.first_name,
                    'middle_name': student_info.middle_name or '',
                    'full_name': student_info.full_name,
                    'gender': student_info.gender,
                    'age': student_info.age,
                    'enrolling_as': student_info.enrolling_as if student_info.enrolling_as else [],
                    'overall_average': academic_info.overall_average if academic_info else None,
                    'status': 'Enrolled' if ps.admin_approved else 'Pending',
                })
        
        # Calculate statistics
        total_students = len(students_data)
        male_count = sum(1 for s in students_data if s['gender'] == 'male')
        female_count = sum(1 for s in students_data if s['gender'] == 'female')
        
        # Calculate averages
        averages = [s['overall_average'] for s in students_data if s['overall_average'] is not None]
        class_average = sum(averages) / len(averages) if averages else 0
        
        ages = [s['age'] for s in students_data if s['age'] is not None]
        average_age = sum(ages) / len(ages) if ages else 0
        
        # Calculate slots remaining
        slots_remaining = section.max_students - total_students
        
        context = {
            'user': request.user,
            'section': section,
            'students': students_data,
            'program': program.code if program else '',         # change this
            'program_full_name': program.name if program else '', # add this
            'program_code': program.code if program else '',    # add this
            'user_profile': user_profile,
            'total_students': total_students,
            'male_count': male_count,
            'female_count': female_count,
            'male_percentage': (male_count / total_students * 100) if total_students > 0 else 0,
            'female_percentage': (female_count / total_students * 100) if total_students > 0 else 0,
            'class_average': round(class_average, 2),
            'average_age': round(average_age, 1),
            'slots_remaining': slots_remaining,
        }
        return render(request, 'coordinator_app/cor-masterlist.html', context)
    except Exception as e:
        context = {
            'user': request.user,
            'error': str(e),
            'students': [],
        }
        return render(request, 'coordinator_app/cor-masterlist.html', context)


@coordinator_required
def export_masterlist_excel(request, section_id):
    """Export masterlist to Excel"""
    try:
        user_profile = request.user.profile
        program = user_profile.program
        
        section = get_object_or_404(
            Section.objects.select_related('program', 'school_year', 'adviser'),
            id=section_id,
            program=program
        )
        
        program_selections = ProgramSelection.objects.filter(
            assigned_section=str(section_id),
            admin_approved=True
        ).select_related(
            'student',
            'student__student_data',
            'student__academic_data'
        ).order_by('student__student_data__last_name', 'student__student_data__first_name')
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"{section.name} Masterlist"
        
        # Add header info
        ws.merge_cells('A1:H1')
        ws['A1'] = f"{section.name} - Student Masterlist"
        ws['A1'].font = Font(bold=True, size=16)
        ws['A1'].alignment = Alignment(horizontal='center')
        
        ws.merge_cells('A2:H2')
        ws['A2'] = f"Program: {section.program.name} | Adviser: {section.adviser.first_name if section.adviser else 'Not assigned'} {section.adviser.last_name if section.adviser else ''}"
        ws['A2'].alignment = Alignment(horizontal='center')
        
        # Add column headers
        headers = ['#', 'LRN', 'Last Name', 'First Name', 'Middle Name', 'Gender', 'Age', 'Overall Average']
        header_fill = PatternFill(start_color="991B1B", end_color="991B1B", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')
        
        # Add student data
        for idx, ps in enumerate(program_selections, 1):
            student = ps.student
            student_info = getattr(student, 'student_data', None)
            academic_info = getattr(student, 'academic_data', None)
            
            if student_info:
                row = idx + 4
                ws.cell(row=row, column=1, value=idx)
                ws.cell(row=row, column=2, value=student.lrn)
                ws.cell(row=row, column=3, value=student_info.last_name)
                ws.cell(row=row, column=4, value=student_info.first_name)
                ws.cell(row=row, column=5, value=student_info.middle_name or '')
                ws.cell(row=row, column=6, value=student_info.gender.capitalize())
                ws.cell(row=row, column=7, value=student_info.age)
                ws.cell(row=row, column=8, value=round(academic_info.overall_average, 2) if academic_info and academic_info.overall_average else 'N/A')
        
        # Adjust column widths
        ws.column_dimensions['A'].width = 5
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 20
        ws.column_dimensions['D'].width = 20
        ws.column_dimensions['E'].width = 20
        ws.column_dimensions['F'].width = 10
        ws.column_dimensions['G'].width = 8
        ws.column_dimensions['H'].width = 15
        
        # Create response
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{section.name}_Masterlist.xlsx"'
        wb.save(response)
        return response
    except Exception as e:
        return HttpResponse(f"Error exporting: {str(e)}", status=500)


@coordinator_required
def export_masterlist_pdf(request, section_id):
    """Export masterlist to PDF"""
    try:
        user_profile = request.user.profile
        program = user_profile.program
        
        section = get_object_or_404(
            Section.objects.select_related('program', 'school_year', 'adviser'),
            id=section_id,
            program=program
        )
        
        program_selections = ProgramSelection.objects.filter(
            assigned_section=str(section_id),
            admin_approved=True
        ).select_related(
            'student',
            'student__student_data',
            'student__academic_data'
        ).order_by('student__student_data__last_name', 'student__student_data__first_name')
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{section.name}_Masterlist.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=landscape(letter))
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title
        title = Paragraph(f"<b>{section.name} - Student Masterlist</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Add section info
        info = Paragraph(f"Program: {section.program.name} | Adviser: {section.adviser.first_name if section.adviser else 'Not assigned'} {section.adviser.last_name if section.adviser else ''}", styles['Normal'])
        elements.append(info)
        elements.append(Spacer(1, 0.3*inch))
        
        # Create table data
        data = [['#', 'LRN', 'Last Name', 'First Name', 'M.I.', 'Gender', 'Age', 'Average']]
        
        for idx, ps in enumerate(program_selections, 1):
            student = ps.student
            student_info = getattr(student, 'student_data', None)
            academic_info = getattr(student, 'academic_data', None)
            
            if student_info:
                data.append([
                    str(idx),
                    student.lrn,
                    student_info.last_name,
                    student_info.first_name,
                    student_info.middle_name[0] if student_info.middle_name else '',
                    student_info.gender.capitalize(),
                    str(student_info.age) if student_info.age else '',
                    f"{academic_info.overall_average:.2f}" if academic_info and academic_info.overall_average else 'N/A'
                ])
        
        # Create table
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
    except Exception as e:
        return HttpResponse(f"Error exporting PDF: {str(e)}", status=500)


@coordinator_required
def export_masterlist_docx(request, section_id):
    """Export masterlist to Word document"""
    try:
        user_profile = request.user.profile
        program = user_profile.program
        
        section = get_object_or_404(
            Section.objects.select_related('program', 'school_year', 'adviser'),
            id=section_id,
            program=program
        )
        
        program_selections = ProgramSelection.objects.filter(
            assigned_section=str(section_id),
            admin_approved=True
        ).select_related(
            'student',
            'student__student_data',
            'student__academic_data'
        ).order_by('student__student_data__last_name', 'student__student_data__first_name')
        
        # Create document
        doc = Document()
        
        # Add title
        title = doc.add_heading(f'{section.name} - Student Masterlist', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add section info
        info = doc.add_paragraph()
        info.add_run(f"Program: {section.program.name} | Adviser: {section.adviser.first_name if section.adviser else 'Not assigned'} {section.adviser.last_name if section.adviser else ''}").bold = True
        info.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add table
        table = doc.add_table(rows=1, cols=8)
        table.style = 'Light Grid Accent 1'
        
        # Add header row
        header_cells = table.rows[0].cells
        headers = ['#', 'LRN', 'Last Name', 'First Name', 'Middle Name', 'Gender', 'Age', 'Average']
        for i, header in enumerate(headers):
            cell = header_cells[i]
            cell.text = header
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
            cell._element.get_or_add_tcPr().append(
                cell._element._new_tag('w:shd', 'w:fill', '991B1B')
            )
        
        # Add student rows
        for idx, ps in enumerate(program_selections, 1):
            student = ps.student
            student_info = getattr(student, 'student_data', None)
            academic_info = getattr(student, 'academic_data', None)
            
            if student_info:
                row_cells = table.add_row().cells
                row_cells[0].text = str(idx)
                row_cells[1].text = student.lrn
                row_cells[2].text = student_info.last_name
                row_cells[3].text = student_info.first_name
                row_cells[4].text = student_info.middle_name or ''
                row_cells[5].text = student_info.gender.capitalize()
                row_cells[6].text = str(student_info.age) if student_info.age else ''
                row_cells[7].text = f"{academic_info.overall_average:.2f}" if academic_info and academic_info.overall_average else 'N/A'
        
        # Save document
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = f'attachment; filename="{section.name}_Masterlist.docx"'
        doc.save(response)
        return response
    except Exception as e:
        return HttpResponse(f"Error exporting DOCX: {str(e)}", status=500)
