"""
DepEd Report Card Grade Extractor using Gemini AI (New SDK)
Supports both API Key and Service Account authentication
"""

from google import genai
from google.genai import types
import json
import os
from typing import Dict
from PIL import Image

# ----------------------------
# CONFIG
# ----------------------------
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if not GEMINI_API_KEY and not GOOGLE_APPLICATION_CREDENTIALS:
    raise ValueError(
        "No authentication found. Set either:\n"
        "1. GEMINI_API_KEY=your-key, OR\n"
        "2. GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json"
    )

SUBJECTS = [
    "Filipino", "English", "Mathematics", "Science", 
    "EsP", "ArPan", "EPP/TLE", "MAPEH"
]


# ----------------------------
# GEMINI SETUP
# ----------------------------
def setup_gemini():
    """Initialize Gemini client."""
    if GEMINI_API_KEY:
        print("  → Using API Key authentication")
        return genai.Client(api_key=GEMINI_API_KEY)
    else:
        print("  → Using Service Account authentication (Vertex AI)")
        # Get project ID from service account JSON
        with open(GOOGLE_APPLICATION_CREDENTIALS, 'r') as f:
            creds = json.load(f)
            project_id = creds.get('project_id')
        
        print(f"  → Project: {project_id}")
        return genai.Client(
            vertexai=True,
            project=project_id,
            location='us-central1'
        )


# ----------------------------
# GRADE EXTRACTION
# ----------------------------
def extract_grades_with_gemini(image_path: str) -> Dict[str, Dict]:
    """Extract grades using Gemini AI vision."""
    
    print("="*70)
    print("DepEd Report Card Grade Extractor (Gemini AI)")
    print("="*70)
    
    # Initialize Gemini
    print("\n[1] Initializing Gemini AI...")
    client = setup_gemini()
    print("✓ Gemini initialized\n")
    
    # Load image
    print(f"[2] Loading image: {image_path}")
    img = Image.open(image_path)
    print(f"✓ Image loaded: {img.size}\n")
    
    # Convert to bytes
    import io
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_data = img_bytes.getvalue()
    
    # Prompt
    prompt = """Analyze this Philippine DepEd report card and extract grades for ALL 8 subjects.

For each subject extract: Q1, Q2, Q3, Q4, and Final Grade (all must be numbers 70-100).

The 8 subjects are:
1. Filipino
2. English  
3. Mathematics
4. Science
5. EsP (Edukasyon sa Pagpapakatao)
6. ArPan (Araling Panlipunan)
7. EPP/TLE
8. MAPEH - ONLY extract the main MAPEH row, NOT sub-components (Music, Arts, P.E., Health)

Return ONLY valid JSON (no markdown, no explanations):
{
  "Filipino": {"Q1": 90, "Q2": 91, "Q3": 92, "Q4": 94, "Final Grade": 92},
  "English": {"Q1": 89, "Q2": 88, "Q3": 88, "Q4": 90, "Final Grade": 89},
  ...
}"""
    
    # Send to Gemini
    print("[3] Sending to Gemini...")
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
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
        
        print("✓ Response received\n")
        
        # Parse response
        print("[4] Parsing response...")
        response_text = response.text.strip()
        
        # Remove markdown if present
        response_text = response_text.replace('```json', '').replace('```', '').strip()
        
        grades = json.loads(response_text)
        print("✓ Successfully parsed JSON\n")
        
        return grades
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON parse error: {e}")
        print(f"Raw response:\n{response_text}")
        return {}
    
    except Exception as e:
        print(f"✗ Gemini error: {e}")
        import traceback
        traceback.print_exc()
        return {}


# ----------------------------
# VALIDATION
# ----------------------------
def validate_grades(grades: Dict) -> Dict:
    """Validate extracted grades."""
    print("[5] Validating grades...")
    
    validated = {}
    required_keys = ['Q1', 'Q2', 'Q3', 'Q4', 'Final Grade']
    
    for subject in SUBJECTS:
        if subject not in grades:
            print(f"  ⚠ {subject}: Missing")
            continue
        
        grade_info = grades[subject]
        
        # Check all keys present
        if not all(k in grade_info for k in required_keys):
            print(f"  ⚠ {subject}: Incomplete")
            continue
        
        # Validate ranges
        valid = True
        for key in required_keys:
            val = grade_info[key]
            if not isinstance(val, (int, float)) or not (70 <= val <= 100):
                print(f"  ⚠ {subject}: {key}={val} invalid")
                valid = False
                break
        
        if valid:
            validated[subject] = grade_info
            print(f"  ✓ {subject}")
    
    print()
    return validated


# ----------------------------
# MAIN
# ----------------------------
def main():
    image_path = "ADELFA_3.jpg"
    
    # Extract
    grades = extract_grades_with_gemini(image_path)
    
    if not grades:
        print("✗ Extraction failed")
        return {}
    
    # Validate
    validated = validate_grades(grades)
    
    # Display
    print("="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    for subject in SUBJECTS:
        if subject in validated:
            g = validated[subject]
            print(f"\n{subject}:")
            print(f"  Q1: {g['Q1']}")
            print(f"  Q2: {g['Q2']}")
            print(f"  Q3: {g['Q3']}")
            print(f"  Q4: {g['Q4']}")
            print(f"  Final Grade: {g['Final Grade']}")
        else:
            print(f"\n{subject}: ⚠ NOT FOUND")
    
    print(f"\n{'='*70}")
    print(f"✓ Extracted {len(validated)}/{len(SUBJECTS)} subjects")
    
    if len(validated) == len(SUBJECTS):
        print("✓ All 8 subjects extracted successfully!")
    else:
        missing = [s for s in SUBJECTS if s not in validated]
        print(f"⚠ Missing: {missing}")
    
    print("="*70)
    
    return validated


if __name__ == "__main__":
    result = main()
    
    print("\nJSON Output:")
    print(json.dumps(result, indent=2))