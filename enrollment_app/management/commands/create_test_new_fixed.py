#!/usr/bin/env python3
"""
Create Paul James G. Mariano test new student.
"""

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
    help = 'Create Paul James Mariano test new student (Grade 7 Top 5)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating test new student (Paul Mariano)...\n'))

        try:
            with transaction.atomic():
                student_lrn = '126113180161'
                Student.objects.filter(lrn=student_lrn).delete()

                sy = SchoolYear.objects.filter(is_active=True).first()
                if not sy:
                    raise CommandError('No active SchoolYear')

                student = Student.objects.create(lrn=student_lrn, is_active=True)
                
                student_data = StudentData.objects.create(
                    student=student,
                    last_name='Mariano',
                    first_name='Paul James',
                    middle_name='G.',
                    gender='male',
                    date_of_birth=timezone.now().date().replace(year=timezone.now().year - 13),
                    address='Test Address',
                    enrolling_as='new',
                    agreed_to_terms=True
                )
                
                # Academic (Grade 6 report)
                g6 = GradeLevel.objects.get_or_create(code='G6', defaults={'name': 'Grade 6'})[0]
                AcademicData.objects.create(
                    student=student,
                    report_card_grade_level=g6,
                    mathematics=85, english=88, science=90, filipino=87,
                    araling_panlipunan=86, edukasyon_sa_pagpapakatao=89,
                    edukasyon_pangkabuhayan=84, mapeh=92,
                    dost_exam_result='passed',
                    overall_average=Decimal('87.50')
                )
                
                # Family
                mother = Parent.objects.create(
                    family_name='Mariano', first_name='Test', parent_type='mother',
                    date_of_birth=timezone.now().date().replace(year=1985),
                    contact_number='09171234567'
                )
                FamilyData.objects.create(student=student, official_guardian_type='mother', mother=mother)
                
                # Survey
                SurveyData.objects.create(
                    student=student,
                    student_name=student_data.full_name,
                    age=13,
                    interested_program='Top 5'
                )
                
                # Enrollment
                g7 = GradeLevel.objects.get_or_create(code='G7', defaults={'name': 'Grade 7'})[0]
                StudentEnrollment.objects.create(
                    student=student,
                    school_year=sy,
                    grade_level=g7,
                    enrollee_type='new',
                    enrollment_status='pending',
                    student_data_completed=True,
                    family_data_completed=True,
                    survey_completed=True,
                    academic_data_completed=True,
                    program_selected=True
                )
                
                # ProgramSelection (AI trigger)
                ProgramSelection.objects.create(
                    student=student,
                    school_year=sy,
                    requires_program_selection=True,
                    selected_program_code='REGULAR',
                    admin_notes='Test new student AI flow'
                )
                
                self.stdout.write(self.style.SUCCESS('✅ Paul James Mariano (New G7 Top 5) created!\n'))
                self.stdout.write(f'LRN: {student_lrn} | Status: pending | Type: new')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ {str(e)}'))
            raise CommandError(str(e))