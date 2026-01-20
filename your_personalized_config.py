"""
DepEd Report Card Grade Extractor using Google Document AI
Enhanced OCR accuracy for Philippine report cards
"""

from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
import json
import os
from typing import Dict, List
from PIL import Image
import re

# ----------------------------
# CONFIG
# ----------------------------
PROJECT_ID = "1094485135926"
PROCESSOR_ID = "a0cbcc2e3afe7ae0"
LOCATION = "us"

# Use service account credentials
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

if not GOOGLE_APPLICATION_CREDENTIALS:
    print("⚠ Warning: GOOGLE_APPLICATION_CREDENTIALS not set")
    print("  Set it with: export GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json")
    print("  Or place service-account.json in the same folder and it will auto-detect\n")

SUBJECTS = [
    "Filipino", "English", "Mathematics", "Science", 
    "EsP", "ArPan", "EPP/TLE", "MAPEH"
]

# Subject name variations to handle OCR errors
SUBJECT_VARIATIONS = {
    "Filipino": ["filipino", "pilipino", "wikang filipino"],
    "English": ["english", "ingles"],
    "Mathematics": ["mathematics", "math", "matematika"],
    "Science": ["science", "agham"],
    "EsP": ["esp", "e.s.p", "edukasyon sa pagpapakatao", "edukasyong pantahanan at pangkabuhayan"],
    "ArPan": ["arpan", "ap", "a.p", "araling panlipunan"],
    "EPP/TLE": ["epp", "tle", "e.p.p", "t.l.e", "epp/tle", "edukasyong pantahanan"],
    "MAPEH": ["mapeh", "m.a.p.e.h"]
}


