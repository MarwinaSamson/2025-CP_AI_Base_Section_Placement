"""
Script to manually assign temp photos to students
Run with: python manage.py shell < fix_photos.py
"""

import os
import shutil
from django.conf import settings
from enrollment_app.models import Student, StudentData, FamilyData

# Get temp directory
temp_dir = os.path.join(settings.BASE_DIR, 'temp_uploads')
temp_files = sorted([f for f in os.listdir(temp_dir) if os.path.isfile(os.path.join(temp_dir, f))])

print(f"\n{'='*60}")
print(f"PHOTO MIGRATION TOOL")
print(f"{'='*60}\n")
print(f"Found {len(temp_files)} files in temp_uploads/\n")

# Get all students without photos
students_without_photos = Student.objects.filter(
    student_data__student_photo__isnull=True
) | Student.objects.filter(
    student_data__student_photo=''
)

students_without_photos = students_without_photos.select_related('student_data').distinct()

print(f"Students without photos: {students_without_photos.count()}\n")

# List students
print("Students needing photos:")
print("-" * 60)
for i, student in enumerate(students_without_photos[:10], 1):
    if hasattr(student, 'student_data'):
        sd = student.student_data
        name = f"{sd.first_name} {sd.last_name}"
    else:
        name = "No data"
    print(f"{i}. LRN: {student.lrn} - {name}")

print("\n" + "="*60)
print("To assign photos manually, use Django admin or run this:")
print("="*60)
print("""
# Example: Assign first temp photo to first student
from enrollment_app.models import Student, StudentData
import os, shutil
from django.conf import settings

student = Student.objects.get(lrn='YOUR_LRN_HERE')
temp_file = 'TEMP_FILENAME_HERE'

# Create permanent directory
media_dir = os.path.join(settings.MEDIA_ROOT, 'student_photos')
os.makedirs(media_dir, exist_ok=True)

# Move file
temp_path = os.path.join(settings.BASE_DIR, 'temp_uploads', temp_file)
new_filename = f"{student.lrn}_photo.jpg"
permanent_path = os.path.join(media_dir, new_filename)
shutil.move(temp_path, permanent_path)

# Update database
student.student_data.student_photo = f"student_photos/{new_filename}"
student.student_data.save()

print(f"✓ Photo saved for {student.lrn}")
""")

print("\n" + "="*60)
print("Or use Django Admin at: http://localhost:8000/admin/")
print("Upload photos directly to StudentData records")
print("="*60 + "\n")
