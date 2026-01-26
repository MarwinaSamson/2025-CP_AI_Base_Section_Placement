import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
import django
django.setup()

from enrollment_app.services.ocr_service import OCRGradeVerifier

if __name__ == "__main__":
    image_path = "MudanBoys_7.jpg"
    verifier = OCRGradeVerifier(tolerance=3.0)
    result = verifier.extract_grades_and_name_from_image(image_path)
    print("\n--- OCR Test Result ---")
    print(f"Student Name: {result.get('student_name')}")
    print("Grades:")
    for subject, grade in result.get('grades', {}).items():
        print(f"  {subject}: {grade}")
    print("\nFull Text Extracted:")
    print(result.get('full_text'))