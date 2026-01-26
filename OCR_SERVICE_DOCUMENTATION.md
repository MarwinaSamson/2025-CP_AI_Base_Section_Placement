# OCR Service Documentation

## Overview

This OCR (Optical Character Recognition) service is designed for extracting student names and subject grades from Philippine DepEd report cards. It is optimized for Django backend integration and uses a hybrid approach for cost efficiency and accuracy.

## Technical Stack

- **Python** (core logic)
- **Django** (backend integration)
- **Google Cloud Vision API** (lightweight OCR fallback)
- **Google Gemini API** (advanced AI extraction for complex/ambiguous cases)
- **Pillow** (image processing)

## Workflow

1. **Image Input**: The user uploads a report card image (e.g., JPG, PNG).
2. **Vision API Fallback**: The service first tries to extract text, grades, and student name using Google Vision API.
   - If Vision API finds at least 6 subjects and a student name, its result is used (saves cost/quota).
   - If Vision API is incomplete or ambiguous, the image is sent to Gemini for advanced extraction.
3. **Gemini AI Extraction**: Gemini is prompted to extract all 8 subject grades (Q1-Q4, Final Grade) and the student name, returning structured JSON.
4. **Post-processing**: All validation, normalization, and verification (grade range, subject mapping, name matching, grade comparison) are handled in Python.
5. **Output**: The service returns a dictionary with extracted grades, student name, and the full OCR text for debugging.

## Key Methods

- `extract_grades_and_name_from_image(image_path)`: Main entry point. Returns extracted grades, student name, and full text.
- `_extract_with_vision(image_path)`: Uses Google Vision API for lightweight OCR.
- `_validate_grades(grades)`: Validates and normalizes grades.
- `verify_student_name(extracted_name, registered_full_name)`: Fuzzy matches extracted name to registered name.
- `verify_grades(extracted, manual)`: Compares extracted grades to manually entered grades.

## Configuration

- **Google Vision API**: Requires service account credentials. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable.
- **Gemini API**: Supports both API key and Vertex AI (service account) authentication.
- **.env**: Stores project IDs, API keys, and other settings.

## Example Usage

```python
from enrollment_app.services.ocr_service import OCRGradeVerifier
verifier = OCRGradeVerifier(tolerance=3.0)
result = verifier.extract_grades_and_name_from_image('MudanBoys_7.jpg')
print(result)
```

## Best Practices

- Use Vision API for most cases to save Gemini quota.
- Only use Gemini for complex layouts or when Vision API is insufficient.
- Validate and post-process all results in Python for reliability.

## Dependencies

- google-cloud-vision
- google-generativeai (Gemini)
- pillow
- django

## File Location

- Main logic: `enrollment_app/services/ocr_service.py`
- Test script: `test_improved_ocr.py`

## Authors

- Maintained by the AI-Based Section Placement System team.
