"""
Test the UPDATED OCR Grade Verification Service
- Extract grades from report card image
- Verify against expected actual grades
"""

import os
import django

# -------------------------------------------------
# Django setup
# -------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "section_placement_system.settings")
django.setup()

# -------------------------------------------------
# Import your UPDATED OCR service
# -------------------------------------------------
from enrollment_app.services.ocr_service import OCRGradeVerifier


def test_updated_ocr(image_path):
    print("=" * 80)
    print("TESTING UPDATED OCR GRADE VERIFICATION SERVICE".center(80))
    print("=" * 80)

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return

    # -------------------------------------------------
    # Expected grades (GROUND TRUTH)
    # -------------------------------------------------
    expected_grades = {
        'filipino': 92,
        'english': 87,
        'mathematics': 89,
        'science': 91,
        'edukasyon_sa_pagpapakatao': 91,
        'araling_panlipunan': 93,
        'edukasyon_pangkabuhayan': 93,
        'mapeh': 86,
    }


    verifier = OCRGradeVerifier(tolerance=2.0)

    # -------------------------------------------------
    # STEP 1: Extract grades
    # -------------------------------------------------
    print("\nSTEP 1: EXTRACTING GRADES FROM IMAGE")
    print("-" * 80)

    extracted_grades = verifier.extract_grades_from_image(image_path)

    if not extracted_grades:
        print("❌ No grades extracted!")
        return

    for subject, grade in extracted_grades.items():
        print(f"  {subject.replace('_', ' ').title():<30} → {grade}")

    # -------------------------------------------------
    # STEP 2: Verification
    # -------------------------------------------------
    print("\nSTEP 2: VERIFYING AGAINST EXPECTED GRADES")
    print("-" * 80)

    verification_result = verifier.verify_grades(
        extracted_grades,
        expected_grades
    )


    # -------------------------------------------------
    # STEP 3: Results
    # -------------------------------------------------
    print("\nVERIFICATION RESULT")
    print("-" * 80)

    print(f"Matched    : {verification_result['matched']}/{verification_result['total']}")
    print(f"Confidence : {verification_result['confidence']:.1f}%")

    print("\nSubject Comparison:")
    correct = 0

    for subject, expected in expected_grades.items():
        actual = extracted_grades.get(subject)

        if actual is None:
            print(f"  ✗ {subject.replace('_', ' ').title():<30} NOT EXTRACTED")
        else:
            diff = abs(actual - expected)
            if diff <= verifier.tolerance:
                print(f"  ✓ {subject.replace('_', ' ').title():<30} {actual} (expected {expected})")
                correct += 1
            else:
                print(f"  ✗ {subject.replace('_', ' ').title():<30} {actual} (expected {expected}, diff {diff})")

    accuracy = (correct / len(expected_grades)) * 100
    print(f"\nAccuracy: {correct}/{len(expected_grades)} = {accuracy:.1f}%")

    if accuracy >= 75:
        print("✅ PASS — OCR verification is acceptable")
    else:
        print("❌ FAIL — OCR verification needs improvement")


# -------------------------------------------------
# Run test
# -------------------------------------------------
if __name__ == "__main__":
    image_path = os.path.join(
        "shared_assets",
        "static",
        "images",
        "MudanBoys_7.jpg"
    )

    test_updated_ocr(image_path)
