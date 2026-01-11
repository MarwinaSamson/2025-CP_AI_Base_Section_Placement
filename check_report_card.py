import os
import django

# ------------------------------------------------------------------
# Django setup
# ------------------------------------------------------------------
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "section_placement_system.settings"
)
django.setup()

from enrollment_app.services.ocr_service import OCRGradeVerifier


def main():
    print("\n📘 REPORT CARD GRADE VERIFICATION")
    print("=" * 50)

    image_path = r"shared_assets/static/images/ADELFA_3.jpg"

    # Manual grades input
    manual_grades = {
        "mathematics": 78,
        "filipino": 78,
        "english": 79,
        "science": 79,
        "araling_panlipunan": 80,
        "edukasyon_sa_pagpapakatao": 78,
        "edukasyon_pangkabuhayan": 79,
        "mapeh": 80,
    }

    verifier = OCRGradeVerifier(tolerance=2.0)

    # ------------------------------------------------------------------
    # OCR Extraction
    # ------------------------------------------------------------------
    print("\n📸 Extracting grades from image...")
    extracted = verifier.extract_grades_from_image(image_path)

    if not extracted:
        print("\n⚠️ WARNING: No grades were extracted from OCR.")
        print("This usually means:")
        print("- OCR text was detected but not parsed")
        print("- Subject names did not match parser rules")
        print("- Handwritten grades need improved parsing\n")

    print("\n📄 OCR Extracted Grades:")
    print(extracted)

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------
    result = verifier.verify_grades(extracted, manual_grades)

    print("\n🔎 VERIFICATION RESULT")
    print("=" * 50)

    print(f"Match: {result.get('is_match', False)}")
    print(f"Confidence: {result.get('confidence', 0)}%")

    mismatches = result.get("mismatches", {})

    if mismatches:
        print("\n❌ Mismatches:")
        for subject, values in mismatches.items():
            print(
                f"- {subject}: "
                f"manual={values.get('manual')} | "
                f"ocr={values.get('ocr')}"
            )
    else:
        print("\n✅ All comparable grades matched")

    # ------------------------------------------------------------------
    # Safe message output
    # ------------------------------------------------------------------
    message = result.get(
        "message",
        "Verification completed."
    )

    print("\n📝 Message:")
    print(message)


if __name__ == "__main__":
    main()
