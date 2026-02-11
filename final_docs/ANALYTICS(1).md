# Analytics Module Documentation

## Overview

The Analytics Module provides coordinators with a comprehensive, real-time dashboard of enrollment and academic performance data for their assigned program. All data is pulled from live database queries — there is no hardcoded or mock data.

**Access**: Coordinator Portal > Sidebar > Analytics
**URL**: `/coordinator/analytics/`
**Authentication**: Requires `@coordinator_required` decorator (logged-in coordinator with assigned program)

---

## Architecture

### Data Flow

```
Database (Django ORM)
    |
    v
coor_analytics_views.py  -->  get_analytics_data()  -->  context dict
    |
    v
analytics.html  -->  window.chartData (JSON injection via {{ |safe }})
    |
    v
analytics.js  -->  Chart.js renders 7 charts
```

### Files

| File | Role |
|------|------|
| `coordinator_app/views/coor_analytics_views.py` | Backend — all DB queries and data aggregation |
| `coordinator_app/templates/coordinator_app/analytics.html` | Template — layout, metrics cards, chart canvases, data table |
| `coordinator_app/static/coordinator_app/js/analytics.js` | Frontend — Chart.js initialization and rendering |

---

## Backend (`coor_analytics_views.py`)

### Entry Point

```python
@coordinator_required
def analytics(request):
```

1. Retrieves the coordinator's assigned program via `request.user.profile.program`
2. Extracts the program code string (e.g., `'STE'`, `'SPFL'`, `'REGULAR'`)
3. Calls `get_analytics_data(program_code, program_obj)` — the universal analytics function
4. Passes the result to the template as context

### Universal Analytics Function

`get_analytics_data(program_code, program_obj)` replaces the previous 5 separate program-specific functions. It works identically for all programs (STE, SPFL, SPTVE, REGULAR, OHSP, SNED).

**Returns a dict with:**
- `metrics` — numeric KPIs (dict)
- `chart_data` — JSON-serialized chart datasets (dict of JSON strings)
- `table_data` — rows for the summary table (list of dicts)
- `key_subjects` — program-specific key subject highlights (list of dicts)
- `feeder_schools` — top feeder school distribution (list of dicts)
- `enrollment_growth` — year-over-year comparison (dict or None)
- `section_academics` — per-section GWA data (list of dicts)

### Constants

| Constant | Description |
|----------|-------------|
| `SUBJECT_FIELDS` | List of 8 subject field names on `AcademicData` model |
| `SUBJECT_LABELS` | Human-readable short labels (e.g., `'araling_panlipunan'` -> `'AP'`) |
| `PROGRAM_NAMES` | Full program names (e.g., `'STE'` -> `'Science, Technology & Engineering'`) |
| `PROGRAM_KEY_SUBJECTS` | Which subjects to highlight per program (e.g., STE -> Math, Science) |

### Helper Functions

#### `_calculate_gwa(academic_record)`
Calculates the General Weighted Average from an `AcademicData` record by averaging all 8 subject grades. Skips `None` values. Returns `float` or `None`.

#### `_get_gwa_distribution(lrns)`
Groups students by GWA into 5 ranges: 75-79, 80-84, 85-89, 90-94, 95-100.
**Input**: list of student LRNs
**Returns**: `(ranges_dict, gwa_list)`

#### `_get_gender_distribution(lrns)`
Counts male vs female students using `StudentData.gender`.
Handles variations: `'male'`, `'m'`, `'Male'`, etc.
**Returns**: `{'Male': int, 'Female': int}`

#### `_get_subject_averages(lrns)`
Uses Django `Avg()` aggregate for efficient DB-level per-subject average calculation.
**Returns**: dict mapping each subject field to its average grade (rounded to 1 decimal)

#### `_get_section_academic_data(sections, all_selections)`
Calculates the average GWA of approved students per section.
Identifies the highest-performing section.
**Returns**: `(section_academics_list, highest_section_name, highest_avg)`

#### `_get_feeder_school_data(lrns, limit=10)`
Queries `StudentData.last_school_attended`, groups by school, orders by count descending.
**Returns**: list of `{'name': str, 'count': int}` (top 10 by default)

