# Admin Dashboard Backend Implementation

## Overview

This implementation provides a complete backend system for the admin dashboard with the following features:

1. **New Student Notifications** - Displays new enrolled students grouped by program
2. **User Header Information** - Shows user fullname, role, school year, and photo/initials
3. **Dashboard Statistics** - Total teachers, students, programs, and sections
4. **Programs Overview** - Detailed table of all programs with enrollment metrics
5. **Dynamic Data Loading** - All data fetched from backend APIs

---

## Backend Views (`admin_app/views/dashboard_views.py`)

### 1. **dashboard(request)**

Main dashboard view that renders the template with context data.

**Features:**

- Fetches active school year
- Loads user profile information
- Returns template with context

**Context Variables:**

- `user`: Current authenticated user
- `user_profile`: UserProfile object with program, position, department
- `active_school_year`: Currently active SchoolYear object

---

### 2. **dashboard_header_data(request)**

API endpoint for header information.

**Endpoint:** `/admin/api/dashboard/header/`

**Returns (JSON):**

```json
{
  "school_year": "2025-2026",
  "full_name": "John Doe",
  "role": "Admin",
  "initials": "JD",
  "photo_url": "/media/user_profiles/john_doe.jpg",
  "program": "STE"
}
```

**Features:**

- Fetches active school year from SchoolYear.get_active_school_year()
- Gets user's full name from User model (first_name + last_name)
- Calculates initials for avatar fallback
- Returns role from UserProfile (Admin/Coordinator)
- Returns photo URL if available (uses new photo field)
- Returns user's assigned program

---

### 3. **dashboard_statistics(request)**

API endpoint for overall statistics.

**Endpoint:** `/admin/api/dashboard/statistics/`

**Returns (JSON):**

```json
{
  "total_teachers": 52,
  "total_students": 1450,
  "total_programs": 7,
  "total_sections": 42,
  "grade_breakdown": {
    "grade_7": 362,
    "grade_8": 362,
    "grade_9": 362,
    "grade_10": 364
  }
}
```

**Features:**

- Counts active teachers (is_active=True)
- Counts enrolled students for active school year (status: submitted, under_review, approved)
- Counts active programs
- Counts sections in active school year
- Provides grade-level student distribution

---

### 4. **dashboard_notifications(request)**

API endpoint for new enrollment notifications grouped by program.

**Endpoint:** `/admin/api/dashboard/notifications/`

**Returns (JSON):**

```json
{
  "total_count": 45,
  "notifications": [
    {
      "program_code": "HETERO",
      "program_name": "Heterogeneous Class",
      "icon": "fas fa-users",
      "count": 25,
      "message": "25 new HETERO applications pending review",
      "students": [
        {
          "lrn": "123456789012",
          "name": "John Smith",
          "created_at": "Jan 05, 2026 02:30 PM",
          "time_ago": "2 hours ago"
        }
      ]
    }
  ]
}
```

**Features:**

- Groups new students (status='submitted') by program
- Fetches student details (LRN, full name)
- Calculates human-readable time (e.g., "2 hours ago", "Just now")
- Sorts by count (highest priority first)
- Limits to 5 most recent students per program
- Maps icons for each program type

**Program Icons:**

- STE: `fas fa-flask`
- SPFL: `fas fa-language`
- SPTVE: `fas fa-tools`
- OHSP: `fas fa-laptop-house`
- SNED: `fas fa-universal-access`
- TOP 5: `fas fa-trophy`
- HETERO: `fas fa-users`

---

### 5. **dashboard_programs_overview(request)**

API endpoint for programs overview table data.

**Endpoint:** `/admin/api/dashboard/programs/`

**Returns (JSON):**

