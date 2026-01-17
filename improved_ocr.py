import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Now import and test
from enrollment_app.services.ocr_service import OCRGradeVerifier

def test():
    verifier = OCRGradeVerifier(tolerance=3.0)
    
    # Test with your image
    image_path = "shared_assets/static/images/MudanBoys_7.jpg"
    
    print("Extracting grades...")
    extracted = verifier.extract_grades_from_image(image_path)
    
    print("\nExtracted:")
    for subject, grade in extracted.items():
        print(f"  {subject}: {grade}")
    
    # Verify
    manual = {
        'filipino': 93.0,
        'english': 93.0,
        'science': 93.0,
        'mathematics': 93.0,
        'araling_panlipunan': 93.0,
        'edukasyon_sa_pagpapakatao': 97.0,
        'edukasyon_pangkabuhayan': 92.0,
        'mapeh': 92.0
    }
    
    result = verifier.verify_grades(extracted, manual)
    print(f"\nMatch: {result['is_match']}")
    print(f"Confidence: {result['confidence']}%")

if __name__ == "__main__":
    test()