# ----------------------------
# DOCUMENT AI SETUP
# ----------------------------
def setup_document_ai():
    """Initialize Document AI client."""
    print("  → Initializing Document AI client")
    print(f"  → Project: {PROJECT_ID}")
    print(f"  → Location: {LOCATION}")
    print(f"  → Processor: {PROCESSOR_ID}")
    
    opts = ClientOptions(api_endpoint=f"{LOCATION}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)
    
    return client


# ----------------------------
# OCR EXTRACTION
# ----------------------------
def process_document(image_path: str) -> documentai.Document:
    """Process document with Document AI OCR."""
    
    print("\n[1] Loading image...")
    with open(image_path, "rb") as image_file:
        image_content = image_file.read()
    
    # Get image info
    img = Image.open(image_path)
    print(f"✓ Image loaded: {img.size}\n")
    
    print("[2] Processing with Document AI...")
    client = setup_document_ai()
    
    # Configure the process request
    name = client.processor_path(PROJECT_ID, LOCATION, PROCESSOR_ID)
    
    # Determine mime type
    mime_type = "image/jpeg"
    if image_path.lower().endswith('.png'):
        mime_type = "image/png"
    
    raw_document = documentai.RawDocument(content=image_content, mime_type=mime_type)
    request = documentai.ProcessRequest(name=name, raw_document=raw_document)
    
    result = client.process_document(request=request)
    document = result.document
    
    print("✓ OCR completed\n")
    return document


# ----------------------------
# GRADE EXTRACTION FROM OCR TEXT
# ----------------------------
def extract_text_blocks(document: documentai.Document) -> List[Dict]:
    """Extract text blocks with positions."""
    blocks = []
    
    for page in document.pages:
        for block in page.blocks:
            text = get_text(block.layout, document.text)
            
            # Get bounding box
            vertices = block.layout.bounding_poly.normalized_vertices
            if vertices:
                y_min = min(v.y for v in vertices)
                y_max = max(v.y for v in vertices)
                x_min = min(v.x for v in vertices)
                
                blocks.append({
                    'text': text.strip(),
                    'y_min': y_min,
                    'y_max': y_max,
                    'x_min': x_min
                })
    
    # Sort by vertical position
    blocks.sort(key=lambda b: (b['y_min'], b['x_min']))
    return blocks


def get_text(layout: documentai.Document.Page.Layout, document_text: str) -> str:
    """Extract text from layout."""
    response = ""
    for segment in layout.text_anchor.text_segments:
        start_index = int(segment.start_index) if segment.start_index else 0
        end_index = int(segment.end_index)
        response += document_text[start_index:end_index]
    return response


def normalize_subject_name(text: str) -> str:
    """Normalize subject name to match standard format."""
    text_lower = text.lower().strip()
    
    for standard_name, variations in SUBJECT_VARIATIONS.items():
        if text_lower in variations:
            return standard_name
    
    return None


def extract_number(text: str) -> float:
    """Extract number from text."""
    # Remove common OCR artifacts
    text = text.replace('O', '0').replace('o', '0').replace('l', '1').replace('I', '1')
    
    # Find numbers
    match = re.search(r'\d+\.?\d*', text)
    if match:
        try:
            num = float(match.group())
            if 70 <= num <= 100:
                return num
        except:
            pass
    return None


def extract_grades_from_blocks(blocks: List[Dict]) -> Dict[str, Dict]:
    """Extract grades by analyzing text blocks."""
    
    print("[3] Analyzing OCR text blocks...")
    
    grades = {}
    current_subject = None
    
    for i, block in enumerate(blocks):
        text = block['text']
        
        # Check if this is a subject name
        subject = normalize_subject_name(text)
        if subject:
            print(f"  → Found subject: {subject}")
            current_subject = subject
            grades[subject] = {}
            
            # Look ahead for grade values in the same row
            # Check next 5-8 blocks (typically Q1, Q2, Q3, Q4, Final)
            for j in range(i + 1, min(i + 10, len(blocks))):
                next_block = blocks[j]
                
                # Stop if we've moved to a new row (significant vertical change)
                if abs(next_block['y_min'] - block['y_min']) > 0.03:
                    break
                
                # Try to extract number
                num = extract_number(next_block['text'])
                if num:
                    # Determine which quarter based on position
                    grade_values = grades[subject]
                    if len(grade_values) == 0:
                        grade_values['Q1'] = num
                    elif len(grade_values) == 1:
                        grade_values['Q2'] = num
                    elif len(grade_values) == 2:
                        grade_values['Q3'] = num
                    elif len(grade_values) == 3:
                        grade_values['Q4'] = num
                    elif len(grade_values) == 4:
                        grade_values['Final Grade'] = num
    
    print(f"✓ Extracted {len(grades)} subjects\n")
    return grades


# ----------------------------
# VALIDATION
# ----------------------------
def validate_grades(grades: Dict) -> Dict:
    """Validate extracted grades."""
    print("[4] Validating grades...")
    
    validated = {}
    required_keys = ['Q1', 'Q2', 'Q3', 'Q4', 'Final Grade']
    
    for subject in SUBJECTS:
        if subject not in grades:
            print(f"  ⚠ {subject}: Missing")
            continue
        
        grade_info = grades[subject]
        
        # Check all keys present
        if not all(k in grade_info for k in required_keys):
            print(f"  ⚠ {subject}: Incomplete (has {list(grade_info.keys())})")
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
def main(image_path="report_card.jpg", debug=True):
    """
    Main extraction function.
    
    Args:
        image_path: Path to report card image
        debug: If True, prints detailed debug info
    """
    
    print("="*70)
    print("DepEd Report Card Grade Extractor (Document AI)")
    print("="*70)
    
    # Process document
    document = process_document(image_path)
    
    # Extract text blocks
    blocks = extract_text_blocks(document)
    print(f"[Debug] Total text blocks extracted: {len(blocks)}\n")
    
    if debug:
        print("[Debug] First 30 text blocks found:")
        for i, block in enumerate(blocks[:30]):
            print(f"  [{i}] {block['text'][:50]}")
        print()
    
    # Extract grades
    grades = extract_grades_from_blocks(blocks)
    
    if debug and grades:
        print("[Debug] Raw extracted grades:")
        print(json.dumps(grades, indent=2))
        print()
    
    if not grades:
        print("✗ Extraction failed - no grades found")
        print("\n[Debug] First 20 text blocks:")
        for block in blocks[:20]:
            print(f"  {block['text']}")
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
    # Change image_path to your report card image
    result = main(
        image_path="report_card.jpg",  # or "img1.jpg"
        debug=True  # Set to False to hide debug output
    )
    
    print("\n" + "="*70)
    print("JSON Output:")
    print("="*70)
    print(json.dumps(result, indent=2))