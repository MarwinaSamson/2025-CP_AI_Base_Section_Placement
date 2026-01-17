# Example configuration for Document AI integration
# Copy this file to your Django settings or environment configuration

import os

# ============================================
# Google Document AI Configuration
# ============================================

# Your Google Cloud Project ID
# Get from: https://console.cloud.google.com/
GOOGLE_CLOUD_PROJECT = os.environ.get(
    'GOOGLE_CLOUD_PROJECT',
    '1094485135926'
)

# Document AI Processor ID
# Create at: https://console.cloud.google.com/document-ai/processors
# Choose: General Document OCR (for report cards)
DOCUMENT_AI_PROCESSOR_ID = os.environ.get(
    'DOCUMENT_AI_PROCESSOR_ID',
    'a0cbcc2e3afe7ae0'
)

# Document AI Region
# Options: us (default), eu, asia-northeast1, etc.
DOCUMENT_AI_LOCATION = os.environ.get(
    'DOCUMENT_AI_LOCATION',
    'us'
)

# ============================================
# OCR Configuration
# ============================================

OCR_CONFIG = {
    # Tolerance for grade matching (0.0 = exact match only)
    'tolerance': 3.0,
    
    # Google Cloud settings
    'project_id': GOOGLE_CLOUD_PROJECT,
    'processor_id': DOCUMENT_AI_PROCESSOR_ID,
    'location': DOCUMENT_AI_LOCATION,
    
    # Use Document AI if available, fall back to Vision API
    'use_document_ai': True,
    
    # For batch processing (optional)
    'async_processing': False,
    'batch_size': 10,
}

# ============================================
# Usage in Django Views
# ============================================

# Example 1: Using environment variables (recommended)
"""
from enrollment_app.services.ocr_service import OCRGradeVerifier

def extract_report_card_grades(image_path):
    # Automatically uses GOOGLE_CLOUD_PROJECT and DOCUMENT_AI_PROCESSOR_ID
    verifier = OCRGradeVerifier(tolerance=3.0)
    return verifier.extract_grades_from_image(image_path)
"""

# Example 2: Using explicit config
"""
from enrollment_app.services.ocr_service import OCRGradeVerifier
from django.conf import settings

def extract_report_card_grades(image_path):
    config = settings.OCR_CONFIG
    verifier = OCRGradeVerifier(
        tolerance=config['tolerance'],
        project_id=config['project_id'],
        processor_id=config['processor_id'],
        location=config['location']
    )
    return verifier.extract_grades_from_image(image_path)
"""

# ============================================
# Environment Variables (Alternative Setup)
# ============================================

# If you don't want to add to Django settings, set these environment variables instead:

"""
Windows (PowerShell):
    $env:GOOGLE_CLOUD_PROJECT = "my-project"
    $env:DOCUMENT_AI_PROCESSOR_ID = "abc123def456"
    $env:DOCUMENT_AI_LOCATION = "us"

Windows (Command Prompt):
    set GOOGLE_CLOUD_PROJECT=my-project
    set DOCUMENT_AI_PROCESSOR_ID=abc123def456
    set DOCUMENT_AI_LOCATION=us

Linux/Mac (in .bashrc, .zshrc, or .env):
    export GOOGLE_CLOUD_PROJECT="my-project"
    export DOCUMENT_AI_PROCESSOR_ID="abc123def456"
    export DOCUMENT_AI_LOCATION="us"

Or in .env file:
    GOOGLE_CLOUD_PROJECT=my-project
    DOCUMENT_AI_PROCESSOR_ID=abc123def456
    DOCUMENT_AI_LOCATION=us
"""

# ============================================
# Service Account Setup (for deployment)
# ============================================

# Ensure your service account (from GOOGLE_APPLICATION_CREDENTIALS) has these roles:
# - roles/documentai.editor (for Document AI)
# - roles/vision.admin (for Vision API fallback)

# You can also use specific minimal roles:
# - documentai.documentProcessors.processDocuments
# - vision.imageAnalyzer

# To add roles to service account:
"""
gcloud projects add-iam-policy-binding YOUR_PROJECT \\
  --member=serviceAccount:YOUR_SERVICE_ACCOUNT \\
  --role=roles/documentai.editor
"""

# ============================================
# Testing the Configuration
# ============================================

"""
from enrollment_app.services.ocr_service import OCRGradeVerifier

# Test if setup is correct
try:
    verifier = OCRGradeVerifier(tolerance=3.0)
    print("✓ OCR Verifier initialized successfully")
    print(f"  Project: {verifier.project_id}")
    print(f"  Processor: {verifier.processor_id}")
    print(f"  Location: {verifier.location}")
except Exception as e:
    print(f"✗ OCR Verifier initialization failed: {e}")
    print("  Please check DOCUMENT_AI_PROCESSOR_ID and GOOGLE_APPLICATION_CREDENTIALS")
"""