#### `_get_enrollment_growth(program_code, current_school_year)`
Compares enrollment count of the current active `SchoolYear` vs the most recent previous `SchoolYear` (by `start_date`).
**Returns**: dict with `current_year`, `previous_year`, `current_count`, `previous_count`, `growth_pct`, `growth_direction` — or `None` if no previous year exists

### Key Query Patterns

All enrollment queries filter by `selected_program_code` (CharField), NOT by a `program` FK:
```python
ProgramSelection.objects.filter(selected_program_code=program_code)
```

Section queries filter by `program` FK (the actual Program model object):
```python
Section.objects.filter(program=program_obj, school_year=school_year)
```

---

## Metrics Computed

| Metric | Source | Description |
|--------|--------|-------------|
| Total Applicants | `ProgramSelection.count()` | All enrollments for this program in active school year |
| Approved | `admin_approved=True` | Coordinator/AI approved |
| Rejected | `admin_rejected=True` | Coordinator/AI rejected |
| Under Review | `enrollment_status='under_review'` | Flagged by AI for manual review |
| Pending | Total - Approved - Rejected - Under Review | Not yet processed |
| Average GWA | Calculated from `AcademicData` | Mean of all student GWAs |
| Approval Rate | `(approved / total) * 100` | Percentage |
| Section Fill Rate | `(enrolled / capacity) * 100` | Across all sections |
| Highest Section | Per-section GWA comparison | Section with highest average GWA |
| Growth % | Current vs previous SchoolYear | Year-over-year enrollment change |
| Key Subject Avg | `Avg()` on specific subjects | Program-relevant subject averages |
| Key Subject 90+ % | Count where `grade >= 90` | Percentage of high-performers per key subject |

### REGULAR-Specific Metrics

| Metric | Description |
|--------|-------------|
| TOP5 Students | Students assigned to TOP5-track sections |
| HETERO Students | Students assigned to HETERO-track sections |

---

## Charts (7 Total)

All charts use **Chart.js** and are rendered in `analytics.js`. Data is injected via `window.chartData` in the template.

### 1. GWA Distribution (Vertical Bar)
- **Canvas ID**: `gwaDistributionChart`
- **Data**: 5 GWA ranges (75-79, 80-84, 85-89, 90-94, 95-100)
- **Colors**: Gray, Amber, Dark Red, Green, Blue (one per range)
- **Y-axis**: Number of students (starts at 0, step 1)

### 2. Subject-wise Averages (Horizontal Bar)
- **Canvas ID**: `subjectAveragesChart`
- **Data**: Average grade for each of the 8 subjects
- **Color**: Dark red (`#991b1b`)
- **X-axis**: Grade scale 70-100
- **Labels**: Short subject names (Math, Science, English, Filipino, AP, ESP, TLE, MAPEH)

### 3. Enrollment Status (Doughnut)
- **Canvas ID**: `enrollmentStatusChart`
- **Data**: Approved, Rejected, Under Review, Pending counts
- **Colors**: Green, Red, Amber, Gray
- **Legend**: Bottom position

### 4. Section Balance (Grouped Bar)
- **Canvas ID**: `sectionBalanceChart`
- **Data**: Two datasets — Current Students vs Max Capacity per section
- **Colors**: Dark red (current), Light gray (max)
- **Y-axis**: Student count (starts at 0, step 5)

### 5. Average GWA per Section (Vertical Bar)
- **Canvas ID**: `sectionGwaChart`
- **Data**: Average GWA per section
- **Colors**: Dark red for all, green (`#10b981`) for highest-performing section
- **Y-axis**: Grade scale 70-100
- **Header badge**: Shows top section name and GWA when available

### 6. Gender Distribution (Doughnut)
- **Canvas ID**: `genderDistributionChart`
- **Data**: Male and Female counts
- **Colors**: Blue (male), Pink (female)
- **Legend**: Bottom position

### 7. Feeder Schools (Horizontal Bar)
- **Canvas ID**: `feederSchoolsChart`
- **Data**: Top 10 feeder schools by student count
- **Color**: Dark red (`#991b1b`)
- **X-axis**: Number of students (starts at 0, step 1)
- **Conditional**: Only rendered if feeder school data exists
- **Note**: School names truncated to 20 characters in chart labels

