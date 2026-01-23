# AI-Enabled Section Assignment Automation Documentation

**Last Updated:** January 19, 2026  
**System:** CP AI Base Section Placement System  
**Version:** 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Configuration & Setup](#configuration--setup)
4. [Automation Flow](#automation-flow)
5. [Validation Pipeline](#validation-pipeline)
6. [Section Assignment Strategy](#section-assignment-strategy)
7. [Coordinator Interface](#coordinator-interface)
8. [API Endpoints](#api-endpoints)
9. [Database Models](#database-models)
10. [Troubleshooting](#troubleshooting)
11. [Key Files Reference](#key-files-reference)

---

## Overview

The AI-Enabled Section Assignment Automation system provides **real-time, rule-based enrollment processing** that automatically approves and assigns students to sections when specific validation criteria are met.

### Key Features

- ✅ **Automatic Enrollment Processing** - Processes new enrollments without manual intervention
- ✅ **Multi-Level Validation** - Ensures all required data is present before approval
- ✅ **Sequential Section Filling** - Fills sections in order (Section 1 → Section 2 → Section 3)
- ✅ **Real-Time Processing** - Runs instantly when students submit enrollments
- ✅ **Configurable Per Program** - Each program can enable/disable automation independently
- ✅ **Manual Fallback** - Coordinators can disable AI and process manually
- ✅ **Audit Trail** - Records who approved students and when

---

## System Architecture

### Component Diagram

```
Student Enrollment Submission
           ↓
    Django Signal: post_save(ProgramSelection)
           ↓
    auto_process_enrollment() [enrollment_app/signals.py]
           ↓
    ┌─────────────────────────────────────────┐
    │      Validation Pipeline                │
    ├─────────────────────────────────────────┤
    │ 1. Check AI is enabled for program      │
    │ 2. Check no duplicate enrollment        │
    │ 3. Validate enrollment form complete    │
    │ 4. Verify report card exists            │
    └─────────────────────────────────────────┘
           ↓
    ┌─ YES: All validations pass
    │      ↓
    │  Auto-Approve Enrollment
    │  Auto-Assign to Section
    │  Update Database
    │
    └─ NO: Validation fails
           ↓
    Enrollment Marked for Manual Review
    Coordinator sees in "Manual Mode" view
```

---

## Configuration & Setup

### AI Assistant Preference Model

**Location:** `coordinator_app/models.py` (Lines 101-148)

Each coordinator has settings for AI automation per program:

```python
class AIAssistantPreference(models.Model):
    user = ForeignKey(User)              # Which coordinator
    program = ForeignKey(Program)        # Which program
    ai_enabled = BooleanField(default=True)  # Automation ON/OFF

    class Meta:
        unique_together = [('user', 'program')]
```

### Enabling/Disabling AI

**How it works:**

- Coordinators toggle the mode using a switch in the UI
- Setting is saved per coordinator × program combination
- Changes apply immediately to new enrollments
- Existing approved enrollments are not affected

**UI Toggle Location:** `coordinator_app/templates/coordinator_app/sectionAssignment.html` (Line 371-380)

```html
<label class="relative inline-flex items-center cursor-pointer">
  <input type="checkbox" id="modeToggle" class="sr-only peer" />
  <div class="w-20 h-10 bg-gray-300 ..."></div>
</label>
<!-- Manual / AI Switch -->
```

---

## Automation Flow

### Step-by-Step Process

#### **Step 1: Enrollment Trigger**

When a student completes enrollment and submits their program selection:

- `ProgramSelection` model is created
- Django post_save signal fires automatically
- `auto_process_enrollment()` function is called

**File:** `enrollment_app/signals.py` (Lines 16-34)

```python
@receiver(post_save, sender=ProgramSelection)
def auto_process_enrollment(sender, instance, created, **kwargs):
    # Only process NEW enrollments
    if not created:
        return

    # Skip if already approved/assigned
    if instance.admin_approved or instance.assigned_section:
        return
```

#### **Step 2: AI Enabled Check**

System checks if AI automation is enabled for this program:

```python
ai_pref = AIAssistantPreference.objects.filter(
    program=program,
    ai_enabled=True
).first()

if not ai_pref:
    return  # AI disabled, skip automation
```

#### **Step 3: Validation Pipeline** (Details in Section 5)

Three critical checks are performed:

1. No duplicate enrollment
2. Enrollment form complete
3. Report card exists

#### **Step 4: Auto-Approval & Assignment**

If all validations pass:

```python
with transaction.atomic():
    # Auto-approve
    instance.admin_approved = True
    instance.approved_by = 'AI Assistant'
    instance.approved_at = timezone.now()
    instance.admin_notes = 'Auto-approved by AI Assistant - all validation criteria met'

    # Auto-assign to section
    section = _get_next_available_section(program_code, instance.school_year)
    if section:
        instance.assigned_section = str(section.id)
        instance.section_assigned_at = timezone.now()
        section.update_current_students_count()

    instance.save()
```

#### **Step 5: Student Status Updated**

Student's enrollment status changes from `pending` → `approved`

---

## Validation Pipeline

### Validation 1: Duplicate Enrollment Check

**Function:** `_has_duplicate_enrollment()` (Lines 97-105)

**Purpose:** Prevent students from being enrolled in multiple programs/sections

**Logic:**

```python
def _has_duplicate_enrollment(student, current_selection):
    existing = ProgramSelection.objects.filter(
        student=student,
        admin_approved=True
    ).exclude(pk=current_selection.pk).exists()

    return existing
```

**Result:**

- ✅ Pass: No approved enrollments found
- ❌ Fail: Student already approved elsewhere (skip automation)

---

### Validation 2: Enrollment Form Completeness

**Function:** `_is_enrollment_complete()` (Lines 108-164)

**Purpose:** Ensure student filled out all required forms

**Checked Fields:**

| **Form**             | **Fields Required**                                                                                        |
| -------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Student Data**     | Last name, First name, Gender, Date of birth                                                               |
| **Family Data**      | At least 1 parent with: Family name, First name, DOB, Occupation, Contact                                  |
| **Academic Data**    | Must exist (any data)                                                                                      |
| **Completion Flags** | student_data_completed, family_data_completed, survey_completed, academic_data_completed, program_selected |

**Code:**

```python
def _is_enrollment_complete(student):
    # Check completion flags
    if not all([
        student.student_data_completed,
        student.family_data_completed,
        student.survey_completed,
        student.academic_data_completed,
        student.program_selected
    ]):
        return False

    # Check required fields exist and are filled
    # ... (validation of each form)

    return True
```

**Result:**

- ✅ Pass: All forms complete with required fields
- ❌ Fail: Missing form or missing required fields (skip automation)

---

### Validation 3: Report Card Document Check ⭐ CRITICAL

**Function:** `_has_report_card()` (Lines 167-183)

**Purpose:** Verify report card PDF/document is uploaded

**Why It Matters:**

- Report card is the **KEY DOCUMENT** for validating academic performance
- System cannot auto-approve without proof of previous academic standing
- Most common reason automation stops and requires manual review

**Code:**

```python
def _has_report_card(student):
    try:
        if hasattr(student, 'academic_data'):
            academic_data = student.academic_data
            if academic_data.report_card and academic_data.report_card.name:
                return True
        return False
    except Exception:
        return False  # Be conservative on error
```

**Result:**

- ✅ Pass: Report card file exists and is not empty
- ❌ Fail: Report card missing or file is null (skip automation - MANUAL REVIEW NEEDED)

---

## Section Assignment Strategy

### Sequential Fill Algorithm

**Function:** `_get_next_available_section()` (Lines 186-224)

**Strategy:** Fill sections **one by one in order** rather than distributing evenly.

### Algorithm Steps

1. **Get Sections** - Retrieve all sections for the program
2. **Sort by Creation** - Order by `created_at` (oldest first)
3. **Check Each Section** - In order, find first with available space
4. **Fill Sequentially** - Complete Section 1 before using Section 2
5. **Repeat** - Continue until section has capacity

### Visual Example

```
Program: Grade 7 English
├─ Section 7-1 "Sampaguita" (Created: Jan 1)
│  Capacity: 40 | Current: 40 | FULL
│
├─ Section 7-2 "Rosal" (Created: Jan 2)
│  Capacity: 40 | Current: 35 | AVAILABLE ← ASSIGN HERE
│
├─ Section 7-3 "Orchid" (Created: Jan 3)
│  Capacity: 40 | Current: 0 | (not used yet)
│
└─ Section 7-4 "Daisy" (Created: Jan 4)
   Capacity: 40 | Current: 0 | (not used yet)
```

**Student arrives:**

- 7-1 is full (40/40) → Skip
- 7-2 has space (35/40) → **ASSIGN HERE**
- Process completes

### Code Implementation

```python
def _get_next_available_section(program_code, school_year):
    sections = Section.objects.filter(
        program__code=program_code,
        school_year=school_year
    ).order_by('created_at')  # Oldest first

    for section in sections:
        actual_count = section.get_actual_count()

        if actual_count < section.max_students:
            return section  # First section with space
        # This section is full, continue to next

    return None  # All sections full
```

### Benefits of Sequential Fill

| **Aspect**            | **Benefit**                             |
| --------------------- | --------------------------------------- |
| **Predictability**    | Students know which sections fill first |
| **Fair Distribution** | All sections reach capacity evenly      |
| **Manageable Load**   | Teachers get full classes sequentially  |
| **Easy to Monitor**   | No complex balancing logic              |

---

## Coordinator Interface

### Two Operating Modes

#### **🤖 AI Mode (Automatic Processing)**

**When Enabled:**

- AI automation processes new enrollments automatically
- Coordinator views already-approved students
- Table shows: Name, LRN, Assigned Section, Approval Date, Status

**What Coordinator Sees:**

```
AI Processed Students Table
├─ John Doe (LRN: 001) → Section 7-1 → Approved Jan 19 ✓
├─ Maria Santos (LRN: 002) → Section 7-1 → Approved Jan 19 ✓
├─ Pedro Garcia (LRN: 003) → Section 7-2 → Approved Jan 19 ✓
└─ (No pending actions needed)

Statistics Panel:
├─ 45 Students Processed by AI
├─ 45 Auto-Approved
├─ 45 Assigned to Sections
└─ 0 Pending Review
```

**Coordinator Actions:**

- ✅ View student details
- ✅ Search/filter students
- ✅ Export to CSV
- ✅ Monitor AI performance

**File:** `coordinator_app/static/coordinator_app/js/sectionAssignment.js` (Lines 156-210)

---

#### **✋ Manual Mode (Manual Approval)**

**When Disabled:**

- Coordinator manually reviews each enrollment
- Must approve or reject each student
- Must assign section manually via dropdown

**What Coordinator Sees:**

```
Enrollment Requests Table (Pending Approval)
├─ [Pending] Alex Reyes (LRN: 101) → [Select Section ▼]
├─ [Pending] Sofia Torres (LRN: 102) → [Select Section ▼]
├─ [Pending] Luis Mendoza (LRN: 103) → [Select Section ▼]
└─ (5 students awaiting action)

Each Row Includes:
├─ Student name & LRN
├─ Exam score
├─ Interview score
├─ Section dropdown
└─ Approve/Reject buttons
```

**Coordinator Actions:**

- 📋 Review enrollment documents
- ✅ Select section from dropdown
- 🔘 Click "Approve" button
- ❌ Reject if incomplete/invalid
- 💬 Add admin notes

**File:** `coordinator_app/static/coordinator_app/js/sectionAssignment.js` (Lines 110-150)

---

### Mode Toggle Switch

**HTML Location:** `coordinator_app/templates/coordinator_app/sectionAssignment.html` (Lines 371-380)

```html
<div class="flex items-center gap-4">
  <span class="text-sm font-semibold">Manual</span>
  <label class="relative inline-flex items-center cursor-pointer">
    <input type="checkbox" id="modeToggle" class="sr-only peer" />
    <div class="w-20 h-10 bg-gray-300 ... peer-checked:bg-green-500"></div>
  </label>
  <span class="text-sm font-semibold">AI</span>
</div>
```

**JavaScript Function:** `switchMode()` (Lines 37-75)

```javascript
function switchMode(mode) {
  if (mode === "manual") {
    manualView.classList.remove("hidden");
    aiView.classList.add("hidden");
    loadManualModeData();
  } else {
    aiView.classList.remove("hidden");
    manualView.classList.add("hidden");
    loadAIModeData();
  }
}
```

---

## API Endpoints

### 1. Approve and Place Student (Manual Mode)

**Endpoint:** `POST /coordinator/api/student/{lrn}/approve-and-place/`

**Purpose:** Manual approval and section assignment by coordinator

**Request Body:**

```json
{
  "section_id": 5,
  "admin_notes": "All documents verified"
}
```

**Response Success (200):**

```json
{
  "success": true,
  "message": "Enrollment approved! John Doe has been placed in Section 7-1",
  "new_status": "approved",
  "section_name": "Section 7-1",
  "section_id": 5,
  "section_current_students": 41,
  "section_max_students": 40
}
```

**Response Error (400/500):**

```json
{
  "success": false,
  "error": "Student is already approved and placed in a section"
}
```

**File:** `coordinator_app/views/coor_studentedit_views.py` (Lines 511-640)

---

### 2. Validation Rules in API

**Rule 1: No Double Placement**

```python
if program_selection.admin_approved and program_selection.assigned_section:
    return error("Already approved and placed")
```

**Rule 2: Sequential Fill Enforcement**

```python
program_sections = Section.objects.filter(...).order_by('created_at')
for s in program_sections:
    if s.id == section.id:
        break
    actual_count = s.get_actual_count()
    if actual_count < s.max_students:
        return error("Previous sections must be full first")
```

**Rule 3: Capacity Check**

```python
actual_section_count = section.get_actual_count()
if actual_section_count >= section.max_students:
    return error(f"Section {section.name} is full")
```

**Rule 4: Database Truth**

```python
# Always count from database, never trust cached field
section.update_current_students_count()
```

---

## Database Models

### ProgramSelection Model

**Purpose:** Represents a student's enrollment in a program for a school year

**Key Fields:**

```python
class ProgramSelection(models.Model):
    student = ForeignKey(Student)
    selected_program_code = CharField()
    school_year = ForeignKey(SchoolYear)

    # Approval fields
    admin_approved = BooleanField(default=False)
    approved_by = CharField()
    approved_at = DateTimeField(null=True)

    # Assignment fields
    assigned_section = CharField(null=True)
    section_assigned_at = DateTimeField(null=True)

    # Notes
    admin_notes = TextField(blank=True)
```

---

### AIAssistantPreference Model

**Purpose:** Controls automation settings per coordinator per program

**Key Fields:**

```python
class AIAssistantPreference(models.Model):
    user = ForeignKey(User)
    program = ForeignKey(Program)
    ai_enabled = BooleanField(default=True)

    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

---

### Section Model

**Purpose:** Represents a class section with capacity limits

**Key Fields:**

```python
class Section(models.Model):
    program = ForeignKey(Program)
    name = CharField()  # e.g., "Section 7-1"
    max_students = IntegerField()
    current_students = IntegerField(default=0)

    created_at = DateTimeField(auto_now_add=True)
```

**Key Method:**

```python
def get_actual_count(self):
    """Count actual approved enrollments from database"""
    return ProgramSelection.objects.filter(
        assigned_section=str(self.id),
        admin_approved=True
    ).count()

def update_current_students_count(self):
    """Sync current_students field with actual count"""
    self.current_students = self.get_actual_count()
    self.save()
```

---

## Troubleshooting

### Issue 1: Students Not Being Auto-Approved

**Symptoms:**

- Students submit enrollment but remain "Pending"
- No automatic approval happens

**Possible Causes:**

| **Cause**            | **Check**                               | **Solution**                      |
| -------------------- | --------------------------------------- | --------------------------------- |
| AI disabled          | Check toggle in coordinator dashboard   | Enable AI mode                    |
| Report card missing  | Review student's academic data          | Ask student to upload report card |
| Forms incomplete     | Check student data, family, survey      | Contact student to complete forms |
| Duplicate enrollment | Check for previous approved enrollments | Reject duplicate, keep original   |
| Database error       | Check Django logs                       | Review error message in logs      |

**Debug Steps:**

```python
# In Django shell:
from enrollment_app.models import ProgramSelection
ps = ProgramSelection.objects.latest('id')

# Check AI preference
from coordinator_app.models import AIAssistantPreference
ai_pref = AIAssistantPreference.objects.filter(
    program=ps.selected_program,
    ai_enabled=True
).first()
print(f"AI Enabled: {ai_pref is not None}")

# Check report card
print(f"Report card exists: {ps.student.academic_data.report_card is not None}")
```

---

### Issue 2: Students Assigned to Wrong Section

**Symptoms:**

- Student assigned to Section 7-3 when Section 7-1 has space
- Sequential fill not working

**Possible Causes:**

- Section 7-1 & 7-2 not actually full (cached count wrong)
- Sections out of creation order

**Solution:**

```python
# Reset section counts (recalculate from database)
from admin_app.models import Section

for section in Section.objects.all():
    section.update_current_students_count()

print("Section counts refreshed")
```

---

### Issue 3: Manual Approval Returns "Previous Sections Must Be Full"

**Symptoms:**

- Coordinator tries to approve student for Section 7-2
- API returns error: "Previous sections must be full first"

**Cause:**

- Section 7-1 is not actually full (some approved students removed or count mismatch)

**Solution:**

```python
# Check section capacities
from admin_app.models import Section

for section in Section.objects.all():
    actual = section.get_actual_count()
    max_capacity = section.max_students
    print(f"{section.name}: {actual}/{max_capacity}")

    # Fill it first if needed
    if actual < max_capacity:
        print(f"  → Section {section.name} has {max_capacity - actual} spaces")
```

---

### Issue 4: Section Capacity Shows Wrong Number

**Symptoms:**

- UI shows "35/40" students
- Actually only 30 students assigned
- Discrepancy between shown and actual

**Cause:**

- `current_students` field not synced with actual database count

**Solution:**

```python
# In Django admin or shell:
from admin_app.models import Section

section = Section.objects.get(id=5)
print(f"Field says: {section.current_students}")
print(f"Actual count: {section.get_actual_count()}")

# Fix it:
section.update_current_students_count()
print(f"After fix: {section.current_students}")
```

---

## Key Files Reference

### Backend Files

| **File**                                          | **Purpose**            | **Key Functions**                                 |
| ------------------------------------------------- | ---------------------- | ------------------------------------------------- |
| `enrollment_app/signals.py`                       | Main automation logic  | `auto_process_enrollment()`, validation functions |
| `coordinator_app/models.py`                       | AI preference settings | `AIAssistantPreference` model                     |
| `admin_app/models.py`                             | Section & School Year  | `Section`, `SchoolYear` models                    |
| `coordinator_app/views/coor_studentedit_views.py` | Manual approval API    | `approve_and_place_student()`                     |
| `enrollment_app/models.py`                        | Enrollment data        | `ProgramSelection`, `Student` models              |

### Frontend Files

| **File**                                                           | **Purpose** | **Key Functions**                                          |
| ------------------------------------------------------------------ | ----------- | ---------------------------------------------------------- |
| `coordinator_app/templates/coordinator_app/sectionAssignment.html` | UI template | Mode toggle, tables, statistics                            |
| `coordinator_app/static/coordinator_app/js/sectionAssignment.js`   | UI logic    | `switchMode()`, `loadAIModeData()`, `loadManualModeData()` |

### Configuration Files

| **File**                               | **Purpose**       |
| -------------------------------------- | ----------------- |
| `section_placement_system/settings.py` | Django settings   |
| `manage.py`                            | Django management |

---

## Quick Reference

### Enable AI Automation

1. Login as Coordinator
2. Navigate to "Enrollment Management"
3. Toggle switch to **AI** mode
4. Changes apply immediately

### Disable AI Automation

1. Login as Coordinator
2. Navigate to "Enrollment Management"
3. Toggle switch to **Manual** mode
4. New enrollments require manual approval

### Manual Approval Process

1. Switch to Manual mode
2. Review "Enrollment Requests" table
3. For each student:
   - Review their documents
   - Select section from dropdown
   - Add notes (optional)
   - Click "Approve"
4. Student moved to "Approved" list

### Check Student Status

```python
# Django shell
from enrollment_app.models import ProgramSelection

ps = ProgramSelection.objects.get(student__lrn='001')
print(f"Status: {'Approved' if ps.admin_approved else 'Pending'}")
print(f"Section: {ps.assigned_section}")
print(f"Approved by: {ps.approved_by}")
print(f"Date: {ps.approved_at}")
```

---

## Support & Contact

For issues or questions about the AI automation system:

1. Check the **Troubleshooting** section above
2. Review **Debug Steps** for your specific issue
3. Check Django logs: `python manage.py runserver` with verbose output
4. Contact system administrator with error details

---

**Document Version:** 1.0  
**Last Updated:** January 19, 2026  
**Next Review:** July 2026
