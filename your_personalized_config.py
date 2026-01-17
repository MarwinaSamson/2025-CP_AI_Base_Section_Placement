"""
Your Personalized Document AI Configuration
Pre-configured with your Google Cloud credentials

Project ID: 1094485135926
Processor ID: a0cbcc2e3afe7ae0
Location: us
"""

import os

# ============================================
# YOUR GOOGLE CLOUD CONFIGURATION
# ============================================

PROJECT_ID = "1094485135926"
PROCESSOR_ID = "a0cbcc2e3afe7ae0"
LOCATION = "us"

# ============================================
# SETUP VERIFICATION
# ============================================

def verify_setup():
    """Verify your Document AI setup is working."""
    print("\n" + "="*70)
    print("VERIFYING YOUR DOCUMENT AI SETUP")
    print("="*70)
    
    print(f"\nProject ID:  {PROJECT_ID}")
    print(f"Processor ID: {PROCESSOR_ID}")
    print(f"Location:    {LOCATION}")
    
    # Set environment variables
    os.environ['GOOGLE_CLOUD_PROJECT'] = PROJECT_ID
    os.environ['DOCUMENT_AI_PROCESSOR_ID'] = PROCESSOR_ID
    os.environ['DOCUMENT_AI_LOCATION'] = LOCATION
    
    print("\n✓ Environment variables set")
    
    try:
        from google.cloud import documentai
        print("✓ google-cloud-documentai installed")
    except ImportError:
        print("✗ google-cloud-documentai not installed")
        print("  Run: pip install --upgrade google-cloud-documentai")
        return False
    
    try:
        from google.auth import default
        credentials, project = default()
        print("✓ Google Cloud credentials found")
    except Exception as e:
        print(f"✗ Credentials error: {e}")
        return False
    
    try:
        client = documentai.DocumentProcessorServiceClient()
        processor_name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
        processor = client.get_processor(name=processor_name)
        print(f"✓ Processor found: {processor.display_name}")
        print(f"  State: {processor.state}")
        return True
    except Exception as e:
        print(f"✗ Processor error: {e}")
        return False

# ============================================
# QUICK START CODE
# ============================================

def extract_grades(image_path):
    """
    Quick example: Extract grades from a report card image.
    
    Usage:
        from your_personalized_config import extract_grades
        grades = extract_grades('path/to/report_card.jpg')
        print(grades)
    """
    from enrollment_app.services.ocr_service import OCRGradeVerifier
    
    # Initialize with your credentials
    verifier = OCRGradeVerifier(
        tolerance=3.0,
        project_id=PROJECT_ID,
        processor_id=PROCESSOR_ID,
        location=LOCATION
    )
    
    # Extract grades
    grades = verifier.extract_grades_from_image(image_path)
    return grades

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    print("\n🚀 Your Personalized Document AI Setup\n")
    
    success = verify_setup()
    
    if success:
        print("\n" + "="*70)
        print("✅ SETUP SUCCESSFUL!")
        print("="*70)
        print("\nYou can now extract grades with:")
        print("  python -c \"from your_personalized_config import extract_grades; print(extract_grades('report.jpg'))\"")
        print("\nOr import and use in your code:")
        print("  from your_personalized_config import extract_grades")
        print("  grades = extract_grades('path/to/report.jpg')")
    else:
        print("\n" + "="*70)
        print("❌ SETUP FAILED - TROUBLESHOOTING NEEDED")
        print("="*70)
        print("\nRun: python test_document_ai_setup.py --verbose")
        print("See: DOCUMENT_AI_MIGRATION.md#troubleshooting")
