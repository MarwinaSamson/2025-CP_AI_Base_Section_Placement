# How to Undo an Accidental Approval

## The Problem You Asked About

You accidentally approved a student and want to:

- ✓ Undo the approval
- ✓ Return them to "Pending" status
- ✓ Remove their section assignment
- ✓ Keep all audit logs of what happened

## The Solution: Revert to Pending

We've added a **"Revert to Pending" button** that appears when a student is already approved.

## How to Use It

### Step 1: Open Student's Profile

```
Enrollment Management Page
      ↓
Click on student to edit
      ↓
Student's Edit Page opens
```

### Step 2: Check Current Status

The page automatically detects if student is already approved:

**If APPROVED:**

```
Status: [Approved ▼]
Reason: [________________]

[Back] [Revert to Pending] ← YELLOW BUTTON
        (Shows ONLY if approved)
```

**If PENDING:**

```
Status: [Pending ▼]
Reason: [________________]

[Back] [Approve & Save] ← GREEN BUTTON
        (Shows ONLY if pending)
```

### Step 3: Click "Revert to Pending"

1. **Optional**: Add a reason why you're reverting (e.g., "Accidental approval", "Need to review more docs")
2. Click the **yellow "Revert to Pending" button**
3. Confirm in the popup: "Are you sure you want to revert this approval?"
4. System will:
   - Remove section assignment
   - Set status back to "Pending"
   - Log the revert action
   - Refresh the page

### Step 4: Confirmation Message

Success message shows:

```
Student [name]'s approval has been reverted to pending

Removed from section: [Section Name]
```

## What Gets Reverted

When you revert an approval:

✅ **What Changes:**

- Status: Approved → Pending
- Section: [Assigned Section] → None
- Approval timestamp: Cleared
- Approved by: Cleared

❌ **What Stays:**

- Student data (forms, documents, surveys)
- Enrollment in system
- Audit logs (all actions recorded)

## What Gets Logged

In the database `enrollment_status_log`:

```
Old Status: approved
New Status: pending
Changed By: [Coordinator Name]
Change Reason: "Enrollment approval reverted: [Your Reason]"
Timestamp: [When reverted]
```

This creates an audit trail so admins know:

- What happened
- Who did it
- When it was done
- Why it was reversed

## Example Workflow

### Scenario: Accidental Approval

```
1. You approve Wade for REGULAR program
   ↓
   Wade → Assigned to Section 7-2 (HETERO)
   Status: Approved ✓

2. You realize you made a mistake
   (Wrong student? Need to verify documents?)
   ↓
3. Open Wade's page again
   ↓
4. Status shows: Approved ✓
   ↓
5. Click "Revert to Pending" button
   ↓
   Confirm: "Yes, revert this approval"
   ↓
6. System reverts:
   - Status: Pending
   - Section: None
   - Approval info: Cleared
   ↓
7. Success message shows
   ↓
8. Wade can now be reviewed again or re-approved
```

## Button Visibility Logic

The system automatically shows the right button based on current status:

```
┌─────────────────────────────────────────┐
│ What's the current enrollment status?   │
└─────────────────────────────────────────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
 PENDING       APPROVED
    ↓             ↓
Show         Show
[Approve]    [Revert]
Button       Button
(green)      (yellow)
```

## Differences Between Actions

| Action      | Effect                                 | Use When                      |
| ----------- | -------------------------------------- | ----------------------------- |
| **Approve** | Moves to Approved, assigns section     | Student is ready, all docs OK |
| **Revert**  | Moves back to Pending, removes section | Oops! Made a mistake          |
| **Reject**  | Marks as Rejected with reason          | Student doesn't qualify       |

## Important Notes

### ✓ Can Always Revert

You can revert an approval anytime after it's been made.

### ⚠ Cannot Revert a Rejection

Once you REJECT an enrollment, you cannot revert it.
**Solution**: Create a new program selection for the student.

### ✓ Reversions Are Logged

Every revert is recorded in the audit trail with:

- Who reverted it
- When it happened
- The reason given

### ✓ Section Space Freed

When you revert, the section capacity updates:

```
Before Revert:
Section 7-2: 36/40 students (Wade is counted)

After Revert:
Section 7-2: 35/40 students (Wade removed)
```

## What Happens to the Student?

After reverting an approval:

```
Student Status: Pending ✓
├─ Can be reviewed again
├─ Can be re-approved with better info
├─ Can be rejected
├─ Stays in the system
└─ No data is lost
```

The student goes back to the enrollment list as "Pending" and can be:

1. **Approved again** - if you fixed the issue
2. **Rejected** - if they don't qualify
3. **Left pending** - for later review

## Technical Details

### API Endpoint

```
POST /coordinator/api/student/{lrn}/revert-approval/

Body:
{
  "revert_reason": "Why you're reverting (optional)"
}

Response (Success):
{
  "success": true,
  "message": "Wade's approval has been reverted to pending",
  "student_name": "Wade",
  "new_status": "pending",
  "section_removed": "Section 7-2"
}
```

### Database Changes

```sql
-- Before Revert
UPDATE program_selection SET
  admin_approved = 1,
  assigned_section = 5,
  approved_by = "Mario Coordinator",
  approved_at = "2026-01-24 14:30:00"
WHERE student_id = 123;

-- After Revert
UPDATE program_selection SET
  admin_approved = 0,
  assigned_section = NULL,
  approved_by = NULL,
  approved_at = NULL,
  admin_notes = "[REVERTED] Accidental approval"
WHERE student_id = 123;

-- Audit Log Entry
INSERT INTO enrollment_status_log
  (student_id, old_status, new_status, changed_by, change_reason)
VALUES
  (123, "approved", "pending", "Mario Coordinator", "Enrollment approval reverted: Accidental approval");
```

## FAQ

**Q: Can I revert an approval I made yesterday?**
A: Yes! Reverts work anytime, regardless of when the approval was made.

---

**Q: What if the student already started attending class?**
A: You can still revert in the system. But you'd need to coordinate with the teacher to remove them from the class roster.

---

**Q: Can the student see I reverted their approval?**
A: The student isn't automatically notified. You may want to contact them to explain.

---

**Q: What if I keep reverting and re-approving?**
A: That's fine! Each action is logged, so admins can see the history.

---

**Q: Can I revert a rejection?**
A: No. Rejections are final. You'd need to create a new program selection for the student.

---

**Q: Does reverting cost the student anything?**
A: No. It just sets them back to pending. They can be approved again immediately.

---

## Quick Comparison: All Approval Actions

```
┌──────────────────────────────────────────────────────────┐
│           APPROVE              REVERT             REJECT │
├──────────────────────────────────────────────────────────┤
│ Status:    Pending → Approved  Approved → Pending  → Rejected
│                                                           │
│ Section:   Assigned Auto       Auto-Assigned → None   None
│                                                           │
│ Requires:  Optinal notes       Confirm revert    Reason Required
│            Admin approval      (reversible)       (final)
│                                                           │
│ Reversible: No (need revert)   Yes (button)      No
│                                                           │
│ Button:    Green ✓             Yellow ↶          Red ✗
│                                                           │
│ Use When:  Ready to enroll     Oops!             Doesn't
│            All docs OK         Made mistake      qualify
└──────────────────────────────────────────────────────────┘
```

## Summary

**To undo an accidental approval:**

1. Open student's page
2. System shows yellow "Revert to Pending" button
3. Click button
4. Confirm you want to revert
5. Status changes to Pending, section removed
6. Action is logged in audit trail
7. Student is back in the pending queue

Simple as that! 🔄
