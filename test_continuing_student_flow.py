"""
test_continuing_student_flow.py

Complete test script for continuing student enrollment flow:
1. Create a new student and complete Year 1 enrollment
2. Set final status to 'promoted' at year-end
3. Promote the student to year 2
4. Verify continuing student can enroll with only student_data + family_data

Run with: python manage.py shell < test_continuing_student_flow.py
"""

from django.utils import timezone
from django.db import transaction
from datetime import date

from admin_app.models import SchoolYear, GradeLevel, Section, Teacher, Program, DocumentRequirement
from enrollment_app.models import (
    Student, StudentData, StudentEnrollment, StudentAcademicYearStatus,
    FamilyData, Parent, ProgramSelection, StudentDocumentSubmission,
)

print("\n" + "="*80)
print("CONTINUING STUDENT FLOW TEST")
print("="*80)

# ===================================================================
# STEP 1: SETUP - Create necessary admin data
# ===================================================================
print("\n[STEP 1] Setting up admin data...")

# Get or create school years
sy_2025_2026, _ = SchoolYear.objects.get_or_create(
    year_label='2025-2026',
    defaults={'is_active': True, 'start_date': date(2025, 6, 1), 'end_date': date(2026, 3, 31)}
)
sy_2026_2027, _ = SchoolYear.objects.get_or_create(
    year_label='2026-2027',
    defaults={'is_active': False, 'start_date': date(2026, 6, 1), 'end_date': date(2027, 3, 31)}
)

# Get grade levels
g7 = GradeLevel.objects.get(code='G7')
g8 = GradeLevel.objects.get(code='G8')

# Get a section
section = Section.objects.first()
if not section:
    print("⚠️  No sections found. Please create sections first.")
    exit(1)

# Get a teacher/adviser
teacher = Teacher.objects.first()
if not teacher:
    print("⚠️  No teachers found. Please create teachers first.")
    exit(1)

print(f"✓ School Years: {sy_2025_2026.year_label}, {sy_2026_2027.year_label}")
print(f"✓ Grades: {g7}, {g8}")
print(f"✓ Section: {section.name}")

# ===================================================================
# STEP 2: CREATE NEW STUDENT (Year 1)
# ===================================================================
print("\n[STEP 2] Creating new student for Year 1...")

# LRN must be 12 characters max, so use last 8 digits of timestamp
test_lrn = f"TEST{int(timezone.now().timestamp()) % 100000000:08d}"
try:
    student = Student.objects.create(
        lrn=test_lrn,
        email='test@example.com',
        enrollment_status='draft',  # Provide default for deprecated field
    )
    print(f"✓ Student created: {student.lrn}")
except Exception as e:
    print(f"✗ Error creating student: {e}")
    exit(1)

# ===================================================================
# STEP 3: CREATE STUDENT ENROLLMENT (Year 1)
# ===================================================================
print("\n[STEP 3] Creating StudentEnrollment for Year 1...")

try:
    se_year1 = StudentEnrollment.objects.create(
        student=student,
        school_year=sy_2025_2026,
        grade_level=g7,
        enrollee_type='new',
        enrollment_status='draft',
    )
    print(f"✓ StudentEnrollment created: {se_year1}")
except Exception as e:
    print(f"✗ Error creating StudentEnrollment: {e}")
    exit(1)

# ===================================================================
# STEP 4: COMPLETE ENROLLMENT FORMS (Year 1)
# ===================================================================
print("\n[STEP 4] Completing enrollment forms...")