```json
{
  "programs": [
    {
      "code": "HETERO",
      "name": "Heterogeneous Class",
      "status": "active",
      "total_applicants": 350,
      "approved": 305,
      "pending": 35,
      "rejected": 10,
      "capacity": 480,
      "sections": 12,
      "acceptance_rate": 96.8,
      "trend": "up",
      "trend_value": 15
    }
  ],
  "summary": {
    "total_approved": 1280,
    "total_pending": 105,
    "total_rejected": 45,
    "overall_acceptance_rate": 96.5
  }
}
```

**Features:**

- Lists all active programs with detailed statistics
- Counts approved, pending, rejected students per program
- Calculates acceptance rate
- Provides section count and total capacity
- Returns trend direction (up/stable/down)
- Calculates overall summary metrics

---

### 6. **get_time_ago(dt)**

Helper function to convert datetime to human-readable format.

**Examples:**

- "Just now" - less than 1 minute
- "5 minutes ago"
- "2 hours ago"
- "3 days ago"
- "2 weeks ago"
- "1 month ago"

---

## URL Configuration (`admin_app/urls.py`)

New API endpoints added:

```python
# Dashboard API Endpoints
path('api/dashboard/header/', dashboard_views.dashboard_header_data, name='api_dashboard_header'),
path('api/dashboard/statistics/', dashboard_views.dashboard_statistics, name='api_dashboard_statistics'),
path('api/dashboard/notifications/', dashboard_views.dashboard_notifications, name='api_dashboard_notifications'),
path('api/dashboard/programs/', dashboard_views.dashboard_programs_overview, name='api_dashboard_programs'),
```

---

## Frontend Implementation (`admin_app/static/admin_app/js/dashboard-api.js`)

### Main Functions

#### **initializeDashboard()**

Initializes the entire dashboard on page load.

Calls in order:

1. `updateDashboardDate()` - Sets current date
2. `loadHeaderData()` - Loads user info and school year
3. `loadStatistics()` - Loads teacher/student/program counts
4. `loadNotifications()` - Loads new student notifications by program
5. `loadProgramsOverview()` - Loads programs table with enrollment data
6. `setupEventHandlers()` - Attaches event listeners
7. `setupSidebar()` - Highlights active menu item
8. `setupLogoutModalEvents()` - Configures logout modal

---

#### **loadHeaderData()**

Fetches and updates header information.

**Updates:**

- School year label
- User full name
- User role
- User initials (for avatar)
- User photo (if available)

---

#### **loadStatistics()**

Fetches and updates statistics cards.

**Updates:**

- Total Teachers
- Total Students
- Total Programs
- Total Sections
- Grade breakdown (7, 8, 9, 10)

---

#### **loadNotifications()**

Fetches and displays new enrollment notifications grouped by program.

**Features:**

- Shows list of recent students for each program
- Displays student LRN and name
- Shows time since enrollment
- "Review Enrollments" button navigates to enrollment review page
- Empty state message when no new enrollments

---

#### **loadProgramsOverview()**

Fetches and populates programs overview table.

**Features:**

- Dynamic color coding per program
- Capacity utilization visualization
- Acceptance rate calculation
- Trend indicators (up/down/stable)
- Summary row with totals
- Clickable rows to filter by program

---

## Template Updates (`admin_app/templates/admin_app/dashboard.html`)

### Header Section Changes

**Before:**

- Static hardcoded user name "Samson, Marwina D."
- Static hardcoded role "Admin"
- Static hardcoded school year selector

**After:**

- Dynamic user full name from backend
- Dynamic role from UserProfile
- Dynamic school year label
- Photo or initials avatar
- Real-time data binding

---

## Model Changes (`admin_app/models.py`)

### UserProfile Model

Added new field:

```python
photo = models.ImageField(
    upload_to='user_profiles/',
    blank=True,
    null=True,
    help_text="User profile photo"
)
```

**Migration Required:**

```bash
python manage.py makemigrations admin_app
python manage.py migrate
```

---

## Database Queries

### Statistics Query