---

## Template Layout (`analytics.html`)

### Structure

1. **Sidebar** — Fixed left navigation (shared coordinator layout)
2. **Header** — Page title, program label, coordinator name/photo, print button
3. **Key Metrics Row** — 4 cards: Total Applicants, Average GWA, Approval Rate, Section Fill Rate
4. **Enrollment Growth Card** — Conditional banner showing year-over-year change (gradient red)
5. **Key Subject Highlights** — Dynamic grid of program-specific subject cards (average + % scoring 90+)
6. **Charts Grid** — 2-column layout with 6 chart cards
7. **Feeder Schools Chart** — Full-width conditional chart
8. **Detailed Analytics Section**:
   - Gender Breakdown (progress bars)
   - Enrollment Summary (status counts)
   - Section Capacity (fill rate)
   - Data Table (all metrics in tabular format)

### Data Injection Pattern

Django context is converted to JavaScript via the `|safe` template filter:
```html
<script>
    window.chartData = {
        gwaDistribution: {{ chart_data.gwa_distribution|safe }},
        enrollmentStatus: {{ chart_data.enrollment_status|safe }},
        ...
    };
</script>
```

The static JS file (`analytics.js`) reads from `window.chartData` on `DOMContentLoaded`.

### Dependencies

| Library | CDN | Purpose |
|---------|-----|---------|
| Tailwind CSS | `cdn.tailwindcss.com` | Utility-first styling |
| Chart.js | `cdn.jsdelivr.net/npm/chart.js` | Chart rendering |
| Font Awesome 6 | `cdnjs.cloudflare.com` | Icons |
| Google Fonts | Poppins + Playfair Display | Typography |

---

## Program-Specific Behavior

### Key Subject Highlights

Each program has designated "key subjects" that are highlighted with dedicated metric cards:

| Program | Key Subjects |
|---------|-------------|
| STE | Mathematics, Science |
| SPFL | English, Filipino |
| SPTVE | TLE (Edukasyon Pangkabuhayan) |
| REGULAR | Mathematics, English, Science |
| OHSP | English, Mathematics |
| SNED | English, Filipino, Mathematics |

Each key subject card shows:
- Average grade across all program applicants
- Count and percentage of students scoring 90+

### REGULAR Program Track Breakdown

When `program_code == 'REGULAR'`, additional metrics are computed:
- TOP5 student count (students in TOP5-track sections)
- HETERO student count (students in HETERO-track sections)
- Track Balance chart data (TOP5 vs HETERO distribution)

---

## Database Models Referenced

| Model | App | Key Fields Used |
|-------|-----|----------------|
| `ProgramSelection` | enrollment_app | `selected_program_code`, `admin_approved`, `admin_rejected`, `assigned_section`, `school_year`, `student` |
| `AcademicData` | enrollment_app | 8 subject fields (mathematics, science, english, filipino, araling_panlipunan, edukasyon_sa_pagpapakatao, edukasyon_pangkabuhayan, mapeh) |
| `StudentData` | enrollment_app | `gender`, `last_school_attended` |
| `Student` | enrollment_app | `lrn`, `enrollment_status` |
| `Section` | admin_app | `program`, `school_year`, `name`, `max_students`, `regular_track`, `get_actual_count()` |
| `SchoolYear` | admin_app | `is_active`, `start_date`, `year_label` |
| `UserProfile` | admin_app | `program`, `photo` |

---

## Print Support

The analytics page supports browser printing via the `printAnalytics()` function, which simply calls `window.print()`. The print button is located in the page header.

---

## Notes

- All queries are scoped to the **active school year** (`SchoolYear.objects.filter(is_active=True).first()`)
- The coordinator only sees data for **their assigned program** — there is no program selector dropdown
- GWA is calculated as the arithmetic mean of all 8 subject grades (equal weight)
- Section assignment uses `assigned_section` as a CharField storing the section ID (string), not a FK
- The enrollment growth card is only shown when a previous school year exists in the database
- Feeder schools chart is only shown when feeder school data exists (non-empty `last_school_attended`)
