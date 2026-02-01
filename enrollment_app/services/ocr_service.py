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
        Handles two name formats:
          - Format 1: FIRSTNAME MIDDLE LASTNAME (e.g., "STEVEN D. SEMANA")
          - Format 2: LASTNAME, FIRSTNAME MIDDLE (e.g., "Semana, Steven D")
        Returns dict with is_match, similarity, extracted, registered, reason.
        """
        import difflib

        def normalize_word(word):
            """Remove periods and lowercase a single word."""
            if not word:
                return ''
            return word.replace('.', '').lower().strip()

        def is_middle_initial(word):
            """Check if a word is likely a middle initial (1-2 chars)."""
            clean = normalize_word(word)
            return len(clean) <= 2

        def parse_name(name):
            """
            Parse a name into (firstname, lastname) tuple, handling both formats:
              - "LASTNAME, FIRSTNAME MIDDLE" (comma-separated)
              - "FIRSTNAME MIDDLE LASTNAME" (space-separated)
            Returns (firstname, lastname) with middle initial/name ignored.
            """
            if not name:
                return ('', '')

            name = name.strip()

            # Check if comma-separated format: "LASTNAME, FIRSTNAME MIDDLE"
            if ',' in name:
                parts = name.split(',', 1)  # Split only on first comma
                lastname = normalize_word(parts[0])

                # Parse firstname from the part after comma
                if len(parts) > 1:
                    rest = parts[1].strip().split()
                    # First word after comma is firstname, rest is middle name(s)
                    firstname = normalize_word(rest[0]) if rest else ''
                else:
                    firstname = ''

                return (firstname, lastname)

            # Space-separated format: "FIRSTNAME MIDDLE LASTNAME"
            parts = name.split()
            if len(parts) == 0:
                return ('', '')
            elif len(parts) == 1:
                return (normalize_word(parts[0]), '')
            elif len(parts) == 2:
                # Could be "FIRSTNAME LASTNAME" or "FIRSTNAME MIDDLE" (unlikely)
                return (normalize_word(parts[0]), normalize_word(parts[1]))
            else:
                # 3+ parts: First word is firstname, last word is lastname
                # Everything in between is middle name(s)
                firstname = normalize_word(parts[0])
                lastname = normalize_word(parts[-1])
                return (firstname, lastname)

        # Parse both names
        ext_first, ext_last = parse_name(extracted_name)
        reg_first, reg_last = parse_name(registered_name)

        # If either is completely empty, fail
        if (not ext_first and not ext_last) or (not reg_first and not reg_last):
            return {
                'is_match': False,
                'similarity': 0.0,
                'extracted': extracted_name,
                'registered': registered_name,
                'reason': 'One or both names are empty.'
            }

        # Build different name order combinations for comparison
        # We compare firstname+lastname in different orders
        combinations = []

        # Standard: extracted "first last" vs registered "first last"
        if ext_first and ext_last and reg_first and reg_last:
            combinations.append((f"{ext_first} {ext_last}", f"{reg_first} {reg_last}"))
            combinations.append((f"{ext_last} {ext_first}", f"{reg_first} {reg_last}"))
            combinations.append((f"{ext_first} {ext_last}", f"{reg_last} {reg_first}"))
            combinations.append((f"{ext_last} {ext_first}", f"{reg_last} {reg_first}"))
        elif ext_first and reg_first:
            # Only firstnames available
            combinations.append((ext_first, reg_first))
        elif ext_last and reg_last:
            # Only lastnames available
            combinations.append((ext_last, reg_last))
        else:
            # Mix: compare whatever is available
            ext_available = ext_first or ext_last
            reg_available = reg_first or reg_last
            if ext_available and reg_available:
                combinations.append((ext_available, reg_available))

        # Find the best similarity score across all combinations
        best_similarity = 0.0
        for a, b in combinations:
            sim = difflib.SequenceMatcher(None, a, b).ratio()
            if sim > best_similarity:
                best_similarity = sim

        # Also try comparing firstnames and lastnames separately and averaging
        firstname_sim = difflib.SequenceMatcher(None, ext_first, reg_first).ratio() if ext_first and reg_first else 0.0
        lastname_sim = difflib.SequenceMatcher(None, ext_last, reg_last).ratio() if ext_last and reg_last else 0.0

        # If both firstname and lastname matched well individually, use their average
        if firstname_sim > 0 and lastname_sim > 0:
            avg_sim = (firstname_sim + lastname_sim) / 2
            if avg_sim > best_similarity:
                best_similarity = avg_sim

        # Also try swapped comparison (in case extracted has firstname/lastname reversed)
        if ext_first and ext_last and reg_first and reg_last:
            swapped_first_sim = difflib.SequenceMatcher(None, ext_last, reg_first).ratio()
            swapped_last_sim = difflib.SequenceMatcher(None, ext_first, reg_last).ratio()
            swapped_avg = (swapped_first_sim + swapped_last_sim) / 2
            if swapped_avg > best_similarity:
                best_similarity = swapped_avg

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
                    