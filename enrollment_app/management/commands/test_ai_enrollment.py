"""
Django management command to test AI auto-enrollment processing.
Tests that the signal fires correctly when a new student enrolls.

Usage:
    python manage.py test_ai_enrollment
    python manage.py test_ai_enrollment --program SPTVE
    python manage.py test_ai_enrollment --keep-data  # Don't clean up test data
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
    help = 'Test AI auto-enrollment processing by simulating a complete enrollment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--program',
            type=str,
            default='SPTVE',
            help='Program code to test (default: SPTVE)'
        )
        parser.add_argument(
            '--keep-data',
            action='store_true',
            help='Keep test data after test (do not clean up)'
        )

    def handle(self, *args, **options):
        program_code = options['program']
        keep_data = options['keep_data']

        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(self.style.SUCCESS('AI AUTO-ENROLLMENT TEST'))
        self.stdout.write(self.style.SUCCESS('='*80))
        self.stdout.write(f"\nTesting program: {program_code}")
        self.stdout.write(f"Keep test data: {keep_data}\n")

        # Generate unique test LRN (max 12 chars)
        # Use last 8 digits of timestamp to keep it under 12 chars
        timestamp = str(int(time.time()))[-8:]
        test_lrn = f'TEST{timestamp}'
        self.stdout.write(f"Test LRN: {test_lrn}\n")

        try:
            # Step 1: Pre-flight checks
            self.stdout.write(self.style.WARNING('\n[STEP 1] Pre-flight Checks'))
            self.stdout.write('-'*80)

            # Check school year
            school_year = SchoolYear.objects.filter(is_active=True).first()
            if not school_year:
                self.stdout.write(self.style.ERROR('✗ No active school year found'))
                return
            self.stdout.write(self.style.SUCCESS(f'✓ Active school year: {school_year.year_label}'))

            # Check program exists
            try:
                program = Program.objects.get(code=program_code)
                self.stdout.write(self.style.SUCCESS(f'✓ Program found: {program.name}'))
            except Program.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'✗ Program "{program_code}" not found'))
                return

            # Check AI is enabled
            ai_pref = AIAssistantPreference.objects.filter(
                program=program,
                ai_enabled=True
            ).first()
            if not ai_pref:
                self.stdout.write(self.style.ERROR(f'✗ AI not enabled for {program_code}'))
                self.stdout.write(self.style.WARNING('  Enable AI in coordinator settings first'))
                return
            self.stdout.write(self.style.SUCCESS(f'✓ AI enabled by: {ai_pref.user.username}'))

            # Check sections available
            sections = Section.objects.filter(
                program=program,
                school_year=school_year
            )
            if not sections.exists():
                self.stdout.write(self.style.ERROR(f'✗ No sections found for {program_code}'))
                return

            available_sections = []
            for section in sections:
                actual = section.get_actual_count()
                available = section.max_students - actual
                if available > 0:
                    available_sections.append(section)
                self.stdout.write(f'  - {section.name}: {actual}/{section.max_students} (Available: {available})')

            if not available_sections:
                self.stdout.write(self.style.ERROR('✗ All sections are full'))
                return
            self.stdout.write(self.style.SUCCESS(f'✓ {len(available_sections)} section(s) with space'))

            # Check report card requirement
            report_req = DocumentRequirement.objects.filter(
                name__icontains='report card',
                is_active=True
            ).first()
            if not report_req:
                self.stdout.write(self.style.ERROR('✗ No "Report Card" requirement found'))
                return
            self.stdout.write(self.style.SUCCESS(f'✓ Report Card requirement exists'))

            # Step 2: Create test enrollment
            self.stdout.write(self.style.WARNING('\n[STEP 2] Creating Test Enrollment'))
            self.stdout.write('-'*80)

            with transaction.atomic():
                # Create Student
                student = Student.objects.create(
                    lrn=test_lrn,
                    email='test@aitest.com',
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
                self.stdout.write(self.style.SUCCESS(f'✓ Student created'))

                # Create StudentData
                StudentData.objects.create(
                    student=student,
                    last_name='TestLast',
                    first_name='TestFirst',
                    middle_name='T',
                    gender='male',
                    date_of_birth=date(2010, 1, 1),
                )
                self.stdout.write(self.style.SUCCESS(f'✓ StudentData created'))

                # Create Parent
                parent = Parent.objects.create(
                    family_name='TestParent',
                    first_name='Mother',
                    parent_type='mother',
                    date_of_birth=date(1980, 1, 1),
                    occupation='Teacher',
                    contact_number='09123456789',
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Parent created'))

                # Create FamilyData
                FamilyData.objects.create(
                    student=student,
                    mother=parent,
                    official_guardian_type='mother',
                )
                self.stdout.write(self.style.SUCCESS(f'✓ FamilyData created'))

                # Create SurveyData
                SurveyData.objects.create(
                    student=student,
                    enjoyed_subjects=['Math', 'Science'],
                    difficulty_areas=[],
                )
                self.stdout.write(self.style.SUCCESS(f'✓ SurveyData created'))

                # Create AcademicData
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
                self.stdout.write(self.style.SUCCESS(f'✓ AcademicData created'))

                # Create Report Card Document Submission
                # This is CRITICAL - must be created BEFORE ProgramSelection
                submission = StudentDocumentSubmission.objects.create(
                    student=student,
                    requirement=report_req,
                    file_name='test_report_card.jpg',
                    file_size=1000,
                    file_format='jpg',
                    status='pending',
                )
                # Add a dummy file
                submission.document_file.save(
                    'test_report_card.jpg',
                    ContentFile(b'dummy test file'),
                    save=True
                )
                self.stdout.write(self.style.SUCCESS(f'✓ Report Card document created'))

                # NOW create ProgramSelection (this should trigger the signal)
                self.stdout.write(self.style.WARNING(f'\n  → Creating ProgramSelection (signal should fire)...'))

                ps = ProgramSelection.objects.create(
                    student=student,
                    school_year=school_year,
                    selected_program_code=program_code,
                    program_description='Test enrollment for AI auto-processing',
                    selection_reason='Testing AI signal',
                )
                self.stdout.write(self.style.SUCCESS(f'✓ ProgramSelection created'))

            # Step 3: Verify auto-processing
            self.stdout.write(self.style.WARNING('\n[STEP 3] Verifying Auto-Processing'))
            self.stdout.write('-'*80)

            # Refresh to get updated data
            ps.refresh_from_db()
            student.refresh_from_db()

            # Check results
            success = True

            if ps.admin_approved:
                self.stdout.write(self.style.SUCCESS(f'✓ Auto-approved: {ps.admin_approved}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ Not approved: {ps.admin_approved}'))
                success = False

            if ps.approved_by == 'AI Assistant':
                self.stdout.write(self.style.SUCCESS(f'✓ Approved by: {ps.approved_by}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ Approved by: {ps.approved_by or "None"}'))
                success = False

            if ps.assigned_section:
                # Get section details
                try:
                    section = Section.objects.get(id=ps.assigned_section)
                    self.stdout.write(self.style.SUCCESS(f'✓ Assigned section: {section.name} (ID: {ps.assigned_section})'))
                except:
                    self.stdout.write(self.style.SUCCESS(f'✓ Assigned section: {ps.assigned_section}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ No section assigned'))
                success = False

            if student.enrollment_status == 'approved':
                self.stdout.write(self.style.SUCCESS(f'✓ Student status: {student.enrollment_status}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ Student status: {student.enrollment_status}'))
                success = False

            # Step 4: Clean up (unless --keep-data)
            if not keep_data:
                self.stdout.write(self.style.WARNING('\n[STEP 4] Cleaning Up Test Data'))
                self.stdout.write('-'*80)
                student.delete()  # Cascade deletes all related data
                self.stdout.write(self.style.SUCCESS('✓ Test data removed'))
            else:
                self.stdout.write(self.style.WARNING('\n[STEP 4] Keeping Test Data'))
                self.stdout.write('-'*80)
                self.stdout.write(f'Test student LRN: {test_lrn}')
                self.stdout.write('  (Clean up manually if needed)')

            # Final result
            self.stdout.write('\n' + '='*80)
            if success:
                self.stdout.write(self.style.SUCCESS('🎉 TEST PASSED! AI auto-processing works correctly!'))
            else:
                self.stdout.write(self.style.ERROR('❌ TEST FAILED! AI auto-processing did not work.'))
                self.stdout.write(self.style.WARNING('\nTroubleshooting:'))
                self.stdout.write('1. Check that signals are registered in enrollment_app/apps.py')
                self.stdout.write('2. Verify the signal code in enrollment_app/signals.py')
                self.stdout.write('3. Check Django logs for errors during signal execution')
            self.stdout.write('='*80 + '\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERROR: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

            # Clean up on error
            try:
                if not keep_data:
                    Student.objects.filter(lrn=test_lrn).delete()
                    self.stdout.write(self.style.WARNING('\nTest data cleaned up after error'))
            except:
                pass
