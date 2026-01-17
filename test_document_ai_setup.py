"""
Document AI Setup Verification and Testing Utility

This script validates your Document AI configuration and tests the OCR service.

Usage:
    python test_document_ai_setup.py
    python test_document_ai_setup.py --test-image path/to/report_card.jpg
    python test_document_ai_setup.py --verbose
"""

import os
import sys
import argparse
from pathlib import Path


def check_environment_variables():
    """Check if required environment variables are set."""
    print("\n" + "="*70)
    print("1. CHECKING ENVIRONMENT VARIABLES")
    print("="*70)
    
    required_vars = {
        'GOOGLE_CLOUD_PROJECT': 'Google Cloud Project ID',
        'DOCUMENT_AI_PROCESSOR_ID': 'Document AI Processor ID',
        'GOOGLE_APPLICATION_CREDENTIALS': 'Service Account Credentials File',
    }
    
    optional_vars = {
        'DOCUMENT_AI_LOCATION': 'Document AI Region (default: us)',
    }
    
    all_good = True
    
    # Check required
    print("\nRequired Variables:")
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'CREDENTIALS' in var:
                display = "✓ Set (file path hidden)"
            elif var == 'DOCUMENT_AI_PROCESSOR_ID':
                display = f"✓ {value[:10]}..."
            else:
                display = f"✓ {value}"
            print(f"  {var:35s} {display}")
        else:
            print(f"  {var:35s} ✗ NOT SET")
            all_good = False
    
    # Check optional
    print("\nOptional Variables:")
    for var, description in optional_vars.items():
        value = os.environ.get(var, 'us')
        print(f"  {var:35s} ✓ {value}")
    
    return all_good


def check_python_packages():
    """Check if required Python packages are installed."""
    print("\n" + "="*70)
    print("2. CHECKING PYTHON PACKAGES")
    print("="*70)
    
    required_packages = {
        'google.cloud.documentai': 'google-cloud-documentai',
        'google.cloud.vision': 'google-cloud-vision',
        'PIL': 'Pillow',
    }
    
    all_good = True
    
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"  {package_name:30s} ✓ Installed")
        except ImportError:
            print(f"  {package_name:30s} ✗ NOT INSTALLED")
            print(f"    → Install with: pip install {package_name}")
            all_good = False
    
    return all_good


