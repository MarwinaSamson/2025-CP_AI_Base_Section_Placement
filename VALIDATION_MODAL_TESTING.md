# Complete Validation Modal Testing Instructions

## Quick Start Test

### Prerequisites

1. Django server running: `python manage.py runserver`
2. At least one student with incomplete requirements
3. At least one section created for the student's program
4. Browser DevTools ready (F12)

### 5-Minute Test

**Step 1: Navigate to Student Edit**

```
URL: http://localhost:8000/coordinator/student-edit/[STUDENT_LRN]/
Example: http://localhost:8000/coordinator/student-edit/981234567898/
```

**Step 2: Verify Student Data Loads**

- Check that student name appears in header
- Check that requirements list shows
- Check section for requirements with empty status (missing)

**Step 3: Set Up for Approval**

1. Scroll to "Enrollment Placement" section (red header)
2. Select a Program (if not already selected)
3. Select a Section (should show capacity)
4. Scroll to bottom, locate "Save Changes" button

**Step 4: Trigger Validation Modal**

1. In the form, find the "Approved" dropdown near bottom
2. Click dropdown and select "Approved"
3. Modal should appear automatically

**Step 5: Verify Modal Content**

```
Modal Should Show:
✓ Student name in header (red gradient bar)
✓ Warning icon (yellow triangle)
✓ Title: "Missing Requirements"
✓ Student display: "Student: [Full Name]"
✓ List of missing requirements
✓ Each item shows red X icon
✓ Warning box with info message
✓ Two buttons: "Back" and "Approve Anyway"
```

**Step 6: Test Back Button**

1. Click "Back" button
2. Modal should close
3. Form should still have all your selections
4. Try again to confirm modal reappears

**Step 7: Test Approve Anyway**

1. Click "Approve Anyway" button
2. Modal should close
3. Loading spinner should appear on Save button
4. Success message should appear
5. Browser should redirect to /coordinator/sections/

## Detailed Test Scenarios

### Test Case 1: Missing Requirements Detection

**Objective**: Verify modal shows all missing mandatory requirements

**Setup**:

- Student with 3 mandatory requirements
- Only 1 requirement has "approved" status (checkbox checked + disabled)
- 2 requirements have no status or "pending" status

**Steps**:

1. Load student edit page
2. Scroll to Requirements section
3. Note which requirements have status badges
4. Select program and section
5. Choose "Approved" from admin dropdown

**Expected Result**:

- Modal appears
- Lists exactly 2 missing requirements
- Does not list the approved requirement
- Student name shows correctly

**Pass Criteria**: ✅ Modal shows only the 2 non-approved mandatory requirements

---

### Test Case 2: No Missing Requirements

**Objective**: Verify normal dialog appears when all requirements met

**Setup**:

- Student with 2 mandatory requirements
- Both have "approved" status (checked and disabled)

**Steps**:

1. Load student edit page
2. Scroll to Requirements section
3. Verify all have green badges with "Approved"
4. Select program and section
5. Choose "Approved" from admin dropdown

**Expected Result**:

- Modal does NOT appear
- Normal browser confirmation dialog appears
- Dialog shows: "You are about to APPROVE this enrollment..."
- After confirming: API call made, redirect to /coordinator/sections/

**Pass Criteria**: ✅ Modal skipped, normal flow proceeds

---

### Test Case 3: Optional Requirements Ignored

**Objective**: Verify optional requirements are not flagged as missing

**Setup**:

- Student with 2 mandatory + 2 optional requirements
- Mandatory: 1 approved, 1 not approved
- Optional: both not approved

**Steps**:

1. Load student edit page
2. Check Requirements section
3. Verify optional items show "(Optional)" text
4. Trigger approval flow

**Expected Result**:

- Modal appears
- Lists only 1 missing requirement (the mandatory one)
- Optional requirements not listed
- Can approve with optional documents missing

**Pass Criteria**: ✅ Only mandatory requirements are validated

---

### Test Case 4: Form State Preservation

**Objective**: Verify form data is preserved after modal interaction

**Setup**:

- Filled form with student data
- Missing requirements
- Selected program and section

**Steps**:

1. Fill in additional fields if needed
2. Trigger approval to show modal
3. Click "Back" button
4. Check all form fields

**Expected Result**:

- All previously entered data still there
- Program selection preserved
- Section selection preserved
- Can modify and try again
- Can choose different action from dropdown

**Pass Criteria**: ✅ All form state preserved after modal

---

### Test Case 5: Modal Accessibility

**Objective**: Verify modal is keyboard and screen-reader accessible

**Steps**:

1. Trigger modal
2. Tab through buttons (should focus on them)
3. Press Enter on "Back" button (should close)
4. Trigger modal again
5. Press Tab to "Approve Anyway" button
6. Press Enter (should approve)

**Expected Result**:

- All buttons are keyboard focusable
- Can navigate with Tab key
- Can activate with Enter key
- Focus order is logical (Back first, then Approve Anyway)

**Pass Criteria**: ✅ Full keyboard navigation works

---

### Test Case 6: Error Handling

**Objective**: Verify graceful error handling

**Steps**:

1. Open browser DevTools (F12)
2. Go to Network tab
3. Set network to "Offline" mode
4. Trigger approval flow with modal
5. Click "Approve Anyway"

**Expected Result**:

- Error notification appears: "Failed to approve student..."
- Form remains intact
- Can retry when connection restored
- No data corruption

**Pass Criteria**: ✅ Error handled gracefully

---

### Test Case 7: Multiple Missing Requirements

**Objective**: Verify modal properly displays many missing requirements

**Setup**:

- Student with 5+ missing mandatory requirements

**Steps**:

1. Load student
2. Trigger approval

**Expected Result**:

- Modal displays all missing requirements
- List is scrollable if exceeds max-height
- All requirements visible (scroll if needed)
- Modal remains properly sized

**Pass Criteria**: ✅ All requirements visible with scrolling

---

## Console Testing

### Test in Browser DevTools Console

```javascript
// 1. Manually check requirements
document.querySelectorAll(".requirement-checkbox").forEach((cb) => {
  console.log("ID:", cb.id, "Checked:", cb.checked, "Disabled:", cb.disabled);
});

// 2. Test requirement detection function
const missing = checkMissingRequirements("Test Student");
console.log("Missing Requirements:", missing);

// 3. Manually show modal
showMissingRequirementsModal(
  ["Birth Certificate", "Medical Form"],
  "Test Student"
);

// 4. Check pendingApprovalData
console.log("Pending Data:", pendingApprovalData);

// 5. Close modal
closeMissingRequirementsModal();

// 6. Check API connectivity
fetch("/coordinator/api/student/").then((r) =>
  console.log("API Status:", r.status)
);
```

## Common Issues & Solutions

### Issue: Modal doesn't appear when approving

**Solution**:

1. Check browser console for JavaScript errors
2. Verify requirement checkboxes have class `requirement-checkbox`
3. Check that requirements exist in DOM
4. Try: `document.querySelectorAll('.requirement-checkbox').length`

### Issue: Modal shows but doesn't list requirements

**Solution**:

1. Check requirement labels exist
2. Verify label `for` attribute matches checkbox `id`
3. Try in console: `document.querySelectorAll('label[for^="req_"]')`

### Issue: "Approve Anyway" button doesn't work

**Solution**:

1. Check browser console for JavaScript errors
2. Verify pendingApprovalData is set
3. Check network tab - is API request being made?
4. Look for error response in Network tab

### Issue: Redirect not working after approval

**Solution**:

1. Check that API returns `success: true`
2. Verify browser allows redirects
3. Check /coordinator/sections/ exists
4. Try manual navigation in new tab

## Performance Monitoring

### Check Modal Performance

```javascript
// Time modal rendering
console.time("modal-render");
showMissingRequirementsModal(["Test"], "Student");
console.timeEnd("modal-render");

// Should be < 50ms for good UX
```

## Browser Compatibility Checklist

- [ ] Chrome/Chromium: Full test
- [ ] Firefox: Test modal animation, buttons
- [ ] Safari: Test backdrop blur, responsive
- [ ] Edge: Test form submission flow
- [ ] Mobile Safari: Test touch, responsive layout
- [ ] Chrome Mobile: Test full flow on phone

## Visual Regression Test

**Before Approval Modal Work**:

- Screenshot normal approval flow
- Screenshot with all requirements met

**After Implementation**:

- Screenshot with missing requirements (modal visible)
- Screenshot with "Approve Anyway" clicked
- Screenshot on mobile (should be responsive)

Compare for:

- ✅ No broken layout
- ✅ Colors matching theme
- ✅ Text readable
- ✅ Buttons clickable

## Load Testing (Optional)

```python
# In Django shell: python manage.py shell
from coordinator_app.models import Student, DocumentRequirement
from enrollment_app.models import ProgramSelection

# Check students with incomplete requirements
incomplete = []
for student in Student.objects.all()[:10]:
    ps = ProgramSelection.objects.filter(student=student).first()
    if ps:
        incomplete.append(student.lrn)

print(f"Students for testing: {incomplete}")
```

## Automated Test Scenario

**Create a test student with known state**:

1. Create student with all data filled
2. Create 3 document requirements: Birth Cert (mandatory), ID (mandatory), Photo (optional)
3. Create 1 submission with "pending" status
4. Create 1 submission with "approved" status
5. Leave 1 requirement with no submission
6. Expected: Modal should show 1 missing (the one with no submission)

## Sign-Off Checklist

- [ ] Modal appears when requirements missing
- [ ] Modal shows correct student name
- [ ] Modal lists all missing mandatory requirements
- [ ] Modal doesn't list optional requirements
- [ ] Modal doesn't list approved requirements
- [ ] "Back" button closes modal and preserves form
- [ ] "Approve Anyway" button proceeds with approval
- [ ] Success message shown after approval
- [ ] Redirect to /coordinator/sections/ works
- [ ] All requirements met = normal dialog appears
- [ ] No console JavaScript errors
- [ ] Form state preserved after interactions
- [ ] Mobile responsive design works
- [ ] Keyboard navigation works

---

**Test Date**: ******\_******
**Tested By**: ******\_******
**Results**: ✅ PASS / ❌ FAIL
**Notes**: ****************\_****************
