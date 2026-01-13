# Complete Testing Guide - Section Assignment Module Fixes

## Pre-Requisites

- Python dependencies installed: `pip install reportlab python-docx`
- Database migrations applied: `python manage.py migrate coordinator_app`
- Django development server running

---

## Test Case 1: Dynamic User Header Information

### Objective

Verify that user information in the header is dynamically pulled from the database and displays correctly.

### Prerequisites

- User logged in with first_name, last_name populated
- User has a UserProfile with user_type and photo (or photo is optional)
- User has a program assigned in their profile

### Test Steps

1. Navigate to `/coordinator/section-assignment/`
2. Look at the top-right header section

### Expected Results

- ✅ User full name displays: "{First Name} {Last Name}"
- ✅ User type displays: "Coordinator" or admin type from UserProfile
- ✅ If photo exists: Photo image displays in circular container
- ✅ If photo doesn't exist: Initials (first letter of first name + first letter of last name) display in circular container with background color
- ✅ Format is: "FirstName LastName" (proper case)

### Test Data

- User: john_doe
- First Name: John
- Last Name: Doe
- Expected: "John Doe"
- Expected Initials: "JD" (if no photo)

---

## Test Case 2: Program Display in Header

### Objective

Verify that the program field displays the coordinator's actual program from the database.

### Prerequisites

- User logged in with a program assigned in UserProfile

### Test Steps

1. Navigate to `/coordinator/section-assignment/`
2. Look at the program filter field in the header

### Expected Results

- ✅ Program field shows user's program code (STEM, STE, SPFL, etc.)
- ✅ Program field is read-only (cannot be changed)
- ✅ Program field reflects the UserProfile.program.code value
- ✅ Different coordinators see their own program

### Test Data

- Coordinator 1: User profile → program = STEM → Display: "STEM"
- Coordinator 2: User profile → program = STE → Display: "STE"

---

## Test Case 3: AI Assistant Toggle - Per Program Isolation

### Objective

Verify that AI Assistant setting is stored per coordinator and program, not globally.

### Setup

Create test users with different programs:

- User 1: coordinator_stem (program: STEM)
- User 2: coordinator_ste (program: STE)

### Test Sequence A: Single Coordinator, Single Program

1. Log in as coordinator_stem
2. Navigate to `/coordinator/section-assignment/`
3. Verify AI toggle is checked (default enabled)
4. Toggle AI Assistant OFF
5. Click refresh or navigate away and back
6. ✅ AI toggle should remain OFF

### Test Sequence B: Different Coordinators, Same Program (if applicable)

1. Create two users with same program: STEM
2. Log in as user1 (STEM program)
3. Toggle AI OFF
4. Log out
5. Log in as user2 (STEM program)
6. ✅ AI toggle should be ON (independent settings)
7. Log back in as user1 (STEM program)
8. ✅ AI toggle should still be OFF for user1

### Test Sequence C: Same Coordinator, Different Programs (if applicable)

1. Update coordinator_stem to also have access to STE
2. Log in as coordinator_stem
3. Switch to STEM program view
4. Toggle AI OFF
5. Switch to STE program view
6. Toggle AI ON
7. Switch back to STEM program
8. ✅ AI should still be OFF (per-program setting)

### Expected Results

- ✅ AI preference saved in database (AIAssistantPreference model)
- ✅ Each coordinator has independent settings per program
- ✅ Toggle state persists across page refreshes
- ✅ No interference between different coordinators
- ✅ Browser console shows successful API calls

### Database Verification

```sql
SELECT user_id, program_id, ai_enabled FROM ai_assistant_preference;
-- Should show (1, STEM, False) for coordinator 1
-- Should show (2, STE, True) for coordinator 2
```

---

## Test Case 4: Export Functionality - PDF Format

### Objective

Verify that export to PDF works correctly with proper formatting.

### Prerequisites

- At least one student assigned to the coordinator's program
- reportlab library installed

### Test Steps

1. Navigate to `/coordinator/section-assignment/`
2. Click "Export" button
3. Prompt appears asking for format
4. Enter "pdf"
5. File downloads automatically

### Expected Results

- ✅ File downloads with name: `section_assignment_{PROGRAM}_{YYYYMMDD}.pdf`
- ✅ PDF opens correctly in PDF viewer
- ✅ PDF contains:
  - Title: "Section Assignment Report - {PROGRAM}"
  - Coordinator info: "Coordinator: {Name}"
  - Date: "Date: {Month} {Day}, {Year}"
  - Table with columns:
    - Student Name
    - LRN
    - Exam Score
    - Interview Score
    - Total Score
    - Assigned Section
- ✅ Table has styling:
  - Red header with white text
  - Centered content
  - Alternating row colors (white and light beige)
  - Grid borders

### Test Data

- Program: STEM
- Expected filename: `section_assignment_STEM_20260113.pdf`
- Coordinator: "John Doe"
- Students: 3-5 records

---

## Test Case 5: Export Functionality - DOCX Format

### Objective

Verify that export to DOCX works correctly with proper formatting.

### Prerequisites

- At least one student assigned to the coordinator's program
- python-docx library installed

### Test Steps

1. Navigate to `/coordinator/section-assignment/`
2. Click "Export" button
3. Prompt appears asking for format
4. Enter "docx"
5. File downloads automatically

### Expected Results

