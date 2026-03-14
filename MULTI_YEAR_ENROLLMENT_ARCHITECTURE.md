# Multi-Year Enrollment Architecture — Complete Design Document

**Status**: ✅ **Database Schema Complete** | Ready for Migration & View Updates

**Last Updated**: Current Session | **Session Phase**: Database Design Complete

---

## 1. Overview: The Problem & Solution

### The Problem

- **Original Design Flaw**: `Student` model had `school_year` as a ForeignKey, preventing a single LRN from existing in multiple school years
- **Impact**: Old students (continuing, returning) couldn't be re-enrolled—would need to create duplicate LRN records
- **Missing Outcome Tracking**: No way to record final academic status (promoted/retained) to gate re-enrollment

### The Solution

Create a **three-tier per-year enrollment architecture**:

```
┌────────────────────────────────────────────────────┐
│  STUDENT (Stable)                                  │
│  - LRN (Primary Key)                               │ One per student
│  - email, is_active, is_lis_verified               │ for entire
│  - [DEPRECATED] old per-year fields (nullable)     │ school life
└────────────────────────────────────────────────────┘
                        ↓
        (One-to-Many: One Student → Many Enrollments)
                        ↓
┌────────────────────────────────────────────────────┐
│  STUDENT ENROLLMENT (Per-Year Enrollment State)    │
│  - student (FK)                                    │ One per
│  - school_year (FK)      [unique_together]         │ student
│  - grade_level (FK)                                │ per year
│  - enrollee_type (new/continuing/transferee/...)   │
│  - enrollment_status (draft/submitted/approved/...) │
│  - All form_completed flags & timestamps           │
│  - is_locked (prevents duplicate submissions)      │ Stores enrollment
│  - required_steps property (depends on enrollee_type) │ state & progress
└────────────────────────────────────────────────────┘
                        ↓
        (One-to-Many: One Student → Many Academic Statuses)
                        ↓
┌────────────────────────────────────────────────────┐
│  STUDENT ACADEMIC YEAR STATUS (Per-Year Outcome)  │
│  - student (FK)                                    │ One per
│  - school_year (FK)      [unique_together]         │ student
│  - grade_level (FK)                                │ per year
│  - section (FK)                                    │
│  - final_status (promoted/retained/graduated/...)  │ GATES
│  - overall_grade (computed from AcademicPerformance)│ OLD STUDENT
│  - recorded_by (FK→Teacher, auto from section.adviser)│ RE-ENROLLMENT
│  - remarks (optional notes)                        │
│  - recorded_at (auto_now_add)                      │
└────────────────────────────────────────────────────┘
```

---

## 2. Data Flow: From Enrollment to Re-enrollment

### School Year Setup (Start of Year)

```
Admin creates SchoolYear (e.g., "SY 2024-2025")
    ↓
Students arrive (New/Continuing/Transferee/Returnee)
    ↓
For each student, create StudentEnrollment:
    - Linked to Student (LRN-based)
    - Linked to SchoolYear
    - enrollee_type determines required steps
    - All form_completed = False initially
```

### Enrollment Process (Throughout Year)

```
Student fills forms in sequence:
    Student Data → Family Data → (Surveys/Academic Data/Programs) → Documents

Each completion updates StudentEnrollment:
    - Sets field_completed = True
    - Sets field_completed_at = now()
    - enrollment_status may auto-progress based on all_complete()

required_steps property on StudentEnrollment:
    - NEW students: [student_data, family_data, survey, academic, docs, program]
    - CONTINUING: [student_data, family_data]  ← simpler!
    - TRANSFEREE: [student_data, family_data, docs]
    - RETURNEE: [student_data, family_data]
```

### Grade Recording (Throughout Year)

```
Teachers enter grades:
    AcademicPerformance table (coordinator_app)
    - Records Q1, Q2, Q3, Q4, Final grades
    - Links to student, school_year, subject

Multiple AcademicPerformance records per student (one per subject)
```

### Year-End Academic Finalization

