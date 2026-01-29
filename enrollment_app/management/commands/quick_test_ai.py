"""
Quick test for AI auto-enrollment - minimal output, fast execution.

Usage:
    python manage.py quick_test_ai
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.core.files.base import ContentFile
from enrollment_app.models import (
    Student, StudentData, Parent, FamilyData,
    SurveyData, AcademicData, ProgramSelection,
    StudentDocumentSubmission
)
from admin_app.models import SchoolYear, Program, Section, DocumentRequirement
from coordinator_app.models import AIAssistantPreference
from datetime import date
import time


class Command(BaseCommand):
    help = 'Quick test of AI auto-enrollment (minimal output)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--program',
            type=str,
            default='SPTVE',
            help='Program code to test (default: SPTVE)'
        )

    def handle(self, *args, **options):
        program_code = options['program']

        self.stdout.write('Testing AI auto-enrollment...')

        # Generate test LRN
        timestamp = str(int(time.time()))[-8:]
        test_lrn = f'TEST{timestamp}'

        try:
            # Quick pre-flight
            school_year = SchoolYear.objects.filter(is_active=True).first()
            if not school_year:
                self.stdout.write(self.style.ERROR('✗ No active school year'))
                return

            program = Program.objects.get(code=program_code)

            ai_pref = AIAssistantPreference.objects.filter(
                program=program, ai_enabled=True
            ).first()
            if not ai_pref:
                self.stdout.write(self.style.ERROR(f'✗ AI not enabled for {program_code}'))
                return

            sections = Section.objects.filter(
                program=program,
                school_year=school_year
            )
            if not sections.exists():
                self.stdout.write(self.style.ERROR('✗ No sections found'))
                return

            report_req = DocumentRequirement.objects.filter(
                name__icontains='report card',
                is_active=True
            ).first()
            if not report_req:
                self.stdout.write(self.style.ERROR('✗ No report card requirement'))
                return

            self.stdout.write('Pre-checks passed. Creating test enrollment...')

            # Create everything in one transaction
            with transaction.atomic():
                # Student
                student = Student.objects.create(
                    lrn=test_lrn,
                    email='test@test.com',
                    school_year=school_year,
                    enrollment_status='submitted',
                    student_data_completed=True,
                    family_data_completed=True,
                    survey_completed=True,
                    academic_data_completed=True,
                    program_selected=True,
                    student_data_completed_at=timezone.now(),
                    family_data_completed_at=timezone.now(),
                    survey_completed_at=timezone.now(),
                    academic_data_completed_at=timezone.now(),
                    program_selected_at=timezone.now(),
                )

                # Student Data
                StudentData.objects.create(
                    student=student,
                    last_name='Test',
                    first_name='Student',
                    gender='male',
                    date_of_birth=date(2010, 1, 1),
                )

                # Parent
                parent = Parent.objects.create(
                    family_name='TestParent',
                    first_name='Mother',
                    parent_type='mother',
                    date_of_birth=date(1980, 1, 1),
                    occupation='Teacher',
                    contact_number='09123456789',
                )

                # Family Data
                FamilyData.objects.create(
                    student=student,
                    mother=parent,
                    official_guardian_type='mother',
                )

                # Survey
                SurveyData.objects.create(
                    student=student,
                    enjoyed_subjects=['Math'],
                    difficulty_areas=[],
                )

                # Academic
                AcademicData.objects.create(
                    student=student,
                    mathematics=90,
                    science=88,
                    english=85,
                    filipino=87,
                    araling_panlipunan=86,
                    edukasyon_sa_pagpapakatao=89,
                    edukasyon_pangkabuhayan=84,
                    mapeh=90,
                )

                # REPORT CARD - Must be before ProgramSelection
                submission = StudentDocumentSubmission.objects.create(
                    student=student,
                    requirement=report_req,
                    file_name='test_report.jpg',
                    file_size=1000,
                    file_format='jpg',
                    status='pending',
                )
                submission.document_file.save(
                    'test_report.jpg',
                    ContentFile(b'test'),
                    save=True
                )

                self.stdout.write('All data created. Creating ProgramSelection (signal fires now)...')

                # PROGRAM SELECTION - Signal fires here
                ps = ProgramSelection.objects.create(
                    student=student,
                    school_year=school_year,
                    selected_program_code=program_code,
                    program_description='Test',
                    selection_reason='Test',
                )

            # Check results
            ps.refresh_from_db()
            student.refresh_from_db()

            self.stdout.write('\n' + '='*60)

            if ps.admin_approved and ps.approved_by == 'AI Assistant' and ps.assigned_section:
                self.stdout.write(self.style.SUCCESS('✅ SUCCESS! AI Auto-Processing Works!'))
                self.stdout.write(f'   - Approved: {ps.admin_approved}')
                self.stdout.write(f'   - Approved By: {ps.approved_by}')
                self.stdout.write(f'   - Section: {ps.assigned_section}')
                self.stdout.write(f'   - Status: {student.enrollment_status}')
            else:
                self.stdout.write(self.style.ERROR('❌ FAILED - AI did not auto-process'))
                self.stdout.write(f'   - Approved: {ps.admin_approved}')
                self.stdout.write(f'   - Approved By: {ps.approved_by or "None"}')
                self.stdout.write(f'   - Section: {ps.assigned_section or "None"}')
                self.stdout.write(f'   - Status: {student.enrollment_status}')

            self.stdout.write('='*60)

            # Clean up
            student.delete()
            self.stdout.write('Test data cleaned up.')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERROR: {str(e)}'))
            # Clean up on error
            try:
                Student.objects.filter(lrn=test_lrn).delete()
            except:
                pass
