from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.core.files.base import ContentFile
from decimal import Decimal

from enrollment_app.models import (
    Student, StudentData, AcademicData, FamilyData, 
    ProgramSelection, StudentEnrollment, Parent, SurveyData
)
from admin_app.models import SchoolYear, Program, GradeLevel


class Command(BaseCommand):
    help = 'Create a test NEW student enrollment for full AI/ML flow testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating test NEW student enrollment...\n'))

        try:
            with transaction.atomic():
                student_lrn = '126113180161'
                
                # PRE-STEP: Clear existing records
                self.stdout.write('Pre-step: Cleaning up existing records...')
                Student.objects.filter(lrn=student_lrn).delete()
                self.stdout.write(self.style.SUCCESS('✅ Cleaned old records\n'))
                
                # Step 1: SchoolYear
                self.stdout.write('Step 1: Setting up school year...')
                active_sy = SchoolYear.objects.filter(is_active=True).first()
                if not active_sy:
                    self.stdout.write(self.style.ERROR('❌ No active school year!'))
                    return
                self.stdout.write(f'✅ School Year: {active_sy.year_label}\n')

                # Step 2: Student
                self.stdout.write('Step 2: Creating student...')
                student = Student.objects.create(lrn=student_lrn, is_active=True)
                self.stdout.write(f'✅ Student: {student.lrn}\n')

                # Step 3: StudentData (NEW student)
                self.stdout.write('Step 3: Creating student data...')
                student_data = StudentData.objects.create(
                    student=student,
                    last_name='Mariano',
                    first_name='Paul James',
                    middle_name='G.',
                    gender='male',
                    date_of_birth=timezone.now().date().replace(year=timezone.now().year - 13),  # ~13yo Grade 7
                    place_of_birth='Test City',
                    religion='Christian',
                    address='Test Address 123',
                    enrolling_as=['new'],
                    is_sped=False,
                    is_working_student=False,
                    agreed_to_terms=True
                )
                self.stdout.write(f'✅ StudentData: {student_data.full_name}\n')

                # Step 4: AcademicData (required for new students)
                self.stdout.write('Step 4: Creating academic data...')
                grade6 = GradeLevel.objects.filter(code='G6').first()
                if not grade6:
                    grade6 = GradeLevel.objects.get_or_create(code='G6', defaults={'name': 'Grade 6'})[0]
                academic_data = AcademicData.objects.create(
                    student=student,
                    report_card_grade_level=grade6,
                    mathematics=Decimal('85'),
                    english=Decimal('88'),
                    science=Decimal('90'),
                    filipino=Decimal('87'),
                    araling_panlipunan=Decimal('86'),
                    edukasyon_sa_pagpapakatao=Decimal('89'),
                    edukasyon_pangkabuhayan=Decimal('84'),
                    mapeh=Decimal('92'),
                    dost_exam_result='passed',
                    overall_average=Decimal('87.50')
                )
                # Mock report card
                mock_pdf = b'%PDF-1.4\n%Grade 6 Report Card - Test Data\n%%EOF'
                academic_data.report_card.save('new_student_report_card.pdf', ContentFile(mock_pdf), save=True)
                self.stdout.write(f'✅ AcademicData: Avg {academic_data.overall_average}\n')

                # Step 5: FamilyData
                self.stdout.write('Step 5: Creating family data...')
                mother = Parent.objects.create(
                    family_name='Mariano',
                    first_name='Test',
                    parent_type='mother',
                    date_of_birth=timezone.now().date().replace(year=1985),
                    occupation='Homemaker',
                    address='Test Address 123',
                    contact_number='09171234567',
                    email='paul.parent@example.com'
                )
                FamilyData.objects.create(
                    student=student,
                    mother=mother,
                    official_guardian_type='mother'
                )
                self.stdout.write('✅ FamilyData created\n')

                # Step 6: SurveyData (for new students)
                self.stdout.write('Step 6: Creating survey data...')
                SurveyData.objects.create(
                    student=student,
                    student_name=student_data.full_name,
                    age=13,
                    current_grade_section='Grade 6 - Top Section',
                    interested_program='Top 5'
                )
                self.stdout.write('✅ SurveyData created\n')

                # Step 7: GradeLevel/Program
                self.stdout.write('Step 7: Setting up grade/program...')
                g7 = GradeLevel.objects.get_or_create(code='G7', defaults={'name': 'Grade 7'})[0]
                program = Program.objects.filter(code='Top 5').first() or Program.objects.create(code='Top 5', name='Top 5 Program', is_active=True)
                self.stdout.write(f'✅ Grade: {g7.code}, Program: {program.code}\n')

                # Step 8: StudentEnrollment
                self.stdout.write('Step 8: Creating enrollment...')
                StudentEnrollment.objects.create(
                    student=student,
                    school_year=active_sy,
                    grade_level=g7,
                    enrollee_type='new',
                    enrollment_status='pending',
                    student_data_completed=True,
                    family_data_completed=True,
                    survey_completed=True,
                    academic_data_completed=True,
                    program_selected=True,
                    documents_completed=False  # Requires upload
                )
                self.stdout.write('✅ StudentEnrollment created\n')

                # Step 9: ProgramSelection (triggers AI signals)
                self.stdout.write('Step 9: Creating program selection (AI trigger)...')
                ProgramSelection.objects.create(
                    student=student,
                    school_year=active_sy,
                    requires_program_selection=True,  # NEW students use AI/ML
                    selected_program_code='Top 5',
                    regular_track='TOP5',
                    admin_approved=False,
                    admin_notes='Test new student - full AI flow'
                )
                self.stdout.write('✅ ProgramSelection created - AI signals triggered!\n')

                self.stdout.write(self.style.SUCCESS('\n🎉 NEW STUDENT ENROLLMENT CREATED!\n'))
                self.stdout.write(f'LRN: {student_lrn} | Name: {student_data.full_name} | Type: NEW | Program: Top 5 | Grade 7')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {str(e)}'))
            raise CommandError(str(e))