```
At end of school year, admin runs end-of-year process:

    For each Student in SchoolYear:
        1. Aggregate grades from AcademicPerformance
        2. Compute overall_grade (average)
        3. Determine final_status:
            - overall_grade >= passing_threshold → 'promoted'
            - overall_grade < passing_threshold → 'retained'
            - special cases: 'graduated', 'transferred', 'dropped_out'
        4. Create StudentAcademicYearStatus with:
            - final_status
            - overall_grade
            - section (from current_enrollment)
            - recorded_by (auto from section.adviser)
        5. Store for re-enrollment gating
```

### Re-enrollment (Next School Year - Continuing Students)

```
Next school year opens, old students apply as CONTINUING:

1. System checks: can_student_continue(student_lrn):
   - Look up latest StudentAcademicYearStatus
   - If final_status == 'promoted' → ✅ ALLOW
   - If final_status != 'promoted' → ❌ BLOCK

2. If allowed:
   - Create new StudentEnrollment for next year
   - Pre-fill from prior StudentEnrollment:
     - section preference (from get_prior_section_preference)
     - document requirements
   - Mark as 'continuing' enrollee_type
   - Carry documents from prior year to new year

3. If blocked:
   - Show error message
   - Don't create enrollment
   - Student cannot proceed
```

---

## 3. Detailed Model Designs

### 3.1 Student Model (REFACTORED)

**Location**: `enrollment_app/models.py` (lines 12-262)

**Purpose**: Stable student identity tied to LRN, reused across all school years

**Key Fields**:

```python
lrn = CharField(max_length=12, primary_key=True)  # Unique identifier
email = EmailField(null=True, blank=True)
is_active = BooleanField(default=True)  # New: can re-enroll?

# DEPRECATED (nullable, for backward compat):
school_year = FK(SchoolYear)     → null, use StudentEnrollment.school_year
grade_level = FK(GradeLevel)     → null, use StudentEnrollment.grade_level
enrollee_type = CharField()      → null, use StudentEnrollment.enrollee_type
enrollment_status = CharField()  → null, use StudentEnrollment.enrollment_status
is_locked = BooleanField()       → null, use StudentEnrollment.is_locked
[all form_completed flags]       → null, use StudentEnrollment.[field]
```

**Key Backward Compatibility Properties**:

```python
@property
def current_enrollment() → StudentEnrollment
    # Latest StudentEnrollment by school_year

@property
def current_school_year() → SchoolYear
    # Read from current_enrollment

@property
def current_grade_level() → GradeLevel
    # Read from current_enrollment

@property
def current_enrollment_status() → str
    # Read from current_enrollment

@property
def latest_academic_status() → StudentAcademicYearStatus
    # Latest by school_year (for re-enrollment gate)

@property
def can_continue_as_old_student() → bool
    # Check if latest_academic_status.final_status == 'promoted'

@property
def required_steps() → [bool, bool, ...]
    # Delegate to current_enrollment.required_steps

@property
def is_complete() → bool
    # Delegate to current_enrollment.is_complete
```

**Migration Strategy**:

- Keep old fields but nullable
- Mark with `help_text="[DEPRECATED] use StudentEnrollment..."`
- Views gradually updated to use StudentEnrollment
- No data migration needed (old fields zero-filled for existing records)
- Eventually can archive deprecated fields after 2-3 releases

---

### 3.2 StudentEnrollment Model (NEW)

**Location**: `enrollment_app/models.py` (lines 1003-1143)

**Purpose**: Track per-year enrollment state and form completion progress

**Key Fields**:

