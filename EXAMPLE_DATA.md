# Admin Dashboard - Example Database Data

This file shows what data should exist in your database for the dashboard to work properly.

## 1. SchoolYear (Active)

```python
SchoolYear.objects.create(
    year_label="2025-2026",
    start_date=date(2025, 8, 1),
    end_date=date(2026, 5, 31),
    is_active=True,
    enrollment_open=True
)
```

**Important:** At least ONE SchoolYear must have `is_active=True`

---

## 2. User & UserProfile

### User Model

```python
from django.contrib.auth.models import User

user = User.objects.create_user(
    username='john.doe',
    email='john@example.com',
    first_name='John',
    last_name='Doe',
    password='secure_password'
)
```

### UserProfile Model

```python
from admin_app.models import UserProfile, Program

program = Program.objects.get(code='STE')

profile = UserProfile.objects.create(
    user=user,
    user_type='admin',  # or 'coordinator'
    program=program,
    employee_id='EMP001'
)
```

**What the dashboard will show:**

- Full Name: "John Doe"
- Role: "Admin"
- Initials: "JD"
- Program: "STE"

---

## 3. Programs

```python
programs = [
    Program.objects.create(
        code='STE',
        name='Science, Technology, and Engineering',
        is_active=True
    ),
    Program.objects.create(
        code='HETERO',
        name='Heterogeneous Class',
        is_active=True
    ),
    Program.objects.create(
        code='TOP 5',
        name='Top 5 Regular Section',
        is_active=True
    ),
    # Add more programs as needed...
]
```

**Dashboard will count:** Total active programs

---

## 4. Teachers

```python
from admin_app.models import Teacher, Position, Department

position = Position.objects.create(name='Master Teacher I')
department = Department.objects.create(name='Science')

teachers = [
    Teacher.objects.create(
        first_name='Alice',
        middle_name='M',
        last_name='Johnson',
        email='alice@school.edu',
        position=position,
        department=department,
        is_active=True
    ),
    Teacher.objects.create(
        first_name='Bob',
        middle_name='J',
        last_name='Smith',
        email='bob@school.edu',
        position=position,
        department=department,
        is_active=True
    ),
]
```

**Dashboard will count:** Total active teachers

---

## 5. Sections

```python
from admin_app.models import Section

school_year = SchoolYear.objects.get(year_label='2025-2026')
hetero_program = Program.objects.get(code='HETERO')
teacher = Teacher.objects.first()

sections = [
    Section.objects.create(
        school_year=school_year,
        program=hetero_program,
        name='7-HETERO-A',
        adviser=teacher,
        building='Building A',
        room='A-101',
        max_students=40,
        current_students=38
    ),
    Section.objects.create(
        school_year=school_year,
        program=hetero_program,
        name='7-HETERO-B',
        adviser=teacher,
        building='Building A',
        room='A-102',
        max_students=40,
        current_students=40
    ),
]
```

**Dashboard will show:**

- Total sections: 2
- Total capacity: 80
- Filled: 78/80 (97.5%)

---

## 6. Students

```python
from enrollment_app.models import Student, StudentData

school_year = SchoolYear.objects.get(year_label='2025-2026')

students = []
for i in range(1, 26):
    lrn = f'12345678901{i:02d}'
    student = Student.objects.create(
        lrn=lrn,
        email=f'student{i}@school.edu',
        school_year=school_year,
        enrollment_status='submitted',  # Important: for notifications
        program_selected=True  # Important: for notifications
    )

    # Create student data
    StudentData.objects.create(
        student=student,
        first_name=f'Student',
        last_name=f'Number {i}',
        gender='male' if i % 2 == 0 else 'female',
        date_of_birth=date(2010, 1, 1)
    )

    students.append(student)
```

---

## 7. Program Selections

```python
from enrollment_app.models import ProgramSelection

school_year = SchoolYear.objects.get(year_label='2025-2026')
hetero_program = Program.objects.get(code='HETERO')
students = Student.objects.filter(school_year=school_year)

for student in students:
    ProgramSelection.objects.create(
        student=student,
        school_year=school_year,
        selected_program_code=hetero_program.code,
        program_description=hetero_program.name,
        admin_approved=False
    )
```

**Dashboard will show:**

- New notifications: "25 new HETERO applications pending review"
- Enrollment metrics in programs table

---

## Complete Data Creation Script

