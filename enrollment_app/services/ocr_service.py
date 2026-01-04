"""
OCR Service for Grade Verification (Google Vision API)

Flow:
- Students input final grades per subject.
- Students upload a report card image (image/PDF).
- We call Google Vision DOCUMENT_TEXT_DETECTION to get raw text.
- Parse each line to find subject names and final grades (last numeric in line).
- Normalize subject names to match system labels.
- Compare extracted grades vs manual input with tolerance.
"""

import re
from typing import Dict, List, Optional

from google.cloud import vision
from PIL import Image


class OCRGradeVerifier:
    """Extract grades from report cards using Google Vision and compare to manual input."""

    SUBJECT_ALIASES = {
        'filipino': ['filipino'],
        'english': ['english'],
        'mathematics': ['math', 'mathematics', 'mathematika'],
        'science': ['science', 'sci'],
        'araling_panlipunan': ['araling panlipunan', 'ap', 'social studies'],
        'edukasyon_sa_pagpapakatao': ['edukasyon sa pagpapakatao', 'esp', 'es p', 'edukasyon sa pagpapatao'],
        'edukasyon_pangkabuhayan': ['technology and livelihood education', 'tle', 'edukasyon pangkabuhayan', 'epp'],
        'mapeh': ['mapeh', 'm.a.p.e.h', 'music arts pe health'],
    }

    def __init__(
        self,
        tolerance: float = 2.0,
        min_grade: int = 70,
        max_grade: int = 100,
    ):
        self.tolerance = tolerance
        self.min_grade = min_grade
        self.max_grade = max_grade
        # Vision client will pick credentials from GOOGLE_APPLICATION_CREDENTIALS
        self.client = vision.ImageAnnotatorClient()

    # ----------------------------------------------------
    # OCR PIPELINE (Google Vision)
    # ----------------------------------------------------

    def extract_grades_from_image(self, image_path: str) -> Dict[str, float]:
        """Call Vision API and parse grades per subject."""
        try:
            with open(image_path, 'rb') as f:
                content = f.read()

            image = vision.Image(content=content)
            response = self.client.document_text_detection(image=image)

            if response.error.message:
                raise Exception(response.error.message)

            full_text = response.full_text_annotation.text or ''
            return self._parse_text(full_text)
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")

    def _parse_text(self, text: str) -> Dict[str, float]:
        """Parse Vision full text: find subject lines and grab last numeric as final grade."""
        extracted: Dict[str, float] = {}
        lines = [line.strip().lower() for line in text.split('\n') if line.strip()]

        for line in lines:
            # Find candidate grade (last numeric value in line)
            numbers = re.findall(r'(\d{2,3}(?:\.\d+)?)', line)
            if not numbers:
                continue
            try:
                grade_val = float(numbers[-1])
            except ValueError:
                continue

            if not (self.min_grade <= grade_val <= self.max_grade):
                continue

            # Find subject match
            matched_subject = self._match_subject(line)
            if matched_subject and matched_subject not in extracted:
                extracted[matched_subject] = grade_val

        return extracted

    def _match_subject(self, line: str) -> Optional[str]:
        for canonical, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                if alias in line:
                    return canonical
        return None

    # ----------------------------------------------------
    # VERIFICATION LOGIC
    # ----------------------------------------------------

    def verify_grades(
        self,
        extracted_grades: Dict[str, float],
        manual_grades: Dict[str, Optional[float]]
    ) -> Dict:
        mismatches = []
        missing_in_ocr = []
        matched = 0
        total_compared = 0

        for subject, manual_grade in manual_grades.items():
            if manual_grade is None:
                continue

            total_compared += 1

            if subject not in extracted_grades:
                missing_in_ocr.append({
                    'subject': subject,
                    'manual_grade': manual_grade,
                    'reason': 'Not detected in image'
                })
                continue

            extracted = extracted_grades[subject]

            if abs(manual_grade - extracted) <= self.tolerance:
                matched += 1
            else:
                mismatches.append({
                    'subject': subject,
                    'manual_grade': manual_grade,
                    'extracted_grade': extracted,
                    'difference': abs(manual_grade - extracted)
                })

        confidence = (matched / total_compared * 100) if total_compared else 0
        is_match = len(mismatches) == 0 or confidence >= 75.0

        return {
            'is_match': is_match,
            'confidence': round(confidence, 2),
            'matched_count': matched,
            'total_compared': total_compared,
            'mismatches': mismatches,
            'missing_in_ocr': missing_in_ocr
        }

    def format_mismatch_message(self, result: Dict) -> str:
        if result['is_match']:
            return "✓ Grades successfully verified."

        message = "⚠ Grade discrepancies detected:\n\n"

        for item in result['mismatches']:
            subject = item['subject'].replace('_', ' ').title()
            message += (
                f"• {subject}: entered {item['manual_grade']}, "
                f"card shows {item['extracted_grade']}\n"
            )

        if result['missing_in_ocr']:
            message += "\n⚠ Subjects not detected from image:\n"
            for item in result['missing_in_ocr']:
                subject = item['subject'].replace('_', ' ').title()
                message += f"• {subject}\n"

        return message


# ----------------------------------------------------
# FALLBACK (NO OCR)
# ----------------------------------------------------

class SimpleGradeVerifier:
    """
    Fallback verifier without OCR
    """

    def verify_image_exists(self, image_path: str) -> bool:
        try:
            image = Image.open(image_path)
            image.verify()
            return True
        except Exception:
            return False

    def basic_verification(self, grades: Dict[str, float]) -> Dict:
        invalid = []

        for subject, grade in grades.items():
            if grade is None:
                continue
            if not (0 <= grade <= 100):
                invalid.append({
                    'subject': subject,
                    'grade': grade,
                    'reason': 'Grade out of range'
                })

        return {
            'is_valid': len(invalid) == 0,
            'invalid_grades': invalid
        }