```python
student = FK(Student)                          # Links to stable identity
school_year = FK(SchoolYear)                   # Which academic year
grade_level = FK(GradeLevel, null, blank)     # Enrolled grade level

enrollee_type = CharField(choices=[
    'new': 'New (Incoming Grade 7)',
    'continuing': 'Continuing (Old Student)',
    'transferee': 'Transferee',
    'returnee': 'Returnee'
])  # default='new'

enrollment_status = CharField(choices=[
    'draft': 'Draft',
    'submitted': 'Submitted',
    'under_review': 'Under Review',
    'approved': 'Approved',
    'rejected': 'Rejected'
])  # default='draft'

# Form completion tracking (all per-enrollment per-year)
student_data_completed = BooleanField(default=False)
student_data_completed_at = DateTimeField(null, blank)

family_data_completed = BooleanField(default=False)
family_data_completed_at = DateTimeField(null, blank)

survey_completed = BooleanField(default=False)
survey_completed_at = DateTimeField(null, blank)

academic_data_completed = BooleanField(default=False)
academic_data_completed_at = DateTimeField(null, blank)

program_selected = BooleanField(default=False)
program_selected_at = DateTimeField(null, blank)

documents_completed = BooleanField(default=False)
documents_completed_at = DateTimeField(null, blank)

is_locked = BooleanField(default=False)  # Prevents duplicate submissions

created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)

class Meta:
    unique_together = [('student', 'school_year')]  # One enrollment per student per year
    indexes = [
        Index(fields=['student', 'school_year']),
        Index(fields=['school_year', 'enrollment_status']),
        Index(fields=['grade_level']),
        Index(fields=['enrollee_type']),
        Index(fields=['enrollment_status']),
    ]
```

**Key Methods**:

```python
@property
def required_steps(self):
    """Returns [bool, bool, ...] based on enrollee_type"""
    base = [student_data_completed, family_data_completed]

    if enrollee_type == 'new':
        return base + [survey, academic, docs, program]  # 6 steps
    elif enrollee_type == 'continuing':
        return base  # 2 steps only
    elif enrollee_type == 'transferee':
        return base + [docs]  # 3 steps
    elif enrollee_type == 'returnee':
        return base  # 2 steps

    return base

@property
def is_complete(self):
    """True if all required steps completed"""
    return all(required_steps)
```

---

### 3.3 StudentAcademicYearStatus Model (NEW)

**Location**: `enrollment_app/models.py` (lines 1145-1320)

**Purpose**: Record per-year academic outcome; gate for old student re-enrollment

**Key Fields**:

```python
student = FK(Student)                          # Links to stable identity
school_year = FK(SchoolYear)                   # Which academic year
grade_level = FK(GradeLevel, null, blank)     # Enrolled grade

section = FK(Section, null, blank)             # Assigned section

final_status = CharField(choices=[
    'promoted': 'Promoted to Next Grade',
    'retained': 'Retained in Same Grade',
    'transferred': 'Transferred Out',
    'graduated': 'Graduated',
    'dropped_out': 'Dropped Out',
    'pending': 'Pending Final Assessment'
])
# ⭐ THIS FIELD GATES OLD STUDENT RE-ENROLLMENT

overall_grade = DecimalField(
    max_digits=5, decimal_places=2,  # 0-100
    validators=[MinValueValidator(0), MaxValueValidator(100)],
    null=True, blank=True
)
# Computed average of all quarters

remarks = TextField(blank=True, null=True)
# "Excellent Math performance", "Needs reading support", etc.

recorded_by = FK(Teacher, null, blank)
# ⭐ AUTO-SET from section.adviser via save() method

recorded_at = DateTimeField(auto_now_add=True)
# When status was finalized

created_at = DateTimeField(auto_now_add=True)
updated_at = DateTimeField(auto_now=True)

class Meta:
    unique_together = [('student', 'school_year')]  # One status per year
    indexes = [
        Index(fields=['student', 'school_year']),
        Index(fields=['school_year', 'final_status']),
        Index(fields=['final_status']),  # For querying promotions
        Index(fields=['recorded_by']),   # For adviser's students
    ]
```

**Key Methods**:

```python
def can_continue_as_old_student(self):
    """Returns True only if promoted to next grade"""
    return self.final_status == 'promoted'

def get_adviser_name(self):
    """Get full name of recording teacher"""
    return self.recorded_by.full_name if self.recorded_by else "N/A"

def save(self, *args, **kwargs):
    """AUTO-SET recorded_by from section adviser"""
    if not self.recorded_by and self.section and self.section.adviser:
        self.recorded_by = self.section.adviser
    super().save(*args, **kwargs)
    # ⭐ CRITICAL: Prevents manual entry errors
```

---

