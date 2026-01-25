#!/usr/bin/env python
"""
Debug script for specific student LRN - check all AI processing requirements
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from enrollment_app.models import Student, ProgramSelection, StudentDocumentSubmission, AcademicData, StudentData, FamilyData, SurveyData
from admin_app.models import Program, DocumentRequirement
from coordinator_app.models import AIAssistantPreference

TARGET_LRN = '199006180366'

print("=" * 80)
print(f"DETAILED DEBUG FOR STUDENT LRN: {TARGET_LRN}")
print("=" * 80)

# 1. Find the student
try:
    student = Student.objects.get(lrn=TARGET_LRN)
    print(f"\n✓ Student found: {student.lrn}")
except Student.DoesNotExist:
    print(f"\n✗ Student NOT found: {TARGET_LRN}")
    sys.exit(1)

# 2. Check ProgramSelection
print("\n" + "─" * 80)
print("PROGRAM SELECTION CHECK")
print("─" * 80)

try:
    prog_sel = ProgramSelection.objects.get(student=student)
    print(f"✓ Program Selection found")
    print(f"  - Selected Program: {prog_sel.selected_program_code}")
    print(f"  - Admin Approved: {prog_sel.admin_approved}")
    print(f"  - Assigned Section: {prog_sel.assigned_section}")
    print(f"  - Created At: {prog_sel.created_at}")
except ProgramSelection.DoesNotExist:
    print(f"✗ No ProgramSelection record found")
    sys.exit(1)

program_code = prog_sel.selected_program_code

# 3. Check if AI is enabled for this program
print("\n" + "─" * 80)
print("AI ASSISTANT PREFERENCE CHECK")
print("─" * 80)

try:
    program = Program.objects.get(code=program_code)
    print(f"✓ Program found: {program.name}")
    
    ai_prefs = AIAssistantPreference.objects.filter(
        program=program,
        ai_enabled=True
    )
    
    if ai_prefs.exists():
        print(f"✓ AI enabled for {program_code}")
        for pref in ai_prefs:
            print(f"  - Coordinator: {pref.user.username}")
    else:
        print(f"✗ AI NOT enabled for {program_code}")
except Program.DoesNotExist:
    print(f"✗ Program {program_code} not found")

# 4. Check for duplicate enrollments
print("\n" + "─" * 80)
print("DUPLICATE ENROLLMENT CHECK")
print("─" * 80)

duplicate_enrollments = ProgramSelection.objects.filter(
    student=student,
    admin_approved=True
).exclude(pk=prog_sel.pk)

if duplicate_enrollments.exists():
    print(f"✗ Student has other approved enrollments:")
    for enroll in duplicate_enrollments:
        print(f"  - {enroll.selected_program_code} (Section: {enroll.assigned_section})")
else:
    print(f"✓ No duplicate approved enrollments")

# 5. Check enrollment completion flags
print("\n" + "─" * 80)
print("ENROLLMENT COMPLETION CHECK")
print("─" * 80)

print(f"Student Data Completed: {student.student_data_completed}")
print(f"Family Data Completed: {student.family_data_completed}")
print(f"Survey Completed: {student.survey_completed}")
print(f"Academic Data Completed: {student.academic_data_completed}")
print(f"Program Selected: {student.program_selected}")

is_complete = all([
    student.student_data_completed,
    student.family_data_completed,
    student.survey_completed,
    student.academic_data_completed,
    student.program_selected
])

if is_complete:
    print(f"✓ All completion flags are True")
else:
    print(f"✗ Some completion flags are False")

# 6. Check actual data existence and validity
print("\n" + "─" * 80)
print("ACTUAL DATA VALIDATION")
print("─" * 80)

# StudentData
print("\n1. StudentData:")
try:
    student_data = StudentData.objects.get(student=student)
    required = {
        'last_name': student_data.last_name,
        'first_name': student_data.first_name,
        'gender': student_data.gender,
        'date_of_birth': student_data.date_of_birth,
    }
    
    for field, value in required.items():
        status = "✓" if value else "✗"
        print(f"  {status} {field}: {value}")
    
    all_required_valid = all(required.values())
    if all_required_valid:
        print(f"  ✓ All required fields present")
    else:
        print(f"  ✗ Some required fields missing")
except StudentData.DoesNotExist:
    print(f"  ✗ No StudentData record found")

# FamilyData
print("\n2. FamilyData:")
try:
    family_data = FamilyData.objects.get(student=student)
    print(f"  ✓ FamilyData found")
    
    has_official_guardian = False
    if family_data.official_guardian_type == 'father' and family_data.father:
        print(f"    - Official Guardian Type: Father")
        print(f"    - Guardian: {family_data.father.full_name}")
        has_official_guardian = True
    elif family_data.official_guardian_type == 'mother' and family_data.mother:
        print(f"    - Official Guardian Type: Mother")
        print(f"    - Guardian: {family_data.mother.full_name}")
        has_official_guardian = True
    elif family_data.official_guardian_type == 'other' and family_data.other_guardian:
        print(f"    - Official Guardian Type: Other")
        print(f"    - Guardian: {family_data.other_guardian.full_name}")
        has_official_guardian = True
    else:
        print(f"    - Official Guardian Type: {family_data.official_guardian_type}")
        print(f"    ✗ No guardian linked")
    
    if has_official_guardian:
        print(f"    ✓ Guardian present")
    else:
        print(f"    ✗ Guardian missing")
except FamilyData.DoesNotExist:
    print(f"  ✗ No FamilyData record found")

# SurveyData
print("\n3. SurveyData:")
try:
    survey_data = SurveyData.objects.get(student=student)
    print(f"  ✓ SurveyData found")
except SurveyData.DoesNotExist:
    print(f"  ✗ No SurveyData record found")

# AcademicData
print("\n4. AcademicData:")
try:
    academic_data = AcademicData.objects.get(student=student)
    print(f"  ✓ AcademicData found")
except AcademicData.DoesNotExist:
    print(f"  ✗ No AcademicData record found")

# 7. Check for report card - BOTH LOCATIONS
print("\n" + "─" * 80)
print("REPORT CARD CHECK (CRITICAL)")
print("─" * 80)

has_academic_report = False
has_doc_submission = False

# Check AcademicData
print("\n1. AcademicData.report_card:")
try:
    academic_data = AcademicData.objects.get(student=student)
    if academic_data.report_card and academic_data.report_card.name:
        has_academic_report = True
        print(f"  ✓ Found: {academic_data.report_card.name}")
    else:
        print(f"  ✗ No file attached")
except AcademicData.DoesNotExist:
    print(f"  ✗ No AcademicData")

# Check DocumentSubmission
print("\n2. StudentDocumentSubmission (Report Card):")
report_card_requirements = DocumentRequirement.objects.filter(
    name__icontains='report card',
    is_active=True
)

if report_card_requirements.exists():
    print(f"  Found {report_card_requirements.count()} active 'Report Card' requirements:")
    for req in report_card_requirements:
        print(f"    - {req.name} (ID: {req.id})")
    
    submissions = StudentDocumentSubmission.objects.filter(
        student=student,
        requirement__in=report_card_requirements
    )
    
    if submissions.exists():
        print(f"\n  ✓ Found {submissions.count()} submission(s)")
        for sub in submissions:
            print(f"    - Requirement: {sub.requirement.name}")
            print(f"    - Status: {sub.status}")
            if sub.document_file and sub.document_file.name:
                has_doc_submission = True
                print(f"    - File: {sub.document_file.name}")
            else:
                print(f"    - File: ✗ NO FILE ATTACHED")
    else:
        print(f"  ✗ No DocumentSubmission found for Report Card")
else:
    print(f"  ✗ No active 'Report Card' DocumentRequirement found")

print(f"\n  Overall Report Card Status:")
print(f"    - AcademicData: {('✓' if has_academic_report else '✗')}")
print(f"    - DocumentSubmission: {('✓' if has_doc_submission else '✗')}")
print(f"    - Has Report Card (either location): {('✓' if (has_academic_report or has_doc_submission) else '✗')}")

# 8. Final verdict
print("\n" + "=" * 80)
print("FINAL VERDICT - WHY NOT PROCESSED?")
print("=" * 80)

issues = []

if prog_sel.admin_approved:
    issues.append("Already admin_approved - signal won't trigger on update")

if duplicate_enrollments.exists():
    issues.append("Has duplicate approved enrollments")

if not is_complete:
    issues.append("Completion flags not all True")

# Check actual data
try:
    student_data = StudentData.objects.get(student=student)
    if not all([student_data.last_name, student_data.first_name, 
                student_data.gender, student_data.date_of_birth]):
        issues.append("StudentData missing required fields")
except:
    issues.append("StudentData not found")

try:
    family_data = FamilyData.objects.get(student=student)
    
    # Check if has official guardian
    has_official_guardian = False
    if family_data.official_guardian_type == 'father' and family_data.father:
        has_official_guardian = True
    elif family_data.official_guardian_type == 'mother' and family_data.mother:
        has_official_guardian = True
    elif family_data.official_guardian_type == 'other' and family_data.other_guardian:
        has_official_guardian = True
    
    if not has_official_guardian:
        issues.append("FamilyData has no official guardian set")
except:
    issues.append("FamilyData not found")

if not (has_academic_report or has_doc_submission):
    issues.append("Report Card not found in either location")

if issues:
    print("\n✗ BLOCKING ISSUES FOUND:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
else:
    print("\n✓ ALL VALIDATIONS PASSED - Should be processed!")
    if prog_sel.admin_approved:
        print(f"\n  Note: Already approved at {prog_sel.approved_at}")
        print(f"  Assigned to: {prog_sel.assigned_section}")
    else:
        print(f"\n  To process now, run:")
        print(f"  python process_pending_enrollments.py")

print("\n" + "=" * 80)
