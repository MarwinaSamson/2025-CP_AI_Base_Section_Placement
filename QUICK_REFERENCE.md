# Admin Dashboard - Quick Reference Guide

## 🚀 Quick Start (5 Minutes)

### 1. Apply Migration

```bash
python manage.py migrate
```

### 2. Start Server

```bash
python manage.py runserver
```

### 3. Go to Dashboard

```
http://localhost:8000/admin/
```

That's it! Dashboard loads with:

- ✅ Your user information
- ✅ School year (if active)
- ✅ Statistics
- ✅ Programs table
- ✅ New student notifications

---

## 🔍 API Endpoints

| Endpoint                              | Method | Purpose                 | Response                                |
| ------------------------------------- | ------ | ----------------------- | --------------------------------------- |
| `/admin/api/dashboard/header/`        | GET    | User info & school year | User name, role, school year, avatar    |
| `/admin/api/dashboard/statistics/`    | GET    | Count data              | Teachers, students, programs, sections  |
| `/admin/api/dashboard/notifications/` | GET    | New enrollments         | Students by program, LRN, timestamps    |
| `/admin/api/dashboard/programs/`      | GET    | Program metrics         | Applicants, approved, pending, rejected |

Test any endpoint in your browser or with curl:

```bash
curl http://localhost:8000/admin/api/dashboard/header/
```

---

## 📊 Data Structure

### Required for Dashboard to Work

```
SchoolYear (must have is_active=True)
├── year_label: "2025-2026"
├── start_date: 2025-08-01
├── end_date: 2026-05-31
└── is_active: True

User
├── username: "john.doe"
├── first_name: "John"
└── last_name: "Doe"

UserProfile (OneToOne with User)
├── user_type: "admin"
├── program: ForeignKey to Program
└── photo: ImageField (optional)

Program (multiple)
├── code: "HETERO", "STE", etc.
├── name: "Full program name"
└── is_active: True

Student (multiple)
├── lrn: "123456789012"
├── enrollment_status: "submitted"
├── program_selected: True
├── school_year: ForeignKey to SchoolYear
└── student_data: OneToOne relation

ProgramSelection (one per student)
├── student: OneToOne
├── selected_program_code: "HETERO"
└── school_year: ForeignKey
```

---

## 🎨 What Shows Where

### Header Section

| Item        | Source                               |
| ----------- | ------------------------------------ |
| School Year | `SchoolYear.year_label` (active)     |
| User Name   | `User.first_name` + `User.last_name` |
| User Role   | `UserProfile.user_type`              |
| Avatar      | `UserProfile.photo` or initials      |

### Notifications Section

| Item          | Source                                                  |
| ------------- | ------------------------------------------------------- |
| Program Name  | `Program.name`                                          |
| Student Count | Count of `Student` with `enrollment_status='submitted'` |
| Student List  | `StudentData` with `first_name` + `last_name`           |
| Time Ago      | Created timestamp formatted                             |

### Statistics Section

| Item     | Source                                    |
| -------- | ----------------------------------------- |
| Teachers | Count of `Teacher` with `is_active=True`  |
| Students | Count of `Student` in active `SchoolYear` |
| Programs | Count of `Program` with `is_active=True`  |
| Sections | Count of `Section` in active `SchoolYear` |

### Programs Table

| Item         | Source                                             |
| ------------ | -------------------------------------------------- |
| Program Name | `Program.code` and `Program.name`                  |
| Applicants   | Count of `ProgramSelection` per program            |
| Approved     | Count with `Student.enrollment_status='approved'`  |
| Pending      | Count with `Student.enrollment_status='submitted'` |
| Rejected     | Count with `Student.enrollment_status='rejected'`  |
| Capacity     | Sum of `Section.max_students`                      |
| Sections     | Count of `Section` per program                     |

---

## ⚠️ Common Issues

### Issue: No data showing

**Solution:** Check if data exists

```bash
python manage.py shell
from admin_app.models import SchoolYear, Program
print(SchoolYear.objects.filter(is_active=True).count())  # Should be > 0
print(Program.objects.filter(is_active=True).count())  # Should be > 0
```

### Issue: "No Active Year" in header

**Solution:** Set a school year as active

```bash
python manage.py shell
from admin_app.models import SchoolYear
sy = SchoolYear.objects.first()
sy.is_active = True
sy.save()
```

### Issue: User name not showing

**Solution:** Make sure User has first_name and last_name

```bash
python manage.py shell
from django.contrib.auth.models import User
u = User.objects.get(username='your_username')
u.first_name = 'John'
u.last_name = 'Doe'
u.save()
```

