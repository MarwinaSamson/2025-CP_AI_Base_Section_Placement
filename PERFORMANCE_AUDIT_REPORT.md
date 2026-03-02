# Performance Bottleneck Audit Report

**Project:** AI-Based Section Placement System  
**Framework:** Django 6.0 / PostgreSQL  
**Date:** Auto-generated

---

## Table of Contents

1. [Database Query Issues](#1-database-query-issues)
2. [Template & Frontend Issues](#2-template--frontend-issues)
3. [Missing Django Performance Configurations](#3-missing-django-performance-configurations)
4. [View-Level Architectural Issues](#4-view-level-architectural-issues)

---

## 1. Database Query Issues

### 1.1 N+1 Query — `update_current_students_count()` in Loops

**Severity: HIGH**  
Every call does 1 SELECT + 1 UPDATE (2 queries per section).

| File                                                        | Line | Context                                                                    |
| ----------------------------------------------------------- | ---- | -------------------------------------------------------------------------- |
| `coordinator_app/views/coor_enrollment_management_views.py` | L51  | `section.update_current_students_count()` inside `for section in sections` |
| `coordinator_app/views/coor_enrollment_management_views.py` | L241 | Same loop in `refresh_enrollment_data()`                                   |
| `coordinator_app/views/coor_sectionmanagement_views.py`     | L29  | `section.update_current_students_count()` inside `for section in sections` |

**Model definition:** `admin_app/models.py` L351-361 — each call runs `ProgramSelection.objects.filter(assigned_section=self, admin_approved=True).count()` then `self.save(update_fields=['current_students'])`.

**Fix:** Replace the loop with a single aggregation query + bulk update:

```python
from django.db.models import Count, Q
Section.objects.filter(pk__in=[s.pk for s in sections]).update(
    current_students=Subquery(
        ProgramSelection.objects.filter(
            assigned_section=OuterRef('pk'), admin_approved=True
        ).values('assigned_section').annotate(c=Count('id')).values('c')
    )
)
```

---

### 1.2 N+1 Query — `get_actual_count()` in Loops

**Severity: HIGH**  
Each call runs a COUNT query per section.

| File                                            | Line     | Context                                                              |
| ----------------------------------------------- | -------- | -------------------------------------------------------------------- |
| `coordinator_app/views/coor_analytics_views.py` | L294-295 | `for section in sections: actual_count = section.get_actual_count()` |
| `coordinator_app/views/coor_reports_views.py`   | L169-170 | `for sec in section_qs: actual_count = sec.get_actual_count()`       |
| `coordinator_app/views/coor_reports_views.py`   | L708     | `section.get_actual_count()` inside section loop                     |

**Model definition:** `admin_app/models.py` L363-367 — `get_actual_count()` runs the same query as `update_current_students_count()` but without saving.

**Fix:** Annotate sections queryset once:

```python
sections = Section.objects.filter(...).annotate(
    actual_count=Count('programselection', filter=Q(programselection__admin_approved=True))
)
```

---

### 1.3 N+1 Query — `dashboard_notifications()` Student Loop

**Severity: HIGH**

| File                                 | Line | Context                                                                   |
| ------------------------------------ | ---- | ------------------------------------------------------------------------- |
| `admin_app/views/dashboard_views.py` | L157 | `for student in new_students:`                                            |
| `admin_app/views/dashboard_views.py` | L159 | `student.program_selection` — triggers lazy load despite `select_related` |
| `admin_app/views/dashboard_views.py` | L172 | `student.student_data` — separate query per student                       |

The queryset at L152 does `select_related('program_selection')` but **not** `select_related('student_data')`. Every iteration accesses `student.student_data` triggering a new query.

**Fix:** Add `student_data` to `select_related`:

```python
new_students = Student.objects.filter(...).select_related('program_selection', 'student_data')
```

---

### 1.4 N+1 Query — `dashboard_programs_overview()` Program Loop

**Severity: MEDIUM**

| File                                 | Line     | Context                                                                    |
| ------------------------------------ | -------- | -------------------------------------------------------------------------- |
| `admin_app/views/dashboard_views.py` | L243     | `for program in programs:` — runs 5+ queries per program                   |
| `admin_app/views/dashboard_views.py` | L247-253 | 4 count queries per program (total, approved, pending, rejected)           |
| `admin_app/views/dashboard_views.py` | L256-260 | Section query + `sum(s.max_students for s in sections)` evaluates queryset |

With 6 programs, this generates **~30 queries** per request.

**Fix:** Use `annotate()` with conditional aggregation:

```python
programs = Program.objects.filter(is_active=True).annotate(
    total=Count('programselection', filter=Q(programselection__school_year=active_school_year)),
    approved=Count('programselection', filter=Q(..., student__enrollment_status='approved')),
    ...
)
```

---

### 1.5 N+1 Query — `get_all_programs()` Section Count

**Severity: MEDIUM**

| File                                | Line | Context                                                          |
| ----------------------------------- | ---- | ---------------------------------------------------------------- |
| `admin_app/views/sections_views.py` | L110 | `p.sections.count()` inside list comprehension over all programs |

**Fix:** Annotate with count:

```python
programs = Program.objects.all().annotate(sections_count=Count('sections')).order_by('code')
```

---

### 1.6 N+1 Query — `get_teachers()` Missing `select_related`

**Severity: LOW-MEDIUM**

| File                                | Line     | Context                                                                                            |
| ----------------------------------- | -------- | -------------------------------------------------------------------------------------------------- |
| `admin_app/views/sections_views.py` | L301-316 | Iterates all teachers; accesses `t.position.name` and `t.department.name` without `select_related` |

Each teacher access triggers 2 lazy loads (position + department).

**Fix:**

```python
teachers = Teacher.objects.select_related('position', 'department').all().order_by(...)
```

---

### 1.7 String Comparison on ForeignKey Fields (`assigned_section=str(...)`)

**Severity: HIGH**  
`ProgramSelection.assigned_section` is a ForeignKey to `Section`. Filtering with `assigned_section=str(section_id)` works only by accident (Django coerces), but **defeats index usage** and is semantically wrong.

| File                                             | Line  | Pattern                               |
| ------------------------------------------------ | ----- | ------------------------------------- |
| `enrollment_app/views/landingpage_view.py`       | L119  | `assigned_section=str(section_id)`    |
| `enrollment_app/views/landingpage_view.py`       | L163  | `assigned_section=str(section_id)`    |
| `coordinator_app/views/coor_masterlist_views.py` | L35   | `assigned_section=str(section_id)`    |
| `coordinator_app/views/coor_masterlist_views.py` | L121  | `assigned_section=str(section_id)`    |
| `coordinator_app/views/coor_masterlist_views.py` | L208  | `assigned_section=str(section_id)`    |
| `coordinator_app/views/coor_masterlist_views.py` | L288  | `assigned_section=str(section_id)`    |
| `coordinator_app/views/coor_dashboard_views.py`  | L153  | `assigned_section=str(s.id)`          |
| `coordinator_app/views/coor_reports_views.py`    | L677  | `Q(assigned_section=str(section.id))` |
| `coordinator_app/views/coor_reports_views.py`    | L1135 | `Q(assigned_section=str(section.id))` |
| `coordinator_app/views/coor_reports_views.py`    | L1154 | `Q(assigned_section=str(section.id))` |
| `coordinator_app/views/coor_reports_views.py`    | L1168 | `Q(assigned_section=str(section.id))` |

**Fix:** Use the FK object or `_id` suffix:

```python
# Instead of: assigned_section=str(section_id)
assigned_section_id=section_id   # Uses the FK index directly
# or: assigned_section=section_obj
```

---

### 1.8 String Section ID Lists for `__in` Queries

**Severity: MEDIUM**

| File                                            | Line | Pattern                                                                             |
| ----------------------------------------------- | ---- | ----------------------------------------------------------------------------------- |
| `coordinator_app/views/coor_dashboard_views.py` | L13  | `section_ids = [str(s.id) for s in spfl_sections]`                                  |
| `coordinator_app/views/coor_dashboard_views.py` | L115 | `section_ids = [str(s.id) for s in sptve_sections]`                                 |
| `coordinator_app/views/coor_analytics_views.py` | L356 | `top5_section_ids = [str(s.id) for s in sections.filter(regular_track='TOP5')]`     |
| `coordinator_app/views/coor_analytics_views.py` | L357 | `hetero_section_ids = [str(s.id) for s in sections.filter(regular_track='HETERO')]` |

Then used as `assigned_section__in=section_ids`. Since `assigned_section` is a FK, the `__in` should receive Section objects or integer PKs, not strings.

**Fix:**

```python
# Use queryset directly (no Python-side evaluation needed)
ProgramSelection.objects.filter(assigned_section__in=sections.filter(regular_track='TOP5'))
```

---

### 1.9 N+1 in `_get_section_academic_data()` — Analytics

**Severity: HIGH**

| File                                            | Line     | Context                                                                            |
| ----------------------------------------------- | -------- | ---------------------------------------------------------------------------------- |
| `coordinator_app/views/coor_analytics_views.py` | L157-179 | For each section: filters `all_selections`, then queries `AcademicData` separately |

In the `for section in sections` loop (L157), each iteration:

1. Filters `all_selections` with string section ID (L161)
2. Runs a separate `AcademicData.objects.filter()` (L170)
3. Computes GWA in Python

This is O(sections × 2) queries.

---

### 1.10 N+1 in `reports()` — Honor/At-Risk Counting

**Severity: MEDIUM**

| File                                          | Line     | Context                                                                          |
| --------------------------------------------- | -------- | -------------------------------------------------------------------------------- |
| `coordinator_app/views/coor_reports_views.py` | L188-195 | `for ps in approved_selections:` accesses `ps.student.academic_data` per student |

Although `_get_base_selections()` (L100) uses `select_related('student', 'student__student_data', 'student__academic_data')`, the loop calculates GWA in Python for every student. This should be done in a single aggregation query.

---

### 1.11 `get_student_details()` Without `select_related`

**Severity: MEDIUM**

| File                                              | Line | Context                                                                                         |
| ------------------------------------------------- | ---- | ----------------------------------------------------------------------------------------------- |
| `admin_app/views/studentedit_views.py`            | —    | `get_object_or_404(Student, lrn=student_id)` without `select_related`                           |
| `coordinator_app/views/coor_studentdetails.py`    | L5   | `get_object_or_404(Student, lrn=lrn)` without `select_related`                                  |
| `coordinator_app/views/coor_studentedit_views.py` | L87  | `get_object_or_404(Student, lrn=student_id)` — then accesses `hasattr()` for 5+ related objects |

Each subsequent `hasattr(student, 'student_data')` check triggers a lazy query.

**Fix:**

```python
student = get_object_or_404(
    Student.objects.select_related(
        'student_data', 'family_data', 'family_data__father',
        'family_data__mother', 'family_data__other_guardian',
        'survey_data', 'academic_data', 'program_selection', 'school_year'
    ),
    lrn=student_id
)
```

---

### 1.12 Duplicate Queries in Export Functions

**Severity: MEDIUM**

| File                                             | Lines                 | Context                                                                                                                                                        |
| ------------------------------------------------ | --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `coordinator_app/views/coor_masterlist_views.py` | L35, L121, L208, L288 | Four functions (`get_masterlist`, `export_masterlist_excel`, `export_masterlist_pdf`, `export_masterlist_docx`) execute identical queries for the same section |

Each export endpoint independently re-queries all students for a section instead of sharing query results.

---

## 2. Template & Frontend Issues

### 2.1 Tailwind CSS Play CDN — NOT Production-Ready

**Severity: CRITICAL**  
The Tailwind Play CDN (`cdn.tailwindcss.com`) is **explicitly not for production**. It dynamically generates styles at runtime via JavaScript, adding ~300ms+ to every page load. It also downloads the full Tailwind config on every page.

**Affected files (21+ templates):**

| File                                                                 | Line          |
| -------------------------------------------------------------------- | ------------- |
| `enrollment_app/templates/enrollment_app/base.html`                  | L9            |
| `enrollment_app/templates/enrollment_app/landing.html`               | L15           |
| `enrollment_app/templates/enrollment_app/studentData.html`           | L8            |
| `enrollment_app/templates/enrollment_app/familyData.html`            | L8            |
| `enrollment_app/templates/enrollment_app/studentAcademic.html`       | L8            |
| `enrollment_app/templates/enrollment_app/studentNonAcademic.html`    | L8            |
| `enrollment_app/templates/enrollment_app/sectionPlacement.html`      | L11           |
| `enrollment_app/templates/enrollment_app/enrollmentCompleteOld.html` | L8            |
| `enrollment_app/templates/enrollment_app/transfereeDocuments.html`   | L8            |
| `enrollment_app/templates/enrollment_app/transfereeComplete.html`    | L8            |
| `enrollment_app/templates/enrollment_app/edit.html`                  | L7            |
| `admin_app/templates/admin_app/analytics.html`                       | L9            |
| `admin_app/templates/admin_app/studentEdit.html`                     | L8            |
| `admin_app/templates/admin_app/studentDetails.html`                  | L9            |
| `admin_app/templates/admin_app/settings.html`                        | L8            |
| `admin_app/templates/admin_app/sections.html`                        | L8            |
| `admin_app/templates/admin_app/reports.html`                         | L9            |
| `admin_app/templates/admin_app/masterlist.html`                      | L9            |
| `admin_app/templates/admin_app/login.html`                           | L8            |
| `admin_app/templates/admin_app/logout.html`                          | L8            |
| `coordinator_app/templates/coordinator_app/coordinator_base.html`    | (in `<head>`) |

**Fix:** Build Tailwind CSS at compile time using the Tailwind CLI and serve the generated CSS as a static file:

```bash
npx tailwindcss -i ./input.css -o ./static/css/tailwind.min.css --minify
```

Then replace the CDN script tag with:

```html
<link rel="stylesheet" href="{% static 'css/tailwind.min.css' %}" />
```

---

### 2.2 Google Fonts — Render-Blocking, Redundant Loads

**Severity: MEDIUM**  
Google Fonts is loaded on nearly every template (both in base templates and individual templates that override `<head>`). Each load is a render-blocking CSS fetch.

| File                                                                 | Line      | Fonts                                                  |
| -------------------------------------------------------------------- | --------- | ------------------------------------------------------ |
| `enrollment_app/templates/enrollment_app/base.html`                  | L11       | Playfair Display + Poppins                             |
| `enrollment_app/templates/enrollment_app/landing.html`               | L17       | Playfair Display + Poppins (duplicate — extends base!) |
| `enrollment_app/templates/enrollment_app/studentData.html`           | L10       | Playfair Display + Poppins                             |
| `enrollment_app/templates/enrollment_app/familyData.html`            | L10       | Playfair Display + Poppins                             |
| `enrollment_app/templates/enrollment_app/studentAcademic.html`       | L10       | Playfair Display + Inter                               |
| `enrollment_app/templates/enrollment_app/studentNonAcademic.html`    | L14       | Playfair Display + Inter                               |
| `enrollment_app/templates/enrollment_app/sectionPlacement.html`      | L15       | Playfair Display + Poppins                             |
| `enrollment_app/templates/enrollment_app/transfereeDocuments.html`   | L9        | Playfair Display + Poppins                             |
| `enrollment_app/templates/enrollment_app/transfereeComplete.html`    | L9        | Playfair Display + Poppins                             |
| `enrollment_app/templates/enrollment_app/enrollmentCompleteOld.html` | L9        | Playfair Display + Poppins                             |
| `coordinator_app/templates/coordinator_app/coordinator_base.html`    | (in head) | Google Fonts                                           |

**Issues:**

1. Templates that `{% extends 'base.html' %}` re-declare fonts, causing **double downloads**
2. No `font-display: swap` or `preconnect` hints
3. Multiple different font combinations (Poppins vs Inter) across pages

**Fix:**

- Move font loading to base template only, use `<link rel="preconnect">` hints
- Self-host fonts with `font-display: swap`
- Standardize on one sans-serif font family

---

### 2.3 Font Awesome CDN — Multiple Versions Loaded

**Severity: MEDIUM**

| File                                                                 | Line   | Version      |
| -------------------------------------------------------------------- | ------ | ------------ |
| `enrollment_app/templates/enrollment_app/studentData.html`           | L15    | FA 5.15.3    |
| `enrollment_app/templates/enrollment_app/familyData.html`            | L15    | FA 5.15.3    |
| `enrollment_app/templates/enrollment_app/transfereeDocuments.html`   | L10    | FA 5.15.3    |
| `enrollment_app/templates/enrollment_app/transfereeComplete.html`    | L10    | FA 5.15.3    |
| `enrollment_app/templates/enrollment_app/enrollmentCompleteOld.html` | L10    | FA 5.15.3    |
| `enrollment_app/templates/enrollment_app/studentAcademic.html`       | L15    | FA **6.0.0** |
| `enrollment_app/templates/enrollment_app/studentNonAcademic.html`    | L11    | FA **6.4.0** |
| `enrollment_app/templates/enrollment_app/edit.html`                  | L10    | FA **6.5.1** |
| `coordinator_app/templates/coordinator_app/coordinator_base.html`    | (head) | FA **6.0.0** |

Three different major versions of Font Awesome (5.15.3, 6.0.0, 6.4.0, 6.5.1) are in use. The full FA CSS is ~80KB per version.

**Fix:** Standardize on one version, load from base template only, or use a subset/icon font with only needed icons.

---

### 2.4 Chart.js CDN on Every Coordinator Page

**Severity: LOW-MEDIUM**

| File                                                              | Line   |
| ----------------------------------------------------------------- | ------ |
| `coordinator_app/templates/coordinator_app/coordinator_base.html` | (head) |

Chart.js (~200KB) is loaded on every coordinator page via the base template, even pages that don't use charts (e.g., student edit, section management).

**Fix:** Load Chart.js only on pages that need it using `{% block extra_js %}`.

---

### 2.5 Landing Page — 944-Line Template with Inline Everything

**Severity: MEDIUM**

| File                                                   | Lines |
| ------------------------------------------------------ | ----- |
| `enrollment_app/templates/enrollment_app/landing.html` | 1-944 |

- L15: Loads Tailwind Play CDN
- L17: Loads Google Fonts
- L22-40: Inline Tailwind config JS
- L41-75: Inline CSS animation styles
- The template is 944 lines of HTML + inline JS + inline CSS

The landing page is the public-facing entry point and loads the heaviest combination of CDN resources on every visit.

---

### 2.6 Individual Templates Override `<head>` — CDN Duplication

**Severity: MEDIUM**

Many enrollment_app templates (studentData, familyData, studentAcademic, etc.) do **not** use `{% extends 'base.html' %}` properly for head content. Instead, they include their own `<head>` with redundant CDN loads (Tailwind, Fonts, Font Awesome). This means:

- CDN scripts are duplicated across base + child template
- No centralized control over resources
- Browser may download the same resources twice

---

## 3. Missing Django Performance Configurations

### 3.1 No Cache Backend Configured

**Severity: CRITICAL**

| File                                   | Context                                         |
| -------------------------------------- | ----------------------------------------------- |
| `section_placement_system/settings.py` | No `CACHES` setting exists anywhere in the file |

Django defaults to `LocMemCache` which is per-process, not shared, and lost on restart. No view caching, no template fragment caching, no session caching, no queryset caching is possible without this.

**Fix:** Add at minimum:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
    }
}
```

Or better, use Redis:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

---

### 3.2 `SESSION_SAVE_EVERY_REQUEST = True` with Database Sessions

**Severity: HIGH**

| File                                   | Line | Setting                             |
| -------------------------------------- | ---- | ----------------------------------- |
| `section_placement_system/settings.py` | L207 | `SESSION_SAVE_EVERY_REQUEST = True` |

The default session backend is `django.contrib.sessions.backends.db` (database). Combined with `SESSION_SAVE_EVERY_REQUEST = True`, **every single HTTP request** writes to the `django_session` database table — even reads/GETs.

**Fix (option A):** Switch session backend to cache:

```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
```

**Fix (option B):** Set `SESSION_SAVE_EVERY_REQUEST = False` (only saves when session data changes).

---

### 3.3 No `CONN_MAX_AGE` — New DB Connection on Every Request

**Severity: HIGH**

| File                                   | Context                                  |
| -------------------------------------- | ---------------------------------------- |
| `section_placement_system/settings.py` | `DATABASES` config has no `CONN_MAX_AGE` |

Django defaults `CONN_MAX_AGE` to `0`, meaning it opens a **new database connection for every request** and closes it afterward. PostgreSQL connection setup has significant overhead (~5-20ms).

**Fix:**

```python
DATABASES = {
    'default': {
        ...
        'CONN_MAX_AGE': 600,  # Reuse connections for 10 minutes
    },
    'lis': {
        ...
        'CONN_MAX_AGE': 600,
    }
}
```

---

### 3.4 No Template Caching (cached.Loader)

**Severity: MEDIUM**

| File                                   | Line   | Context                                 |
| -------------------------------------- | ------ | --------------------------------------- |
| `section_placement_system/settings.py` | L60-76 | `TEMPLATES` config uses default loaders |

Templates are re-read from disk and re-parsed on every request in production.

**Fix:** Enable the cached template loader:

```python
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [...],
    'OPTIONS': {
        'loaders': [
            ('django.template.loaders.cached.Loader', [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ]),
        ],
        'context_processors': [...],
    },
}]
```

Note: Remove `APP_DIRS: True` when using explicit loaders.

---

### 3.5 No GZip Middleware

**Severity: LOW-MEDIUM**

| File                                   | Line   | Context                                 |
| -------------------------------------- | ------ | --------------------------------------- |
| `section_placement_system/settings.py` | L48-56 | `MIDDLEWARE` list — no `GZipMiddleware` |

HTML and JSON responses are served uncompressed.

**Fix:** Add to beginning of middleware:

```python
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',   # Add this
    'django.middleware.security.SecurityMiddleware',
    ...
]
```

---

## 4. View-Level Architectural Issues

### 4.1 Hardcoded HTML in Python — `PROGRAM_DATA` Dictionary

**Severity: MEDIUM (maintainability + memory)**

| File                                            | Lines   |
| ----------------------------------------------- | ------- |
| `coordinator_app/views/coor_dashboard_views.py` | ~L1-500 |

The `PROGRAM_DATA` dictionary contains **hundreds of lines of raw HTML strings** with hardcoded statistics (e.g., "142 Total Trainees", "95% Workshop Completion"). This is:

1. Loaded into memory on every process start
2. Hardcoded data that never updates from the database
3. HTML mixed into Python code (violates separation of concerns)

The programs OHSP, SNED, and REGULAR use these hardcoded fallback values even though STE, SPTVE, and SPFL have real database functions.

**Fix:** Move HTML to template partials. Replace hardcoded stats with database queries like the STE/SPTVE/SPFL implementations.

---

### 4.2 Duplicate `header_data` / `log_activity` Functions

**Severity: LOW (code quality)**

| File                                 | Function                          |
| ------------------------------------ | --------------------------------- |
| `admin_app/views/analytics_views.py` | `analytics_header_data()`         |
| `admin_app/views/analytics_views.py` | `reports_header_data()`           |
| `admin_app/views/analytics_views.py` | `settings_header_data()`          |
| `admin_app/views/sections_views.py`  | `log_activity()`                  |
| `admin_app/views/settings_views.py`  | `log_activity()` (identical copy) |

The three `*_header_data` functions are identical — each queries `UserProfile` for the current user. The `log_activity` helper is duplicated across two files.

**Fix:** Extract into a shared utility module:

```python
# admin_app/utils.py
def get_header_data(request): ...
def log_activity(user, action, description, request=None): ...
```

---

### 4.3 Duplicate Queries Across Report Formats (coor_reports_views.py)

**Severity: MEDIUM**

| File                                          | Lines      | Context                                                             |
| --------------------------------------------- | ---------- | ------------------------------------------------------------------- |
| `coordinator_app/views/coor_reports_views.py` | L260       | `generate_enrollment_report()` — iterates all selections per format |
| `coordinator_app/views/coor_reports_views.py` | L499       | `generate_academic_report()` — same base queryset re-evaluated      |
| `coordinator_app/views/coor_reports_views.py` | L673       | Section masterlist — loops sections, queries per section            |
| `coordinator_app/views/coor_reports_views.py` | L1132-1172 | Three section loops with identical query patterns                   |

**The file is 2,891 lines long** with massive code duplication across PDF/Excel/Word generation. The same data is queried and formatted 3x for each report type.

**Fix:** Extract data collection into shared functions (already partially done with `_get_base_selections`), then pass data to format-specific renderers.

---

### 4.4 Session Polling Every 10 Seconds

**Severity: LOW-MEDIUM**

| File                                      | Context                                                                     |
| ----------------------------------------- | --------------------------------------------------------------------------- |
| `admin_app/templates/admin_app/base.html` | JavaScript at bottom — `setInterval(fetch('/admin/check-session/'), 10000)` |

With `SESSION_SAVE_EVERY_REQUEST = True`, this means every 10 seconds each open admin tab:

1. Makes an HTTP request
2. Reads from the session DB table
3. Writes back to the session DB table

With 10 admin users, that's 60 session DB writes per minute just from polling.

**Fix:** Increase interval to 60-120 seconds, or use a dedicated lightweight endpoint that doesn't touch sessions.

---

### 4.5 `coor_reports_views.py` — GWA Calculation in Python Loops

**Severity: MEDIUM**

| File                                            | Lines    | Context                                                                   |
| ----------------------------------------------- | -------- | ------------------------------------------------------------------------- |
| `coordinator_app/views/coor_analytics_views.py` | L79-90   | `_calculate_gwa()` — loops 8 subject fields in Python                     |
| `coordinator_app/views/coor_analytics_views.py` | L93-114  | `_get_gwa_distribution()` — fetches all AcademicData, computes in Python  |
| `coordinator_app/views/coor_reports_views.py`   | L188-195 | `reports()` — loops approved students, computes GWA per student in Python |

All GWA calculations fetch individual records and compute in Python instead of using database aggregation.

**Fix:** Compute GWA in the database:

```python
from django.db.models import F, Avg, Value
from django.db.models.functions import Coalesce

