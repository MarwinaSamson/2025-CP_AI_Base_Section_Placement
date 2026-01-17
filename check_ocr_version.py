"""
Quick check to see which OCR version you're using
"""



import sys
sys.path.insert(0, 'enrollment_app/services')
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
django.setup()

try:
    from enrollment_app.services.ocr_service import OCRGradeVerifier
    
    print("Checking your current OCR service...")
    print("="*70)
    
    # Check if it has the new methods
    has_preprocessing = hasattr(OCRGradeVerifier, 'preprocess_image')
    has_digit_correction = hasattr(OCRGradeVerifier, 'apply_digit_corrections')
    has_validation = hasattr(OCRGradeVerifier, 'validate_grade_ranges')
    
    print(f"✓ Has preprocess_image:         {has_preprocessing}")
    print(f"✓ Has apply_digit_corrections:  {has_digit_correction}")
    print(f"✓ Has validate_grade_ranges:    {has_validation}")
    
    # Check init parameters
    import inspect
    init_sig = inspect.signature(OCRGradeVerifier.__init__)
    params = list(init_sig.parameters.keys())
    
    print(f"\n__init__ parameters: {params}")
    has_enable_preprocessing = 'enable_preprocessing' in params
    print(f"✓ Has enable_preprocessing param: {has_enable_preprocessing}")
    
    print("\n" + "="*70)
    
    if has_preprocessing and has_digit_correction and has_validation:
        print("✅ You have the COMPLETE ENHANCED version!")
        print("   File is ready for handwriting optimization.")
    elif has_preprocessing or has_digit_correction:
        print("⚠️  You have a PARTIAL enhanced version")
        print("   Some methods are missing. Replace the file.")
    else:
        print("❌ You have the OLD version (no preprocessing)")
        print("   You need to replace ocr_service.py with complete_enhanced_ocr.py")
    
    print("\n" + "="*70)
    print("To update:")
    print("  1. Backup: copy enrollment_app\\services\\ocr_service.py enrollment_app\\services\\ocr_service_OLD.py")
    print("  2. Replace: copy complete_enhanced_ocr.py enrollment_app\\services\\ocr_service.py")
    print("  3. Test: python test_ocr_with_image.py")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()