### Issue: No notifications showing

**Solution:** Create students with correct status

```bash
python manage.py shell
from enrollment_app.models import Student, ProgramSelection
from admin_app.models import SchoolYear, Program

sy = SchoolYear.objects.get(is_active=True)
prog = Program.objects.get(code='HETERO')

# Create student with correct status
student = Student.objects.create(
    lrn='123456789012',
    school_year=sy,
    enrollment_status='submitted',  # Important!
    program_selected=True  # Important!
)

# Create program selection
ProgramSelection.objects.create(
    student=student,
    school_year=sy,
    selected_program_code='HETERO'
)
```

---

## 🧪 Quick Testing

### Test 1: Check Header API

```bash
curl http://localhost:8000/admin/api/dashboard/header/
```

Should return JSON with user info.

### Test 2: Check Statistics API

```bash
curl http://localhost:8000/admin/api/dashboard/statistics/
```

Should return numbers for teachers, students, programs, sections.

### Test 3: Check Notifications API

```bash
curl http://localhost:8000/admin/api/dashboard/notifications/
```

Should return list of new students by program (empty if no submitted students).

### Test 4: Check Programs API

```bash
curl http://localhost:8000/admin/api/dashboard/programs/
```

Should return all active programs with enrollment data.

---

## 📁 Key Files

| File                                             | Purpose                 |
| ------------------------------------------------ | ----------------------- |
| `admin_app/views/dashboard_views.py`             | Backend views & APIs    |
| `admin_app/urls.py`                              | API routes              |
| `admin_app/models.py`                            | UserProfile photo field |
| `admin_app/static/admin_app/js/dashboard-api.js` | Frontend JavaScript     |
| `admin_app/templates/admin_app/dashboard.html`   | HTML template           |

---

## 🔧 Configuration

### Django Settings Required

```python
# settings.py

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'admin_app',
    'enrollment_app',
]
```

### URLs Required

```python
# urls.py - root level

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your patterns
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## 🎯 Expected Results

After setup, dashboard should show:

```
┌─────────────────────────────────────────────────┐
│ Admin Dashboard                                  │
│                                                 │
│ School Year: 2025-2026  [JD]                    │
│ John Doe, Admin                                 │
├─────────────────────────────────────────────────┤
│ New Enrollment Submissions                      │
│ 25 new HETERO applications pending review       │
│ 18 new STE applications pending review          │
│ ... (more programs)                             │
├─────────────────────────────────────────────────┤
│ Quick Statistics                                │
│ [52 Teachers] [1450 Students] [7 Programs] [42] │
├─────────────────────────────────────────────────┤
│ Programs Overview                               │
│ HETERO  | 350 | 305 | 35 | 10 | 430/480 | 12   │
│ STE     | 220 | 190 | 20 | 10 | 270/320 | 8    │
│ TOP 5   | 250 | 220 | 22 | 8  | 175/200 | 5    │
│ ... (more programs)                             │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Next Steps

1. ✅ Run migration
2. ✅ Create test data (see EXAMPLE_DATA.md)
3. ✅ Navigate to dashboard
4. ✅ Verify all sections display correctly
5. ✅ Test APIs with curl
6. ✅ Share with team

---

## 📚 Documentation

For more details, see:

- `ADMIN_DASHBOARD_BACKEND.md` - Technical documentation
- `SETUP_GUIDE.md` - Detailed setup guide
- `EXAMPLE_DATA.md` - Database structure & sample data
- `IMPLEMENTATION_SUMMARY.md` - Complete overview

---

## ⚡ Performance Tips

1. **Caching** - Consider caching statistics (updates hourly)
2. **Pagination** - Limit notifications to top 10 programs
3. **Indexing** - Database has indexes on common queries
4. **Lazy Loading** - JavaScript loads data asynchronously

---

## 🔐 Security Notes

- All views protected with `@admin_required` decorator
- APIs require authentication (same as dashboard view)
- Filters prevent unauthorized data access
- User only sees their own data + general statistics

---

## 💡 Pro Tips

1. **Update Logo** - Change in settings > content management
2. **Customize Colors** - Edit Tailwind config in dashboard.html
3. **Add Charts** - Import Chart.js and add analytics
4. **Export Data** - Add button to export as PDF/Excel
5. **Real-time Updates** - Use WebSockets for live notifications

---

## 📞 Support

**Still have questions?**

- Check error console (F12 → Console)
- Look at Network tab to see API responses
- Review Django logs for backend errors
- Refer to ADMIN_DASHBOARD_BACKEND.md for details

---

**Last Updated:** January 5, 2026
**Status:** ✅ Production Ready
