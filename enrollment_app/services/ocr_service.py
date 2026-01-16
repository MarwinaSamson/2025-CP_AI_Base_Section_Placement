"""
Complete OCR Grade Verification System v2
Handles multiple DepEd report card layouts with robust parsing
Supports both printed and handwritten report cards
"""

import re
import difflib
from typing import Dict, Optional, List, Tuple
from google.cloud import vision
from PIL import Image


class OCRGradeVerifier:
    """Advanced OCR grade extractor for DepEd-style report cards."""

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
            'edukasyon pangkabuhayan', 'e.p.p', 'education(tle)'
        ],
        'mapeh': ['mapeh', 'm.a.p.e.h', 'm.a.p.e.h.'],
    }

    IGNORE_KEYWORDS = [
        'quarter', 'remarks', 'descriptor', 'grading scale', 'grade',
        'passed', 'failed', 'general average', 'conduct', 'periodic',
        'rating', 'final', 'learning areas', 'behavior', 'observed',
        'values', 'outstanding', 'satisfactory', 'action taken',
        'promoted', 'homeroom', 'guidance', 'marking'
    ]

    NOISE_WORDS = {
        'adelfagirls', 'adelfa', 'daffodil', 'girls', 'boys', 'school',
        'report', 'card', 'academic', 'performance', 'learner', 'grading',
        'system', 'secondary', 'junior', 'senior', 'high', 'district',
        'division', 'department'
    }

    SUBJECT_FUZZY_THRESHOLD = 0.70
    ROW_Y_PADDING = 35  # wider band to catch misaligned rows
    COLUMN_PAD = 50  # increased to accommodate wider subject text blocks

    def __init__(self, tolerance: float = 3.0):
        # tolerance: maximum allowed difference between extracted and manual grades
        # e.g., tolerance=2.0 means 85 matches 83-87, tolerance=3.0 means 85 matches 82-88
        self.tolerance = tolerance
        self.client = vision.ImageAnnotatorClient()

    
    # OCR ENTRY POINT
    
    def extract_grades_from_image(self, image_path: str) -> Dict[str, float]:
        """Extract grades from report card image using Google Cloud Vision OCR."""
        try:
            with open(image_path, 'rb') as f:
                content = f.read()

            image = vision.Image(content=content)
            response = self.client.document_text_detection(image=image)

            if response.error.message:
                raise Exception(f"Vision API Error: {response.error.message}")

            full_text = response.full_text_annotation.text or ''
            
            print(f"\n{'='*70}")
            print(f"OCR for: {image_path.split('/')[-1]}")
            print(f"{'='*70}")
            print(full_text[:500] + "..." if len(full_text) > 500 else full_text)
            print(f"{'='*70}\n")
            
            results = self._parse_grades(full_text, response.full_text_annotation)
            
            print(f"\n{'='*70}")
            print("EXTRACTED GRADES:")
            print(f"{'='*70}")
            for subject, grade in sorted(results.items()):
                print(f"  {subject:30s}: {grade}")
            print(f"{'='*70}\n")
            
            return results
        
        except Exception as e:
            error_msg = str(e)
            if "DNS resolution failed" in error_msg or "UNAVAILABLE" in error_msg:
                raise Exception(
                    "Network error: Cannot reach Google Cloud Vision API.\n"
                    "Please check your internet connection and firewall settings."
                )
            elif "credentials" in error_msg.lower():
                raise Exception(
                    "Authentication error: Invalid Google Cloud credentials.\n"
                    "Please set GOOGLE_APPLICATION_CREDENTIALS environment variable."
                )
            else:
                raise Exception(f"OCR Error: {error_msg}")

    # =====================================================
    # MAIN PARSING LOGIC
    # =====================================================
    def _parse_grades(self, text: str, annotation=None) -> Dict[str, float]:
        """
        Main parsing logic with multiple strategies.
        Returns dictionary of subject -> final grade.
        """
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        # Strategy 0: Bounding-box layout parsing (best for tabular report cards)
        results = {}
        detected_subjects = set()  # Track what was detected
        
        if annotation:
            layout_results, subjects = self._parse_with_layout(annotation)
            results.update(layout_results)
            detected_subjects.update(subjects)
        
        # Strategy 1: Direct line parsing (best for well-formatted cards)
        direct_results = self._parse_direct_lines(lines)
        results.update({k: v for k, v in direct_results.items() if k not in results})
        
        # Strategy 2: Context-aware parsing (handles split lines)
        if len(results) < 6:  # If we didn't get most subjects
            context_results = self._parse_with_context(lines)
            results.update({k: v for k, v in context_results.items() if k not in results})
        
        # Strategy 3: Pattern matching (fallback for difficult layouts)
        if len(results) < 6:
            pattern_results = self._parse_patterns(text)
            results.update({k: v for k, v in pattern_results.items() if k not in results})
        
        # Post-processing: catch subjects that were detected but have no grades
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
    # STRATEGY 0: LAYOUT-AWARE PARSING USING BOUNDING BOXES
    # =====================================================
    def _parse_with_layout(self, annotation) -> tuple:
        """Parse grades using word bounding boxes to keep table structure.
        Returns (results_dict, detected_subjects_set)
        """
        print("\n[Strategy 0: Layout-Aware Parsing]")

        words = self._extract_word_boxes(annotation)
        if not words:
            return {}, set()

        observed_stop_y = self._detect_observed_values_y(words)
        if observed_stop_y:
            words = [w for w in words if w['y_center'] < observed_stop_y]

        x_min = min(w['xmin'] for w in words)
        x_max = max(w['xmax'] for w in words)

        columns = self._detect_columns(words, x_min, x_max)
        print(f"  Column bands: {[ (c['label'], c['xmin'], c['xmax']) for c in columns ]}")

        # Index numeric words up front for quick lookup
        numeric_words = [w for w in words if self._is_valid_grade_text(w['text'])]

        results: Dict[str, float] = {}
        mapeh_parts: Dict[str, float] = {}
        detected = set()  # Track detected subjects

        # Identify subject rows by subject words' y-position
        subject_rows: Dict[str, Dict] = {}
        for w in words:
            subject_key = self._match_subject_word(w['text'])
            if not subject_key:
                continue

            detected.add(subject_key)  # Record detection
            
            # Keep the highest (earliest) occurrence to avoid duplicates from headers
            if subject_key not in subject_rows or w['y_center'] < subject_rows[subject_key]['y_center']:
                subject_rows[subject_key] = {
                    'y_center': w['y_center'],
                    'xmax': w['xmax'],
                    'xmin': w['xmin'],
                }

        if not subject_rows:
            return {}, set()

        print(f"  Detected subject anchors: {subject_rows}")

        for subject_key, row_info in subject_rows.items():
            row_numbers = self._collect_numbers_for_row(numeric_words, row_info['y_center'])
            if not row_numbers:
                # fallback: grab closest numbers to the right of the subject block
                print(f"  Fallback for {subject_key} at y={row_info['y_center']}, xmax={row_info['xmax']}")
                row_numbers = self._collect_nearest_numbers(numeric_words, row_info, columns)
                if row_numbers:
                    print(f"    √ found {len(row_numbers)} fallback numbers: {[n['value'] for n in row_numbers]}")
                else:
                    print(f"    × no fallback numbers found")
                    continue

            column_grades = self._assign_numbers_to_columns(row_numbers, columns)
            grade = self._choose_final_grade(column_grades)

            if grade is None:
                continue
            
            # Validate: if no final column grade and we have 5 numbers, force final position
            if not column_grades.get('final') and len(row_numbers) >= 5:
                # Assume rightmost number is final grade
                rightmost = max(row_numbers, key=lambda n: n['x_center'])
                grade = rightmost['value']
                print(f"    Forced rightmost as final for {subject_key}: {grade}")

            if subject_key == 'mapeh':
                results['mapeh'] = grade
            elif subject_key.startswith('mapeh_'):
                mapeh_parts[subject_key.replace('mapeh_', '')] = grade
            else:
                results[subject_key] = grade

        # Handle MAPEH aggregation when no direct final grade is present
        if 'mapeh' not in results and mapeh_parts:
            aggregated = round(sum(mapeh_parts.values()) / len(mapeh_parts), 2)
            results['mapeh'] = aggregated
            print(f"  MAPEH aggregated from components: {mapeh_parts} -> {aggregated}")

        return results, detected

    
    # LAYOUT HELPERS
    
    def _extract_word_boxes(self, annotation) -> List[Dict]:
        words = []

        for page in annotation.pages:
            for block in page.blocks:
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

        return words

    def _detect_observed_values_y(self, words: List[Dict]) -> Optional[float]:
        """Locate the y-position of the Observed Values section to ignore below it."""
        candidates = [w for w in words if 'observed' in w['text'].lower() or 'values' in w['text'].lower()]
        if not candidates:
            return None
        return min(w['y_center'] for w in candidates) - 5

    def _detect_columns(self, words: List[Dict], x_min: float, x_max: float) -> List[Dict]:
        header_tokens = {
            '1', '2', '3', '4', 'final', 'final grade', 'finalgrade', 'fg', 'grade'
        }

        header_words = []
        for w in words:
            clean = w['text'].lower().replace('.', '').strip()
            if clean in header_tokens:
                header_words.append(w)

        header_centers = sorted(set([w['x_center'] for w in header_words]))

        width = max(x_max - x_min, 1)
        default_centers = [x_min + (i + 0.5) * (width / 5) for i in range(5)]

        col_centers = default_centers

        # Identify final column explicitly
        final_candidates = [w['x_center'] for w in header_words if 'final' in w['text'].lower() or w['text'].lower() == 'grade']
        quarter_candidates = [w['x_center'] for w in header_words if w['text'] in ['1', '2', '3', '4']]
        
        # If we found explicit headers for quarters AND final, use them
        if quarter_candidates and final_candidates:
            # Use actual detected positions
            col_centers = sorted(quarter_candidates[:4])
            # Final column is rightmost header
            col_centers.append(max(final_candidates))
            print(f"  Using detected headers: Q={len(quarter_candidates)}, Final={len(final_candidates)}")
        elif header_centers and len(header_centers) >= 5:
            # Use detected centers if we have 5+ headers
            col_centers = list(header_centers[:5])
        elif header_centers:
            # Partial headers: blend detected with defaults
            col_centers = list(header_centers[:4])
            while len(col_centers) < 5:
                col_centers.append(default_centers[len(col_centers)])
        
        # Ensure final column is truly rightmost
        if len(col_centers) >= 5 and final_candidates:
            col_centers[-1] = max(max(final_candidates), col_centers[-1])

        columns = []
        for idx, center in enumerate(col_centers):
            if idx == 0:
                xmin_band = center - self.COLUMN_PAD
                xmax_band = (center + col_centers[idx + 1]) / 2
            elif idx == len(col_centers) - 1:
                # Final column: extend all the way to the right edge
                xmin_band = (col_centers[idx - 1] + center) / 2
                xmax_band = x_max + 100  # Extend well beyond to catch rightmost numbers
            else:
                xmin_band = (col_centers[idx - 1] + center) / 2
                xmax_band = (center + col_centers[idx + 1]) / 2

            label = f"q{idx + 1}" if idx < 4 else 'final'
            columns.append({'label': label, 'xmin': xmin_band, 'xmax': xmax_band})

        return columns

    def _is_valid_grade_text(self, text: str) -> bool:
        cleaned = text.strip().replace('O', '0')  # common OCR swap
        if not re.fullmatch(r'\d{2,3}', cleaned):
            return False
        try:
            val = int(cleaned)
        except ValueError:
            return False
        return 70 <= val <= 100

    def _match_subject_word(self, text: str) -> Optional[str]:
        """Match single-word subjects using aliases and MAPEH components."""
        word = re.sub(r'[^a-z0-9 /]', '', text.lower()).strip()
        if not word:
            return None

        # Filter noise words
        if word in self.NOISE_WORDS:
            return None

        # Handle slash-separated compound subjects (e.g., "gmrc/esp" → "esp")
        if '/' in word:
            parts = [p.strip() for p in word.split('/')]
            for part in parts:
                result = self._match_subject_word(part)
                if result:
                    return result
            return None

        mapeh_components = {
            'music': 'mapeh_music',
            'arts': 'mapeh_arts',
            'art': 'mapeh_arts',
            'pe': 'mapeh_pe',
            'p e': 'mapeh_pe',
            'physical education': 'mapeh_pe',
            'health': 'mapeh_health'
        }

        if word in mapeh_components:
            return mapeh_components[word]

        for subject, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                alias_clean = alias.lower()
                if alias_clean == word:
                    return subject

        # Light fuzzy fallback for single words
        best_match = None
        best_ratio = 0
        for subject, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                if ' ' in alias or len(alias) < 4:
                    continue
                ratio = difflib.SequenceMatcher(None, alias.lower(), word).ratio()
                if ratio >= self.SUBJECT_FUZZY_THRESHOLD and ratio > best_ratio:
                    best_match = subject
                    best_ratio = ratio

        return best_match

    def _collect_numbers_for_row(self, numeric_words: List[Dict], row_y: float) -> List[Dict]:
        numbers = []
        for w in numeric_words:
            if abs(w['y_center'] - row_y) <= self.ROW_Y_PADDING:
                try:
                    val = int(w['text'].replace('O', '0'))
                except ValueError:
                    continue
                numbers.append({'value': float(val), 'x_center': w['x_center']})
        return numbers

    def _collect_nearest_numbers(self, numeric_words: List[Dict], row_info: Dict, columns: List[Dict], y_padding: float = 150) -> List[Dict]:
        """Pick closest numeric tokens near the subject row, prioritizing final grade column."""
        candidates = []
        y_center = row_info['y_center']
        subject_xmax = row_info['xmax']
        
        # Find final grade column bounds
        final_col = next((c for c in columns if c['label'] == 'final'), None)
        final_xmin = final_col['xmin'] if final_col else 1012
        final_xmax = final_col['xmax'] if final_col else 1131.5
        final_center = (final_xmin + final_xmax) / 2
        
        for w in numeric_words:
            if abs(w['y_center'] - y_center) <= y_padding:
                try:
                    val = int(w['text'].replace('O', '0'))
                except ValueError:
                    continue
                
                x_pos = w['x_center']
                
                # Strong incentive: numbers in final grade column
                if final_xmin <= x_pos <= final_xmax:
                    final_penalty = 0  # Highest priority
                    x_dist_score = abs(x_pos - final_center)
                else:
                    # Penalize numbers outside final column
                    final_penalty = 2.0 if x_pos < subject_xmax else 1.0
                    x_dist_score = abs(x_pos - final_center)
                    
                candidates.append({
                    'value': float(val),
                    'x_center': x_pos,
                    'score': (final_penalty, abs(w['y_center'] - y_center), x_dist_score)
                })

        # Sort: prioritize final column, then vertical closeness, then distance from final center
        candidates.sort(key=lambda c: c['score'])
        result = candidates[:6]
        
        if result:
            print(f"    final col: x={final_xmin:.0f}-{final_xmax:.0f}")
            print(f"    top picks: {[(round(r['value']), round(r['x_center']), round(r['score'][0], 1)) for r in result[:3]]}")
        else:
            print(f"    search band: y={y_center}±{y_padding}")
        
        return result

    def _assign_numbers_to_columns(self, numbers: List[Dict], columns: List[Dict]) -> Dict[str, List[float]]:
        assigned = {c['label']: [] for c in columns}

        for num in numbers:
            matched = None
            for col in columns:
                if col['xmin'] <= num['x_center'] <= col['xmax']:
                    matched = col['label']
                    break
            if not matched:
                # Fallback to nearest column center
                nearest = min(columns, key=lambda c: abs(((c['xmin'] + c['xmax']) / 2) - num['x_center']))
                matched = nearest['label']
            assigned[matched].append(num['value'])

        return assigned

    def _choose_final_grade(self, column_grades: Dict[str, List[float]]) -> Optional[float]:
        # Strong preference: final column
        if column_grades.get('final') and len(column_grades['final']) > 0:
            # If multiple numbers in final column, take the rightmost (last)
            return column_grades['final'][-1]

        # Fallback: compute average from 4 quarters
        quarters = []
        for q in ['q1', 'q2', 'q3', 'q4']:
            if column_grades.get(q) and len(column_grades[q]) > 0:
                quarters.append(column_grades[q][0])

        if len(quarters) == 4:
            return round(sum(quarters) / 4, 2)
        
        # Last resort: take rightmost available number
        if quarters:
            return quarters[-1]
        
        return None

    
    # STRATEGY 1: DIRECT LINE PARSING
    
    def _parse_direct_lines(self, lines: List[str]) -> Dict[str, float]:
        """
        Parse each line looking for subject name followed by grades.
        Works best for: MudanBoys, clean printed cards
        """
        print("\n[Strategy 1: Direct Line Parsing]")
        results = {}
        
        for i, line in enumerate(lines):
            # Skip header/footer lines
            if self._is_noise_line(line):
                continue
            
            subject = self._identify_subject(line)
            if not subject:
                continue
            
            print(f"  Line {i}: Found '{subject}' in: {line[:60]}...")
            
            # Try to extract grades from this line and next few lines
            grade_lines = [line]
            for j in range(1, 4):
                if i + j < len(lines):
                    next_line = lines[i + j]
                    if self._identify_subject(next_line):
                        break  # Stop if we hit another subject
                    if self._is_noise_line(next_line):
                        continue
                    grade_lines.append(next_line)
            
            grade = self._extract_final_grade_from_lines(grade_lines)
            if grade:
                results[subject] = grade
                print(f"    → Extracted: {grade}")
        
        return results

    
    # STRATEGY 2: CONTEXT-AWARE PARSING
    
    def _parse_with_context(self, lines: List[str]) -> Dict[str, float]:
        """
        Parse using context windows around subject names.
        Works best for: ADELFA, handwritten cards with irregular spacing
        """
        print("\n[Strategy 2: Context-Aware Parsing]")
        results = {}
        
        for i, line in enumerate(lines):
            if self._is_noise_line(line):
                continue
            
            subject = self._identify_subject(line)
            if not subject or subject in results:
                continue
            
            # Get context: 2 lines before and 5 lines after
            context_start = max(0, i - 2)
            context_end = min(len(lines), i + 6)
            context = '\n'.join(lines[context_start:context_end])
            
            print(f"  Analyzing context for '{subject}'...")
            
            # Extract all valid grades from context
            all_grades = self._extract_all_grades_from_text(context)
            
            if len(all_grades) >= 5:
                # Typical format: Q1 Q2 Q3 Q4 Final
                grade = all_grades[4]
                results[subject] = grade
                print(f"    → Found {grade} from {all_grades[:6]}")
            elif len(all_grades) == 4:
                # Only quarters, compute average
                grade = round(sum(all_grades) / 4, 2)
                results[subject] = grade
                print(f"    → Computed {grade} from {all_grades}")
            elif all_grades:
                # Take last number
                grade = all_grades[-1]
                results[subject] = grade
                print(f"    → Using last: {grade} from {all_grades}")
        
        return results

    
    # STRATEGY 3: PATTERN MATCHING
    
    def _parse_patterns(self, text: str) -> Dict[str, float]:
        """
        Pattern-based extraction for difficult cases.
        Works as fallback for any layout.
        """
        print("\n[Strategy 3: Pattern Matching]")
        results = {}
        
        for subject_key, aliases in self.SUBJECT_ALIASES.items():
            if subject_key in results:
                continue
            
            for alias in aliases:
                # Find subject position in text
                pattern = re.compile(re.escape(alias), re.IGNORECASE)
                match = pattern.search(text)
                
                if match:
                    # Extract surrounding text
                    start = match.end()
                    chunk = text[start:start + 200]
                    
                    # Stop at certain keywords
                    for stop_word in ['general average', 'grading scale', 'behavior']:
                        if stop_word in chunk.lower():
                            chunk = chunk[:chunk.lower().index(stop_word)]
                    
                    # Extract grades
                    grades = self._extract_all_grades_from_text(chunk)
                    
                    if len(grades) >= 5:
                        results[subject_key] = grades[4]
                        print(f"  {subject_key}: {grades[4]} from {grades[:6]}")
                        break
                    elif len(grades) == 4:
                        avg = round(sum(grades) / 4, 2)
                        results[subject_key] = avg
                        print(f"  {subject_key}: {avg} (avg of {grades})")
                        break
                    elif grades:
                        results[subject_key] = grades[-1]
                        print(f"  {subject_key}: {grades[-1]} from {grades}")
                        break
        
        return results

    
    # GRADE EXTRACTION HELPERS
    
    def _extract_all_grades_from_text(self, text: str) -> List[float]:
        """Extract all valid grade numbers from text."""
        grades = []
        
        # Method 1: Find separated numbers
        numbers = re.findall(r'\b\d{2,3}\b', text)
        for num in numbers:
            val = int(num)
            if 70 <= val <= 100:
                grades.append(float(val))
        
        # Method 2: Handle concatenated numbers (e.g., "768283")
        if len(grades) < 4:
            # Remove all non-digits
            digits_only = re.sub(r'[^\d]', '', text)
            
            # Try to split into 2-digit chunks
            if len(digits_only) >= 8:
                chunks = []
                for i in range(0, min(len(digits_only), 20), 2):
                    if i + 2 <= len(digits_only):
                        chunk = int(digits_only[i:i+2])
                        if 70 <= chunk <= 100:
                            chunks.append(float(chunk))
                
                # Use concatenated if we got more valid grades
                if len(chunks) > len(grades):
                    grades = chunks[:10]  # Limit to prevent garbage
        
        return grades

    def _extract_final_grade_from_lines(self, lines: List[str]) -> Optional[float]:
        """Extract final grade from a list of lines."""
        combined_text = ' '.join(lines)
        grades = self._extract_all_grades_from_text(combined_text)
        
        if len(grades) >= 5:
            return grades[4]  # 5th position is Final Grade
        elif len(grades) == 4:
            return round(sum(grades) / 4, 2)  # Average of 4 quarters
        elif grades:
            return grades[-1]  # Last valid grade
        
        return None

    
    # SUBJECT IDENTIFICATION
    
    def _identify_subject(self, line: str) -> Optional[str]:
        """Identify which subject a line refers to."""
        line_clean = line.lower().strip()
        
        # Remove line numbers like "1. " or "1) "
        line_clean = re.sub(r'^\d+[\.\)]\s*', '', line_clean)
        
        # Filter noise words (school names, etc.)
        if any(noise in line_clean for noise in self.NOISE_WORDS):
            # Only skip if it's a short line (e.g., just "Adelfa" or "Daffodil")
            if len(line_clean) < 20:
                return None
        
        # Special case: Ignore MAPEH sub-components when standalone
        if any(sub in line_clean for sub in ['music', 'arts', 'art', 'p.e', 'health', 'pe']):
            if 'mapeh' not in line_clean:
                return None
        
        # Handle slash-separated subjects (e.g., "gmrc/esp" → "esp")
        if '/' in line_clean:
            parts = [p.strip() for p in line_clean.split('/')]
            for part in parts:
                result = self._identify_subject(part)
                if result:
                    return result
            return None
        
        # Exact and partial matching
        for subject, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                # Exact match
                if alias == line_clean:
                    return subject
                
                # Substring match (for longer subject names)
                if alias in line_clean and len(alias) > 3:
                    return subject
                
                # Word boundary match
                if re.search(r'\b' + re.escape(alias) + r'\b', line_clean):
                    return subject
        
        # Fuzzy matching for OCR errors
        best_match = None
        best_ratio = 0
        
        for subject, aliases in self.SUBJECT_ALIASES.items():
            for alias in aliases:
                if len(alias) < 4 or len(line_clean) < 4:
                    continue
                
                ratio = difflib.SequenceMatcher(None, alias, line_clean).ratio()
                
                if ratio >= self.SUBJECT_FUZZY_THRESHOLD and ratio > best_ratio:
                    # Ensure character overlap
                    common_chars = sum(1 for c in alias if c in line_clean)
                    if common_chars / len(alias) >= 0.6:
                        best_ratio = ratio
                        best_match = subject
        
        return best_match

    def _is_noise_line(self, line: str) -> bool:
        """Check if line is header/footer/noise."""
        line_lower = line.lower().strip()
        
        # Skip empty or very short lines
        if len(line_lower) < 3:
            return True
        
        # Skip lines that are purely numbers (like LRN)
        if re.match(r'^[\d\s\-/]+$', line):
            return True
        
        # Skip header/footer keywords
        for keyword in self.IGNORE_KEYWORDS:
            if keyword in line_lower and len(line_lower) < 50:
                # Allow "Araling Panlipunan (AP)" even though it contains "AP"
                if 'araling' in line_lower or 'panlipunan' in line_lower:
                    continue
                # Allow "Technology and Livelihood" even though it contains "education"
                if 'technology' in line_lower or 'livelihood' in line_lower:
                    continue
                return True
        
        return False

    def _recover_subject_grade(self, subject: str, lines: List[str], full_text: str) -> Optional[float]:
        """Last-resort recovery for subjects detected but not extracted. Ultra-aggressive search."""
        print(f"    Recovering {subject}...")
        
        # Strategy 1: Line-by-line context search
        for i, line in enumerate(lines):
            if self._identify_subject(line) == subject:
                # Collect next 5 lines as wide context
                context_lines = lines[i:min(i+6, len(lines))]
                context_text = ' '.join(context_lines)
                
                # Extract all valid grades from context
                grades = self._extract_all_grades_from_text(context_text)
                
                if len(grades) >= 5:
                    # Assume 5th number is final grade
                    grade = grades[4]
                elif len(grades) == 4:
                    # Average of quarters
                    grade = round(sum(grades) / 4, 2)
                elif len(grades) >= 1:
                    # Take the last number as fallback
                    grade = grades[-1]
                else:
                    continue
                
                if 70 <= grade <= 100:
                    return grade
        
        # Strategy 2: Pattern-based search across full text
        # Search for subject aliases in the full text
        for alias in self.SUBJECT_ALIASES.get(subject, []):
            # Case-insensitive search for the alias
            pattern = re.compile(re.escape(alias), re.IGNORECASE)
            match = pattern.search(full_text)
            
            if match:
                # Extract 300 characters after the subject name
                start_pos = match.end()
                chunk = full_text[start_pos:start_pos + 300]
                
                # Extract all grades from this chunk
                grades = self._extract_all_grades_from_text(chunk)
                
                if len(grades) >= 5:
                    grade = grades[4]  # Final grade position
                elif len(grades) == 4:
                    grade = round(sum(grades) / 4, 2)  # Average
                elif len(grades) >= 1:
                    grade = grades[-1]  # Last available
                else:
                    continue
                
                if 70 <= grade <= 100:
                    print(f"      Found via pattern: {grade}")
                    return grade
        
        # Strategy 3: Desperate - find ANY occurrence of the subject abbreviation
        abbreviations = {
            'araling_panlipunan': ['arpan', 'ap'],
            'edukasyon_sa_pagpapakatao': ['esp'],
            'edukasyon_pangkabuhayan': ['epp', 'tle'],
            'mapeh': ['mapeh']
        }
        
        if subject in abbreviations:
            for abbrev in abbreviations[subject]:
                pattern = re.compile(r'\b' + re.escape(abbrev) + r'\b', re.IGNORECASE)
                match = pattern.search(full_text)
                
                if match:
                    start_pos = match.end()
                    chunk = full_text[start_pos:start_pos + 200]
                    grades = self._extract_all_grades_from_text(chunk)
                    
                    if len(grades) >= 5:
                        return grades[4]
                    elif len(grades) == 4:
                        return round(sum(grades) / 4, 2)
                    elif grades:
                        return grades[-1]
        
        print(f"      Failed to recover")
        return None

    # =====================================================
    # VERIFICATION
    # =====================================================
    def verify_grades(
        self,
        extracted: Dict[str, float],
        manual: Dict[str, float]
    ) -> Dict:
        """Compare extracted grades with manually entered grades."""
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