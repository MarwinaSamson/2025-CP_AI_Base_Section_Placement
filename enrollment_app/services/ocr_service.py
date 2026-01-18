"""
Complete OCR Grade Verification System v5 - STANDALONE WITH HANDWRITING OPTIMIZATION
Full-featured OCR system with all parsing strategies + handwriting enhancements
NO EXTERNAL DEPENDENCIES (self-contained)

Features:
1. Image preprocessing (contrast, sharpening, denoising, binarization)
2. Document AI table parsing
3. Bounding box layout analysis  
4. Text-based multi-pass extraction
5. Digit correction for handwriting
6. Grade validation and error detection
"""

import re
import difflib
from typing import Dict, Optional, List, Tuple
from google.cloud import documentai
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import io

# Try to import OpenCV, but make it optional
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: opencv-python not installed. Image preprocessing disabled.")
    print("Install with: pip install opencv-python")


class OCRGradeVerifier:
    """Complete OCR system with handwriting optimization for DepEd report cards."""

    SUBJECT_ALIASES = {
        'filipino': ['filipino', 'pilipino'],
        'english': ['english'],
        'mathematics': ['mathematics', 'math'],
        'science': ['science'],
        'araling_panlipunan': ['araling panlipunan', 'arpan', 'ap', 'a.p', 'a.p.', 'araling', 'panlipunan'],
        'edukasyon_sa_pagpapakatao': [
            'esp', 'edukasyon sa pagpapakatao', 'e.s.p', 'e.s.p.',
            'good manners and right conduct', 'gmrc', 'g.m.r.c', 'gmrc/esp'
        ],
        'edukasyon_pangkabuhayan': [
            'epp', 'tle', 'epp/tle', 'technology and livelihood',
            'edukasyon pangkabuhayan', 'e.p.p', 'education(tle)', 'technology'
        ],
        'mapeh': ['mapeh', 'm.a.p.e.h', 'm.a.p.e.h.'],
    }

    IGNORE_KEYWORDS = [
        'quarter', 'remarks', 'descriptor', 'grading scale', 'grade',
        'passed', 'failed', 'general average', 'conduct', 'periodic',
        'rating', 'learning areas', 'behavior', 'observed',
        'values', 'outstanding', 'satisfactory', 'action taken',
        'promoted', 'homeroom', 'guidance', 'marking'
    ]

    NOISE_WORDS = {
        'adelfagirls', 'adelfa', 'daffodil', 'girls', 'boys', 'school',
        'report', 'card', 'academic', 'performance', 'learner', 'grading',
        'system', 'secondary', 'junior', 'senior', 'high', 'district',
        'division', 'department'
    }

    MAPEH_SUBCOMPONENTS = {'music', 'arts', 'art', 'pe', 'p.e', 'p.e.', 'health', 'physical education'}

    SUBJECT_FUZZY_THRESHOLD = 0.70
    ROW_Y_PADDING = 40
    COLUMN_PAD = 60

    def __init__(self, tolerance: float = 3.0, project_id: Optional[str] = None, 
                 processor_id: Optional[str] = None, location: str = 'us',
                 enable_preprocessing: bool = True):
        """
        Initialize OCR Grade Verifier with handwriting optimization.
        
        Args:
            tolerance: Maximum allowed difference (±3.0 recommended)
            project_id: Google Cloud Project ID
            processor_id: Document AI Processor ID  
            location: Processor location (default: 'us')
            enable_preprocessing: Enable image preprocessing for handwriting (recommended)
        """
        self.tolerance = tolerance
        self.project_id = project_id or self._get_project_id()
        self.processor_id = processor_id or self._get_processor_id()
        self.location = location
        self.enable_preprocessing = enable_preprocessing and CV2_AVAILABLE
        self.doc_ai_client = documentai.DocumentProcessorServiceClient()
        # Runtime tuning flags
        import os
        # Strict final-grade enforcement: only accept values inside detected final column band
        self.strict_final_only = os.environ.get('OCR_STRICT_FINAL_ONLY', '1').lower() in {'1', 'true', 'yes'}
        # Aggressive digit correction toggle (disabled by default to avoid miscorrections like 97→92)
        self.enable_aggressive_digit_correction = os.environ.get('OCR_ENABLE_AGGRESSIVE_DIGIT_CORRECTION', '0').lower() in {'1', 'true', 'yes'}
        
        if enable_preprocessing and not CV2_AVAILABLE:
            print("⚠️  Warning: Preprocessing requested but opencv-python not available")
            print("   Install with: pip install opencv-python")
    
    def _get_project_id(self) -> str:
        """Get Google Cloud project ID from environment."""
        import os
        # 1) Environment variables
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID')
        if project_id:
            return project_id

        # 2) Django settings OCR_CONFIG
        try:
            from django.conf import settings  # lazily import to avoid early Django dependency
            if hasattr(settings, 'OCR_CONFIG'):
                project_id = settings.OCR_CONFIG.get('project_id')
                if project_id:
                    return project_id
        except Exception:
            pass

        # 3) your_personalized_config module
        try:
            from your_personalized_config import PROJECT_ID as CONFIG_PROJECT_ID
            if CONFIG_PROJECT_ID:
                return CONFIG_PROJECT_ID
        except Exception:
            pass

        # 4) No source found → raise with guidance
        raise ValueError(
            "Project ID not found. Set GOOGLE_CLOUD_PROJECT or GCP_PROJECT_ID environment variable, "
            "or define OCR_CONFIG['project_id'] in Django settings, or set PROJECT_ID in your_personalized_config.py."
        )
    
    def _get_processor_id(self) -> str:
        """Get Document AI Processor ID from environment."""
        import os
        # 1) Environment variable
        processor_id = os.environ.get('DOCUMENT_AI_PROCESSOR_ID')
        if processor_id:
            return processor_id

        # 2) Django settings OCR_CONFIG
        try:
            from django.conf import settings
            if hasattr(settings, 'OCR_CONFIG'):
                processor_id = settings.OCR_CONFIG.get('processor_id')
                if processor_id:
                    return processor_id
        except Exception:
            pass

        # 3) your_personalized_config module
        try:
            from your_personalized_config import PROCESSOR_ID as CONFIG_PROCESSOR_ID
            if CONFIG_PROCESSOR_ID:
                return CONFIG_PROCESSOR_ID
        except Exception:
            pass

        # 4) No source found → raise with guidance
        raise ValueError(
            "Document AI Processor ID not found. Set DOCUMENT_AI_PROCESSOR_ID environment variable, "
            "or define OCR_CONFIG['processor_id'] in Django settings, or set PROCESSOR_ID in your_personalized_config.py."
        )

    # =====================================================
    # IMAGE PREPROCESSING FOR HANDWRITING OPTIMIZATION
    # =====================================================
    
    def preprocess_image(self, image_path: str) -> bytes:
        """
        Preprocess image to improve OCR accuracy on handwritten text.
        
        Applies: denoising, contrast enhancement, sharpening, binarization, resizing
        Returns: Preprocessed image as bytes (PNG format)
        """
        if not CV2_AVAILABLE:
            print("  ⚠️  Preprocessing skipped (opencv not available)")
            with open(image_path, 'rb') as f:
                return f.read()
        
        print(f"\n[Image Preprocessing for Handwriting]")
        
        try:
            # Read image
            img = Image.open(image_path)
            print(f"  Original size: {img.size}")
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Convert to OpenCV format
            img_array = np.array(img)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # 1. Denoise
            img_cv = cv2.fastNlMeansDenoisingColored(img_cv, None, 10, 10, 7, 21)
            print(f"  ✓ Applied denoising")
            
            # 2. Grayscale
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # 3. Adaptive contrast (CLAHE)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            print(f"  ✓ Enhanced contrast (CLAHE)")
            
            # 4. Sharpen
            kernel = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
            gray = cv2.filter2D(gray, -1, kernel)
            print(f"  ✓ Applied sharpening")
            
            # 5. Binarization (Otsu's threshold)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            print(f"  ✓ Applied binarization (black/white)")
            
            # 6. Resize if too small (optimal ~1500px height for OCR)
            height, width = binary.shape
            if height < 1500:
                scale = 1500 / height
                new_width = int(width * scale)
                new_height = int(height * scale)
                binary = cv2.resize(binary, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                print(f"  ✓ Resized: {img.size} → {new_width}x{new_height}")
            
            # Convert to PIL and then to bytes
            img_processed = Image.fromarray(binary)
            byte_arr = io.BytesIO()
            img_processed.save(byte_arr, format='PNG')
            
            print(f"  ✓ Preprocessing complete\n")
            return byte_arr.getvalue()
            
        except Exception as e:
            print(f"  × Preprocessing failed: {e}")
            print(f"  → Using original image\n")
            with open(image_path, 'rb') as f:
                return f.read()

    
    # =====================================================
    # OCR ENTRY POINT
    # =====================================================
    
    def extract_grades_and_name_from_image(self, image_path: str) -> Dict:
        """
        Extract both grades and student name from report card image.
        Returns dict with 'grades' (Dict[str, float]) and 'student_name' (str).
        """
        try:
            # Preprocess image if enabled (improves handwriting recognition)
            if self.enable_preprocessing:
                content = self.preprocess_image(image_path)
                mime_type = 'image/png'
            else:
                with open(image_path, 'rb') as f:
                    content = f.read()
                import mimetypes
                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type:
                    mime_type = 'image/jpeg'

            # Build the Document AI processor path
            name = self.doc_ai_client.processor_path(
                self.project_id,
                self.location,
                self.processor_id
            )

            # Create the request
            raw_document = documentai.RawDocument(
                content=content,
                mime_type=mime_type
            )

            request = documentai.ProcessRequest(
                name=name,
                raw_document=raw_document
            )

            # Process the document
            response = self.doc_ai_client.process_document(request=request)
            document = response.document

            # Extract text from the document
            full_text = document.text or ''
            
            print(f"\n{'='*70}")
            print(f"OCR for: {image_path.split('/')[-1]}")
            print(f"{'='*70}")
            print(f"OCR Engine: Google Document AI (Processor: {self.processor_id})")
            print(full_text[:500] + "..." if len(full_text) > 500 else full_text)
            print(f"{'='*70}\n")
            
            # Parse grades using improved logic
            grades = self._parse_grades(full_text, document)
            
            # Apply handwriting corrections if preprocessing was used
            if self.enable_preprocessing and grades:
                grades = self.apply_digit_corrections(grades, full_text)
                grades = self.validate_grade_ranges(grades)
            
            # Extract student name
            student_name = self._extract_student_name(full_text)
            
            return {
                'grades': grades,
                'student_name': student_name,
                'full_text': full_text
            }
        except Exception as e:
            error_msg = str(e)
            if "DNS resolution failed" in error_msg or "UNAVAILABLE" in error_msg:
                raise Exception(
                    "Network error: Cannot reach Google Document AI API.\n"
                    "Please check your internet connection and firewall settings."
                )
            elif "credentials" in error_msg.lower() or "permission denied" in error_msg.lower():
                raise Exception(
                    "Authentication error: Invalid Google Cloud credentials or insufficient permissions.\n"
                    "Please ensure:\n"
                    "1. GOOGLE_APPLICATION_CREDENTIALS is set correctly\n"
                    "2. Your service account has Document AI API permissions\n"
                    "3. The processor ID exists and is in the correct region"
                )
            elif "NOT_FOUND" in error_msg or "not found" in error_msg.lower():
                raise Exception(
                    f"Document AI processor not found: {self.processor_id}\n"
                    "Please verify the processor ID and region are correct.\n"
                    "Create a processor at: https://console.cloud.google.com/document-ai/processors"
                )
            else:
                raise Exception(f"OCR Error: {error_msg}")

    def extract_grades_from_image(self, image_path: str) -> Dict[str, float]:
        """Extract grades from report card image using Google Document AI with optional preprocessing."""
        result = self.extract_grades_and_name_from_image(image_path)
        return result['grades']

    # =====================================================
    # STUDENT NAME EXTRACTION
    # =====================================================
    
    def _extract_student_name(self, text: str) -> Optional[str]:
        """
        Extract student name from report card text.
        Looks for 'Name:' field or similar patterns common in DepEd report cards.
        Returns normalized full name or None if not found.
        """
        if not text:
            return None
        
        lines = text.split('\n')
        name = None
        
        # Pattern 1: "Name:" or "NAME:" followed by student name
        name_pattern = r'(?:^|[:\s])name\s*:?\s*([a-zA-Z\s,\.]+?)(?:\n|$|age|grade|yr|year)'
        matches = re.finditer(name_pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            candidate = match.group(1).strip()
            # Validate: must have at least 2 parts (first and last name)
            if len(candidate.split()) >= 2 and len(candidate) > 5:
                name = candidate
                break
        
        if not name:
            # Pattern 2: Check line-by-line; lines with "Name" followed by actual name
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                if line_lower.startswith('name'):
                    # The name might be on the same line or next line
                    potential_name = line.replace('Name', '').replace('name', '').replace(':', '').strip()
                    if potential_name and len(potential_name) > 5:
                        name = potential_name
                        break
                    elif i + 1 < len(lines):
                        potential_name = lines[i + 1].strip()
                        if potential_name and len(potential_name) > 5 and not any(keyword in potential_name.lower() for keyword in ['age', 'grade', 'year', 'school']):
                            name = potential_name
                            break
        
        if name:
            # Normalize: uppercase first letter of each word, remove extra spaces
            name = ' '.join(word.capitalize() for word in name.split())
            # Remove trailing metadata (comma-separated notes)
            name = name.split(',')[0].strip()
            return name
        
        return None
    
    def verify_student_name(self, extracted_name: Optional[str], registered_full_name: str) -> Dict[str, any]:
        """
        Compare extracted name from report card with registered student name.
        Returns dict with:
          - 'is_match': bool (True if names match within tolerance)
          - 'extracted': str (extracted name or None)
          - 'registered': str (registered name)
          - 'similarity': float (0-100, similarity score)
          - 'reason': str (explanation of match/mismatch)
        """
        if not extracted_name:
            return {
                'is_match': False,
                'extracted': None,
                'registered': registered_full_name,
                'similarity': 0,
                'reason': 'Could not extract name from report card. Please ensure the card is clear.'
            }
        
        if not registered_full_name:
            return {
                'is_match': False,
                'extracted': extracted_name,
                'registered': None,
                'similarity': 0,
                'reason': 'No registered name to compare against.'
            }
        
        # Normalize both names for comparison
        extracted_norm = self._normalize_name(extracted_name)
        registered_norm = self._normalize_name(registered_full_name)
        
        # Exact match (after normalization)
        if extracted_norm.lower() == registered_norm.lower():
            return {
                'is_match': True,
                'extracted': extracted_name,
                'registered': registered_full_name,
                'similarity': 100,
                'reason': 'Exact match'
            }
        
        # Check if extracted name is a substring or vice versa (for partial matches)
        extracted_parts = extracted_norm.lower().split()
        registered_parts = registered_norm.lower().split()
        
        # Count matching parts (first name, last name, middle name)
        matching_parts = sum(1 for part in extracted_parts if part in registered_parts)
        total_parts = max(len(extracted_parts), len(registered_parts))
        similarity = (matching_parts / total_parts * 100) if total_parts > 0 else 0
        
        # Accept if at least 80% similarity or if key parts match
        if similarity >= 80:
            return {
                'is_match': True,
                'extracted': extracted_name,
                'registered': registered_full_name,
                'similarity': round(similarity, 2),
                'reason': f'{round(similarity, 0)}% name match (partial match acceptable)'
            }
        elif similarity >= 50:
            return {
                'is_match': False,
                'extracted': extracted_name,
                'registered': registered_full_name,
                'similarity': round(similarity, 2),
                'reason': f'{round(similarity, 0)}% name match - likely mismatch. Please verify the name on your report card matches your registered name.'
            }
        else:
            return {
                'is_match': False,
                'extracted': extracted_name,
                'registered': registered_full_name,
                'similarity': round(similarity, 2),
                'reason': 'Name does not match. The name on the report card does not match your registered name.'
            }
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize a name for comparison by:
        - Converting to lowercase
        - Removing extra spaces
        - Removing special characters
        - Handling common abbreviations (Jr., Sr., etc.)
        """
        if not name:
            return ""
        
        name = name.strip()
        # Remove suffixes
        name = re.sub(r',?\s*(jr|sr|iii|ii|i|iv|v)\.?\s*$', '', name, flags=re.IGNORECASE)
        # Remove multiple spaces
        name = re.sub(r'\s+', ' ', name)
        return name.lower()

    # =====================================================
    # MAIN PARSING LOGIC
    # =====================================================
    
    def _parse_grades(self, text: str, document=None) -> Dict[str, float]:
        """
        Main parsing logic with multiple strategies.
        Returns dictionary of subject -> final grade (5th column only).
        """
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        results = {}
        detected_subjects = set()
        
        # Strategy 0A: Document AI table parsing (most accurate)
        if document and hasattr(document, 'pages') and document.pages:
            # Check if tables exist in the document
            has_tables = False
            for page in document.pages:
                if hasattr(page, 'tables') and page.tables:
                    has_tables = True
                    break
            
            if has_tables:
                try:
                    layout_results, subjects = self._parse_with_document_layout(document)
                    results.update(layout_results)
                    detected_subjects.update(subjects)
                    print(f"  Strategy 0A extracted {len(layout_results)} subjects")
                except Exception as e:
                    print(f"  Strategy 0A failed: {e}")
        
        # Strategy 0B: Bounding box parsing (fallback - skip if we already have good results)
        if len(results) < 4 and document and hasattr(document, 'pages'):
            try:
                layout_results, subjects = self._parse_with_layout(document)
                results.update(layout_results)
                detected_subjects.update(subjects)
            except Exception as e:
                print(f"  Strategy 0B failed: {e}, continuing with text-based strategies")
        
        # Strategy 1: Direct line parsing with improved column detection
        if len(results) < 6:
            direct_results = self._parse_direct_lines_improved(lines)
            results.update({k: v for k, v in direct_results.items() if k not in results})
        
        # Strategy 2: Context-aware parsing with column awareness
        if len(results) < 6:
            context_results = self._parse_with_context_improved(lines)
            results.update({k: v for k, v in context_results.items() if k not in results})
        
        # Strategy 3: Pattern matching with spatial analysis
        if len(results) < 6:
            pattern_results = self._parse_patterns_improved(text)
            results.update({k: v for k, v in pattern_results.items() if k not in results})
        
        # Post-processing: recover missing subjects
        missing_subjects = detected_subjects - set(results.keys())
        if missing_subjects:
            print(f"\n[Post-Processing] Retrying missing subjects: {missing_subjects}")
            for subject in missing_subjects:
                recovery_grade = self._recover_subject_grade(subject, lines, text)
                if recovery_grade is not None:
                    results[subject] = recovery_grade
                    print(f"  ✓ Recovered {subject}: {recovery_grade}")
        
        return results

    # =====================================================
    # STRATEGY 0A: IMPROVED DOCUMENT AI TABLE PARSING
    # =====================================================
    
    def _parse_with_document_layout(self, document) -> tuple:
        """
        Parse grades using Document AI's native table detection.
        IMPROVED: Better 5th column detection and MAPEH handling.
        """
        print("\n[Strategy 0A: Document AI Table Parsing - IMPROVED]")
        
        results: Dict[str, float] = {}
        detected = set()
        
        try:
            for page in document.pages:
                if hasattr(page, 'tables') and page.tables:
                    print(f"  Found {len(page.tables)} table(s) on page")
                    for table_idx, table in enumerate(page.tables):
                        print(f"    Processing table {table_idx}...")
                        table_results = self._parse_table_structure_improved(table, document.text)
                        results.update(table_results)
        
        except Exception as e:
            print(f"  Table parsing failed: {e}")
            return {}, set()
        
        # Detect subjects mentioned in text
        full_text = document.text.lower() if document.text else ""
        for subject, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                if alias.lower() in full_text:
                    detected.add(subject)
                    break
        
        print(f"  Detected subjects: {detected}")
        return results, detected
    
    def _parse_table_structure_improved(self, table, full_text: str) -> Dict[str, float]:
        """
        IMPROVED: Extract grades from Document AI table with accurate 5th column detection.
        
        Strategy:
        1. Find header row and locate "Final" column explicitly
        2. For each subject row, extract grade from 5th column position
        3. Skip MAPEH sub-components (Music, Arts, PE, Health)
        4. For MAPEH, only take the main MAPEH row
        """
        results = {}

        try:
            # Extract header to find column structure
            header_cells: List[str] = []
            final_col_idx: Optional[int] = None
            
            if hasattr(table, 'header_rows') and table.header_rows:
                first_header = table.header_rows[0]
                for idx, header_cell in enumerate(getattr(first_header, 'cells', [])):
                    header_text = self._extract_text_from_layout_element(
                        header_cell.layout, full_text
                    ) if hasattr(header_cell, 'layout') else ""
                    header_text_clean = header_text.strip().lower()
                    header_cells.append(header_text_clean)
                    
                    # Detect Final column explicitly
                    if any(token in header_text_clean for token in ['final', 'rating', 'fg']):
                        final_col_idx = idx
                        print(f"      Found 'Final' column at index {idx}: '{header_text_clean}'")

            print(f"    Table headers: {header_cells}")
            if final_col_idx is not None:
                print(f"    Final column detected at index: {final_col_idx}")

            # Extract data rows
            rows_text: List[List[str]] = []
            for row in getattr(table, 'body_rows', []):
                row_cells: List[str] = []
                for cell in getattr(row, 'cells', []):
                    cell_text = self._extract_text_from_layout_element(
                        cell.layout, full_text
                    ) if hasattr(cell, 'layout') else ""
                    row_cells.append(cell_text.strip())
                rows_text.append(row_cells)

            # Process each data row
            for row_idx, row_cells in enumerate(rows_text):
                if not row_cells:
                    continue

                # First cell is subject name
                subject_text = row_cells[0].lower().strip()
                
                # Skip MAPEH sub-components
                if any(sub in subject_text for sub in self.MAPEH_SUBCOMPONENTS):
                    if 'mapeh' not in subject_text:
                        print(f"    Row {row_idx}: Skipping MAPEH sub-component: '{subject_text}'")
                        continue
                
                subject_key = self._identify_subject(subject_text)
                if not subject_key:
                    continue

                print(f"    Row {row_idx}: Subject='{subject_key}', Cells={row_cells}")

                # Extract numeric values from all cells (except first)
                numeric_cells: List[Optional[float]] = []
                for cell_text in row_cells[1:]:
                    numeric_cells.append(self._extract_single_grade(cell_text))

                print(f"      Numeric values: {numeric_cells}")

                # Strategy 1: Use detected Final column if available
                grade: Optional[float] = None
                
                if final_col_idx is not None and len(row_cells) > final_col_idx:
                    # Adjust for subject column (header includes subject, data doesn't)
                    data_col_idx = final_col_idx - 1
                    if 0 <= data_col_idx < len(numeric_cells):
                        grade = numeric_cells[data_col_idx]
                        print(f"      → Using Final column (idx {data_col_idx}): {grade}")

                # Strategy 2: Look for 5th numeric value (Q1 Q2 Q3 Q4 FINAL)
                if grade is None:
                    valid_numbers = [v for v in numeric_cells if v is not None]
                    if len(valid_numbers) >= 5:
                        grade = valid_numbers[4]  # 5th value (index 4)
                        print(f"      → Using 5th value: {grade} from {valid_numbers}")
                    elif len(valid_numbers) == 4:
                        # Only 4 quarters, compute average
                        grade = round(sum(valid_numbers) / 4, 2)
                        print(f"      → Averaging 4 quarters: {grade}")

                # Strategy 3: Take rightmost number
                if grade is None and numeric_cells:
                    valid_numbers = [v for v in numeric_cells if v is not None]
                    if valid_numbers:
                        grade = valid_numbers[-1]
                        print(f"      → Using rightmost value: {grade}")

                if grade is None:
                    print(f"      × No grade found")
                    continue

                # Store result
                results[subject_key] = grade
                print(f"      ✓ Extracted: {subject_key} = {grade}")

        except Exception as e:
            print(f"    Table parsing error: {e}")

        return results
    
    def _extract_text_from_layout_element(self, layout, full_text: str) -> str:
        """Extract text from Document AI layout element."""
        try:
            if not layout:
                return ""

            anchor = getattr(layout, 'text_anchor', None)
            if not anchor:
                return ""

            # Try direct content first
            direct = getattr(anchor, 'content', None)
            if direct:
                return direct

            # Extract from text segments
            segments = getattr(anchor, 'text_segments', [])
            if not segments:
                return ""

            pieces: List[str] = []
            for seg in segments:
                start = getattr(seg, 'start_index', None) or getattr(seg, 'start', None)
                end = getattr(seg, 'end_index', None) or getattr(seg, 'end', None)
                if start is None or end is None:
                    continue
                pieces.append(full_text[int(start):int(end)])

            return ''.join(pieces)
        except Exception:
            return ""
    
    def _extract_single_grade(self, cell_text: str) -> Optional[float]:
        """Extract a single grade value from cell text."""
        cell_text = cell_text.strip()
        if not cell_text:
            return None
        
        # Find 2-3 digit numbers
        numbers = re.findall(r'\b\d{2,3}\b', cell_text)
        for num in numbers:
            try:
                val = int(num)
                if 70 <= val <= 100:
                    return float(val)
            except ValueError:
                pass
        
        return None

    # =====================================================
    # STRATEGY 0B: BOUNDING BOX LAYOUT PARSING (FALLBACK)
    # =====================================================
    
    def _parse_with_layout(self, annotation) -> tuple:
        """Parse grades using bounding boxes (Vision API fallback)."""
        print("\n[Strategy 0B: Bounding Box Layout Parsing]")

        words = self._extract_word_boxes(annotation)
        if not words:
            return {}, set()

        # Remove "Observed Values" section
        observed_stop_y = self._detect_observed_values_y(words)
        if observed_stop_y:
            words = [w for w in words if w['y_center'] < observed_stop_y]

        x_min = min(w['xmin'] for w in words)
        x_max = max(w['xmax'] for w in words)

        # Detect columns with improved header matching
        columns = self._detect_columns_improved(words, x_min, x_max)
        col_info = [(c['label'], f"{c['xmin']:.0f}-{c['xmax']:.0f}") for c in columns]
        print(f"  Column structure: {col_info}")

        # Detect Remarks column band (to clip final-grade search)
        remarks_band = self._detect_remarks_band(words)
        if remarks_band:
            print(f"  Remarks band: x={remarks_band['xmin']:.0f}-{remarks_band['xmax']:.0f}")

        # Index numeric words
        numeric_words = [w for w in words if self._is_valid_grade_text(w['text'])]
        for idx, w in enumerate(numeric_words):
            w['id'] = idx
            w['value'] = float(int(w['text'].replace('O', '0')))

        # Detect final column band (prefer rightmost numeric cluster before Remarks)
        final_band = None
        if remarks_band:
            final_band = self._detect_final_column_band_left_of(numeric_words, remarks_band['xmin'])
        if not final_band:
            final_band = self._detect_final_column_band(numeric_words)
        if final_band:
            print(f"  Final column band: x={final_band['xmin']:.0f}-{final_band['xmax']:.0f}")

        results: Dict[str, float] = {}
        detected = set()
        used_ids = set()

        # Find subject rows (leftmost column grouping + subject identification)
        subject_rows: Dict[str, Dict] = {}
        left_x_threshold = x_min + (x_max - x_min) * 0.20  # first 20% of width
        left_words = [w for w in words if w['x_center'] <= left_x_threshold]
        left_words.sort(key=lambda w: w['y_center'])

        # IMPROVED: Better y-banding with stricter grouping and adaptive padding
        # Calculate adaptive padding based on row density
        if len(left_words) > 8:
            y_values = [w['y_center'] for w in left_words]
            y_diffs = sorted([y_values[i+1] - y_values[i] for i in range(len(y_values)-1)])
            median_y_gap = y_diffs[len(y_diffs) // 2] if y_diffs else self.ROW_Y_PADDING
            adaptive_padding = max(median_y_gap * 0.4, self.ROW_Y_PADDING * 0.5)
        else:
            median_y_gap = self.ROW_Y_PADDING
            adaptive_padding = self.ROW_Y_PADDING / 2
        
        row_groups: List[List[Dict]] = []
        for w in left_words:
            if not row_groups:
                row_groups.append([w])
                continue
            last_group = row_groups[-1]
            avg_y = sum(item['y_center'] for item in last_group) / len(last_group)
            # Use stricter grouping to avoid mixing adjacent rows
            if abs(w['y_center'] - avg_y) <= adaptive_padding:
                last_group.append(w)
            else:
                row_groups.append([w])

        for group in row_groups:
            group_sorted = sorted(group, key=lambda g: g['x_center'])
            text_concat = ' '.join(g['text'] for g in group_sorted)
            subject_key = self._identify_subject(text_concat)
            if not subject_key:
                continue

            # Skip MAPEH sub-components unless main MAPEH row
            if any(sub in text_concat.lower() for sub in self.MAPEH_SUBCOMPONENTS) and 'mapeh' not in text_concat.lower():
                continue

            detected.add(subject_key)
            y_center = sum(g['y_center'] for g in group_sorted) / len(group_sorted)
            subject_rows[subject_key] = {
                'y_center': y_center,
                'xmin': min(g['xmin'] for g in group_sorted),
                'xmax': max(g['xmax'] for g in group_sorted),
                'text': text_concat,  # Store for debugging
            }

        # Fallback: if top row label (e.g., Filipino) is cropped but we have English,
        # estimate the Filipino row y using the median gap and include it for final-band search.
        if 'filipino' not in subject_rows and 'english' in subject_rows and final_band:
            est_y = subject_rows['english']['y_center'] - median_y_gap
            subject_rows['filipino'] = {
                'y_center': est_y,
                'xmin': subject_rows['english']['xmin'],
                'xmax': subject_rows['english']['xmax'],
                'text': '(estimated top row)'
            }
            detected.add('filipino')

        print(f"  Detected subject anchors: {list(subject_rows.keys())}")
        for subj, info in subject_rows.items():
            print(f"    - {subj}: y={info['y_center']:.0f} (text: '{info['text'][:40]}')")

        # Extract grades for each subject
        for subject_key, row_info in subject_rows.items():
            # Find numbers in final column first
            row_numbers: List[Dict] = []
            
            # Use adaptive y-padding for grade matching (tighter than anchor detection)
            grade_y_tolerance = min(self.ROW_Y_PADDING * 0.8, 25)
            
            if final_band:
                # STRICT: only accept numbers inside the detected final column band
                for w in numeric_words:
                    if w['id'] in used_ids:
                        continue
                    if remarks_band and w['x_center'] >= remarks_band['xmin']:
                        continue
                    if (final_band['xmin'] <= w['x_center'] <= final_band['xmax'] and
                        abs(w['y_center'] - row_info['y_center']) <= grade_y_tolerance):
                        row_numbers.append(w)

                if not row_numbers:
                    if self.strict_final_only:
                        print(f"    × No final-column numbers found for {subject_key}")
                        continue
                    # Non-strict fallback: allow proximity-based numbers left of Remarks
                    for w in numeric_words:
                        if w['id'] in used_ids:
                            continue
                        if remarks_band and w['x_center'] >= remarks_band['xmin']:
                            continue
                        if abs(w['y_center'] - row_info['y_center']) <= grade_y_tolerance:
                            row_numbers.append(w)
                    if not row_numbers:
                        print(f"    × No numbers found for {subject_key}")
                        continue
            else:
                # No final band detected; allow proximity-based scan (still clipped before Remarks)
                for w in numeric_words:
                    if w['id'] in used_ids:
                        continue
                    if remarks_band and w['x_center'] >= remarks_band['xmin']:
                        continue
                    if abs(w['y_center'] - row_info['y_center']) <= grade_y_tolerance:
                        row_numbers.append(w)

                if not row_numbers:
                    print(f"    × No numbers found for {subject_key}")
                    continue

            # Group by column (sorted by x) and choose last group as final
            row_numbers_sorted = sorted(row_numbers, key=lambda n: n['x_center'])
            columns_group: List[List[Dict]] = []
            col_gap = 45.0
            for n in row_numbers_sorted:
                if not columns_group:
                    columns_group.append([n])
                else:
                    last_col = columns_group[-1]
                    if n['x_center'] - last_col[-1]['x_center'] > col_gap:
                        columns_group.append([n])
                    else:
                        last_col.append(n)

            final_group = columns_group[-1]
            closest = max(final_group, key=lambda n: n['x_center'])
            grade = closest['value']
            used_ids.add(closest['id'])

            results[subject_key] = grade
            print(f"    ✓ {subject_key}: {grade} (x={closest['x_center']:.0f})")

        return results, detected

    def _detect_columns_improved(self, words: List[Dict], x_min: float, x_max: float) -> List[Dict]:
        """Improved column detection with explicit header matching."""
        
        # Look for column headers
        header_tokens = {
            'q1': ['1', 'q1'],
            'q2': ['2', 'q2'],
            'q3': ['3', 'q3'],
            'q4': ['4', 'q4'],
            'final': ['final', 'fg', 'rating', 'grade']
        }
        
        detected_columns = {}
        
        for w in words:
            clean = w['text'].lower().replace('.', '').strip()
            for col_type, tokens in header_tokens.items():
                if clean in tokens:
                    if col_type not in detected_columns:
                        detected_columns[col_type] = []
                    detected_columns[col_type].append(w['x_center'])
        
        # Build column bands
        columns = []
        width = max(x_max - x_min, 1)
        
        # Use detected headers if available
        if len(detected_columns) >= 4:
            col_centers = []
            for col in ['q1', 'q2', 'q3', 'q4', 'final']:
                if col in detected_columns:
                    col_centers.append(sum(detected_columns[col]) / len(detected_columns[col]))
                else:
                    # Fallback position
                    idx = len(col_centers)
                    col_centers.append(x_min + (idx + 0.5) * (width / 5))
        else:
            # Default equal spacing
            col_centers = [x_min + (i + 0.5) * (width / 5) for i in range(5)]
        
        # Create column bands
        for idx, center in enumerate(col_centers):
            if idx == 0:
                xmin_band = center - self.COLUMN_PAD
                xmax_band = (center + col_centers[idx + 1]) / 2
            elif idx == len(col_centers) - 1:
                xmin_band = (col_centers[idx - 1] + center) / 2
                xmax_band = x_max + 100
            else:
                xmin_band = (col_centers[idx - 1] + center) / 2
                xmax_band = (center + col_centers[idx + 1]) / 2
            
            label = f"q{idx + 1}" if idx < 4 else 'final'
            columns.append({'label': label, 'xmin': xmin_band, 'xmax': xmax_band})
        
        return columns

    def _extract_word_boxes(self, annotation) -> List[Dict]:
        """Extract word bounding boxes from Document AI response."""
        words = []
        
        try:
            for page in annotation.pages:
                # Document AI structure: page -> tokens directly
                # Check if we have tokens (Document AI) or blocks (Vision API)
                if hasattr(page, 'tokens') and page.tokens:
                    # Document AI structure
                    for token in page.tokens:
                        if not hasattr(token, 'layout'):
                            continue
                        
                        layout = token.layout
                        if not hasattr(layout, 'bounding_poly'):
                            continue
                        
                        # Extract text from token
                        text = self._extract_text_from_layout_element(layout, annotation.text)
                        if not text or not text.strip():
                            continue
                        
                        # Get bounding box
                        bounding_poly = layout.bounding_poly
                        if not hasattr(bounding_poly, 'normalized_vertices') or not bounding_poly.normalized_vertices:
                            continue
                        
                        vertices = bounding_poly.normalized_vertices
                        xs = [v.x for v in vertices]
                        ys = [v.y for v in vertices]
                        
                        # Convert normalized coordinates (0-1) to pixel coordinates
                        # Assuming standard page dimensions
                        page_width = 1000
                        page_height = 1400
                        
                        xmin, xmax = min(xs) * page_width, max(xs) * page_width
                        ymin, ymax = min(ys) * page_height, max(ys) * page_height
                        
                        words.append({
                            'text': text.strip(),
                            'xmin': xmin,
                            'xmax': xmax,
                            'ymin': ymin,
                            'ymax': ymax,
                            'x_center': (xmin + xmax) / 2,
                            'y_center': (ymin + ymax) / 2
                        })
                
                elif hasattr(page, 'blocks') and page.blocks:
                    # Vision API structure (fallback)
                    for block in page.blocks:
                        if not hasattr(block, 'paragraphs'):
                            continue
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                text = ''.join([symbol.text for symbol in word.symbols]).strip()
                                if not text:
                                    continue

                                xs = [v.x or 0 for v in word.bounding_box.vertices]
                                ys = [v.y or 0 for v in word.bounding_box.vertices]

                                xmin, xmax = min(xs), max(xs)
                                ymin, ymax = min(ys), max(ys)

                                words.append({
                                    'text': text,
                                    'xmin': xmin,
                                    'xmax': xmax,
                                    'ymin': ymin,
                                    'ymax': ymax,
                                    'x_center': (xmin + xmax) / 2,
                                    'y_center': (ymin + ymax) / 2
                                })
        
        except Exception as e:
            print(f"  Warning: Could not extract word boxes: {e}")
            return []
        
        return words

    def _detect_observed_values_y(self, words: List[Dict]) -> Optional[float]:
        """Locate y-position of Observed Values section."""
        candidates = [w for w in words if 'observed' in w['text'].lower() or 'values' in w['text'].lower()]
        if not candidates:
            return None
        return min(w['y_center'] for w in candidates) - 5

    def _detect_remarks_band(self, words: List[Dict]) -> Optional[Dict[str, float]]:
        """Detect the 'Remarks' column band using header token."""
        header_words = [w for w in words if w['text'].lower().strip() in {'remarks', 'remark'}]
        if not header_words:
            return None
        xs = [w['x_center'] for w in header_words]
        xmin = min(xs) - 20
        xmax = max(xs) + 40
        return {'xmin': xmin, 'xmax': xmax}

    def _detect_final_column_band(self, numeric_words: List[Dict]) -> Optional[Dict[str, float]]:
        """Detect rightmost numeric cluster as Final column."""
        if not numeric_words:
            return None

        # Cluster by x-position
        bin_size = 30.0
        bins: Dict[int, List[float]] = {}
        for w in numeric_words:
            bin_key = int(w['x_center'] // bin_size)
            bins.setdefault(bin_key, []).append(w['x_center'])

        if not bins:
            return None

        # Get rightmost cluster
        rightmost_bin = max(bins.keys())
        x_vals = bins[rightmost_bin]
        return {'xmin': min(x_vals) - 5, 'xmax': max(x_vals) + 5}

    def _detect_final_column_band_left_of(self, numeric_words: List[Dict], x_limit: float) -> Optional[Dict[str, float]]:
        """Detect rightmost numeric cluster that lies completely left of x_limit."""
        if not numeric_words:
            return None
        bin_size = 30.0
        bins: Dict[int, List[float]] = {}
        for w in numeric_words:
            if w['x_center'] >= x_limit:
                continue
            bin_key = int(w['x_center'] // bin_size)
            bins.setdefault(bin_key, []).append(w['x_center'])
        if not bins:
            return None
        rightmost_bin = max(bins.keys())
        x_vals = bins[rightmost_bin]
        return {'xmin': min(x_vals) - 5, 'xmax': max(x_vals) + 5}

    def _is_valid_grade_text(self, text: str) -> bool:
        """Check if text is a valid grade number."""
        cleaned = text.strip().replace('O', '0')
        if not re.fullmatch(r'\d{2,3}', cleaned):
            return False
        try:
            val = int(cleaned)
        except ValueError:
            return False
        return 70 <= val <= 100

    def _match_subject_word(self, text: str) -> Optional[str]:
        """Match single-word subjects."""
        word = re.sub(r'[^a-z0-9 /]', '', text.lower()).strip()
        if not word or word in self.NOISE_WORDS:
            return None

        # Check for exact matches
        for subject, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                if alias.lower() == word:
                    return subject

        return None

    # =====================================================
    # STRATEGY 1: IMPROVED DIRECT LINE PARSING
    # =====================================================
    
    def _parse_direct_lines_improved(self, lines: List[str]) -> Dict[str, float]:
        """Parse lines with improved 5th column extraction."""
        print("\n[Strategy 1: Direct Line Parsing - IMPROVED]")
        results = {}
        
        for i, line in enumerate(lines):
            if self._is_noise_line(line):
                continue
            
            subject = self._identify_subject(line)
            if not subject or subject in results:
                continue
            
            # Skip MAPEH sub-components
            if any(sub in line.lower() for sub in self.MAPEH_SUBCOMPONENTS):
                if 'mapeh' not in line.lower():
                    continue
            
            print(f"  Line {i}: '{subject}' in: {line[:60]}...")
            
            # Collect context lines
            grade_lines = [line]
            for j in range(1, 3):
                if i + j < len(lines):
                    next_line = lines[i + j]
                    if self._identify_subject(next_line):
                        break
                    if self._is_noise_line(next_line):
                        continue
                    grade_lines.append(next_line)
            
            grade = self._extract_fifth_column_grade(grade_lines)
            if grade:
                results[subject] = grade
                print(f"    → {grade}")
        
        return results
    
    def _extract_fifth_column_grade(self, lines: List[str]) -> Optional[float]:
        """Extract 5th column grade with improved logic."""
        if not lines:
            return None

        combined = ' '.join(lines)
        grades = self._extract_all_grades_from_text(combined)
        
        # 5th value is final grade
        if len(grades) >= 5:
            return grades[4]
        elif len(grades) == 4:
            return round(sum(grades) / 4, 2)
        elif grades:
            return grades[-1]
        
        return None

    # =====================================================
    # STRATEGY 2: IMPROVED CONTEXT-AWARE PARSING
    # =====================================================
    
    def _parse_with_context_improved(self, lines: List[str]) -> Dict[str, float]:
        """Context-aware parsing with 5th column priority."""
        print("\n[Strategy 2: Context-Aware Parsing - IMPROVED]")
        results = {}
        
        for i, line in enumerate(lines):
            if self._is_noise_line(line):
                continue
            
            subject = self._identify_subject(line)
            if not subject or subject in results:
                continue
            
            # Skip MAPEH sub-components
            if any(sub in line.lower() for sub in self.MAPEH_SUBCOMPONENTS):
                if 'mapeh' not in line.lower():
                    continue
            
            # Build context
            context_lines = [line]
            for j in range(i + 1, min(len(lines), i + 4)):
                if self._identify_subject(lines[j]):
                    break
                if self._is_noise_line(lines[j]):
                    continue
                context_lines.append(lines[j])
            
            context = '\n'.join(context_lines)
            grades = self._extract_all_grades_from_text(context)
            
            grade = None
            if len(grades) >= 5:
                grade = grades[4]
                print(f"  {subject}: {grade} (5th value from {grades[:6]})")
            elif len(grades) == 4:
                grade = round(sum(grades) / 4, 2)
                print(f"  {subject}: {grade} (avg of {grades})")
            elif grades:
                grade = grades[-1]
                print(f"  {subject}: {grade} (last from {grades})")
            
            if grade:
                results[subject] = grade
        
        return results

    # =====================================================
    # STRATEGY 3: IMPROVED PATTERN MATCHING
    # =====================================================
    
    def _parse_patterns_improved(self, text: str) -> Dict[str, float]:
        """Pattern matching with spatial awareness."""
        print("\n[Strategy 3: Pattern Matching - IMPROVED]")
        results = {}
        
        # Find all subjects and their positions
        subject_positions = []
        for subject_key, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                pattern = re.compile(re.escape(alias), re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    subject_positions.append({
                        'subject': subject_key,
                        'start': match.start(),
                        'end': match.end(),
                    })
                    break
        
        subject_positions.sort(key=lambda x: x['start'])
        
        for i, subj_info in enumerate(subject_positions):
            subject_key = subj_info['subject']
            if subject_key in results:
                continue
            
            # Extract text chunk for this subject
            start = subj_info['end']
            if i + 1 < len(subject_positions):
                end = subject_positions[i + 1]['start']
            else:
                end = start + 200
            
            chunk = text[start:end]
            
            # Stop at certain keywords
            for stop in ['general average', 'grading scale', 'behavior']:
                if stop in chunk.lower():
                    chunk = chunk[:chunk.lower().index(stop)]
            
            grades = self._extract_all_grades_from_text(chunk)
            
            if len(grades) >= 5:
                results[subject_key] = grades[4]
                print(f"  {subject_key}: {grades[4]} (5th from {grades[:6]})")
            elif len(grades) == 4:
                avg = round(sum(grades) / 4, 2)
                results[subject_key] = avg
                print(f"  {subject_key}: {avg} (avg of {grades})")
            elif grades:
                results[subject_key] = grades[-1]
                print(f"  {subject_key}: {grades[-1]} (last from {grades})")
        
        return results

    # =====================================================
    # HELPER METHODS
    # =====================================================
    
    def _extract_all_grades_from_text(self, text: str) -> List[float]:
        """Extract all valid grade numbers from text."""
        grades = []
        
        # Method 1: Separated numbers
        numbers = re.findall(r'\b\d{2,3}\b', text)
        for num in numbers:
            val = int(num)
            if 70 <= val <= 100:
                grades.append(float(val))
        
        # Method 2: Concatenated numbers
        if len(grades) < 4:
            digits_only = re.sub(r'[^\d]', '', text)
            if len(digits_only) >= 8:
                chunks = []
                for i in range(0, min(len(digits_only), 20), 2):
                    if i + 2 <= len(digits_only):
                        chunk = int(digits_only[i:i+2])
                        if 70 <= chunk <= 100:
                            chunks.append(float(chunk))
                
                if len(chunks) > len(grades):
                    grades = chunks[:10]
        
        return grades

    def _identify_subject(self, line: str) -> Optional[str]:
        """Identify which subject a line refers to."""
        line_clean = line.lower().strip()
        line_clean = re.sub(r'^\d+[\.\)]\s*', '', line_clean)
        
        # Filter noise
        if any(noise in line_clean for noise in self.NOISE_WORDS):
            if len(line_clean) < 20:
                return None
        
        # Skip MAPEH sub-components when standalone
        if any(sub in line_clean for sub in self.MAPEH_SUBCOMPONENTS):
            if 'mapeh' not in line_clean:
                return None
        
        # Handle slashes
        if '/' in line_clean:
            parts = [p.strip() for p in line_clean.split('/')]
            for part in parts:
                result = self._identify_subject(part)
                if result:
                    return result
            return None
        
        # Exact matching
        for subject, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                if alias == line_clean:
                    return subject
                if alias in line_clean and len(alias) > 3:
                    return subject
                if re.search(r'\b' + re.escape(alias) + r'\b', line_clean):
                    return subject
        
        # Fuzzy matching
        best_match = None
        best_ratio = 0
        
        for subject, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                if len(alias) < 4 or len(line_clean) < 4:
                    continue
                
                ratio = difflib.SequenceMatcher(None, alias, line_clean).ratio()
                
                if ratio >= self.SUBJECT_FUZZY_THRESHOLD and ratio > best_ratio:
                    common_chars = sum(1 for c in alias if c in line_clean)
                    if common_chars / len(alias) >= 0.6:
                        best_ratio = ratio
                        best_match = subject
        
        return best_match

    def _is_noise_line(self, line: str) -> bool:
        """Check if line is noise."""
        line_lower = line.lower().strip()
        
        if len(line_lower) < 3:
            return True
        
        if re.match(r'^[\d\s\-/]+$', line):
            return True
        
        for keyword in self.IGNORE_KEYWORDS:
            if keyword in line_lower and len(line_lower) < 50:
                if 'araling' in line_lower or 'panlipunan' in line_lower:
                    continue
                if 'technology' in line_lower or 'livelihood' in line_lower:
                    continue
                return True
        
        return False

    def _recover_subject_grade(self, subject: str, lines: List[str], full_text: str) -> Optional[float]:
        """Last-resort grade recovery with enhanced multi-pass fallback."""
        print(f"    Recovering {subject}...")
        
        # Pass 1: Line-by-line search with context
        for i, line in enumerate(lines):
            if self._identify_subject(line) == subject:
                context_lines = lines[i:min(i+6, len(lines))]
                context_text = ' '.join(context_lines)
                grades = self._extract_all_grades_from_text(context_text)
                
                if len(grades) >= 5:
                    print(f"    ✓ Recovered via line search: {grades[4]}")
                    return grades[4]
                elif len(grades) == 4:
                    avg = round(sum(grades) / 4, 2)
                    print(f"    ✓ Recovered via line avg: {avg}")
                    return avg
                elif grades:
                    print(f"    ✓ Recovered via line fallback: {grades[-1]}")
                    return grades[-1]
        
        # Pass 2: Pattern search with wider context window
        for alias in self.SUBJECT_ALIASES.get(subject, []):
            pattern = re.compile(re.escape(alias), re.IGNORECASE)
            match = pattern.search(full_text)
            
            if match:
                start_pos = match.end()
                chunk = full_text[start_pos:start_pos + 500]  # Wider window
                grades = self._extract_all_grades_from_text(chunk)
                
                if len(grades) >= 5:
                    print(f"    ✓ Recovered via pattern: {grades[4]}")
                    return grades[4]
                elif len(grades) == 4:
                    avg = round(sum(grades) / 4, 2)
                    print(f"    ✓ Recovered via pattern avg: {avg}")
                    return avg
                elif grades:
                    print(f"    ✓ Recovered via pattern fallback: {grades[-1]}")
                    return grades[-1]
        
        # Pass 3: Fuzzy subject match + context search
        for i, line in enumerate(lines):
            if self._identify_subject(line) is None:
                continue
            # Try fuzzy match for this subject in the line
            line_lower = line.lower()
            for alias in self.SUBJECT_ALIASES.get(subject, []):
                ratio = difflib.SequenceMatcher(None, alias.lower(), line_lower).ratio()
                if ratio >= 0.65:  # Slightly lower threshold for recovery
                    context_lines = lines[i:min(i+6, len(lines))]
                    context_text = ' '.join(context_lines)
                    grades = self._extract_all_grades_from_text(context_text)
                    
                    if len(grades) >= 5:
                        print(f"    ✓ Recovered via fuzzy match: {grades[4]}")
                        return grades[4]
                    elif len(grades) == 4:
                        avg = round(sum(grades) / 4, 2)
                        print(f"    ✓ Recovered via fuzzy avg: {avg}")
                        return avg
                    elif grades:
                        print(f"    ✓ Recovered via fuzzy fallback: {grades[-1]}")
                        return grades[-1]
        
        print(f"    × Could not recover {subject}")
        return None

    # =====================================================
    # VERIFICATION
    # =====================================================
    
    def verify_grades(
        self,
        extracted: Dict[str, float],
        manual: Dict[str, float]
    ) -> Dict:
        """
        Compare extracted grades with manually entered grades.
        
        Args:
            extracted: Grades extracted from OCR
            manual: Manually entered grades
        
        Returns:
            Dictionary with verification results
        """
        matched = 0
        mismatches = []
        missing = []

        for subject, expected in manual.items():
            actual = extracted.get(subject)

            if actual is None:
                missing.append(subject)
                mismatches.append({
                    'subject': subject,
                    'expected': expected,
                    'actual': None,
                    'reason': 'missing_in_scan'
                })
            elif abs(actual - expected) <= self.tolerance:
                matched += 1
            else:
                mismatches.append({
                    'subject': subject,
                    'expected': expected,
                    'actual': actual,
                    'reason': 'value_mismatch',
                    'difference': abs(actual - expected)
                })

        confidence = (matched / len(manual)) * 100 if manual else 0
        is_match = len(mismatches) == 0 and len(missing) == 0

        return {
            'is_match': is_match,
            'confidence': round(confidence, 2),
            'matched': matched,
            'total': len(manual),
            'mismatches': mismatches,
            'missing': missing
        }
    # =====================================================
    # DIGIT CORRECTION FOR HANDWRITING
    # =====================================================
    
    def apply_digit_corrections(self, results: Dict[str, float], full_text: str) -> Dict[str, float]:
        """Apply common handwriting OCR corrections."""
        print("\\n[Digit Correction for Handwriting]")
        
        corrected = {}
        
        for subject, grade in results.items():
            original_grade = grade
            grade_str = str(int(grade))
            corrected_str = grade_str
            corrections_applied = []
            
            if self.enable_aggressive_digit_correction:
                # 87 vs 81 (7 misread as 1)
                if grade_str == '81':
                    if '87' in full_text and full_text.count('87') >= full_text.count('81'):
                        corrected_str = '87'
                        corrections_applied.append("81→87 (handwritten 7/1 confusion)")

                # 85 vs 87 (5/7 confusion)
                if grade_str == '85':
                    if '87' in full_text and full_text.count('87') > full_text.count('85'):
                        corrected_str = '87'
                        corrections_applied.append("85→87 (handwritten 5/7 confusion)")

                # 92 vs 97 (2/7 confusion) — disabled by default to avoid false corrections
                if grade_str == '97':
                    if full_text.count('92') > full_text.count('97') * 2:
                        # Only correct if it stays within ±2 of original (very conservative)
                        proposed = '92'
                        if abs(int(proposed) - int(grade_str)) <= 2:
                            corrected_str = proposed
                            corrections_applied.append("97→92 (handwritten 2/7 confusion)")

                # 87 vs 89 (check context)
                if grade_str == '89':
                    nearby_87 = full_text.count('87')
                    nearby_89 = full_text.count('89')
                    if nearby_87 > max(nearby_89, 1) * 2:
                        corrected_str = '87'
                        corrections_applied.append("89→87 (context-based correction)")
            
            corrected_grade = float(corrected_str)
            corrected[subject] = corrected_grade
            
            if corrections_applied:
                print(f"  ⚠️  {subject}: {original_grade} → {corrected_grade} ({', '.join(corrections_applied)})")
            else:
                print(f"  ✓ {subject}: {grade} (no corrections)")
        
        return corrected
    
    def validate_grade_ranges(self, results: Dict[str, float]) -> Dict[str, float]:
        """Validate grades are within acceptable ranges (70-100)."""
        print("\\n[Grade Range Validation]")
        
        validated = {}
        
        for subject, grade in results.items():
            if 70 <= grade <= 100:
                validated[subject] = grade
                print(f"  ✓ {subject}: {grade} (valid range)")
            else:
                print(f"  × {subject}: {grade} (INVALID - out of range 70-100)")
                # Try automatic correction
                if grade < 70:
                    corrected = float(str(int(grade)) + '0')
                    if 70 <= corrected <= 100:
                        validated[subject] = corrected
                        print(f"    → Auto-corrected to {corrected}")
                elif grade > 100:
                    corrected = float(str(int(grade))[:-1])
                    if 70 <= corrected <= 100:
                        validated[subject] = corrected
                        print(f"    → Auto-corrected to {corrected}")
        
        return validated





# =====================================================
# FALLBACK CHECKER
# =====================================================

class SimpleGradeVerifier:
    """Simple image verification fallback."""
    
    def verify_image_exists(self, image_path: str) -> bool:
        """Check if image file is valid."""
        try:
            img = Image.open(image_path)
            img.verify()
            return True
        except Exception:
            return False

# Backward compatibility alias
EnhancedOCRGradeVerifier = OCRGradeVerifier