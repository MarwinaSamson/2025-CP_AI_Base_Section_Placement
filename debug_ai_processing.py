#!/usr/bin/env python
"""
Debug script to check AI processing issues
Checks:
1. ProgramSelection records exist
2. AIAssistantPreference is enabled
3. Report cards are attached
4. Signal execution issues
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from enrollment_app.models import Student, ProgramSelection, AcademicData
from coordinator_app.models import AIAssistantPreference
from admin_app.models import Program
from django.contrib.auth.models import User

print("=" * 80)
print("AI PROCESSING DEBUG SCRIPT")
print("=" * 80)

# 1. Check for pending ProgramSelections
print("\n1. CHECKING PROGRAM SELECTIONS...")
pending_selections = ProgramSelection.objects.filter(admin_approved=False)
print(f"   Found {pending_selections.count()} unapproved program selections")

for sel in pending_selections[:5]:  # Show first 5
    student = sel.student
    print(f"\n   Student LRN: {student.lrn}")
    print(f"   Program: {sel.selected_program_code}")
    print(f"   Admin Approved: {sel.admin_approved}")
    print(f"   Status: {student.enrollment_status}")
    
    # Check if student data is complete
    print(f"   Student Data Complete: {student.student_data_completed}")
    print(f"   Family Data Complete: {student.family_data_completed}")
    print(f"   Survey Complete: {student.survey_completed}")
    print(f"   Academic Data Complete: {student.academic_data_completed}")
    print(f"   Program Selected: {student.program_selected}")
    
    # Check if report card exists
    try:
        academic = AcademicData.objects.get(student=student)
        if academic.report_card:
            print(f"   Report Card: ✓ {academic.report_card.name}")
        else:
            print(f"   Report Card: ✗ NO FILE")
    except AcademicData.DoesNotExist:
        print(f"   Report Card: ✗ NO ACADEMIC DATA")

# 2. Check AIAssistantPreference settings
print("\n\n2. CHECKING AI ASSISTANT PREFERENCES...")
ai_prefs = AIAssistantPreference.objects.all()
print(f"   Found {ai_prefs.count()} AI preference records")

for pref in ai_prefs:
    print(f"\n   User: {pref.user.username}")
    print(f"   Program: {pref.program.code}")
    print(f"   AI Enabled: {pref.ai_enabled}")

# 3. Check for SPTVE program
print("\n\n3. CHECKING SPTVE PROGRAM...")
try:
    sptve_program = Program.objects.get(code='SPTVE')
    print(f"   SPTVE Program Found: {sptve_program.name}")
    
    # Check if any coordinator has it enabled
    sptve_prefs = AIAssistantPreference.objects.filter(program=sptve_program, ai_enabled=True)
    print(f"   Coordinators with AI enabled for SPTVE: {sptve_prefs.count()}")
    
    for pref in sptve_prefs:
        print(f"     - {pref.user.username}")
except Program.DoesNotExist:
    print("   SPTVE Program NOT found in database!")

# 4. Check pending SPTVE enrollments specifically
print("\n\n4. CHECKING SPTVE ENROLLMENTS...")
sptve_selections = ProgramSelection.objects.filter(
    selected_program_code='SPTVE',
    admin_approved=False
)
print(f"   Found {sptve_selections.count()} pending SPTVE enrollments")

from enrollment_app.models import StudentDocumentSubmission
from admin_app.models import DocumentRequirement

for sel in sptve_selections[:5]:
    print(f"\n   LRN: {sel.student.lrn}")
    print(f"   Is Complete: {sel.student.is_complete}")
    
    # Check both sources of report cards
    has_report_card_academic = False
    try:
        academic = AcademicData.objects.get(student=sel.student)
        has_report_card_academic = bool(academic.report_card)
    except:
        pass
    
    # Check document submissions
    has_report_card_submission = False
    report_card_requirements = DocumentRequirement.objects.filter(
        name__icontains='report card',
        is_active=True
    )
    
    if report_card_requirements.exists():
        submission = StudentDocumentSubmission.objects.filter(
            student=sel.student,
            requirement__in=report_card_requirements,
            document_file__isnull=False
        ).exclude(document_file='').first()
        has_report_card_submission = bool(submission)
    
    print(f"   Has Report Card (AcademicData): {has_report_card_academic}")
    print(f"   Has Report Card (DocumentSubmission): {has_report_card_submission}")
    print(f"   Should Process: {has_report_card_academic or has_report_card_submission}")

# 5. Summary
print("\n\n5. SUMMARY & RECOMMENDATIONS...")
print("-" * 80)

sptve_prog = Program.objects.filter(code='SPTVE').first()
if not sptve_prog:
    print("❌ ISSUE: SPTVE program not found in database")
else:
    sptve_ai_prefs = AIAssistantPreference.objects.filter(program=sptve_prog, ai_enabled=True)
    if sptve_ai_prefs.count() == 0:
        print("❌ ISSUE: No coordinator has AI enabled for SPTVE program")
        print("   Action: Go to Section Assignment dashboard and toggle AI ON")
    else:
        print(f"✓ AI is enabled for SPTVE ({sptve_ai_prefs.count()} coordinators)")
        
        # Check if students have complete data
        pending = ProgramSelection.objects.filter(
            selected_program_code='SPTVE',
            admin_approved=False
        )
        
        if pending.exists():
            incomplete = []
            ready_to_process = []
            
            for sel in pending:
                if not sel.student.is_complete:
                    incomplete.append(sel.student.lrn)
                else:
                    # Check for report card in BOTH locations
                    has_academic_report = False
                    try:
                        academic = AcademicData.objects.get(student=sel.student)
                        has_academic_report = bool(academic.report_card)
                    except:
                        pass
                    
                    # Check document submissions
                    report_card_reqs = DocumentRequirement.objects.filter(
                        name__icontains='report card',
                        is_active=True
                    )
                    has_doc_submission = False
                    if report_card_reqs.exists():
                        doc_sub = StudentDocumentSubmission.objects.filter(
                            student=sel.student,
                            requirement__in=report_card_reqs,
                            document_file__isnull=False
                        ).exclude(document_file='').first()
                        has_doc_submission = bool(doc_sub)
                    
                    if has_academic_report or has_doc_submission:
                        ready_to_process.append(sel.student.lrn)
                    else:
                        incomplete.append(f"{sel.student.lrn} (no report card)")
            
            if incomplete:
                print(f"⚠️  ISSUE: {len(incomplete)} students missing report card:")
                for item in incomplete[:5]:
                    print(f"     - {item}")
            
            if ready_to_process:
                print(f"✓ {len(ready_to_process)} students are READY FOR AI PROCESSING:")
                for item in ready_to_process:
                    print(f"     - {item}")
                print("\n   NOTE: After code fix, these students should be auto-approved and assigned.")
        else:
            print("✓ No pending SPTVE enrollments")

print("\n" + "=" * 80)
