#!/usr/bin/env python
"""
Debug script to check section capacity vs actual enrolled students
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
django.setup()

from admin_app.models import Section
from enrollment_app.models import ProgramSelection

print("\n" + "="*80)
print("SECTION CAPACITY DEBUG REPORT")
print("="*80 + "\n")

sections = Section.objects.all()

for section in sections:
    actual_count = section.get_actual_count()
    stored_count = section.current_students
    is_full = actual_count >= section.max_students
    
    print(f"Section: {section.name}")
    print(f"  Max Capacity: {section.max_students}")
    print(f"  Stored Count: {stored_count}")
    print(f"  Actual Count: {actual_count}")
    print(f"  Space Available: {section.max_students - actual_count}")
    print(f"  Is Full: {'YES ❌' if is_full else 'NO ✓'}")
    
    # Show enrolled students
    enrollments = ProgramSelection.objects.filter(
        assigned_section=str(section.id),
        admin_approved=True
    )
    print(f"  Enrolled Students ({enrollments.count()}):")
    for enrollment in enrollments:
        student_name = "Unknown"
        if hasattr(enrollment.student, 'student_data') and enrollment.student.student_data:
            student_name = enrollment.student.student_data.full_name
        print(f"    - {enrollment.student.lrn} ({student_name})")
    
    print()

print("="*80)
print("TROUBLESHOOTING:")
print("="*80)
print("\n✓ If 'Stored Count' ≠ 'Actual Count': Run section.update_current_students_count()")
print("✓ If 'Actual Count' shows wrong: Check if assigned_section is stored correctly")
print("\n")
