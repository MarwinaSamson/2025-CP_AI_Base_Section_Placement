#!/usr/bin/env python
"""
Script to manually trigger AI processing for pending enrollments.
Use this when students have all required data but signals weren't triggered.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

from enrollment_app.models import ProgramSelection, Student, StudentDocumentSubmission, AcademicData
from admin_app.models import Section, SchoolYear, Program, DocumentRequirement
from coordinator_app.models import AIAssistantPreference
from django.utils import timezone
from django.db import transaction

print("=" * 80)
print("MANUAL AI PROCESSING TRIGGER")
print("=" * 80)

# Helper functions (copied from signals.py)
def _has_duplicate_enrollment(student, current_selection):
    """Check if student is already enrolled in another program/section"""
    existing = ProgramSelection.objects.filter(
        student=student,
        admin_approved=True
    ).exclude(pk=current_selection.pk).exists()
    return existing

def _is_enrollment_complete(student):
    """Validate all required enrollment forms are complete"""
    if not all([
        student.student_data_completed,
        student.family_data_completed,
        student.survey_completed,
        student.academic_data_completed,
        student.program_selected
    ]):
        return False
    
    if not hasattr(student, 'student_data'):
        return False
    
    student_data = student.student_data
    required_fields = [
        student_data.last_name,
        student_data.first_name,
        student_data.gender,
        student_data.date_of_birth,
    ]
    
    if not all(required_fields):
        return False
    
    if not hasattr(student, 'family_data'):
        return False
    
    family_data = student.family_data
    
    # Check that official guardian is present (required)
    has_official_guardian = False
    if family_data.official_guardian_type == 'father' and family_data.father:
        has_official_guardian = True
    elif family_data.official_guardian_type == 'mother' and family_data.mother:
        has_official_guardian = True
    elif family_data.official_guardian_type == 'other' and family_data.other_guardian:
        has_official_guardian = True
    
    if not has_official_guardian:
        return False
    
    if not hasattr(student, 'academic_data'):
        return False
    
    return True

def _has_report_card(student):
    """Check if report card exists in either location"""
    try:
        # Method 1: Check AcademicData model (legacy)
        if hasattr(student, 'academic_data'):
            academic_data = student.academic_data
            if academic_data.report_card and academic_data.report_card.name:
                return True
        
        # Method 2: Check StudentDocumentSubmission for Report Card document
        report_card_requirements = DocumentRequirement.objects.filter(
            name__icontains='report card',
            is_active=True
        )
        
        if report_card_requirements.exists():
            submission = StudentDocumentSubmission.objects.filter(
                student=student,
                requirement__in=report_card_requirements,
                document_file__isnull=False
            ).exclude(document_file='').first()
            
            if submission and submission.document_file:
                return True
        
        return False
    except Exception as e:
        print(f"  Error checking report card: {e}")
        return False

def _get_next_available_section(program_code, school_year, target_track=None):
    """Get next available section using sequential fill strategy"""
    if not school_year:
        school_year = (
            SchoolYear.objects.filter(is_active=True).order_by('-start_date').first()
            or SchoolYear.objects.order_by('-start_date').first()
        )
    
    if not school_year:
        return None
    
    filters = {
        'program__code': program_code,
        'school_year': school_year
    }
    
    if program_code == 'REGULAR' and target_track:
        filters['regular_track'] = target_track
    
    sections = Section.objects.filter(**filters).order_by('created_at')
    
    for section in sections:
        actual_count = section.get_actual_count()
        if actual_count < section.max_students:
            return section
    
    # Try alternative track for REGULAR program
    if program_code == 'REGULAR' and target_track:
        alternative_track = 'TOP5' if target_track == 'HETERO' else 'HETERO'
        filters['regular_track'] = alternative_track
        sections = Section.objects.filter(**filters).order_by('created_at')
        
        for section in sections:
            actual_count = section.get_actual_count()
            if actual_count < section.max_students:
                return section
    
    return None

# Find pending enrollments
pending_selections = ProgramSelection.objects.filter(admin_approved=False)
print(f"\nFound {pending_selections.count()} unapproved program selections")

processed_count = 0
skipped_count = 0

for sel in pending_selections:
    student = sel.student
    program_code = sel.selected_program_code
    
    print(f"\n{'─' * 80}")
    print(f"Student: {student.lrn} | Program: {program_code}")
    
    # Check if AI is enabled for this program
    try:
        program = Program.objects.get(code=program_code)
        ai_pref = AIAssistantPreference.objects.filter(
            program=program,
            ai_enabled=True
        ).first()
        
        if not ai_pref:
            print(f"  ⊘ AI not enabled for {program_code}")
            skipped_count += 1
            continue
    except Exception as e:
        print(f"  ⊘ Error checking AI preference: {e}")
        skipped_count += 1
        continue
    
    # Validation checks
    if _has_duplicate_enrollment(student, sel):
        print(f"  ⊘ Student already has approved enrollment elsewhere")
        skipped_count += 1
        continue
    
    if not _is_enrollment_complete(student):
        print(f"  ⊘ Enrollment data incomplete")
        skipped_count += 1
        continue
    
    if not _has_report_card(student):
        print(f"  ⊘ No report card found")
        skipped_count += 1
        continue
    
    # All validations passed - process
    print(f"  ✓ All validations passed - PROCESSING...")
    
    try:
        with transaction.atomic():
            # Auto-approve
            sel.admin_approved = True
            sel.approved_by = 'Manual AI Processor'
            sel.approved_at = timezone.now()
            sel.admin_notes = 'Auto-approved by manual processor - all validation criteria met'
            
            # Auto-assign to section
            section = _get_next_available_section(program_code, sel.school_year, None)
            if section:
                sel.assigned_section = str(section.id)
                sel.section_assigned_at = timezone.now()
                section.update_current_students_count()
                print(f"  ✓ Assigned to section: {section.name}")
            else:
                print(f"  ⚠ No available sections found")
            
            sel.save()
            
            # Update Student enrollment status
            student.enrollment_status = 'approved'
            student.save()
            
            print(f"  ✓ PROCESSED SUCCESSFULLY")
            processed_count += 1
    
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        skipped_count += 1

print(f"\n{'═' * 80}")
print(f"SUMMARY:")
print(f"  Processed: {processed_count}")
print(f"  Skipped: {skipped_count}")
print(f"  Total: {pending_selections.count()}")
print("=" * 80)
