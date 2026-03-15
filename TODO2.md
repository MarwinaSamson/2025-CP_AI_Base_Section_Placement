.py# TASK 2: Enrollment Filter Fix
## Status: [ ] Planning

### Step 1: Backend - Rewrite enrollment_requests [ ]
- Target `admin_app/views/enrollment_views.py`
- Replace legacy Student query → StudentEnrollment joins
- Add grade_level + program + status filters
- Test G8+REGULAR+Approved

### Step 2: Frontend - JS Filter Params [ ]
- `admin_app/templates/admin_app/enrollment.html`
- Update filter dropdown → GET params
- Refresh table on change

### Step 3: Test & Complete [ ]
- Create test data
- Verify G8/REGULAR/Approved works

Ready: Confirm → Execute Step 1
