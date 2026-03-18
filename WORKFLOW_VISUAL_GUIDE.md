# Section Placement Workflow - Visual Guide

## Complete Enrollment Approval & Auto-Assignment Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    COORDINATOR LOGS IN                                   │
│                                                                          │
│  1. Selects Program (e.g., "STE", "SPFL") from 2 options               │
│  2. Enters Username & Password                                          │
│  3. Can only access assigned program (not others)                       │
└──────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────────┐
│              COORDINATOR VIEWS ENROLLMENT MANAGEMENT                      │
│                                                                          │
│  - Lists all students in their program awaiting enrollment              │
│  - Shows: Name, LRN, Status, Program                                    │
│  - Can filter/search students                                           │
└──────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────────┐
│              COORDINATOR CLICKS ON STUDENT → OPENS EDIT PAGE            │
│                                                                          │
│  Page shows:                                                             │
│  ┌─────────────────────────────────────┐                               │
│  │ Student Forms:                      │                               │
│  │ - Student Data                      │                               │
│  │ - Family Data                       │                               │
│  │ - Academic Data                     │                               │
│  │ - Survey Data                       │                               │
│  │ - Document Requirements             │                               │
│  └─────────────────────────────────────┘                               │
│                                                                          │
│  ┌─────────────────────────────────────┐  ← NEW UI                     │
│  │ Enrollment Approval Section:        │                               │
│  │                                     │                               │
│  │ Program: [STE (READ-ONLY)]         │  (Only their program)         │
│  │ Status:  [Pending ▼]               │  (Dropdown)                   │
│  │ Notes:   [________________]        │  (Optional)                   │
│  │                                     │                               │
│  │ [Back] [Action Button]             │  (Action button hidden)       │
│  └─────────────────────────────────────┘                               │
└──────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌──────────────────────────────────────────────────────────────────────────┐
│                     COORDINATOR SELECTS ACTION                           │
│                                                                          │
│  Option 1: SELECT "APPROVED"                                             │
│  ═══════════════════════════════════════════════════════════════════    │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │ Status: [Approved ▼]                                     │           │
│  │ Notes:  [Any optional notes about approval] (optional)   │           │
│  │ [Back] [Approve & Save Changes] ✓ (GREEN BUTTON)       │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                          │
│  Option 2: SELECT "REJECTED"                                             │
│  ═══════════════════════════════════════════════════════════════════    │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │ Status: [Rejected ▼]                                     │           │
│  │ Reason: [Why was enrollment rejected?] (REQUIRED)       │           │
│  │ [Back] [Reject Enrollment] ✗ (RED BUTTON)              │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                          │
│  Option 3: LEAVE AS "PENDING" (DEFAULT)                                  │
│  ═══════════════════════════════════════════════════════════════════    │
│  ┌──────────────────────────────────────────────────────────┐           │
│  │ Status: [Pending ▼] (no action button shown)            │           │
│  │ [Back] (return later)                                    │           │
│  └──────────────────────────────────────────────────────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
                                   ↓
                    ┌──────────────┴──────────────┐
                    ↓                             ↓
         ┌────────────────────┐     ┌────────────────────┐
         │  APPROVAL PATH     │     │  REJECTION PATH    │
         └────────────────────┘     └────────────────────┘
                    ↓                             ↓
         ┌────────────────────┐     ┌────────────────────┐
         │ Click "Approve"    │     │ Click "Reject"     │
         │ button             │     │ button             │
         └────────────────────┘     └────────────────────┘
                    ↓                             ↓
    ┌───────────────────────────┐  ┌──────────────────────────┐
    │ STEP 1: VALIDATE          │  │ STEP 1: CONFIRM          │
    │                           │  │                          │
    │ Check: Student exists     │  │ Show: "Confirm           │
    │ Check: Program selected   │  │        rejection?"       │
    │ Check: Not already        │  │                          │
    │        approved/rejected  │  │ [Cancel] [Confirm]      │
    └───────────────────────────┘  └──────────────────────────┘
                    ↓                             ↓
    ┌───────────────────────────┐  ┌──────────────────────────┐
    │ STEP 2: AUTO-ASSIGN       │  │ STEP 2: MARK REJECTED    │
    │                           │  │                          │
    │ 1. Get all sections in    │  │ Update fields:           │
    │    program/school year    │  │ - admin_rejected = True  │
    │ 2. Sort by creation date  │  │ - rejected_by = Username │
    │    (oldest first)         │  │ - rejected_at = Now      │
    │ 3. Find FIRST section     │  │ - rejection_reason = ... │
    │    with available spots   │  │                          │
    │ 4. Auto-assign student    │  │ Update student status:   │
    │    to that section        │  │ enrollment_status =      │
    │                           │  │ 'rejected'               │
    │ Example:                  │  │                          │
    │ ┌─────────────────────┐   │  │ Log action:              │
    │ │ Sec 7-1: 40/40 FULL │   │  │ - old_status = pending   │
    │ │ Sec 7-2: 35/40 ✓ ← │   │  │ - new_status = rejected  │
    │ │          ASSIGN     │   │  │ - reason = provided      │
    │ │ Sec 7-3: 0/40       │   │  │                          │
    │ └─────────────────────┘   │  └──────────────────────────┘
    └───────────────────────────┘                ↓
                    ↓          ┌──────────────────────────┐
    ┌───────────────────────────────┐          │ DONE: Enrollment    │
    │                               │          │ marked as REJECTED   │
    │ STEP 3: UPDATE DATABASE       │          │ with reason         │
    │                               │          └──────────────────────┘
    │ Update section counts:        │                    ↓
    │ Sec 7-2: 36/40 (was 35)      │          ┌──────────────────────┐
    │                               │          │ REDIRECT TO:         │
    │ Update enrollment status:     │          │ Enrollment           │
    │ student.status = 'approved'   │          │ Management Page      │
    │                               │          └──────────────────────┘
    │ Log in audit trail:           │
    │ - old: pending → new: approved│
    │ - approved_by: Username       │
    │ - approved_at: 2026-01-24 ... │
    └───────────────────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │  STEP 4: SHOW SUCCESS POPUP        │
    │                                   │
    │ ╔════════════════════════════════╗│
    │ ║  SUCCESS!                      ║│
    │ ║  ✓ Enrollment Confirmed        ║│
    │ ║                                ║│
    │ ║  Student John Doe has          ║│
    │ ║  successfully enrolled under    ║│
    │ ║  the program STE in             ║│
    │ ║  Section 7-2                   ║│
    │ ║                                ║│
    │ ║  [Check Sections] [Back]      ║│
    │ ║                                ║│
    │ ║ Button 1: "Check Sections"    ║│
    │ ║  → Navigates to masterlist     ║│
    │ ║  → Shows all students in       ║│
    │ ║     Section 7-2                ║│
    │ ║                                ║│
    │ ║ Button 2: "Back"              ║│
    │ ║  → Returns to Enrollment       ║│
    │ ║     Management page            ║│
    │ ║  → Coordinator can continue    ║│
    │ ║     processing next students   ║│
    │ ╚════════════════════════════════╝│
    └───────────────────────────────────┘