## 4. Service Layer: Business Logic

**Location**: `enrollment_app/services/old_student_service.py`

**Purpose**: Encapsulate all old student re-enrollment logic

### Key Functions

#### 1. `can_student_continue(student_lrn: str) → bool`

```python
Checks if a student can re-enroll as continuing.

Logic:
    1. Get latest StudentAcademicYearStatus for student
    2. If status.final_status == 'promoted' → return True
    3. Otherwise → return False

Used by: Enrollment validation gate (prevent non-promoted re-enrollment)
```

#### 2. `create_continuation_enrollment(student_lrn: str, new_school_year: SchoolYear) → StudentEnrollment`

```python
Create new StudentEnrollment for next school year if student promoted.

Logic:
    1. Validate can_student_continue(student_lrn)
    2. Get prior StudentEnrollment (base template)
    3. Create new StudentEnrollment:
        - student = same
        - school_year = new_school_year
        - grade_level = next grade (computed)
        - enrollee_type = 'continuing'
        - All form_completed = False (except inherited docs if allowed)
    4. Copy document requirements from prior year
    5. Return new enrollment

Used by: Old student enrollment form submission
```

#### 3. `promote_students_to_next_year(from_year: SchoolYear, to_year: SchoolYear) → int`

```python
Batch operation: Create StudentEnrollment for all promoted students.

Logic:
    1. Query StudentAcademicYearStatus.objects.filter(
        school_year=from_year,
        final_status='promoted'
      )
    2. For each promoted student, call create_continuation_enrollment()
    3. Return count created

Used by: Admin batch operation at year boundary
```

#### 4. `finalize_academic_year(school_year: SchoolYear) → int`

```python
End-of-year process: Compute overall grades and create StudentAcademicYearStatus.

Logic:
    1. Query all students enrolled in this school_year
    2. For each student:
        a. Aggregate AcademicPerformance records:
           - Get Q1, Q2, Q3, Q4, Final grades
           - Compute overall_grade = (Q1+Q2+Q3+Q4+Final) / 5
        b. Determine final_status based on overall_grade
        c. Get section from StudentEnrollment
        d. Create StudentAcademicYearStatus:
              - final_status
              - overall_grade
              - section
              - (recorded_by auto-set from section.adviser)
    3. Return count created

Used by: Admin year-end operation
```

#### 5. `get_student_enrollment_history(student_lrn: str) → [StudentEnrollment]`

```python
Retrieve all enrollments for a student across years.

Returns: OrderedDict[school_year] → StudentEnrollment
Used by: Enrollment history view, re-assessment purposes
```

#### 6. `get_prior_section_preference(student_lrn: str) → Section`

```python
Get the section the student was in last year (if any).
Used for intelligent section re-assignment.

Logic:
    1. Get latest StudentEnrollment for prior year
    2. Get section from that enrollment
    3. Return adviser's preferred re-assignment section

Used by: Section adviser's continuation planning
```

---

## 5. Data Migration Strategy

### Phase 1: Apply Migration (Current Phase ✅)

```bash
python manage.py migrate enrollment_app
```

- Creates StudentEnrollment table
- Creates StudentAcademicYearStatus table
- Indexes and constraints applied

### Phase 2: Existing Data Migration (If Needed)

```python
# If existing students have school_year set, migrate to StudentEnrollment
from enrollment_app.models import Student, StudentEnrollment

for student in Student.objects.filter(school_year__isnull=False):
    StudentEnrollment.objects.get_or_create(
        student=student,
        school_year=student.school_year,
        defaults={
            'grade_level': student.grade_level,
            'enrollee_type': student.enrollee_type,
            'enrollment_status': student.enrollment_status,
            'student_data_completed': student.student_data_completed,
            'family_data_completed': student.family_data_completed,
            # ... copy other fields
        }
    )
```

### Phase 3: View Updates (Gradual)

- Update enrollment views to use `StudentEnrollment` instead of `Student` for per-year data
- Use backward compatibility properties for non-breaking compatibility
- Gradual rollout over 2-3 releases

### Phase 4: Deprecation (Future)

