"""
Management command to create a test transferee enrollment for testing AI mode.

Usage:
  python manage.py create_test_transferee
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.core.files.base import ContentFile
from decimal import Decimal
import sys

from enrollment_app.models import (
    Student, StudentData, AcademicData, FamilyData, 
    ProgramSelection, StudentEnrollment, Parent
)
from admin_app.models import SchoolYear, Program, GradeLevel


class Command(BaseCommand):
    help = 'Create a test transferee enrollment request for AI processing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating test transferee enrollment...\n'))

        try:
            with transaction.atomic():
                student_lrn = '199006180405'
                
                # PRE-STEP: Clear any existing ProgramSelection to force signal re-trigger
                self.stdout.write('Pre-step: Cleaning up existing records...')
                ProgramSelection.objects.filter(student__lrn=student_lrn).delete()
                self.stdout.write(self.style.SUCCESS('✅ Cleaned old records\n'))
                
                # Step 1: Get or create SchoolYear
                self.stdout.write('Step 1: Setting up school year...')
                active_sy = SchoolYear.objects.filter(is_active=True).first()
                if not active_sy:
                    self.stdout.write(self.style.ERROR('❌ No active school year found!'))
                    return
                self.stdout.write(self.style.SUCCESS(f'✅ School Year: {active_sy.year_label}\n'))

                # Step 2: Get or create Student
                self.stdout.write('Step 2: Creating/updating student...')
                student, created = Student.objects.get_or_create(
                    lrn=student_lrn,
                    defaults={'is_active': True}
                )
                status = "Created" if created else "Found existing"
                self.stdout.write(self.style.SUCCESS(f'✅ {status}: {student.lrn}\n'))

                # Step 3: Create/update StudentData
                self.stdout.write('Step 3: Creating student data...')
                student_data, _ = StudentData.objects.update_or_create(
                    student=student,
                    defaults={
                        'last_name': 'Rubio',
                        'first_name': 'Aidan Ruselle',
                        'middle_name': '',
                        'gender': 'Female',
                        'date_of_birth': timezone.now().date().replace(year=timezone.now().year - 14),
                        'place_of_birth': 'Test City',
                        'religion': 'Islam',
                        'address': 'Test Address',
                        'enrolling_as': 'transferee',
                        'is_sped': False,
                        'is_working_student': False,
                        'last_school_attended': 'Previous School Inc.',
                        'previous_grade_section': 'Grade 7 - Test Section',
                        'last_school_year': '2024-2025',
                        'transferee_grade_level': '8',
                        'previous_program': 'REGULAR',
                        'coordinator_selected_track': 'TOP5',
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'✅ StudentData: {student_data.full_name}\n'))

                # Step 4: Create/update AcademicData
                self.stdout.write('Step 4: Creating academic data...')
                academic_data, _ = AcademicData.objects.update_or_create(
                    student=student,
                    defaults={
                        'mathematics': Decimal('82'),
                        'english': Decimal('80'),
                        'science': Decimal('81'),
                        'filipino': Decimal('83'),
                        'araling_panlipunan': Decimal('80'),
                        'edukasyon_sa_pagpapakatao': Decimal('82'),
                        'edukasyon_pangkabuhayan': Decimal('81'),
                        'mapeh': Decimal('80'),
                        'dost_exam_result': 'passed',
                        'overall_average': Decimal('81.25'),
                        'is_working_student': False,
                        'is_pwd': False,
                    }
                )
                self.stdout.write(self.style.SUCCESS(f'✅ AcademicData: Average = {academic_data.overall_average}\n'))

                # Step 4.5: Create mock report card file
                self.stdout.write('Step 4.5: Creating report card file...')
                if not academic_data.report_card:
                    mock_pdf_content = b'%PDF-1.4\n%Mock Report Card for Testing\n%%EOF'
                    academic_data.report_card.save(
                        f'report_card_{student_lrn}.pdf',
                        ContentFile(mock_pdf_content),
                        save=True
                    )
                    self.stdout.write(self.style.SUCCESS('✅ Report Card file created\n'))
                else:
                    self.stdout.write(self.style.SUCCESS('✅ Report Card already exists\n'))

                # Step 5: Create/update FamilyData
                self.stdout.write('Step 5: Creating family data...')
                mother, _ = Parent.objects.get_or_create(
                    family_name='Alfad',
                    first_name='Test',
                    defaults={
                        'middle_name': 'Mother',
                        'date_of_birth': timezone.now().date().replace(year=1980),
                        'occupation': 'Teacher',
                        'address': 'Test Address',
                        'contact_number': '09123456789',
                        'email': 'test.mother@example.com',
                    }
                )
                family_data, _ = FamilyData.objects.update_or_create(
                    student=student,
                    defaults={
                        'mother': mother,
                        'official_guardian_type': 'mother',
                    }
                )
                self.stdout.write(self.style.SUCCESS('✅ FamilyData created\n'))

                # Step 6: Get or create Program
                self.stdout.write('Step 6: Setting up program...')
                program, _ = Program.objects.get_or_create(
                    code='REGULAR',
                    defaults={'name': 'Regular Program', 'is_active': True}
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Program: {program.code}\n'))

                # Step 7: Get or create Grade Level
                self.stdout.write('Step 7: Setting up grade level...')
                grade_level, _ = GradeLevel.objects.get_or_create(
                    code='G8',
                    defaults={'name': 'Grade 8'}
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Grade Level: {grade_level.code}\n'))

                # Step 8: Create/update StudentEnrollment
                self.stdout.write('Step 8: Creating enrollment record...')
                enrollment, created = StudentEnrollment.objects.update_or_create(
                    student=student,
                    school_year=active_sy,
                    defaults={
                        'enrollment_status': 'pending',
                        'enrollee_type': 'transferee',
                        'grade_level': grade_level,
                        'student_data_completed': True,
                        'family_data_completed': True,
                        'survey_completed': True,
                        'academic_data_completed': True,
                        'program_selected': True,
                        'documents_completed': False,
                    }
                )
                status = "Created" if created else "Updated"
                self.stdout.write(self.style.SUCCESS(f'✅ StudentEnrollment: {status}\n'))

                # Step 9: Create ProgramSelection
                self.stdout.write('Step 9: Creating program selection...')
                prog_selection = ProgramSelection.objects.create(
                    student=student,
                    school_year=active_sy,
                    requires_program_selection=False,
                    selected_program_code='REGULAR',
                    regular_track='HETERO',
                    program_description='Regular Program - Hetero Track',
                    selection_reason='Transferee enrollment',
                    admin_approved=False,
                    admin_rejected=False,
                    admin_notes='Created via test script - transferee requires manual review per AI rules',
                )
                self.stdout.write(self.style.SUCCESS('✅ ProgramSelection created\n'))

                # Success summary
                self.stdout.write(self.style.SUCCESS('\n' + '='*80))
                self.stdout.write(self.style.SUCCESS('✅ TEST TRANSFEREE ENROLLMENT CREATED SUCCESSFULLY!'))
                self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
                
                self.stdout.write(self.style.WARNING('📋 ENROLLMENT DETAILS:'))
                self.stdout.write(f'   LRN: {student.lrn}')
                self.stdout.write(f'   Name: {student_data.full_name}')
                self.stdout.write(f'   Enrolling As: Transferee')
                self.stdout.write(f'   Grade Level: {grade_level.code}')
                self.stdout.write(f'   Program: {program.code}')
                self.stdout.write(f'   Track: HETERO')
                self.stdout.write(f'   Average Grade: {academic_data.overall_average}')
                self.stdout.write(f'   School Year: {active_sy.year_label}')
                self.stdout.write(f'   Status: Under Manual Review (Transferee flag)')
                self.stdout.write('\n')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERROR: {str(e)}'))
            import traceback
            traceback.print_exc()
            raise CommandError(f'Failed to create test transferee: {str(e)}')