```python
# Get active teachers
Teacher.objects.filter(is_active=True).count()

# Get enrolled students for active school year
Student.objects.filter(
    school_year=active_school_year,
    enrollment_status__in=['submitted', 'under_review', 'approved']
).count()

# Get active programs
Program.objects.filter(is_active=True).count()

# Get sections in active school year
Section.objects.filter(school_year=active_school_year).count()
```

### Notifications Query

```python
# Get new students (submitted status)
Student.objects.filter(
    school_year=active_school_year,
    enrollment_status='submitted',
    program_selected=True
).select_related('program_selection')
```

### Programs Overview Query

```python
# Get program statistics
ProgramSelection.objects.filter(
    school_year=active_school_year,
    selected_program_code=program.code
).select_related('student')
```

---

## Important Classes Used

### SchoolYear

- **Method:** `get_active_school_year()` - Returns currently active school year
- **Field:** `year_label` - Display format (e.g., "2025-2026")

### UserProfile

- **Related:** User (OneToOneField)
- **Fields:** program, position, department, employee_id, photo
- **Methods:** get_user_type_display(), get_program_name()

### Student

- **Fields:** lrn (primary key), enrollment_status, school_year, program_selected
- **Related:** StudentData (OneToOneField for name/details)

### ProgramSelection

- **Fields:** selected_program_code, admin_approved, created_at
- **Related:** Student (OneToOneField), SchoolYear (ForeignKey)

### Program

- **Fields:** code, name, is_active
- **Related:** Section (reverse relation)

### Section

- **Fields:** name, max_students, current_students
- **Related:** Program, SchoolYear, Teacher (adviser)

---

## Error Handling

All API endpoints include try-catch blocks that:

1. Log errors to console
2. Return error status
3. Show user-friendly notification
4. Prevent page crashes

---

## Performance Optimizations

1. **select_related()** - Used for foreign key lookups (program, position, department)
2. **API Separation** - Each data type has its own endpoint
3. **Lazy Loading** - Data loads on page init, then refreshed as needed
4. **Efficient Queries** - Single queries with filters instead of N+1 queries

---

## Future Enhancements

1. **Real-time Updates** - WebSocket for live notifications
2. **Export Functionality** - Download reports as PDF/Excel
3. **Advanced Filtering** - Filter by date range, program, status
4. **Caching** - Cache statistics for performance
5. **Pagination** - For large datasets
6. **Search** - Search students by LRN or name
7. **Analytics Charts** - Enrollment trends over time

---

## Testing

### Test Header Data

```bash
curl http://localhost:8000/admin/api/dashboard/header/
```

### Test Statistics

```bash
curl http://localhost:8000/admin/api/dashboard/statistics/
```

### Test Notifications

```bash
curl http://localhost:8000/admin/api/dashboard/notifications/
```

### Test Programs Overview

```bash
curl http://localhost:8000/admin/api/dashboard/programs/
```

---

## Troubleshooting

### School Year Not Showing

- Check that a SchoolYear exists with `is_active=True`
- View: SchoolYear model in admin

### No Students Showing in Notifications

- Ensure students have `enrollment_status='submitted'`
- Ensure students have `program_selected=True`
- Ensure ProgramSelection records exist with `selected_program_code`

### Photo Not Displaying

- Ensure MEDIA_ROOT and MEDIA_URL are configured in settings
- Check that user_profile.photo file exists
- Verify file permissions

### Statistics Showing 0

- Check that records exist in database
- Verify filters match your data (e.g., is_active=True)
- Check SchoolYear.is_active = True

---

## Summary

The admin dashboard now features:

- ✅ Real-time notifications for new student enrollments per program
- ✅ Dynamic header with user info (fullname, role, school year, photo)
- ✅ Live statistics (teachers, students, programs, sections)
- ✅ Detailed programs overview table
- ✅ Backend-driven data (no hardcoded mock data)
- ✅ RESTful API endpoints
- ✅ Error handling and user feedback
- ✅ Responsive design with Tailwind CSS