- ✅ File downloads with name: `section_assignment_{PROGRAM}_{YYYYMMDD}.docx`
- ✅ File opens correctly in Microsoft Word or compatible editor
- ✅ Document contains:
  - Title heading: "Section Assignment Report - {PROGRAM}"
  - Coordinator info: "Coordinator: {Name}"
  - Date: "Date: {Month} {Day}, {Year}"
  - Table with columns:
    - Student Name
    - LRN
    - Exam Score
    - Interview Score
    - Total Score
    - Assigned Section
- ✅ Table has styling:
  - Bold header row
  - Proper cell alignment
  - Professional appearance
  - Editable in Word

### Test Data

- Program: STEM
- Expected filename: `section_assignment_STEM_20260113.docx`

---

## Test Case 6: Export Error Handling

### Objective

Verify proper error handling for export functionality.

### Test Sequence A: Invalid Format

1. Click Export button
2. Enter "xlsx" (not supported)
3. ✅ Error notification appears: "Invalid format. Use 'pdf' or 'docx'"

### Test Sequence B: Missing Library

1. Temporarily uninstall reportlab: `pip uninstall reportlab`
2. Click Export and choose "pdf"
3. ✅ Error notification appears: "PDF generation library not installed..."
4. Reinstall: `pip install reportlab`

### Test Sequence C: Export Cancelled

1. Click Export button
2. Cancel the prompt
3. ✅ Nothing happens, no errors

---

## Test Case 7: AI Toggle API Error Handling

### Objective

Verify that API errors are handled gracefully.

### Test Steps

1. Open browser DevTools (F12)
2. Go to Network tab
3. Navigate to section-assignment page
4. Toggle AI Assistant OFF
5. Check network tab for POST to `/coordinator/api/section-assignment/ai-toggle/`

### Expected Results

- ✅ Request sent with correct headers (X-CSRFToken)
- ✅ Response status 200 with success JSON
- ✅ Response contains: `{"success": true, "ai_enabled": false, ...}`
- ✅ Success notification appears on page

---

## Test Case 8: Data Accuracy in Export

### Objective

Verify that exported data matches the database records.

### Test Steps

1. Note student data visible on page (names, LRN, scores)
2. Export to PDF/DOCX
3. Open exported file
4. Compare data with page display

### Expected Results

- ✅ All student names match exactly
- ✅ All LRN values match exactly
- ✅ All exam scores match exactly
- ✅ All interview scores match exactly
- ✅ Total scores are calculated correctly (exam + interview)
- ✅ Assigned sections match page display

---

## Test Case 9: Integration Test - Complete Workflow

### Objective

Test the complete workflow as a coordinator would use it.

### Steps

1. Log in as coordinator with STEM program
2. Verify header shows your name and STEM program
3. Toggle AI Assistant OFF
4. Refresh page - verify it's still OFF
5. Perform some section assignments (manual or AI)
6. Click Export button
7. Choose "pdf"
8. Save file to desktop
9. Open file and verify all data
10. Export again as "docx"
11. Compare both files for consistency

### Expected Results

- ✅ All dynamic information displays correctly
- ✅ AI setting persists across refreshes
- ✅ Both PDF and DOCX exports contain same data
- ✅ Files are properly formatted
- ✅ No errors occur during workflow

---

## Automated Test Script (Optional)

```python
# tests.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from admin_app.models import UserProfile, Program
from coordinator_app.models import AIAssistantPreference
import json

class SectionAssignmentTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.program = Program.objects.create(code='STEM', name='STEM Program')
        self.user = User.objects.create_user(
            username='test_coordinator',
            first_name='John',
            last_name='Doe',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            user_type='coordinator',
            program=self.program
        )

    def test_dynamic_user_info(self):
        self.client.login(username='test_coordinator', password='testpass123')
        response = self.client.get('/coordinator/section-assignment/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('John Doe', response.content.decode())
        self.assertIn('STEM', response.content.decode())

    def test_ai_toggle_api(self):
        self.client.login(username='test_coordinator', password='testpass123')
        response = self.client.post(
            '/coordinator/api/section-assignment/ai-toggle/',
            data=json.dumps({'enabled': False}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertFalse(data['ai_enabled'])

    def test_ai_preference_persistence(self):
        AIAssistantPreference.set_ai_enabled(self.user, self.program, False)
        result = AIAssistantPreference.get_ai_enabled(self.user, self.program)
        self.assertFalse(result)
```

---

## Troubleshooting Matrix

| Issue                    | Symptom                        | Solution                                                |
| ------------------------ | ------------------------------ | ------------------------------------------------------- |
| Header shows static name | "Garcia, Juan P." appears      | Check user.first_name, user.last_name in database       |
| AI toggle not persisting | Resets after refresh           | Check database migration applied, check browser console |
| Export shows error       | "Export library not installed" | Install: `pip install reportlab python-docx`            |
| Program shows dropdown   | Can select multiple programs   | Check template is using readonly input, not select      |
| API returns CSRF error   | 403 Forbidden on toggle        | Ensure CSRF token passed in header                      |
| Export returns 404       | Cannot find endpoint           | Check URLs.py has both API routes registered            |
| Initials not showing     | Blank circle when no photo     | Check template has fallback for initials                |

---

## Performance Considerations

- AI preference is cached during request
- Export query uses select_related for optimization
- Database indexes on (user, program) for fast lookups
- Typical export time for 100 students: 1-3 seconds

---

## Security Notes

✅ CSRF protection on all POST endpoints
✅ Login required on all views
✅ User can only see their own program's data
✅ AI preference scoped to user and program
✅ File downloads include proper headers