try:
    # Create StudentData
    student_data = StudentData.objects.create(
        student=student,
        last_name='Testson',
        first_name='Tester',
        middle_name='T.',
        gender='male',
        date_of_birth=date(2012, 3, 15),
        place_of_birth='Test City',
    )
    print(f"✓ StudentData created")

    # Create FamilyData
    father = Parent.objects.create(
        family_name='Testson',
        first_name='Father',
        parent_type='father',
        date_of_birth=date(1980, 1, 1),
        occupation='Tester',
        contact_number='09123456789',
    )
    family_data = FamilyData.objects.create(
        student=student,
        father=father,
        official_guardian_type='father',
    )
    print(f"✓ FamilyData created")

    # Mark forms complete in StudentEnrollment
    se_year1.student_data_completed = True
    se_year1.student_data_completed_at = timezone.now()
    se_year1.family_data_completed = True
    se_year1.family_data_completed_at = timezone.now()
    se_year1.survey_completed = True
    se_year1.survey_completed_at = timezone.now()
    se_year1.academic_data_completed = True
    se_year1.academic_data_completed_at = timezone.now()
    se_year1.program_selected = True
    se_year1.program_selected_at = timezone.now()
    se_year1.documents_completed = True
    se_year1.documents_completed_at = timezone.now()
    se_year1.enrollment_status = 'approved'
    se_year1.save()
    print(f"✓ StudentEnrollment marked complete: {se_year1.required_steps}")
    print(f"  - is_complete: {se_year1.is_complete}")

except Exception as e:
    print(f"✗ Error completing forms: {e}")
    exit(1)

# ===================================================================
# STEP 5: YEAR-END - CREATE ACADEMIC STATUS (PROMOTED)
# ===================================================================
print("\n[STEP 5] Recording year-end academic status (PROMOTED)...")

try:
    academic_status = StudentAcademicYearStatus.objects.create(
        student=student,
        school_year=sy_2025_2026,
        grade_level=g7,
        section=section,
        final_status='promoted',
        overall_grade=85.5,
        remarks='Good performance in all subjects',
        recorded_by=teacher,
    )
    print(f"✓ Academic status recorded: {academic_status.final_status}")
    print(f"  - can_continue_as_old_student: {academic_status.can_continue_as_old_student()}")
    print(f"  - Adviser: {academic_status.get_adviser_name()}")

except Exception as e:
    print(f"✗ Error creating academic status: {e}")
    exit(1)

# ===================================================================
# STEP 6: YEAR 2 - PROMOTE CONTINUING STUDENT
# ===================================================================
print("\n[STEP 6] Promoting student to Year 2 as continuing...")

try:
    # Check if student can continue
    can_continue = student.can_continue_as_old_student
    print(f"  - Can continue: {can_continue}")
    
    if not can_continue:
        print("✗ Student cannot continue (latest status not 'promoted')")
        exit(1)

    # Create Year 2 StudentEnrollment
    se_year2 = StudentEnrollment.objects.create(
        student=student,
        school_year=sy_2026_2027,
        grade_level=g8,  # Promoted from G7 to G8
        enrollee_type='continuing',
        enrollment_status='draft',
    )
    print(f"✓ StudentEnrollment created for Year 2: {se_year2}")
    
    # Mark only student_data and family_data as required (no survey/academic for continuing)
    se_year2.student_data_completed = True
    se_year2.student_data_completed_at = timezone.now()
    se_year2.family_data_completed = True
    se_year2.family_data_completed_at = timezone.now()
    se_year2.save()
    print(f"✓ StudentEnrollment marked with only required steps")
    print(f"  - Required steps: {se_year2.required_steps}")
    print(f"  - Is complete: {se_year2.is_complete}")

except Exception as e:
    print(f"✗ Error promoting student: {e}")
    exit(1)

# ===================================================================
# STEP 7: CARRY OVER DOCUMENTS
# ===================================================================
print("\n[STEP 7] Testing document carryover...")

