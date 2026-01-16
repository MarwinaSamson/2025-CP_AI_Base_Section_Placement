# Backend Integration - Quick Reference Guide

## File Changes Overview

### Modified Files

1. **coordinator_app/static/coordinator_app/js/sectionAssignment.js**

   - Removed all mock data constants
   - Integrated backend-injected `window.STUDENTS_DATA` and `window.SECTIONS_DATA`
   - Added backend API calls for approval and assignment
   - Updated AI mode filtering

2. **coordinator_app/templates/coordinator_app/sectionAssignment.html**
   - Added `{% csrf_token %}` for CSRF protection

---

## Key Functions

### Data Loading

```javascript
// Manual mode - loads pending students
loadManualModeData();

// AI mode - loads auto-approved students
loadAIModeData();
```

### Student Actions

```javascript
// Approve student and assign section
approveStudent(lrn, sectionId);

// Delegate to approval (same endpoint)
assignSection(lrn, sectionId);
```

### Utilities

```javascript
// Get section name from section ID
getSectionNameById(sectionId);

// View student details modal
viewStudentDetails(lrn);
```

---

## Backend Expectations

### Required Injections in Template Context

```python
# In Django view
context = {
    'students_json': json.dumps(students_payload),
    'sections_json': json.dumps(sections_payload),
    'program_code': program.code,
    ...
}
```

### Student Object Fields

```javascript
{
    lrn: "2023-0001",           // Must match API endpoint parameter
    name: "Student Name",
    admin_approved: true/false,
    auto_approved_by_ai: true/false,    // For AI mode
    finalSection: 1,                     // Section ID
    approved_date: "ISO-8601 datetime"  // Optional
}
```

### Section Object Fields

```javascript
{
    id: 1,
    name: "SEC-A-10",
    current: 35,
    capacity: 40
}
```

---

## API Call Example

```javascript
// Frontend makes this call
POST /coordinator/api/student/2023-0001/approve-and-place/
Headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': 'token-value'
}
Body: {
    section_id: 5
}
```

---

## Data Flow Diagram

```
Page Load
    ↓
Django View builds students_payload & sections_payload
    ↓
Template receives context with JSON
    ↓
Script injection: window.STUDENTS_DATA = [...], window.SECTIONS_DATA = [...]
    ↓
sectionAssignment.js DOMContentLoaded
    ↓
loadManualModeData() or loadAIModeData()
    ↓
Table Rendered with Backend Data
    ↓
User Action → API Call → Backend Processing → Response → UI Update
```

---

## Common Issues & Solutions

| Issue                                      | Cause                           | Solution                                           |
| ------------------------------------------ | ------------------------------- | -------------------------------------------------- |
| Table shows "No enrollment requests found" | `window.STUDENTS_DATA` is empty | Check backend payload generation                   |
| Section dropdown is empty                  | `window.SECTIONS_DATA` is empty | Verify sections exist in backend                   |
| CSRF token error on approve                | Missing CSRF token              | Ensure `{% csrf_token %}` in template              |
| Student not found after approve            | Using wrong identifier          | Use `lrn` not `id` in API endpoint                 |
| Approved students disappear after reload   | Data not persisted in backend   | Check `approve_and_place_student()` implementation |

---

## Testing Endpoints

### Via cURL

```bash
# Test approval endpoint
curl -X POST http://localhost:8000/coordinator/api/student/2023-0001/approve-and-place/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{"section_id": 5}'
```

### Via Browser Console

```javascript
// Check injected data
console.log("Students:", window.STUDENTS_DATA);
console.log("Sections:", window.SECTIONS_DATA);
console.log("Program Code:", window.PROGRAM_CODE);

// Test API call
fetch("/coordinator/api/student/2023-0001/approve-and-place/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
  },
  body: JSON.stringify({ section_id: 5 }),
})
  .then((r) => r.json())
  .then(console.log);
```

---

## Important Notes

⚠️ **LRN vs ID:** The API endpoint uses `lrn` (Student LRN), not database `id`

⚠️ **Section Filtering:** AI mode filters for `admin_approved=true AND (auto_approved_by_ai OR auto_assigned_by_ai)`

⚠️ **CSRF Required:** All POST requests must include CSRF token from Django

⚠️ **Page Reload:** After successful approval, the page reloads to fetch fresh data

⚠️ **Error Handling:** All API errors show user-friendly notifications

---

## Debugging Tips

1. **Check Browser Console** for JavaScript errors
2. **Network Tab** to inspect API requests/responses
3. **Element Inspector** to verify CSRF token presence
4. **Application/Storage** to check localStorage for mode preference
5. **Django Logs** to see backend validation/errors

---

## Version Info

- **Integration Date:** [Current Date]
- **Backend API Version:** v1
- **Data Format:** JSON
- **CSRF Protection:** Django Middleware
- **Framework:** Django + Vanilla JavaScript
