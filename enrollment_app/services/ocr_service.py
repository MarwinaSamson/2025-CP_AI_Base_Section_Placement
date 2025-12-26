"""
OCR Service for Grade Verification

Purpose:
- Students manually input final grades per subject
- Students upload a report card image
- System extracts ONLY the Final Grade column
- Extracted grades are compared with manual input
"""

import cv2
import easyocr
import numpy as np
from PIL import Image
from typing import Dict, List, Optional


class OCRGradeVerifier:
    """
    Service class to extract FINAL GRADES from report card images
    and verify them against manually entered grades.
    """

    SUBJECT_ORDER = [
        'filipino',
        'english',
        'mathematics',
        'science',
        'araling_panlipunan',
        'edukasyon_sa_pagpapakatao',
        'edukasyon_pangkabuhayan',
        'mapeh'
    ]

    def __init__(self, tolerance: float = 2.0):
        """
        Initialize OCR verifier

        Args:
            tolerance: Acceptable grade difference
        """
        self.tolerance = tolerance
        self.reader = easyocr.Reader(['en'], gpu=False)

    # ----------------------------------------------------
    # OCR PIPELINE
    # ----------------------------------------------------

    def extract_grades_from_image(self, image_path: str) -> Dict[str, float]:
        """
        Extract final grades from report card image using EasyOCR

        Args:
            image_path: Path to report card image

        Returns:
            Dict of subject -> extracted final grade
        """
        try:
            cropped = self._crop_final_grade_column(image_path)
            processed = self._preprocess_image(cropped)
            grades = self._ocr_digits_only(processed)
            return self._map_grades_to_subjects(grades)

        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")

    # ----------------------------------------------------
    # IMAGE PROCESSING
    # ----------------------------------------------------

    def _crop_final_grade_column(self, image_path: str) -> np.ndarray:
        """
        Crop the Final Grade column from the report card image
        Tuned for DepEd-style report cards
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Unable to load image")

        h, w, _ = image.shape

        # Column crop (ratio-based, safer than hardcoded pixels)
        x_start = int(w * 0.68)
        x_end   = int(w * 0.80)
        y_start = int(h * 0.18)
        y_end   = int(h * 0.75)

        return image[y_start:y_end, x_start:x_end]

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for handwritten digit OCR
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            5
        )

        return thresh

    # ----------------------------------------------------
    # OCR LOGIC
    # ----------------------------------------------------

    def _ocr_digits_only(self, image: np.ndarray) -> List[int]:
        """
        Run OCR and extract valid final grades only
        """
        results = self.reader.readtext(
            image,
            allowlist='0123456789',
            detail=0,
            paragraph=False
        )

        grades = []
        for text in results:
            text = text.strip()
            if text.isdigit():
                value = int(text)
                if 75 <= value <= 100:
                    grades.append(value)

        return grades

    def _map_grades_to_subjects(self, grades: List[int]) -> Dict[str, float]:
        """
        Map OCR grades to subjects by row order
        """
        mapped = {}
        for subject, grade in zip(self.SUBJECT_ORDER, grades):
            mapped[subject] = float(grade)
        return mapped

    # ----------------------------------------------------
    # VERIFICATION LOGIC (UNCHANGED CORE)
    # ----------------------------------------------------

    def verify_grades(
        self,
        extracted_grades: Dict[str, float],
        manual_grades: Dict[str, Optional[float]]
    ) -> Dict:
        """
        Verify extracted grades against manually entered grades
        """
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
        """
        Format verification result for UI display
        """
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
