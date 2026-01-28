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
        # Use the cheapest Gemini model ("gemini-pro-vision")
        response = self.client.models.generate_content(
            model='gemini-3-pro-image-preview',
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

if __name__ == "__main__":
    ocr = GeminiAPIKeyOCR()
    # Replace with the path to your test image
    result = ocr.extract_grades_and_name_from_image("Aliya.jpg")
    print(result)