"""
Gemini API Key-based OCR Service (No Service Account)
"""

import os
import json
import io
from typing import Dict
from PIL import Image
from google import genai
from google.genai import types

class GeminiAPIKeyOCR:
    def verify_grades(self, extracted: dict, manual: dict, tolerance: float = 3.0) -> dict:
        """
        Compare extracted grades to manually entered grades.
        Returns dict with is_match, mismatches, confidence, matched, total.
        """
        mismatches = []
        matched = 0
        total = 0
        for subject in self.SUBJECTS:
            ext_grade = extracted.get(subject)
            man_grade = manual.get(subject)
            if ext_grade is None or man_grade is None:
                mismatches.append({
                    'subject': subject,
                    'expected': man_grade,
                    'actual': ext_grade,
                    'reason': 'Missing grade'
                })
                continue
            try:
                ext_val = float(ext_grade)
                man_val = float(man_grade)
            except Exception:
                mismatches.append({
                    'subject': subject,
                    'expected': man_grade,
                    'actual': ext_grade,
                    'reason': 'Non-numeric grade'
                })
                continue
            total += 1
            if abs(ext_val - man_val) <= tolerance:
                matched += 1
            else:
                mismatches.append({
                    'subject': subject,
                    'expected': man_val,
                    'actual': ext_val,
                    'reason': f'Grade difference > tolerance ({tolerance})'
                })
        confidence = round((matched / total) * 100, 1) if total > 0 else 0.0
        is_match = len(mismatches) == 0
        return {
            'is_match': is_match,
            'mismatches': mismatches,
            'confidence': confidence,
            'matched': matched,
            'total': total
        }

    def verify_student_name(self, extracted_name: str, registered_name: str, threshold: float = 0.7) -> dict:
        """
        Fuzzy match extracted name to registered name, allowing for swapped first/last order and ignoring middle initial.
        Returns dict with is_match, similarity, extracted, registered, reason.
        """
        import difflib
        def normalize(name):
            if not name:
                return ''
            # Remove periods and commas, lowercase, collapse spaces
            name = name.replace('.', '').replace(',', '').lower()
            return ' '.join(name.strip().split())

        def split_name(name):
            # Split into parts, extract first and last name only (ignore middle)
            parts = normalize(name).split()
            if len(parts) == 0:
                return []
            elif len(parts) == 1:
                return parts  # Just one name part
            elif len(parts) == 2:
                return parts  # Likely first, last
            else:
                # 3+ parts: assume first and last are at the ends, ignore middle
                return [parts[0], parts[-1]]

        # Try to match both orders: first last and last first
        extracted_parts = split_name(extracted_name)
        registered_parts = split_name(registered_name)

        # If either is empty, fail
        if not extracted_parts or not registered_parts:
            return {
                'is_match': False,
                'similarity': 0.0,
                'extracted': extracted_name,
                'registered': registered_name,
                'reason': 'One or both names are empty.'
            }

        # Build possible name forms (first last, last first)
        extracted_first_last = ' '.join(extracted_parts)
        extracted_last_first = ' '.join(extracted_parts[::-1])
        registered_first_last = ' '.join(registered_parts)
        registered_last_first = ' '.join(registered_parts[::-1])

        # Compare all combinations
        combos = [
            (extracted_first_last, registered_first_last),
            (extracted_first_last, registered_last_first),
            (extracted_last_first, registered_first_last),
            (extracted_last_first, registered_last_first),
        ]
        best_similarity = 0.0
        for a, b in combos:
            sim = difflib.SequenceMatcher(None, a, b).ratio()
            if sim > best_similarity:
                best_similarity = sim

        similarity_pct = round(best_similarity * 100, 1)
        is_match = best_similarity >= threshold
        reason = 'Names match.' if is_match else 'Names do not match.'
        return {
            'is_match': is_match,
            'similarity': similarity_pct,
            'extracted': extracted_name,
            'registered': registered_name,
            'reason': reason
        }

    SUBJECTS = [
        "Filipino", "English", "Mathematics", "Science",
        "EsP", "ArPan", "EPP/TLE", "MAPEH"
    ]
    SUBJECT_ALIASES = {
        "GMRC": "EsP",
        "Good Manners and Right Conduct": "EsP",
    }

    def __init__(self, tolerance: float = 3.0):
        self.tolerance = tolerance
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        self.client = genai.Client(api_key=api_key)
        print("✓ Gemini API Key OCR initialized.")

    def _validate_grades(self, grades: Dict) -> Dict[str, float]:
        validated = {}
        normalized_grades = {}
        for subject, grade in grades.items():
            normalized_subject = self.SUBJECT_ALIASES.get(subject, subject)
            normalized_grades[normalized_subject] = grade
        for subject in self.SUBJECTS:
            if subject not in normalized_grades:
                continue
            grade = normalized_grades[subject]
            if isinstance(grade, dict):
                if 'Final Grade' in grade:
                    grade = grade['Final Grade']
                else:
                    continue
            if isinstance(grade, (int, float)) and 70 <= grade <= 100:
                validated[subject] = float(grade)
        return validated

    def extract_grades_and_name_from_image(self, image_path: str) -> Dict:
        img = Image.open(image_path)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_data = img_bytes.getvalue()
        prompt = (
            "Analyze this Philippine DepEd report card and extract:\n\n"
            "1. ALL 8 subject grades (Q1, Q2, Q3, Q4, Final Grade - all must be numbers 70-100)\n"
            "2. Student name from the \"Name:\" field\n\n"
            "The 8 subjects are:\n"
            "1. Filipino\n"
            "2. English\n"
            "3. Mathematics\n"
            "4. Science\n"
            "5. EsP (Edukasyon sa Pagpapakatao) - may also appear as \"GMRC\" in older cards\n"
            "6. ArPan (Araling Panlipunan)\n"
            "7. EPP/TLE\n"
            "8. MAPEH - ONLY extract the main MAPEH row, NOT sub-components (Music, Arts, P.E., Health)\n\n"
            "IMPORTANT: If you see \"GMRC\" or \"Good Manners and Right Conduct\", extract it as \"GMRC\"\n\n"
            "Return ONLY valid JSON (no markdown, no explanations):\n"
            "{\n"
            "\"student_name\": \"LAST NAME, FIRST NAME MIDDLE INITIAL\",\n"
            "\"grades\": {\n"
            "    \"Filipino\": {\"Q1\": 90, \"Q2\": 91, \"Q3\": 92, \"Q4\": 94, \"Final Grade\": 92},\n"
            "    \"English\": {\"Q1\": 89, \"Q2\": 88, \"Q3\": 88, \"Q4\": 90, \"Final Grade\": 89},\n"
            "    \"Mathematics\": {\"Q1\": 87, \"Q2\": 93, \"Q3\": 87, \"Q4\": 87, \"Final Grade\": 89},\n"
            "    \"Science\": {\"Q1\": 85, \"Q2\": 87, \"Q3\": 89, \"Q4\": 89, \"Final Grade\": 88},\n"
            "    \"EsP\": {\"Q1\": 93, \"Q2\": 98, \"Q3\": 95, \"Q4\": 95, \"Final Grade\": 95},\n"
            "    \"ArPan\": {\"Q1\": 85, \"Q2\": 86, \"Q3\": 89, \"Q4\": 91, \"Final Grade\": 88},\n"
            "    \"EPP/TLE\": {\"Q1\": 89, \"Q2\": 90, \"Q3\": 92, \"Q4\": 93, \"Final Grade\": 91},\n"
            "    \"MAPEH\": {\"Q1\": 92, \"Q2\": 88, \"Q3\": 87, \"Q4\": 91, \"Final Grade\": 89}\n"
            "}\n"
            "}\n\n"
            "Note: Use \"GMRC\" as the key if the card shows \"GMRC\" instead of \"EsP\"."
        )
        # Use the correct Gemini model for image support
        response = self.client.models.generate_content(
            model='models/gemini-3-pro-image-preview',
            contents=[
                prompt,
                types.Part(
                    inline_data=types.Blob(
                        mime_type="image/jpeg",
                        data=img_data
                    )
                )
            ]
        )
        response_text = response.text.strip()
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        data = json.loads(response_text)
        grades = {}
        for subject, grade_info in data.get('grades', {}).items():
            if isinstance(grade_info, dict) and 'Final Grade' in grade_info:
                grades[subject] = grade_info['Final Grade']
            elif isinstance(grade_info, (int, float)):
                grades[subject] = grade_info
        student_name = data.get('student_name', None)
        validated_grades = self._validate_grades(grades)
        return {
            'grades': validated_grades,
            'student_name': student_name,
            'full_text': response_text
        }

# Usage Example
# if __name__ == "__main__":
#     ocr = GeminiAPIKeyOCR()
#     # Replace with your actual image path
#     result = ocr.extract_grades_and_name_from_image("report_card.jpg")
#     print("Student Name:", result['student_name'])
#     print("Grades:")
#     for subject, grade in result['grades'].items():
#         print(f"  {subject}: {grade}")
                    