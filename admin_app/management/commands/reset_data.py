from django.core.management.base import BaseCommand
from django.db import connection
from enrollment_app.models import (
    Student, StudentData, Parent, Guardian, FamilyData,
    SurveyData, AcademicData, ProgramSelection, EnrollmentStatusLog
)

class Command(BaseCommand):
    help = 'Delete all data from Enrollment App models and reset IDs to 1'

    def handle(self, *args, **kwargs):
        try:
            self.stdout.write('Starting data deletion...')
            
            # Delete all data (order matters due to foreign keys)
            deleted_counts = {}
            deleted_counts['EnrollmentStatusLog'] = EnrollmentStatusLog.objects.all().delete()[0]
            deleted_counts['ProgramSelection'] = ProgramSelection.objects.all().delete()[0]
            deleted_counts['AcademicData'] = AcademicData.objects.all().delete()[0]
            deleted_counts['SurveyData'] = SurveyData.objects.all().delete()[0]
            deleted_counts['FamilyData'] = FamilyData.objects.all().delete()[0]
            deleted_counts['Guardian'] = Guardian.objects.all().delete()[0]
            deleted_counts['Parent'] = Parent.objects.all().delete()[0]
            deleted_counts['StudentData'] = StudentData.objects.all().delete()[0]
            deleted_counts['Student'] = Student.objects.all().delete()[0]

            # Display deletion summary
            self.stdout.write('\nDeleted records:')
            for model, count in deleted_counts.items():
                self.stdout.write(f'  - {model}: {count}')

            # Reset the ID counters for PostgreSQL
            self.stdout.write('\nResetting ID sequences...')
            with connection.cursor() as cursor:
                sequences = [
                    'enrollment_app_student_id_seq',
                    'enrollment_app_studentdata_id_seq',
                    'enrollment_app_parent_id_seq',
                    'enrollment_app_guardian_id_seq',
                    'enrollment_app_familydata_id_seq',
                    'enrollment_app_surveydata_id_seq',
                    'enrollment_app_academicdata_id_seq',
                    'enrollment_app_programselection_id_seq',
                    'enrollment_app_enrollmentstatuslog_id_seq',
                ]
                
                for seq in sequences:
                    try:
                        cursor.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1;")
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'  ⚠️ Could not reset {seq}: {e}'))

            self.stdout.write(self.style.SUCCESS('\n✅ All enrollment data deleted and IDs reset to 1.'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error occurred: {e}'))