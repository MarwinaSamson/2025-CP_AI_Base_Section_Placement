#!/usr/bin/env python
"""Find Steven Semana and check placement"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
django.setup()

from enrollment_app.models import Student, StudentData, ProgramSelection
from coordinator_app.models import Section

# Search for Steven in student data
print("\n🔍 SEARCHING FOR STEVEN...\n")

# Try to find by name
from enrollment_app.models import EnrollmentData
stevens = EnrollmentData.objects.filter(first_name__icontains='steven')
print(f"Found {stevens.count()} students with first name 'Steven':\n")

for enrollment in stevens:
    lrn = enrollment.student.lrn if enrollment.student else "??"
    full_name = f"{enrollment.first_name} {enrollment.middle_name or ''} {enrollment.last_name}".strip()
    print(f"  LRN: {lrn}")
    print(f"  Name: {full_name}")
    
    # Get student data
    student = enrollment.student
    if student:
        prog_sel = ProgramSelection.objects.filter(student=student).first()
        if prog_sel and prog_sel.assigned_section:
            section = prog_sel.assigned_section
            print(f"  Placed in: {section.name} (Grade {section.grade_level.code if section.grade_level else '?'})")
            
            student_data = getattr(student, 'student_data', None)
            if student_data:
                print(f"  Transferee Grade Level Set: {student_data.transferee_grade_level}")
                print(f"  Coordinator Track: {student_data.coordinator_selected_track}")
        else:
            print(f"  Placed in: NOT YET")
    print()

# Also search StudentData
print("\n📋 CHECKING STUDENT DATA:\n")
student_datas = StudentData.objects.filter(full_name__icontains='steven')
print(f"Found {student_datas.count()} StudentData records with 'steven':\n")

for std_data in student_datas:
    lrn = std_data.student.lrn if std_data.student else "??"
    print(f"  LRN: {lrn}")
    print(f"  Name: {std_data.full_name}")
    print(f"  Enrolling As: {std_data.enrolling_as}")
    print(f"  Transferee Grade: {std_data.transferee_grade_level}")
    print(f"  Track: {std_data.coordinator_selected_track}")
    
    student = std_data.student
    if student:
        prog_sel = ProgramSelection.objects.filter(student=student).first()
        if prog_sel and prog_sel.assigned_section:
            section = prog_sel.assigned_section
            print(f"  ➜ Placed in: {section.name} (Grade {section.grade_level.code})")
    print()
