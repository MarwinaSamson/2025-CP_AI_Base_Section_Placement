"""
Test script for Gemini OCR Service
Tests grade and name extraction from ADELFA_3.jpg
"""

import os
import sys
import json


import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "section_placement_system.settings"  # change to your settings module
)

django.setup()
# Add your project to Python path if needed
# sys.path.insert(0, '/path/to/your/project')

# Import the Gemini OCR Verifier
# If you renamed the class to OCRGradeVerifier in ocr_service.py, use that
try:
    from enrollment_app.services.ocr_service  import GeminiAPIKeyOCR
    print("✓ Imported GeminiAPIKeyOCR from services.ocr_service")
except ImportError:
    try:
        from enrollment_app.services.ocr_service  import GeminiAPIKeyOCR
        print("✓ Imported GeminiAPIKeyOCR from ocr_service")
    except ImportError:
        print("✗ Could not import GeminiAPIKeyOCR")
        print("Make sure ocr_service.py is in your path")
        sys.exit(1)


def test_ocr_extraction():
    """Test OCR extraction on ADELFA_3.jpg"""
    
    print("\n" + "="*70)
    print("GEMINI OCR TEST - ADELFA_3.jpg")
    print("="*70)
    
    # Image path
    image_path = "report_card.jpg"
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"\n✗ Error: Image file not found: {image_path}")
        print(f"  Current directory: {os.getcwd()}")
        print(f"  Files in current directory:")
        for f in os.listdir('.'):
            if f.endswith(('.jpg', '.jpeg', '.png')):
                print(f"    - {f}")
        return
    
    print(f"\n✓ Image file found: {image_path}")
    print(f"  Size: {os.path.getsize(image_path) / 1024:.2f} KB")
    
    # Initialize verifier
    try:
        print("\n[1] Initializing Gemini OCR Verifier...")
        verifier = OCRGradeVerifier(tolerance=3.0)
        print("✓ Verifier initialized")
    except Exception as e:
        print(f"\n✗ Failed to initialize verifier: {e}")
        print("\nTroubleshooting:")
        print("1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("   export GOOGLE_APPLICATION_CREDENTIALS='path/to/service-account.json'")
        print("2. OR set GEMINI_API_KEY")
        print("   export GEMINI_API_KEY='your-api-key'")
        return
    
    # Extract grades and name
    try:
        print("\n[2] Extracting grades and name from image...")
        result = verifier.extract_grades_and_name_from_image(image_path)
        
        print("\n" + "="*70)
        print("EXTRACTION RESULTS")
        print("="*70)
        
        # Display student name
        student_name = result.get('student_name')
        print(f"\n📛 Student Name: {student_name or 'NOT FOUND'}")
        
        # Display grades
        grades = result.get('grades', {})
        print(f"\n📊 Grades Extracted: {len(grades)}/8 subjects")
        print("-" * 70)
        
        if grades:
            print("\nSubject Grades:")
            for subject, grade in grades.items():
                subject_display = subject.replace('_', ' ').title()
                print(f"  {subject_display:30s}: {grade}")
        else:
            print("  ⚠ No grades extracted")
        
        # Calculate average
        if grades:
            avg = sum(grades.values()) / len(grades)
            print(f"\n📈 Overall Average: {avg:.2f}")
        
        print("\n" + "="*70)
        
        # Test name verification
        print("\n[3] Testing Name Verification...")
        print("-" * 70)
        
        # Test cases
        test_names = [
            "ADELFA GIRL",  # Example - replace with actual name if you know it
            "SMITH, JOHN A.",  # Mismatch test
        ]
        
        if student_name:
            print(f"\nExtracted Name: '{student_name}'")
            
            for test_name in test_names:
                verification = verifier.verify_student_name(student_name, test_name)
                print(f"\nTest: '{test_name}'")
                print(f"  Match: {verification['is_match']}")
                print(f"  Similarity: {verification['similarity']}%")
                print(f"  Reason: {verification['reason']}")
        else:
            print("  ⚠ Cannot test - no name extracted")
        
        # Test grade verification
        print("\n" + "="*70)
        print("[4] Testing Grade Verification...")
        print("-" * 70)
        
        if grades:
            # Create manual grades (same as extracted for perfect match test)
            manual_grades = grades.copy()
            
            print("\nTest 1: Perfect Match (manual = extracted)")
            verification = verifier.verify_grades(grades, manual_grades)
            print(f"  Match: {verification['is_match']}")
            print(f"  Confidence: {verification['confidence']}%")
            print(f"  Matched: {verification['matched']}/{verification['total']}")
            
            # Test with one mismatch
            if 'filipino' in manual_grades:
                manual_grades_mismatch = manual_grades.copy()
                manual_grades_mismatch['filipino'] = 85  # Change one grade
                
                print("\nTest 2: One Mismatch (Filipino changed to 85)")
                verification = verifier.verify_grades(grades, manual_grades_mismatch)
                print(f"  Match: {verification['is_match']}")
                print(f"  Confidence: {verification['confidence']}%")
                print(f"  Matched: {verification['matched']}/{verification['total']}")
                
                if verification['mismatches']:
                    print(f"  Mismatches:")
                    for m in verification['mismatches']:
                        print(f"    - {m['subject']}: Expected {m['expected']}, Got {m.get('actual', 'N/A')}")
        else:
            print("  ⚠ Cannot test - no grades extracted")
        
        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)
        
        # Save results to JSON
        output_file = "ocr_test_results.json"
        with open(output_file, 'w') as f:
            json.dump({
                'image': image_path,
                'student_name': student_name,
                'grades': grades,
                'grade_count': len(grades),
                'average': sum(grades.values()) / len(grades) if grades else 0,
            }, f, indent=2)
        
        print(f"\n✓ Results saved to: {output_file}")
        
        return result
        
    except Exception as e:
        print(f"\n✗ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("Starting Gemini OCR Test...")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check environment variables
    print("\nEnvironment Check:")
    if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        print(f"  ✓ GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")
    elif os.environ.get('GEMINI_API_KEY'):
        print(f"  ✓ GEMINI_API_KEY: {'*' * 20}")
    else:
        print("  ⚠ No credentials found in environment")
        print("    Set one of:")
        print("      export GOOGLE_APPLICATION_CREDENTIALS='path/to/service-account.json'")
        print("      export GEMINI_API_KEY='your-api-key'")
    
    # Run test
    result = test_ocr_extraction()
    
    if result:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed - check errors above")