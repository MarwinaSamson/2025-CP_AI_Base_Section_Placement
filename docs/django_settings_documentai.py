"""
Django Settings - Document AI Configuration Template

Copy this into your Django settings.py file with your credentials pre-filled.
"""

import os

# ============================================
# DOCUMENT AI CONFIGURATION (PRE-CONFIGURED)
# ============================================

# Your Google Cloud credentials
GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT', '1094485135926')
DOCUMENT_AI_PROCESSOR_ID = os.environ.get('DOCUMENT_AI_PROCESSOR_ID', 'a0cbcc2e3afe7ae0')
DOCUMENT_AI_LOCATION = os.environ.get('DOCUMENT_AI_LOCATION', 'us')

# OCR Configuration
OCR_CONFIG = {
    # Grade matching tolerance
    'tolerance': 3.0,
    
    # Google Cloud settings (pre-configured with your credentials)
    'project_id': GOOGLE_CLOUD_PROJECT,
    'processor_id': DOCUMENT_AI_PROCESSOR_ID,
    'location': DOCUMENT_AI_LOCATION,
    
    # Use Document AI if available, fall back to Vision API
    'use_document_ai': True,
    
    # For batch processing (optional)
    'async_processing': False,
    'batch_size': 10,
    
    # Report card specific settings
    'subject_tolerance': 0.70,  # Fuzzy matching threshold
    'row_y_padding': 35,        # Vertical padding for row detection
    'column_pad': 50,           # Horizontal padding for column detection
}

# ============================================
# USAGE IN VIEWS
# ============================================

"""
Example: Using OCR in a Django view

from django.conf import settings
from enrollment_app.services.ocr_service import GeminiAPIKeyOCR

def process_report_card(request):
    # Get config from Django settings
    config = settings.OCR_CONFIG
    
    # Initialize verifier with your credentials (already loaded)
    verifier = GeminiAPIKeyOCR(
        tolerance=config['tolerance'],
        project_id=config['project_id'],
        processor_id=config['processor_id'],
        location=config['location']
    )
    
    # Extract grades from uploaded image
    if request.FILES.get('report_card'):
        image_path = save_uploaded_file(request.FILES['report_card'])
        grades = verifier.extract_grades_from_image(image_path)
        
        # Verify against manual entry
        result = verifier.verify_grades(grades, manually_entered_grades)
        
        if result['is_match']:
            return JsonResponse({'status': 'success', 'message': 'Grades verified!'})
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Grade mismatch',
                'mismatches': result['mismatches']
            })
"""

# ============================================
# ENVIRONMENT VARIABLES FOR REFERENCE
# ============================================

"""
If you prefer to use environment variables instead of hardcoding:

Windows (PowerShell):
    $env:GOOGLE_CLOUD_PROJECT = "1094485135926"
    $env:DOCUMENT_AI_PROCESSOR_ID = "a0cbcc2e3afe7ae0"
    $env:DOCUMENT_AI_LOCATION = "us"

Linux/Mac:
    export GOOGLE_CLOUD_PROJECT="1094485135926"
    export DOCUMENT_AI_PROCESSOR_ID="a0cbcc2e3afe7ae0"
    export DOCUMENT_AI_LOCATION="us"

Or in .env file:
    GOOGLE_CLOUD_PROJECT=1094485135926
    DOCUMENT_AI_PROCESSOR_ID=a0cbcc2e3afe7ae0
    DOCUMENT_AI_LOCATION=us
"""

# ============================================
# OPTIONAL: LOGGING CONFIGURATION
# ============================================

"""
Add to your Django settings for debugging OCR operations:

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
"""
