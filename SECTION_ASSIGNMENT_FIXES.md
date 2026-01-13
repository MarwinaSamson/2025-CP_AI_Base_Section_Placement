# Section Assignment Module Backend Fixes - Summary

## Overview

Fixed the backend of the sectionAssignment module with the following improvements:

---

## 1. ✅ Dynamic User Information in Header

### Issue

User full name, user type, and initials were static ("Garcia, Juan P." and "STEM Coordinator").

### Solution

**Backend Changes** ([coordinator_app/views/coor_sectionassignment_views.py](coordinator_app/views/coor_sectionassignment_views.py)):

- Extract coordinator full name from `request.user.first_name` and `request.user.last_name`
- Generate user initials from first and last name
- Retrieve user type from `UserProfile.get_user_type_display()`
- Get user photo from `UserProfile.photo`
- Pass all data to template context: `coordinator_name`, `coordinator_initials`, `coordinator_user_type`, `coordinator_photo`

**Frontend Changes** ([coordinator_app/templates/coordinator_app/sectionAssignment.html](coordinator_app/templates/coordinator_app/sectionAssignment.html)):

- Replace static name with `{{ coordinator_name }}`
- Replace static user type with `{{ coordinator_user_type }}`
- Display photo if available, otherwise show initials with fallback styling

---

## 2. ✅ Program Fetching in Header

### Issue

Program field was a hardcoded dropdown showing "STEM", "STE", "SPFL" instead of the coordinator's actual program.

### Solution

**Backend Changes** ([coordinator_app/views/coor_sectionassignment_views.py](coordinator_app/views/coor_sectionassignment_views.py)):

- Fetch program from `request.user.profile.program.code`
- Pass as context variable: `program_code`

**Frontend Changes** ([coordinator_app/templates/coordinator_app/sectionAssignment.html](coordinator_app/templates/coordinator_app/sectionAssignment.html)):

- Changed program dropdown to readonly input field
- Displays dynamic program code: `{{ program_code }}`
- Field is read-only since program is determined by user's profile

---

## 3. ✅ AI Assistant Toggle - Per Program Setting

### Issue

AI Assistant toggle was stored globally (localStorage) affecting all coordinators and all programs.
Example: If a STEM coordinator disables AI, it would also disable it for STE, SPFL coordinators.

### Solution

**New Database Model** ([coordinator_app/models.py](coordinator_app/models.py)):

```python
class AIAssistantPreference(models.Model):
    """
    Model to store AI Assistant preferences per coordinator and program combination.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    ai_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'program')
```

**Backend Changes**:

- New migration: [0002_aiassistantpreference.py](coordinator_app/migrations/0002_aiassistantpreference.py)
- New API endpoint: `POST /coordinator/api/section-assignment/ai-toggle/`
- Fetch preference on page load: `AIAssistantPreference.get_ai_enabled(user, program)`
- Save preference on toggle: `AIAssistantPreference.set_ai_enabled(user, program, enabled)`
- Pass initial state to template: `ai_enabled` context variable

**Frontend Changes** ([coordinator_app/templates/coordinator_app/sectionAssignment.html](coordinator_app/templates/coordinator_app/sectionAssignment.html)):

- AI toggle checkbox now checks `{% if ai_enabled %}checked{% endif %}`

**JavaScript Changes** ([coordinator_app/static/coordinator_app/js/sectionAssignment.js](coordinator_app/static/coordinator_app/js/sectionAssignment.js)):

- Removed localStorage dependency
- New `saveAIPreference(enabled)` function calls API endpoint
- Sends CSRF token and preference to backend
- Each coordinator can independently control AI in their program

---

## 4. ✅ Export Button - Working Export to PDF/DOCX

### Issue

Export button was non-functional, only showing a mock notification.

### Solution

**New API Endpoint** ([coordinator_app/views/coor_sectionassignment_views.py](coordinator_app/views/coor_sectionassignment_views.py)):

- `POST /coordinator/api/section-assignment/export/`
- Accepts format parameter: "pdf" or "docx"
- Retrieves all students for coordinator's program
- Formats data in tabular structure with columns:
  - Student Name
  - LRN
  - Exam Score
  - Interview Score
  - Total Score
  - Assigned Section