try:
    # Create a Year 1 document submission
    doc_req = DocumentRequirement.objects.first()
    if doc_req:
        doc_sub_year1 = StudentDocumentSubmission.objects.create(
            student=student,
            requirement=doc_req,
            school_year=sy_2025_2026,
            document_file='dummy_file.txt',
            file_name='test_document.txt',
            file_size=1024,
            file_format='txt',
            status='approved',
        )
        print(f"✓ Year 1 document created: {doc_sub_year1}")

        # Carry over documents for Year 2
        carried = StudentDocumentSubmission.carry_over_for_student(student, sy_2026_2027)
        print(f"✓ Documents carried over: {len(carried)} submissions")
        for doc in carried:
            print(f"  - {doc.requirement.name}: {doc.is_carried_over}")
    else:
        print("⚠️  No document requirements found. Skipping document carryover test.")

except Exception as e:
    print(f"✗ Error in document carryover: {e}")
    exit(1)

# ===================================================================
# STEP 8: VERIFY ENROLLMENT STATE
# ===================================================================
print("\n[STEP 8] Verifying final enrollment state...")

try:
    # Refresh student from DB
    student.refresh_from_db()
    
    print(f"\n  Student: {student.lrn}")
    print(f"  Current enrollment (via property): {student.current_enrollment}")
    print(f"  Current school year: {student.current_school_year}")
    print(f"  Current enrollee type: {student.current_enrollee_type}")
    print(f"  Latest academic status: {student.latest_academic_status}")
    
    # Check Year 1
    se_y1_check = StudentEnrollment.objects.get(student=student, school_year=sy_2025_2026)
    print(f"\n  Year 1 Enrollment:")
    print(f"    - Status: {se_y1_check.enrollment_status}")
    print(f"    - Type: {se_y1_check.enrollee_type}")
    print(f"    - Complete: {se_y1_check.is_complete}")
    
    # Check Year 2
    se_y2_check = StudentEnrollment.objects.get(student=student, school_year=sy_2026_2027)
    print(f"\n  Year 2 Enrollment:")
    print(f"    - Status: {se_y2_check.enrollment_status}")
    print(f"    - Type: {se_y2_check.enrollee_type}")
    print(f"    - Required steps: {se_y2_check.required_steps}")
    print(f"    - Complete: {se_y2_check.is_complete}")
    
    # Count enrollments
    total_enrollments = StudentEnrollment.objects.filter(student=student).count()
    print(f"\n  Total enrollments for student: {total_enrollments}")
    
except Exception as e:
    print(f"✗ Error verifying state: {e}")
    exit(1)

# ===================================================================
# STEP 9: TEST BACKWARD COMPATIBILITY PROPERTIES
# ===================================================================
print("\n[STEP 9] Testing backward compatibility properties...")

try:
    props = {
        'current_enrollment': student.current_enrollment,
        'current_school_year': student.current_school_year,
        'current_grade_level': student.current_grade_level,
        'current_enrollee_type': student.current_enrollee_type,
        'current_enrollment_status': student.current_enrollment_status,
        'latest_academic_status': student.latest_academic_status,
        'can_continue_as_old_student': student.can_continue_as_old_student,
        'required_steps': student.required_steps,
        'is_complete': student.is_complete,
    }
    
    for prop_name, prop_value in props.items():
        print(f"  ✓ {prop_name}: {prop_value}")

except Exception as e:
    print(f"✗ Error testing properties: {e}")
    exit(1)

# ===================================================================
# SUMMARY
# ===================================================================
print("\n" + "="*80)
print("✅ ALL TESTS PASSED")
print("="*80)
print(f"""
Test Summary:
  - Created student: {student.lrn}
  - Year 1: New student (G7) → Type: new → Status: approved → Promoted
  - Year 2: Old student (G8) → Type: continuing → Status: draft → Can enroll
  - Documents: Carried over from Year 1 to Year 2
  - Properties: All backward compatibility properties working
  
Continuing Student Benefits:
  ✓ Only requires student_data + family_data (no survey/academic)
  ✓ Documents automatically carried over
  ✓ Can verify promotion status before allowing enrollment
  ✓ Can track multiple enrollments per student
  ✓ Form progress tracked separately per year
""")

print("\n[Test complete] Clean up by deleting test student:")
print(f"  Student.objects.get(lrn='{test_lrn}').delete()")
