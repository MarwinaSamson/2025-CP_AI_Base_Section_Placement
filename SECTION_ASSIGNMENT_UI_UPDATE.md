# Section Assignment UI Update - Summary

## Overview

Updated the Section Assignment module in coordinator_app to change the table columns and layout when the AI Assistant is disabled.

## Changes Made

### 1. **HTML Template**

File: `coordinator_app/templates/coordinator_app/sectionAssignment.html`

#### Changes:

- **Modified Table Headers**: Added two separate header rows with IDs:

  - `tableHeaderAI` (id): Shows when AI is enabled (7 columns)

    - Student | LRN | Exam Score | Interview | AI Suggested | Manual Assign | Final Section

  - `tableHeaderDisabled` (id): Shows when AI is disabled (6 columns)
    - Name | LRN | Exam Score | Interview | Status | Action

### 2. **JavaScript Logic**

File: `coordinator_app/static/coordinator_app/js/sectionAssignment.js`

#### AI Toggle Enhancement:

- Modified the AI toggle event listener to reload table data when toggled
- Now calls `loadStudentsData()` and `initializeTableInteractions()` on toggle change

#### Updated `loadStudentsData()` Function:

- **Checks AI status** to determine table layout
- **Toggles visibility** of header rows based on `aiToggle.checked` state

  - AI Enabled: Shows AI Suggested, Manual Assign, and Final Section columns
  - AI Disabled: Shows Status (badge) and Action (with section selector + View button)

- **Two row formats**:

  **AI Enabled Row Layout:**

  ```
  Name | LRN | Exam Score | Interview | AI Suggested (badge) | Manual Assign (dropdown) | Final Section
  ```

  **AI Disabled Row Layout:**

  ```
  Name | LRN | Exam Score | Interview | Status Badge (Pending/Assigned) | Action (dropdown + View button)
  ```

#### Status Badge Implementation:

- **Pending**: Amber badge with clock icon `<i class="fas fa-clock"></i> Pending`
- **Assigned**: Green badge with check-circle icon `<i class="fas fa-check-circle"></i> Assigned`
- Status updates dynamically when section is selected/deselected

#### Action Column:

- Contains a **Section Selector Dropdown** with options for STEM-1, STEM-2, STEM-3, STEM-4
- Contains a **View Button** that displays student details (front-end ready, backend TODO)
- Similar styling to enrollment.html as reference

#### Updated `initializeTableInteractions()` Function:

- **AI Enabled**: Handles `.section-select` dropdown changes

  - Updates Final Section span when selection changes
  - Auto-suggests AI recommendation if user clears selection

- **AI Disabled**: Handles `.section-select-disabled` dropdown changes
  - Updates Status badge to "Assigned" (green) when section is selected
  - Reverts to "Pending" (amber) when selection is cleared
  - View button triggers `viewStudentDetails()` function

## UI Features

### Color Scheme:

- **Exam/Interview Scores**:

  - 90+: Green (`bg-green-100 text-green-800`)
  - 80-89: Red/Primary (`bg-red-100 text-primary`)
  - 70-79: Yellow (`bg-yellow-100 text-yellow-800`)
  - Below 70: Red (`bg-red-100 text-red-800`)

- **Status Badges**:

  - Pending: Amber (`bg-amber-100 text-amber-800`)
  - Assigned: Green (`bg-green-100 text-green-800`)

- **Action Buttons**:
  - Gradient primary color with hover effects
  - Icon + text label format

## How It Works

1. **Initial Load**: Page loads with AI Assistant **Enabled** by default

   - Shows 7-column layout with AI suggestions

2. **Toggle AI Off**: User clicks AI Assistant toggle

   - Header changes to 6-column layout (Status & Action)
   - Table rows regenerate with new format
   - Status badges show "Pending" by default
   - Users can assign sections via dropdown or click View to see details

3. **Toggle AI On**: User clicks AI Assistant toggle again
   - Returns to 7-column layout with AI suggestions
   - Table rows regenerate with original format

## Frontend Only

✅ No backend changes required yet
✅ Ready for backend integration when API endpoints are available

## Styling Notes

- Uses Tailwind CSS (already in project)
- Consistent with existing admin_app/enrollment.html styling
- Responsive design maintained
- Icon library: Font Awesome 6.0.0

## Next Steps (Backend Implementation)

- Connect `viewStudentDetails()` function to actual student detail page/modal
- API integration for saving section assignments
- Dynamic student data loading (replace sample data)
- Status update persistence