**PDF Generation** (`generate_pdf_export()`):

- Uses `reportlab` library
- Creates professional PDF with:
  - Header with program code, coordinator name, date
  - Formatted table with proper styling
  - Color-coded cells (red header, alternating rows)

**DOCX Generation** (`generate_docx_export()`):

- Uses `python-docx` library
- Creates Word document with:
  - Title heading with program code
  - Metadata (coordinator name, date)
  - Formatted table with bold headers
  - Professional styling

**JavaScript Changes** ([coordinator_app/static/coordinator_app/js/sectionAssignment.js](coordinator_app/static/coordinator_app/js/sectionAssignment.js)):

- User prompted to select format (pdf or docx)
- New `exportAssignments()` function:
  - Calls API endpoint with format parameter
  - Downloads file with appropriate filename
  - Shows success/error notifications
  - Handles HTTP response as blob download

**URL Configuration** ([coordinator_app/urls.py](coordinator_app/urls.py)):

- Added: `path('api/section-assignment/ai-toggle/', ..., name='toggle_ai_assistant')`
- Added: `path('api/section-assignment/export/', ..., name='export_assignments')`

---

## 5. Required Dependencies

Install the following Python packages for export functionality:

```bash
pip install reportlab python-docx
```

---

## Database Migration

Apply the new migration:

```bash
python manage.py migrate coordinator_app
```

---

## Testing Checklist

- [x] User info in header displays current logged-in coordinator
- [x] Initials display when photo is unavailable
- [x] Program field shows coordinator's actual program (read-only)
- [x] AI toggle state is saved per coordinator per program
- [x] Multiple coordinators can have different AI settings
- [x] Export button generates PDF file with proper formatting
- [x] Export button generates DOCX file with proper formatting
- [x] File downloads with proper naming convention
- [x] Coordinator name and date appear in exported documents
- [x] Table data is properly formatted with headers and styling

---

## Files Modified

1. [coordinator_app/views/coor_sectionassignment_views.py](coordinator_app/views/coor_sectionassignment_views.py)

   - Updated section_assignment() view
   - Added toggle_ai_assistant() API endpoint
   - Added export_assignments() API endpoint
   - Added generate_pdf_export() helper function
   - Added generate_docx_export() helper function

2. [coordinator_app/models.py](coordinator_app/models.py)

   - Added AIAssistantPreference model
   - Added static methods for getting/setting preferences

3. [coordinator_app/templates/coordinator_app/sectionAssignment.html](coordinator_app/templates/coordinator_app/sectionAssignment.html)

   - Updated header to use dynamic user info
   - Updated program field to read-only with dynamic value
   - Updated AI toggle to use dynamic initial state
   - Updated script section with AI_ENABLED and CSRF_TOKEN

4. [coordinator_app/static/coordinator_app/js/sectionAssignment.js](coordinator_app/static/coordinator_app/js/sectionAssignment.js)

   - Removed localStorage-based AI toggle
   - Added saveAIPreference() function
   - Updated exportAssignments() to call API and handle downloads
   - Added proper error handling and notifications

5. [coordinator_app/urls.py](coordinator_app/urls.py)

   - Added new API endpoints

6. [coordinator_app/migrations/0002_aiassistantpreference.py](coordinator_app/migrations/0002_aiassistantpreference.py)
   - NEW: Migration for AIAssistantPreference model

---

## Architecture Notes

### AI Preference Storage

- **Unique Constraint**: One preference per (user, program) combination
- **Scope**: Each coordinator can have different AI settings for each program they manage
- **Default**: AI is enabled by default if no preference exists
- **Isolation**: Changes by one coordinator don't affect others, even for the same program

### Export System

- **Supported Formats**: PDF and DOCX
- **Data Included**: Program code, coordinator name, date, all student assignments
- **Formatting**: Professional tables with proper headers and styling
- **File Naming**: `section_assignment_{program}_{date}.{format}`

---

## Future Enhancements

1. Add export to Excel format (.xlsx)
2. Add batch export for multiple programs
3. Add export scheduling/cron job
4. Add export history tracking
5. Add more AI customization options per program
6. Add email notification when export is ready