- Mark old Student fields as deprecated (admin notice)
- Eventually remove old fields after 1-2 years

---

## 6. Migration File

**Location**: `enrollment_app/migrations/0020_studentenrollment_studentacademicyearstatus.py`

**What it does**:

1. Creates `StudentEnrollment` table with all fields, constraints, indexes
2. Creates `StudentAcademicYearStatus` table
3. Adds `UniqueConstraint(student, school_year)` to prevent duplicates
4. Adds performance indexes

**Status**: ✅ Ready for `python manage.py migrate`

---

## 7. Implementation Checklist

### ✅ Completed

- [x] Identified database design flaw
- [x] Designed three-tier architecture
- [x] Created Student model (refactored)
- [x] Created StudentEnrollment model
- [x] Created StudentAcademicYearStatus model
- [x] Added backward compatibility properties
- [x] Implemented auto-adviser assignment (save() override)
- [x] Created migration file 0020\_...
- [x] Created old_student_service.py with all business logic

### ⏳ Next Steps

**Immediate (High Priority)**:

1. [ ] Apply migration: `python manage.py migrate enrollment_app`
2. [ ] Test migration: Verify tables created in database
3. [ ] Update `enrollment_app/views/studentdata_view.py`:
   - Read enrollee_type from StudentEnrollment, not Student
   - Read form_completed flags from StudentEnrollment
4. [ ] Implement old student validation gate:
   - Before allowing 'continuing' enrollment, call `can_student_continue()`
   - Show block message if not promoted
5. [ ] Test critical flows:
   - New student enrollment (should work as before)
   - Continuing student successful re-enrollment (promoted)
   - Continuing student blocked re-enrollment (not promoted)

**Medium Priority**: 6. [ ] Update all enrollment views:

- `familydata_view.py`
- `academicdata_view.py`
- `survey_view.py`
- `program_selection_view.py`
- `documents_view.py`

7. [ ] Create year-end admin action:
   - `admin_app/actions/finalize_academic_year.py`
   - Button in admin interface
8. [ ] Create batch re-enrollment action:
   - `admin_app/actions/promote_to_next_year.py`
   - At year boundary

**Lower Priority**: 9. [ ] Create existing data migration (if production data exists) 10. [ ] Add enrollment history view 11. [ ] Add old student re-enrollment flow UI 12. [ ] Deprecate old Student fields in admin

---

## 8. Key Design Decisions Explained

### Decision 1: Why Three Tables Instead of One?

**Alternative Rejected**: Single table with annual history

**Reason Chosen**:

- Separates concerns: identity ≠ enrollment ≠ outcome
- Prevents duplicate LRNs while allowing multi-year tracking
- Clear data flow: grades → outcome → re-enrollment gate
- Allows data retention after graduation (student history)

### Decision 2: Why Make Old Fields Nullable?

**Alternative Rejected**: Immediate hard removal

**Reason Chosen**:

- Backward compatibility: existing code won't break
- Gradual migration: views updated iteratively, not all at once
- Reduces risk: can rollback if issues discovered
- Documentation: `[DEPRECATED]` helps developers find replacement

### Decision 3: Why Auto-Set recorded_by?

**Alternative Rejected**: Manual adviser selection in admin

**Reason Chosen**:

- Reduces data entry errors (no adviser name typos)
- Matches real workflow (section adviser naturally records status)
- Ensures consistency (one source of truth = section.adviser)
- Auditable (can trace recording decision to specific adviser)

### Decision 4: Why Use final_status Choices?

**Alternative Rejected**: Single boolean (promoted_yn)

**Reason Chosen**:

- Handles edge cases (graduated, transferred, dropped_out)
- Clearer semantics (no guessing what False means)
- Extensible (easy to add new statuses)
- Searchable (can query by specific status type)

---

## 9. Related Models (For Reference)

These models interact with the new architecture:

### `coordinator_app.AcademicPerformance`

- Input for computing overall_grade
- Records Q1-4 and Final grades per subject
- Aggregated at year-end to StudentAcademicYearStatus

### `admin_app.Section`

