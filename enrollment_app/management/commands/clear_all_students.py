from django.core.management.base import BaseCommand
from enrollment_app.models import Student, ProgramSelection, StudentDocumentSubmission, AcademicData

class Command(BaseCommand):
    help = "Delete all student-related records in enrollment_app (Student, ProgramSelection, AcademicData, StudentDocumentSubmission) and reset primary keys."

    def handle(self, *args, **options):
        confirm = input("Are you sure you want to delete ALL student records and related data? This cannot be undone! (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return

        print("Deleting ProgramSelection records...")
        ProgramSelection.objects.all().delete()
        print("Deleting AcademicData records...")
        AcademicData.objects.all().delete()
        print("Deleting StudentDocumentSubmission records...")
        StudentDocumentSubmission.objects.all().delete()
        print("Deleting Student records...")
        Student.objects.all().delete()

        # Optionally, reset auto-increment counters (PostgreSQL/MySQL only)
        from django.db import connection
        with connection.cursor() as cursor:
            for table in ['enrollment_app_student', 'enrollment_app_programselection', 'enrollment_app_academicdata', 'enrollment_app_studentdocumentsubmission']:
                try:
                    cursor.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1;")
                except Exception:
                    pass  # Ignore if not PostgreSQL

        print("All student records and related data have been deleted. Primary keys reset (if supported by DB backend).")