def check_google_credentials():
    """Check if Google Cloud credentials are valid."""
    print("\n" + "="*70)
    print("3. CHECKING GOOGLE CLOUD CREDENTIALS")
    print("="*70)
    
    try:
        from google.auth import default
        from google.auth.exceptions import DefaultCredentialsError
        
        credentials, project = default()
        print(f"  ✓ Credentials Found")
        print(f"    Project: {project}")
        print(f"    Type: {credentials.universe_domain}")
        return True
    except DefaultCredentialsError:
        print("  ✗ Credentials NOT Found")
        print("    Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        return False
    except Exception as e:
        print(f"  ✗ Credentials Error: {e}")
        return False


def check_document_ai_access():
    """Check if we can access Document AI API."""
    print("\n" + "="*70)
    print("4. CHECKING DOCUMENT AI API ACCESS")
    print("="*70)
    
    try:
        from google.cloud import documentai
        
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        processor_id = os.environ.get('DOCUMENT_AI_PROCESSOR_ID')
        location = os.environ.get('DOCUMENT_AI_LOCATION', 'us')
        
        if not project_id or not processor_id:
            print("  ✗ Missing GOOGLE_CLOUD_PROJECT or DOCUMENT_AI_PROCESSOR_ID")
            return False
        
        # Try to initialize the client
        client = documentai.DocumentProcessorServiceClient()
        
        # Build the processor path
        processor_name = client.processor_path(project_id, location, processor_id)
        print(f"  ✓ Client Initialized")
        print(f"    Processor Path: {processor_name}")
        
        # Try to get processor info
        processor = client.get_processor(name=processor_name)
        print(f"  ✓ Processor Found")
        print(f"    Display Name: {processor.display_name}")
        print(f"    Type: {processor.type_}")
        print(f"    State: {processor.state}")
        
        return True
    
    except Exception as e:
        print(f"  ✗ Document AI Access Error: {e}")
        if "NOT_FOUND" in str(e):
            print("    Check DOCUMENT_AI_PROCESSOR_ID and DOCUMENT_AI_LOCATION")
        elif "PERMISSION_DENIED" in str(e):
            print("    Service account lacks Document AI permissions")
        elif "UNAVAILABLE" in str(e):
            print("    Document AI API is unavailable or network issue")
        return False


def test_ocr_service(image_path=None):
    """Test the OCR service with an optional image."""
    print("\n" + "="*70)
    print("5. TESTING OCR SERVICE")
    print("="*70)
    
    try:
        from enrollment_app.services.ocr_service import OCRGradeVerifier
        
        print("  ✓ OCRGradeVerifier imported successfully")
        
        # Try to initialize
        verifier = OCRGradeVerifier(tolerance=3.0)
        print(f"  ✓ OCRGradeVerifier initialized")
        print(f"    Project: {verifier.project_id}")
        print(f"    Processor: {verifier.processor_id}")
        print(f"    Location: {verifier.location}")
        
        # Test with image if provided
        if image_path and Path(image_path).exists():
            print(f"\n  Testing with image: {image_path}")
            grades = verifier.extract_grades_from_image(image_path)
            print(f"  ✓ Extracted {len(grades)} subjects:")
            for subject, grade in grades.items():
                print(f"    {subject}: {grade}")
            return True
        else:
            if image_path:
                print(f"  ⚠ Image file not found: {image_path}")
            return True
    
    except ModuleNotFoundError:
        print("  ✗ Cannot import OCRGradeVerifier")
        print("    Ensure you're running from the project directory")
        return False
    except Exception as e:
        print(f"  ✗ OCR Service Error: {e}")
        return False


def print_setup_instructions():
    """Print setup instructions if something is missing."""
    print("\n" + "="*70)
    print("QUICK SETUP GUIDE")
    print("="*70)
    
    print("""
1. Create a Document AI Processor:
   - Go to: https://console.cloud.google.com/document-ai/processors
   - Click "Create Processor"
   - Choose: "General Document OCR"
   - Copy the Processor ID

2. Set Environment Variables:
   
   Windows (PowerShell):
   $env:GOOGLE_CLOUD_PROJECT = "your-project-id"
   $env:DOCUMENT_AI_PROCESSOR_ID = "your-processor-id"
   
   Linux/Mac:
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export DOCUMENT_AI_PROCESSOR_ID="your-processor-id"

3. Set Google Cloud Credentials:
   $env:GOOGLE_APPLICATION_CREDENTIALS = "path/to/service-account.json"

4. Install Required Packages:
   pip install google-cloud-documentai

5. Run this test again:
   python test_document_ai_setup.py
""")


def main():
    parser = argparse.ArgumentParser(
        description='Verify Document AI setup and test OCR service'
    )
    parser.add_argument(
        '--test-image',
        help='Path to report card image to test'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("DOCUMENT AI SETUP VERIFICATION")
    print("="*70)
    
    checks = [
        ("Environment Variables", check_environment_variables),
        ("Python Packages", check_python_packages),
        ("Google Credentials", check_google_credentials),
        ("Document AI Access", check_document_ai_access),
        ("OCR Service", lambda: test_ocr_service(args.test_image)),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"  ✗ {check_name} check failed: {e}")
            results.append((check_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {check_name}")
    
    print(f"\n  {passed}/{total} checks passed")
    
    if passed < total:
        print_setup_instructions()
        sys.exit(1)
    else:
        print("\n✓ All checks passed! Document AI is ready to use.")
        sys.exit(0)


if __name__ == '__main__':
    main()