```

## Sequential Section Filling Example

When approving students one-by-one, they fill sections in order:

```
PROGRAM: Grade 7 English (STE)
School Year: 2025-2026

Sections (sorted by creation date - oldest first):

┌─────────────────────────────────────────┐
│ Section 7-1 "Sampaguita" (Created: 1/1) │
│ Capacity: 40                            │
│ Current: 0 → 40 (FULL)                  │
│                                         │
│ Students added:                         │
│ 1. Maria Santos ← First approval        │
│ 2. Pedro Garcia                         │
│ ...                                     │
│ 40. Last Student                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Section 7-2 "Rosal" (Created: 1/2)      │
│ Capacity: 40                            │
│ Current: 0 → 35 (HAS SPACE)             │
│                                         │
│ Students added:                         │
│ 1. John Doe ← 41st approval goes here   │
│ 2. Sofia Torres                         │
│ ...                                     │
│ 35. (5 more spots available)            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ Section 7-3 "Orchid" (Created: 1/3)     │
│ Capacity: 40                            │
│ Current: 0 (NOT USED YET)               │
│                                         │
│ Will be used after Section 7-2 is full  │
└─────────────────────────────────────────┘
```

## Program Isolation Security

```
┌─────────────────────────────────────┐
│ Coordinator Login                   │
│                                     │
│ User: mario@school.edu              │
│ Program: STE (LOCKED IN)            │
│                                     │
│ Can access:                         │
│ ✓ Students in STE program           │
│ ✓ STE sections and masterlist       │
│ ✓ STE statistics                    │
│                                     │
│ Cannot access:                      │
│ ✗ SPFL students (different program) │
│ ✗ REGULAR students                  │
│ ✗ Other programs' sections          │
└─────────────────────────────────────┘
                    ↓
        If coordinator tries to:
        View /coordinator/student-edit/001/
        But Student 001 is in SPFL
                    ↓
        ┌─────────────────────────────┐
        │ ERROR: 403 Forbidden        │
        │                             │
        │ "You do not have           │
        │  permission to view this    │
        │  student."                  │
        └─────────────────────────────┘
```

## Key Technical Points

### 1. **Automatic Section Assignment**

- No dropdown selection needed
- System automatically assigns to first available
- Uses creation date order (sequential fill)
- Prevents all-or-nothing assignment to sections

### 2. **Rejection with Reason**

- Coordinator must provide reason
- System tracks who rejected and when
- Enrollments marked as rejected in database
- Audit trail maintained

### 3. **Program Isolation**

- Coordinators locked to their program at login
- No program dropdown on student edit page
- Backend validation prevents cross-program access
- 403 Forbidden error if attempting unauthorized access

### 4. **Success Feedback**

- Modal popup confirms details
- Links to related pages
- Clear navigation back to enrollment management

---

## Status Codes & Error Messages

### Successful Approval

```json
{
  "success": true,
  "message": "John Doe has successfully enrolled under the program STE in Section 7-2",
  "student_name": "John Doe",
  "program_name": "Science, Technology, Engineering",
  "section_name": "Section 7-2",
  "section_id": 5,
  "new_status": "approved"
}
```

### Successful Rejection

```json
{
  "success": true,
  "message": "John Doe's enrollment has been rejected",
  "student_name": "John Doe",
  "new_status": "rejected"
}
```

### Error: No Available Sections

```json
{
  "success": false,
  "error": "No available sections in STE. All sections are full."
}
```

### Error: Already Approved

```json
{
  "success": false,
  "error": "Student is already approved and placed in a section. Cannot approve again."
}
```

---

from enrollment_app.models import Student, StudentEnrollment, ProgramSelection, StudentDocumentSubmission, EnrollmentStatusLog
from admin_app.models import SchoolYear

lrn = '126221180029'
sy_2026 = SchoolYear.objects.get(year_label='2026-2027')
student = Student.objects.get(lrn=lrn)

StudentDocumentSubmission.objects.filter(student=student, school_year=sy_2026).delete()
ProgramSelection.objects.filter(student=student).delete()
StudentEnrollment.objects.filter(student=student, school_year=sy_2026).delete()
EnrollmentStatusLog.objects.filter(student=student).delete()
print("Done!")

Created: January 24, 2026
