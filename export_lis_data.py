import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
django.setup()

from admin_app.models import LISStudent

students = LISStudent.objects.all()

result = []
if students.exists():
    result.append("INSERT INTO lis_students (lrn, first_name, last_name, birth_date, last_school) VALUES")
    values = []
    for student in students:
        value = f"('{student.lrn}', '{student.first_name}', '{student.last_name}', '{student.birth_date}', '{student.last_school}')"
        values.append(value)
    result.append(",\n".join(values) + ";")
    output = "\n".join(result)
    print(output)
    with open('lis_insert.sql', 'w') as f:
        f.write(output)
    print("\n✓ SQL saved to lis_insert.sql")
else:
    print("No LIS students found in database")
