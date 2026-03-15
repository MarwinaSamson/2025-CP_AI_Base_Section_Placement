# Enrollment System Testing Progress

## TODO Steps
- [x] Create TODO.md
- [ ] Update create_test_transferee.py ✅
- [ ] Create create_test_new.py ✅
- [ ] Run `python manage.py create_test_new_fixed` 
- [ ] Run `python manage.py create_test_transferee_fixed`
- [ ] Verify DB: StudentEnrollment for both LRNs
- [ ] Later: Continuing student

## Run Commands
```bash
python manage.py create_test_new           # New: 126113180161
python manage.py create_test_transferee    # Transferee: 199006180405
```

## Verification
```python
python manage.py shell
from enrollment_app.models import StudentEnrollment
from admin_app.models import SchoolYear
sy = SchoolYear.objects.filter(is_active=True).first()
print(StudentEnrollment.objects.filter(school_year=sy).values('student__lrn', 'enrollee_type', 'enrollment_status'))
```

