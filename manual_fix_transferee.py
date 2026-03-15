#!/usr/bin/env python
"""
Manual fix script to update the existing transferee enrollment 
and create ProgramSelection for testing coordinator visibility.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from enrollment_app.models import Student, StudentEnrollment, ProgramSelection, StudentDocumentSubmission, StudentData
from admin_app.models import SchoolYear, GradeLevel
from django.utils import timezone

LRN = '126108180012'

print("=" * 80)
print("MANUAL FIX: Complete Transferee Enrollment Setup")
print("=" * 80)

# Get objects
student = Student.objects.get(lrn=LRN)
active_sy = SchoolYear.objects.filter(is_active=True).first()
enrollment = StudentEnrollment.objects.get(student=student, school_year=active_sy)
student_data = StudentData.objects.get(student=student)

print(f"\n1. UPDATING StudentData FIELDS...")
print(f"   BEFORE: transferee_grade_level={student_data.transferee_grade_level}, previous_program={student_data.previous_program}")

student_data.transferee_grade_level = '8'
student_data.previous_program = 'REGULAR'
student_data.save()

print(f"   AFTER:  transferee_grade_level={student_data.transferee_grade_level}, previous_program={student_data.previous_program} ✓")

print(f"\n2. UPDATING ENROLLMENT...")
print(f"   BEFORE: enrollee_type={enrollment.enrollee_type}, status={enrollment.enrollment_status}, program_selected={enrollment.program_selected}")

enrollment.enrollee_type = 'transferee'
enrollment.enrollment_status = 'under_review'
enrollment.program_selected = True
enrollment.program_selected_at = timezone.now()
enrollment.grade_level = GradeLevel.objects.get(code='G8')
enrollment.save()

print(f"   AFTER:  enrollee_type={enrollment.enrollee_type}, status={enrollment.enrollment_status}, program_selected={enrollment.program_selected} ✓")

print(f"\n3. CREATING PROGRAM SELECTION...")
ps, created = ProgramSelection.objects.get_or_create(
    student=student,
    school_year=active_sy,
    defaults={
        'requires_program_selection': False,
        'selected_program_code': 'REGULAR',
        'selection_reason': f'Transferee - Manual fix for testing. Program: REGULAR'
    }
)

if created:
    print(f"   ✓ CREATED NEW ProgramSelection: {ps.selected_program_code}")
else:
    print(f"   UPDATING existing ProgramSelection...")
    ps.requires_program_selection = False
    ps.selected_program_code = 'REGULAR'
    ps.selection_reason = f'Transferee - Manual fix for testing. Program: REGULAR'
    ps.save()
    print(f"   ✓ UPDATED ProgramSelection: {ps.selected_program_code}")

print(f"\n4. FIXING DOCUMENTS...")
docs = StudentDocumentSubmission.objects.filter(student=student, school_year__isnull=True)
print(f"   Found {docs.count()} documents without school_year")

for doc in docs:
    doc.school_year = active_sy
    doc.save()
    print(f"   ✓ {doc.requirement.name}: school_year set to {active_sy.year_label}")

print("\n" + "=" * 80)
print("VERIFICATION:")
print("=" * 80)

enrollment.refresh_from_db()
ps.refresh_from_db()
student_data.refresh_from_db()

print(f"\n✓ StudentData:")
print(f"  transferee_grade_level: {student_data.transferee_grade_level}")
print(f"  previous_program: {student_data.previous_program}")

print(f"\n✓ StudentEnrollment:")
print(f"  enrollee_type: {enrollment.enrollee_type}")
print(f"  enrollment_status: {enrollment.enrollment_status}")
print(f"  program_selected: {enrollment.program_selected}")

print(f"\n✓ ProgramSelection:")
print(f"  selected_program_code: {ps.selected_program_code}")
print(f"  requires_program_selection: {ps.requires_program_selection}")

docs_with_sy = StudentDocumentSubmission.objects.filter(student=student, school_year=active_sy).count()
print(f"\n✓ Documents with school_year: {docs_with_sy}")

print("\n" + "=" * 80)
print("✓ MANUAL FIX COMPLETE")
print("=" * 80)
print("""
Now test:
1. Reload the coordinator enrollment management page
2. Check if LRN: 126108180012 appears in the list
3. Verify it shows as Transferee with STE program
4. If YES: The coordinator dashboard works correctly
   The real issue was just manually fixing this test record
5. If NO: The coordinator query/template needs to be fixed
""")