```python
from django.contrib.auth.models import User
from admin_app.models import (
    SchoolYear, UserProfile, Program, Teacher,
    Position, Department, Section
)
from enrollment_app.models import Student, StudentData, ProgramSelection
from datetime import date

# 1. Create SchoolYear
school_year = SchoolYear.objects.create(
    year_label='2025-2026',
    start_date=date(2025, 8, 1),
    end_date=date(2026, 5, 31),
    is_active=True,
    enrollment_open=True
)
print(f"✓ Created SchoolYear: {school_year.year_label}")

# 2. Create User
user = User.objects.create_user(
    username='admin.user',
    email='admin@school.edu',
    first_name='Admin',
    last_name='User',
    password='admin123'
)
print(f"✓ Created User: {user.get_full_name()}")

# 3. Create Programs
programs = {}
program_data = [
    ('STE', 'Science, Technology, and Engineering'),
    ('HETERO', 'Heterogeneous Class'),
    ('TOP 5', 'Top 5 Regular Section'),
    ('SPFL', 'Special Program in Foreign Language'),
    ('SPTVE', 'Special Program in Technical-Vocational Education'),
    ('OHSP', 'Open High School Program'),
    ('SNED', 'Special Needs Education'),
]

for code, name in program_data:
    program = Program.objects.create(
        code=code,
        name=name,
        is_active=True
    )
    programs[code] = program
print(f"✓ Created {len(programs)} Programs")

# 4. Create Position & Department
position = Position.objects.create(name='Master Teacher I')
department = Department.objects.create(name='Science')
print("✓ Created Position and Department")

# 5. Create UserProfile
profile = UserProfile.objects.create(
    user=user,
    user_type='admin',
    program=programs['STE'],
    position=position,
    department=department,
    employee_id='ADM001'
)
print(f"✓ Created UserProfile for {user.get_full_name()}")

# 6. Create Teachers
teachers = []
for i in range(1, 6):
    teacher = Teacher.objects.create(
        first_name=f'Teacher {i}',
        last_name=f'Name {i}',
        email=f'teacher{i}@school.edu',
        position=position,
        department=department,
        is_active=True
    )
    teachers.append(teacher)
print(f"✓ Created {len(teachers)} Teachers")

# 7. Create Sections
sections = []
for prog_code in ['HETERO', 'STE', 'TOP 5']:
    program = programs[prog_code]
    for i in range(1, 4):
        section = Section.objects.create(
            school_year=school_year,
            program=program,
            name=f'7-{prog_code}-{chr(64+i)}',
            adviser=teachers[i-1],
            building='Building A',
            room=f'A-{100+i}',
            max_students=40,
            current_students=38
        )
        sections.append(section)
print(f"✓ Created {len(sections)} Sections")

# 8. Create Students with StudentData
students = []
for i in range(1, 26):
    lrn = f'12345678901{i:02d}'
    student = Student.objects.create(
        lrn=lrn,
        email=f'student{i}@school.edu',
        school_year=school_year,
        enrollment_status='submitted',
        program_selected=True
    )

    StudentData.objects.create(
        student=student,
        first_name=f'Student',
        last_name=f'Number {i}',
        gender='male' if i % 2 == 0 else 'female',
        date_of_birth=date(2010, 1, 1)
    )

    students.append(student)
print(f"✓ Created {len(students)} Students with StudentData")

# 9. Create ProgramSelections
hetero_program = programs['HETERO']
for student in students:
    ProgramSelection.objects.create(
        student=student,
        school_year=school_year,
        selected_program_code=hetero_program.code,
        program_description=hetero_program.name,
        admin_approved=False
    )
print(f"✓ Created {len(students)} ProgramSelections")

print("\n✅ All test data created successfully!")
print(f"\nDashboard will show:")
print(f"  • School Year: {school_year.year_label}")
print(f"  • User: {user.get_full_name()} ({profile.get_user_type_display()})")
print(f"  • Total Teachers: {len(teachers)}")
print(f"  • Total Students: {len(students)}")
print(f"  • Total Programs: {len(programs)}")
print(f"  • Total Sections: {len(sections)}")
print(f"  • New Enrollments (HETERO): {len(students)}")
```

---

## How to Use This Data

### Option 1: Django Shell

```bash
# Open Django shell
python manage.py shell

# Copy and paste the complete script above
```

### Option 2: Django Admin Panel

1. Go to `/admin/`
2. Create objects manually through the admin interface
3. Make sure:
   - SchoolYear has `is_active=True`
   - Student has `enrollment_status='submitted'` and `program_selected=True`
   - UserProfile exists for logged-in user

### Option 3: Fixtures

Save as `fixture.json` and load with:

```bash
python manage.py loaddata fixture.json
```

---

## Verification Checklist

After creating data, verify in Django admin:

- [ ] SchoolYear with `is_active=True` exists
- [ ] UserProfile exists for your user
- [ ] Program(s) with `is_active=True` exist
- [ ] Teacher(s) with `is_active=True` exist
- [ ] Section(s) linked to active SchoolYear exist
- [ ] Student(s) with `enrollment_status='submitted'` exist
- [ ] Student(s) with `program_selected=True` exist
- [ ] ProgramSelection(s) exist with correct program_code

---

## Expected Dashboard Output

With the example data above, your dashboard should show:

### Header

- School Year: "2025-2026"
- User: "Admin User"
- Role: "Admin"
- Initials: "AU"

### Statistics

- Total Teachers: 5+
- Total Students: 25+
- Total Programs: 7
- Total Sections: 9+

### Notifications

- New HETERO applications: 25

### Programs Table

- Shows all 7 programs
- HETERO: 25 applicants (pending)
- Others: 0 applicants
- Capacity utilization varies