- Links students to advisers
- `adviser = OneToOneField(Teacher)`
- Used for auto-setting `recorded_by`

### `admin_app.Teacher`

- Referenced by Section.adviser
- Referenced by StudentAcademicYearStatus.recorded_by

### `admin_app.SchoolYear`

- Referenced by StudentEnrollment
- Referenced by StudentAcademicYearStatus
- Used for year-to-year comparisons

---

## 10. Testing Scenarios

### Test Case 1: New Student Enrollment (Control/Validation)

```
Expected: Works as before, no breaking changes
Steps:
  1. Create new StudentEnrollment with enrollee_type='new'
  2. Complete all required steps (6 total)
  3. Verify is_complete = True
  4. Verify enrollment_status can update to 'approved'
  5. Verify Student.current_enrollment returns this enrollment
```

### Test Case 2: Continuing Student (Promoted)

```
Expected: Can re-enroll successfully
Steps:
  1. Student S1 completes SY2024 enrollment, gets overall_grade=85
  2. At year-end, StudentAcademicYearStatus created with final_status='promoted'
  3. Next year SY2025 opens
  4. S1 applies as continuing
  5. System calls can_student_continue(S1.lrn) → True
  6. Allow new StudentEnrollment creation
  7. Mark as 'continuing' type (fewer required steps)
  8. S1.current_enrollment now points to SY2025 enrollment
```

### Test Case 3: Continuing Student (Not Promoted)

```
Expected: Cannot re-enroll, shows error
Steps:
  1. Student S2 completes SY2024 enrollment, gets overall_grade=45
  2. At year-end, StudentAcademicYearStatus created with final_status='retained'
  3. Next year SY2025 opens
  4. S2 tries to apply as continuing
  5. System calls can_student_continue(S2.lrn) → False
  6. Block enrollment creation, show error message
  7. S2 cannot proceed until status manually overridden
```

### Test Case 4: Adviser Auto-Assignment

```
Expected: recorded_by auto-set from section adviser
Steps:
  1. Section SCIE-A has adviser = Teacher(name='Mr. Smith')
  2. Create StudentAcademicYearStatus with section=SCIE-A
  3. Call .save()
  4. Verify recorded_by = Mr. Smith (auto-assigned)
  5. Verify no manual input needed
```

### Test Case 5: Backward Compatibility Properties

```
Expected: Old code reading Student fields still works
Steps:
  1. Have existing code: student.grade_level
  2. Create StudentEnrollment with grade_level=Grade8
  3. Call current_enrollment property (reads StudentEnrollment)
  4. Call current_grade_level property (reads from current_enrollment)
  5. Verify returns Grade8 (backward compatible)
```

---

## 11. Next Action Items (For User)

**This Week**:

1. [ ] Review architecture document (this file) - DONE ✅
2. [ ] Run migration: `python manage.py migrate enrollment_app`
3. [ ] Verify tables exist in database
4. [ ] Run test cases 1-2 (new and promoted student)

**Next Week**: 5. [ ] Update enrollment views 6. [ ] Implement re-enrollment validation gate 7. [ ] Test edge cases (transferred, graduated students)

---

## 12. File Locations Summary

| File                                             | Purpose                                               | Status          |
| ------------------------------------------------ | ----------------------------------------------------- | --------------- |
| `enrollment_app/models.py`                       | Student, StudentEnrollment, StudentAcademicYearStatus | ✅ Complete     |
| `enrollment_app/migrations/0020_...py`           | Create new tables                                     | ✅ Ready        |
| `enrollment_app/services/old_student_service.py` | Business logic                                        | ✅ Complete     |
| `enrollment_app/views/studentdata_view.py`       | Form view                                             | ⏳ Needs update |
| `enrollment_app/views/*.py` (other)              | Other enrollment views                                | ⏳ Needs update |
| `admin_app/admin.py`                             | Admin interface                                       | ⏳ Needs update |
| `admin_app/actions/*.py`                         | Year-end actions                                      | ⏳ To create    |

---

**Document Version**: 1.0  
**Last Updated**: Current Session  
**Status**: Architecture Complete, Ready for Implementation Phase
