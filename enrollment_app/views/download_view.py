"""
Download application form as PDF
"""
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from ..services.session_manager import EnrollmentSessionManager
from ..models import Student, StudentData, Parent, Guardian, FamilyData
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def generate_application_pdf(request):
    """
    Generate a PDF of the student's application form (Student Data + Family Data)
    """
    try:
        # Get student data from session first
        student_data = EnrollmentSessionManager.get_student_data(request)
        family_data = EnrollmentSessionManager.get_family_data(request)
        
        # If session data not available, try to get from database using LRN
        if not student_data or not family_data:
            # Try to get LRN from session
            lrn = None
            if student_data:
                lrn = student_data.get('lrn')
            
            # Try to fetch from database
            if lrn:
                try:
                    student = Student.objects.get(lrn=lrn)
                    student_data_obj = StudentData.objects.filter(student=student).first()
                    family_data_obj = FamilyData.objects.filter(student=student).first()
                    
                    if student_data_obj:
                        student_data = {
                            'lrn': student.lrn,
                            'first_name': student_data_obj.first_name,
                            'middle_name': student_data_obj.middle_name,
                            'last_name': student_data_obj.last_name,
                            'gender': student_data_obj.gender,
                            'date_of_birth': str(student_data_obj.date_of_birth) if student_data_obj.date_of_birth else '',
                            'place_of_birth': student_data_obj.place_of_birth,
                            'religion': student_data_obj.religion,
                            'dialect_spoken': student_data_obj.dialect_spoken,
                            'ethnic_tribe': student_data_obj.ethnic_tribe,
                            'current_address': student_data_obj.current_address,
                            'enrolling_as': [student_data_obj.enrolling_as] if student_data_obj.enrolling_as else [],
                            'is_sped': 'yes' if student_data_obj.is_sped else 'no',
                            'sped_details': student_data_obj.sped_details or '',
                            'is_working_student': 'yes' if student_data_obj.is_working_student else 'no',
                            'working_details': student_data_obj.working_type or '',
                        }
                    
                    if family_data_obj:
                        # Get parent info
                        father = Parent.objects.filter(student=student, relationship='FATHER').first()
                        mother = Parent.objects.filter(student=student, relationship='MOTHER').first()
                        guardian = Guardian.objects.filter(student=student).first()
                        
                        family_data = {
                            'father_first_name': father.first_name if father else '',
                            'father_family_name': father.last_name if father else '',
                            'father_dob': str(father.date_of_birth) if father and father.date_of_birth else '',
                            'father_occupation': father.occupation if father else '',
                            'father_address': father.address if father else '',
                            'father_contact_number': father.contact_number if father else '',
                            'father_email': father.email if father else '',
                            'mother_first_name': mother.first_name if mother else '',
                            'mother_family_name': mother.last_name if mother else '',
                            'mother_dob': str(mother.date_of_birth) if mother and mother.date_of_birth else '',
                            'mother_occupation': mother.occupation if mother else '',
                            'mother_address': mother.address if mother else '',
                            'mother_contact_number': mother.contact_number if mother else '',
                            'mother_email': mother.email if mother else '',
                            'guardian_first_name': guardian.first_name if guardian else '',
                            'guardian_family_name': guardian.last_name if guardian else '',
                            'guardian_relationship': guardian.relationship if guardian else '',
                            'guardian_contact_number': guardian.contact_number if guardian else '',
                            'guardian_address': guardian.address if guardian else '',
                            'number_of_siblings': family_data_obj.number_of_siblings,
                            'birth_order': family_data_obj.birth_order,
                            'living_arrangement': family_data_obj.living_arrangement,
                            'house_type': family_data_obj.house_type,
                            'monthly_household_income': family_data_obj.monthly_household_income,
                        }
                except (Student.DoesNotExist, Exception) as e:
                    print(f"Error fetching from database: {e}")
        
        # Final check if we have data
        if not student_data:
            return HttpResponse(
                "Student data not found. Please complete the enrollment form first.",
                status=400,
                content_type='text/plain'
            )
        
        if not family_data:
            family_data = {}  # Use empty dict if no family data
        
        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
            title="Enrollment Application Form"
        )
        
        # Container for PDF elements
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#991b1b'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        section_header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#ca3a31'),
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold',
            borderPadding=4,
            borderColor=colors.HexColor('#ca3a31'),
            borderWidth=0.5
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=4
        )
        
        label_style = ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            spaceAfter=2,
            fontName='Helvetica-Bold'
        )
        
        # Header Section
        header_data = [
            ['ZAMBOANGA NATIONAL HIGH SCHOOL WEST', 'ENROLLMENT APPLICATION FORM'],
        ]
        header_table = Table(header_data, colWidths=[3*inch, 3*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#991b1b')),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # =====================================================================
        # SECTION A: STUDENT INFORMATION
        # =====================================================================
        elements.append(Paragraph("A. STUDENT INFORMATION", section_header_style))
        
        # Student name and basic info
        student_name = f"{student_data.get('first_name', '')} {student_data.get('middle_name', '')} {student_data.get('last_name', '')}".strip()
        
        student_info_data = [
            ['Full Name:', student_name, 'LRN:', student_data.get('lrn', '')],
            ['Gender:', student_data.get('gender', ''), 'Date of Birth:', student_data.get('date_of_birth', '')],
            ['Place of Birth:', student_data.get('place_of_birth', ''), 'Age:', ''],
            ['Religion:', student_data.get('religion', ''), 'Mother Tongue:', student_data.get('dialect_spoken', '')],
            ['Ethnic Tribe:', student_data.get('ethnic_tribe', ''), 'Current Address:', student_data.get('current_address', '')],
        ]
        
        student_table = Table(student_info_data, colWidths=[1.2*inch, 1.8*inch, 1.2*inch, 1.8*inch])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        elements.append(student_table)
        elements.append(Spacer(1, 0.15*inch))
        
        # Enrollment info
        enrollment_type = ', '.join(student_data.get('enrolling_as', []))
        elements.append(Paragraph(f"<b>Enrolling As:</b> {enrollment_type}", normal_style))
        
        if student_data.get('is_sped') == 'yes':
            elements.append(Paragraph(f"<b>PWD/SPED:</b> Yes - {student_data.get('sped_details', '')}", normal_style))
        
        if student_data.get('is_working_student') == 'yes':
            elements.append(Paragraph(f"<b>Working Student:</b> Yes - {student_data.get('working_details', '')}", normal_style))
        
        elements.append(Spacer(1, 0.2*inch))
        
        # =====================================================================
        # SECTION B: FAMILY INFORMATION
        # =====================================================================
        elements.append(Paragraph("B. FAMILY INFORMATION", section_header_style))
        
        # Father's Information
        elements.append(Paragraph("<b>Father's Information:</b>", ParagraphStyle(
            'SubHeader',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceAfter=4
        )))
        
        father_data = [
            ['Name:', f"{family_data.get('father_first_name', '')} {family_data.get('father_family_name', '')}"],
            ['Date of Birth:', family_data.get('father_dob', ''), 'Occupation:', family_data.get('father_occupation', '')],
            ['Address:', family_data.get('father_address', '')],
            ['Contact Number:', family_data.get('father_contact_number', ''), 'Email:', family_data.get('father_email', '')],
        ]
        
        father_table = Table(father_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
        father_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f3f4f6'), colors.white]),
        ]))
        elements.append(father_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # Mother's Information
        elements.append(Paragraph("<b>Mother's Information:</b>", ParagraphStyle(
            'SubHeader',
            parent=styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceAfter=4
        )))
        
        mother_data = [
            ['Name:', f"{family_data.get('mother_first_name', '')} {family_data.get('mother_family_name', '')}"],
            ['Date of Birth:', family_data.get('mother_dob', ''), 'Occupation:', family_data.get('mother_occupation', '')],
            ['Address:', family_data.get('mother_address', '')],
            ['Contact Number:', family_data.get('mother_contact_number', ''), 'Email:', family_data.get('mother_email', '')],
        ]
        
        mother_table = Table(mother_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
        mother_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f3f4f6'), colors.white]),
        ]))
        elements.append(mother_table)
        elements.append(Spacer(1, 0.1*inch))
        
        # Guardian's Information (if applicable)
        if family_data.get('guardian_relationship'):
            elements.append(Paragraph("<b>Guardian's Information:</b>", ParagraphStyle(
                'SubHeader',
                parent=styles['Normal'],
                fontSize=10,
                fontName='Helvetica-Bold',
                spaceAfter=4
            )))
            
            guardian_data = [
                ['Name:', f"{family_data.get('guardian_first_name', '')} {family_data.get('guardian_family_name', '')}"],
                ['Relationship:', family_data.get('guardian_relationship', ''), 'Contact:', family_data.get('guardian_contact_number', '')],
                ['Address:', family_data.get('guardian_address', '')],
            ]
            
            guardian_table = Table(guardian_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
            guardian_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f3f4f6'), colors.white]),
            ]))
            elements.append(guardian_table)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # =====================================================================
        # SECTION C: HOUSEHOLD INFORMATION
        # =====================================================================
        elements.append(Paragraph("C. HOUSEHOLD INFORMATION", section_header_style))
        
        household_data = [
            ['Number of Siblings:', family_data.get('number_of_siblings', ''), 'Birth Order:', family_data.get('birth_order', '')],
            ['Living Arrangement:', family_data.get('living_arrangement', ''), 'House Type:', family_data.get('house_type', '')],
            ['Monthly Household Income:', family_data.get('monthly_household_income', '')],
        ]
        
        household_table = Table(household_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 2*inch])
        household_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        elements.append(household_table)
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Footer
        footer_data = [
            ['Date Generated:', datetime.now().strftime('%B %d, %Y %I:%M %p')],
            ['Status:', 'Form Submitted Successfully'],
        ]
        footer_table = Table(footer_data, colWidths=[2*inch, 4*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(footer_table)
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        pdf_data = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        # Create response
        lrn = student_data.get('lrn', 'student')
        filename = f"Enrollment_Application_{lrn}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Error generating PDF: {str(e)}'
        }, status=500)


def download_application_form(request):
    """
    AJAX endpoint that returns download information
    Currently just triggers the PDF generation view
    """
    return generate_application_pdf(request)
