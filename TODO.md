# Dynamic Notification Backend Implementation
## Status: [ ] Not Started

### Step 1: Backend - Update dashboard_notifications API [ ]
- [ ] Edit `admin_app/views/dashboard_views.py`
  - Add `?tab=pending|review|approved` param
  - Query `StudentEnrollment.enrollment_status` per tab
  - Test: `curl http://localhost:8000/admin/api/dashboard/notifications/?tab=review`

### Step 2: Frontend - Multi-tab Fetch [ ]
- [ ] Edit `admin_app/templates/admin_app/base.html` (JS)
  - Parallel `Promise.all()` for 3 tabs on drawer open
  - Badge: pending + review sum
  - Test: All tabs populate in drawer

### Step 3: Verify URLs/Routing [ ]
- [ ] Check `admin_app/urls.py` has `api/dashboard/notifications/`
- [ ] Test all endpoints work

### Step 4: Test & Validate [ ]
- [ ] `python manage.py runserver`
- [ ] Create test data: Students with 'submitted'/'under_review'/'approved'
- [ ] Load dashboard → Bell badge + drawer tabs correct

### Step 5: Complete [ ]
- [ ] Update TODO.md: Mark all complete
- [ ] `attempt_completion`: "Notification backend fully dynamic ✅"

**Estimated Time**: 30-45 min  
**Risks**: None (uses existing fields/queries)
