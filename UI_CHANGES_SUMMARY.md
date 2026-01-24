# UI Changes Summary - Student Edit Page

## Before vs After Comparison

### BEFORE: Old Enrollment Placement Section

```
┌──────────────────────────────────────────────────────────────┐
│ ENROLLMENT PLACEMENT (ADMIN ONLY)                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Program:        [Select Program ▼]                       │ │
│ │ (Dropdown with all programs)                             │ │
│ │                                                           │ │
│ │ Grade Level:    [Select Grade ▼]                         │ │
│ │ (7, 8, 9, 10, 11, 12)                                    │ │
│ │                                                           │ │
│ │ Section:        [Select program first ▼]                │ │
│ │ (Disabled until program selected)                        │ │
│ │                                                           │ │
│ │ Admin Approved: [Pending ▼]  [Approved]                 │ │
│ │ (Binary choice: approve or stay pending)                 │ │
│ │                                                           │ │
│ │ Admin Notes:    [Enter admin notes________]              │ │
│ │ (Single line input)                                      │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                              │
│ [Back to Enrollment] [Save All Changes] ◀ OLD BUTTONS       │
└──────────────────────────────────────────────────────────────┘
```

### AFTER: New Enrollment Approval Section

```
┌──────────────────────────────────────────────────────────────┐
│ ENROLLMENT APPROVAL (ADMIN ONLY)                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Program:        [STE (READ-ONLY)]                        │ │
│ │ (Shows only coordinator's program, read-only)            │ │
│ │                                                           │ │
│ │ Status:         [-- Select Status -- ▼]                 │ │
│ │ (NEW: 3 options: Pending, Approved, Rejected)            │ │
│ │                                                           │ │
│ │ Notes/Reason:   [Enter admin notes or rejection reason]  │ │
│ │ (NEW: Textarea, multi-line, placeholder changes)         │ │
│ │ (Multi-line, clearer for longer content)                │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                              │
│ [Back] [Approve & Save] [Reject] ◀ NEW BUTTONS             │
│ (Context-sensitive, show/hide based on status)             │
│                                                              │
│ NOTE: Section field is GONE - auto-assigned by system      │
│       Grade level is GONE - not needed                     │
│       Program dropdown is GONE - locked to coordinator      │
└──────────────────────────────────────────────────────────────┘
```

## Key UI Changes

### 1. Program Field

**BEFORE**: Dropdown to select any program
**AFTER**: Read-only field showing only coordinator's program
**Reason**: Program isolation - coordinators can only work with their program

### 2. Status Field

**BEFORE**: "Admin Approved" binary choice (Pending/Approved)
**AFTER**: "Status" dropdown with 3 options:

- -- Select Status -- (placeholder)
- Pending (default, no action needed)
- Approved (triggers auto-assignment)
- Rejected (triggers rejection flow)
  **Reason**: Support rejection workflow

### 3. Notes/Reason Field

**BEFORE**: Single-line "Admin Notes" input
**AFTER**: Multi-line "Notes / Rejection Reason" textarea
**Reason**: Support longer rejection explanations

### 4. Action Buttons

**BEFORE**: Always visible "Save All Changes" button
**AFTER**: Context-sensitive buttons:

- Status = "Pending": No action button visible
- Status = "Approved": GREEN "Approve & Save Changes" appears
- Status = "Rejected": RED "Reject Enrollment" appears
  **Reason**: Clear action intent, prevent accidental clicks

### 5. Section Assignment

**BEFORE**: Coordinator manually selects section from dropdown
**AFTER**: System automatically assigns section
**Reason**: Ensures sequential filling algorithm is followed

### 6. Grade Level

**BEFORE**: Required selection (7-12)
**AFTER**: REMOVED
**Reason**: No longer needed - system knows grade from section

## Button Behavior

### Approval Button (Green)

```
Appears when: Status = "Approved"
Click action:
  1. Validate student data
  2. Get first available section (sequential fill)
  3. Auto-assign to section
  4. Show success popup with details
  5. Popup offers: Check Masterlist OR Back to Enrollment
```

### Reject Button (Red)

```
Appears when: Status = "Rejected"
Click action:
  1. Require rejection reason (validation)
  2. Ask for confirmation
  3. Mark enrollment as rejected
  4. Save rejection reason
  5. Redirect to enrollment management page
```

### Back Button (Gray)

```
Always visible
Remains as: "Back to Enrollment"
Takes user to: /coordinator/section-assignment/
```

## Success Popup Display

When approval succeeds, modal popup appears:

```
╔════════════════════════════════════════════╗
║                                            ║
║  ✓ SUCCESS! - Enrollment Confirmed        ║
║                                            ║
║  Student John Doe has successfully        ║
║  enrolled under the program STE in        ║
║  Section 7-2                              ║
║                                            ║
║  ┌──────────────────────────────────────┐  ║
║  │ Check Sections Masterlist            │  ║
║  │ (opens: /coordinator/masterlist/5/)  │  ║
║  └──────────────────────────────────────┘  ║
║                                            ║
║  ┌──────────────────────────────────────┐  ║
║  │ Back to Enrollment Management        │  ║
║  │ (opens: /coordinator/section-...)    │  ║
║  └──────────────────────────────────────┘  ║
║                                            ║
╚════════════════════════════════════════════╝
```

**Popup Features:**

- Green header with checkmark icon
- Displays: Student name, program name, section name
- Two action buttons for navigation
- Auto-populated with correct details from API response
- Modal overlay prevents accidental clicks
- Click "Check Sections" to verify student in masterlist
- Click "Back" to continue processing other students

## Form Validation Rules

### When Approving:

- ✓ Admin notes are optional
- ✓ Section is auto-assigned (no selection needed)
- ✓ Program is locked (cannot change)
- ✓ Status must be "Approved"

### When Rejecting:

- ✗ Rejection reason is REQUIRED
- ✗ Cannot reject without providing reason
- ✓ Confirmation prompt before final rejection
- ✓ Status must be "Rejected"

### When Leaving Pending:

- ✓ No action taken
- ✓ Can return later to approve/reject
- ✓ Status stays "Pending"

## Error Messages

### If all sections are full:

```
ERROR
No available sections in STE.
All sections are full.
```

### If already approved:

```
ERROR
Student is already approved and placed in a section.
Cannot approve again.
```

### If rejection reason missing:

```
ERROR (Client-side validation)
Please provide a rejection reason
```

### If trying to access another program's student:

```
HTTP 403 - Forbidden
You do not have permission to view this student.
```

## Status Badge Colors (on masterlist/listing)

After approval/rejection, student shows with status badge:

- **Approved**: ✓ Green badge "Approved"
- **Rejected**: ✗ Red badge "Rejected"
- **Pending**: ⚠ Yellow badge "Pending"

Example:

```
┌────────────────────────────────────────┐
│ John Doe                               │
│ LRN: 12345                             │
│ Program: STE                           │
│ Status: [✓ Approved] (Green badge)    │
│ Assigned Section: Section 7-2         │
└────────────────────────────────────────┘
```

## Database Fields Now Visible in Admin Panel

If you open Django admin for `ProgramSelection`:

**Old Fields (still present):**

- selected_program_code
- admin_approved (boolean)
- admin_notes
- approved_by
- approved_at
- assigned_section
- section_assigned_at

**New Fields (added):**

- admin_rejected (boolean) ← NEW
- rejected_by (text) ← NEW
- rejected_at (datetime) ← NEW
- rejection_reason (text) ← NEW

## JavaScript Enhancements

### Status Dropdown Change Handler

```javascript
// When user changes status dropdown:
if status === "Approved":
  - Show green "Approve & Save Changes" button
  - Hide reject button
  - Change notes placeholder to "Enter admin notes (optional)"

else if status === "Rejected":
  - Show red "Reject Enrollment" button
  - Hide approve button
  - Change notes placeholder to "Enter rejection reason"

else:
  - Hide both action buttons
  - Change notes placeholder to generic text
```

### Approval Button Click Handler

```javascript
// When user clicks "Approve & Save Changes":
1. Get notes from textarea
2. Send POST to /coordinator/api/student/{lrn}/approve-and-place/
3. On success:
   - Display success popup with details
   - Popup shows student name, program, section
   - User can navigate to masterlist or back
```

### Reject Button Click Handler

```javascript
// When user clicks "Reject Enrollment":
1. Validate reason is provided
2. Ask for confirmation: "Sure you want to reject?"
3. On confirm, send POST to /coordinator/api/student/{lrn}/reject/
4. On success:
   - Redirect to enrollment management page
   - User can process next students
```

---

## Visual Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Review Student Enrollment Request                  │
│ (Shows logged-in coordinator name & avatar)                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Student Forms Section                                      │
│ - Student Data                                             │
│ - Family Data                                              │
│ - Academic Data                                            │
│ - Survey Data                                              │
│ - Documents                                                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ENROLLMENT APPROVAL SECTION (Red header)                   │
│                                                             │
│ Program:    [STE]                  (Read-only)            │
│ Status:     [-- Select -- ▼]      (Dropdown)             │
│ Reason:     [________________]     (Textarea)             │
│             [____________________]                         │
│                                                             │
│ [Back] [Approve Button] [Reject Button]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

**Summary**: The new UI is simpler, more focused, and guides coordinators toward the intended workflow of approve-with-auto-assignment or reject-with-reason. No more manual section selection!