AcademicData.objects.filter(student__lrn__in=lrns).aggregate(
    avg_gwa=Avg(
        (F('mathematics') + F('science') + F('english') + F('filipino') +
         F('araling_panlipunan') + F('edukasyon_sa_pagpapakatao') +
         F('edukasyon_pangkabuhayan') + F('mapeh')) / 8.0
    )
)
```

---

### 4.6 `landing_page()` — N+1 on Programs → Sections

**Severity: LOW-MEDIUM**

| File                                       | Line | Context                                                       |
| ------------------------------------------ | ---- | ------------------------------------------------------------- |
| `enrollment_app/views/landingpage_view.py` | L38  | `for prog in active_programs:` — queries sections per program |

**Fix:** Use `prefetch_related('sections')` on the programs queryset.

---

## Summary — Prioritized Fix List

| Priority | Issue                                                           | Impact                                           | Effort  |
| -------- | --------------------------------------------------------------- | ------------------------------------------------ | ------- |
| 🔴 P0    | Replace Tailwind Play CDN with compiled CSS (§2.1)              | Every page load ~300ms slower                    | Medium  |
| 🔴 P0    | Add `CACHES` configuration (§3.1)                               | No caching possible at all                       | Low     |
| 🔴 P0    | Set `CONN_MAX_AGE` (§3.3)                                       | New DB connection every request (~10ms overhead) | Trivial |
| 🔴 P0    | Fix `SESSION_SAVE_EVERY_REQUEST` (§3.2)                         | DB write on every request                        | Trivial |
| 🟠 P1    | Fix `assigned_section=str()` patterns (§1.7, §1.8)              | Index bypass on 14+ queries                      | Medium  |
| 🟠 P1    | Fix `update_current_students_count()` N+1 loops (§1.1)          | 2 queries × N sections per page load             | Medium  |
| 🟠 P1    | Fix `get_actual_count()` N+1 loops (§1.2)                       | 1 query × N sections per page load               | Medium  |
| 🟠 P1    | Fix `dashboard_notifications()` missing `select_related` (§1.3) | 1 query per submitted student                    | Trivial |
| 🟡 P2    | Enable cached template loader (§3.4)                            | Re-parse templates every request                 | Low     |
| 🟡 P2    | Fix `dashboard_programs_overview()` N+1 (§1.4)                  | ~30 queries per dashboard load                   | Medium  |
| 🟡 P2    | Fix `get_student_details()` missing `select_related` (§1.11)    | 5+ lazy queries per student view                 | Trivial |
| 🟡 P2    | Consolidate Font Awesome versions (§2.3)                        | 80KB × 4 versions                                | Medium  |
| 🟡 P2    | Move Google Fonts to base template only (§2.2)                  | Duplicate downloads                              | Low     |
| 🟢 P3    | Load Chart.js conditionally (§2.4)                              | 200KB on non-chart pages                         | Low     |
| 🟢 P3    | Add GZip middleware (§3.5)                                      | Uncompressed responses                           | Trivial |
| 🟢 P3    | Move GWA calc to database (§4.5)                                | Python loop vs SQL aggregate                     | Medium  |
| 🟢 P3    | Deduplicate report code (§4.3)                                  | 2891 lines with heavy repetition                 | High    |
| 🟢 P3    | Remove hardcoded HTML from views (§4.1)                         | Stale data, memory waste                         | Medium  |
| 🟢 P3    | Deduplicate header_data/log_activity (§4.2)                     | Code quality                                     | Low     |
| 🟢 P3    | Reduce session poll interval (§4.4)                             | Unnecessary DB writes                            | Trivial |
