#!/usr/bin/env python3
"""
Management command to create a test transferee enrollment for testing AI mode.

Usage:
  python manage.py create_test_transferee_fixed
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.core.files.base import ContentFile
from decimal import Decimal

from enrollment_app.models import (
    Student, StudentData, AcademicData, FamilyData, 
    ProgramSelection, StudentEnrollment, Parent
)
from admin_app.models import SchoolYear, Program, GradeLevel


class Command(BaseCommand):
    help = 'Create Aidan Ruselle Rubio test transferee (Grade 8, Top 5)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Creating test transferee (Aidan Rubio)...\n'))

        try:
            with transaction.atomic():
                student_lrn = '199006180405'
                
                # Clean up
                self.stdout.write('Cleaning up...')
                Student.objects.filter(lrn=student_lrn).delete()
                self.stdout.write(self.style.SUCCESS('✅ Cleaned\n'))
                
                sy = SchoolYear.objects.filter(is_active=True).first()
                if not sy:
                    raise CommandError('No active SchoolYear')
                
                student = Student.objects.create(lrn=student_lrn, is_active=True)
                
                StudentData.objects.create(
                    student=student,
                    last_name='Rubio',
                    first_name='Aidan Ruselle',
                    middle_name='',
                    gender='male',
                    date_of_birth=timezone.now().date().replace(year=timezone.now().year - 14),
                    address='Test Address',
                    enrolling_as='transferee',
                    transferee_grade_level='8',
                    previous_program='REGULAR',
                    coordinator_selected_track='TOP5',
                    agreed_to_terms=True
                )
                
                g8 = GradeLevel.objects.get_or_create(code='G8', defaults={'name': 'Grade 8'})[0]
                
                StudentEnrollment.objects.create(
                    student=student,
                    school_year=sy,
                    grade_level=g8,
                    enrollee_type='transferee',
                    enrollment_status='pending',
                    student_data_completed=True,
                    family_data_completed=True,
                    documents_completed=False
                )
                
                ProgramSelection.objects.create(
                    student=student,
                    school_year=sy,
                    requires_program_selection=False,
                    selected_program_code='REGULAR',
                    admin_notes='Test transferee Grade 8 Top 5'
                )
                
                self.stdout.write(self.style.SUCCESS('✅ Aidan Ruselle Rubio (Transferee G8 Top 5) created!\n'))
                self.stdout.write(f'LRN: {student_lrn} | Status: pending | Type: transferee')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ {str(e)}'))
            raise CommandError(str(e))