#!/usr/bin/env python
"""
Improved OCR Service Test with Django Initialization
Features:
- Automatic verification against expected grades
- Detailed column detection logging
- Tolerance testing
- Multiple image testing
- Export results to JSON/CSV
"""
import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime

# Set default environment variables if not already set
if 'GOOGLE_CLOUD_PROJECT' not in os.environ and 'GCP_PROJECT_ID' not in os.environ:
    os.environ['GOOGLE_CLOUD_PROJECT'] = '1094485135926'

if 'DOCUMENT_AI_PROCESSOR_ID' not in os.environ:
    os.environ['DOCUMENT_AI_PROCESSOR_ID'] = 'a0cbcc2e3afe7ae0'

if 'DOCUMENT_AI_LOCATION' not in os.environ:
    os.environ['DOCUMENT_AI_LOCATION'] = 'us'

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
django.setup()

# Now import Django-dependent modules
from enrollment_app.services.ocr_service import OCRGradeVerifier


class OCRTester:
    """Enhanced OCR testing with verification and logging."""
    
    def __init__(self, tolerance=3.0):
        """Initialize OCR tester."""
        self.tolerance = tolerance
        self.verifier = None
        self.test_results = []
        
    def initialize_verifier(self):
        """Initialize OCR verifier with credentials."""
        print(f"\n{'='*70}")
        print("INITIALIZING OCR VERIFIER")
        print(f"{'='*70}\n")
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCP_PROJECT_ID') or '1094485135926'
        processor_id = os.getenv('DOCUMENT_AI_PROCESSOR_ID') or 'a0cbcc2e3afe7ae0'
        location = os.getenv('DOCUMENT_AI_LOCATION') or 'us'
        credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        print(f"📋 Configuration:")
        print(f"  Project ID:        {project_id}")
        print(f"  Processor ID:      {processor_id}")
        print(f"  Location:          {location}")
        print(f"  Tolerance:         ±{self.tolerance}")
        print(f"  Credentials:       {credentials or 'Using default credentials'}")
        
        try:
            self.verifier = OCRGradeVerifier(
                tolerance=self.tolerance,
                project_id=project_id,
                processor_id=processor_id,
                location=location
            )
            print(f"\n✅ Verifier initialized successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Failed to initialize verifier: {e}")
            return False
    
    def extract_grades(self, image_path):
        """Extract grades from image with detailed logging."""
        print(f"\n{'='*70}")
        print("EXTRACTING GRADES")
        print(f"{'='*70}\n")
        print(f"📁 Image: {image_path}")
        
        # Check file exists
        if not os.path.exists(image_path):
            print(f"❌ ERROR: File not found!")
            return None
        
        # Check file size
        file_size = os.path.getsize(image_path) / (1024 * 1024)  # MB
        print(f"📊 File size: {file_size:.2f} MB")
        
        try:
            print(f"\n🔍 Processing with Document AI...")
            print(f"⏳ This may take 10-30 seconds...\n")
            
            # Extract grades
            grades = self.verifier.extract_grades_from_image(image_path)
            
            print(f"\n{'='*70}")
            print("✅ EXTRACTION SUCCESSFUL!")
            print(f"{'='*70}\n")
            
            return grades
            
        except FileNotFoundError:
            print(f"\n❌ ERROR: Image file not found: {image_path}")
            return None
        except Exception as e:
            print(f"\n❌ ERROR: {type(e).__name__}: {e}")
            import traceback
            print("\n📋 Full traceback:")
            traceback.print_exc()
            return None
    
    def display_results(self, grades, expected_grades=None):
        """Display extraction results with optional verification."""
        if not grades:
            print("❌ No grades extracted")
            return
        
        print(f"📊 Extracted {len(grades)} subjects:\n")
        
        # Determine if we should verify
        verify_mode = expected_grades is not None
        
        if verify_mode:
            print(f"{'Subject':<30} {'Extracted':>10} {'Expected':>10} {'Diff':>8} {'Status':>12}")
            print("-" * 80)
            
            all_match = True
            for subject in sorted(set(list(grades.keys()) + list(expected_grades.keys()))):
                extracted = grades.get(subject)
                expected = expected_grades.get(subject)
                
                if extracted is None:
                    print(f"{'× ' + subject:<30} {'MISSING':>10} {expected:>10.1f} {'N/A':>8} {'❌ MISSING':>12}")
                    all_match = False
                elif expected is None:
                    print(f"{'? ' + subject:<30} {extracted:>10.1f} {'N/A':>10} {'N/A':>8} {'⚠️  EXTRA':>12}")
                else:
                    diff = abs(extracted - expected)
                    
                    if diff == 0:
                        status = "✅ EXACT"
                        symbol = "✓"
                    elif diff <= self.tolerance:
                        status = f"✅ MATCH"
                        symbol = "✓"
                    else:
                        status = "❌ MISMATCH"
                        symbol = "×"
                        all_match = False
                    
                    print(f"{symbol + ' ' + subject:<30} {extracted:>10.1f} {expected:>10.1f} {diff:>8.1f} {status:>12}")
            
            print(f"\n{'='*70}")
            if all_match:
                print("🎉 ALL GRADES VERIFIED SUCCESSFULLY!")
            else:
                print("⚠️  VERIFICATION FAILED - Manual review required")
            print(f"{'='*70}")
            
        else:
            # Simple display without verification
            print(f"{'Subject':<30} {'Grade':>10}")
            print("-" * 50)
            for subject, grade in sorted(grades.items()):
                print(f"  {subject:<28} {grade:>10.1f}")
        
        print(f"\n{'='*70}")
        print("📋 JSON Output:")
        print(f"{'='*70}\n")
        print(json.dumps(grades, indent=2, sort_keys=True))
    
    def verify_grades(self, extracted, expected):
        """Verify extracted grades against expected values."""
        if not extracted or not expected:
            return None
        
        result = self.verifier.verify_grades(extracted, expected)
        
        print(f"\n{'='*70}")
        print("VERIFICATION SUMMARY")
        print(f"{'='*70}\n")
        print(f"  Match:       {result['is_match']}")
        print(f"  Confidence:  {result['confidence']}%")
        print(f"  Matched:     {result['matched']}/{result['total']} subjects")
        print(f"  Tolerance:   ±{self.tolerance}")
        
        if result['mismatches']:
            print(f"\n  ⚠️  Mismatches: {len(result['mismatches'])}")
            for m in result['mismatches']:
                if m['actual'] is None:
                    print(f"    - {m['subject']}: MISSING (expected {m['expected']})")
                else:
                    print(f"    - {m['subject']}: Expected {m['expected']}, got {m['actual']} (diff: {m['difference']:.1f})")
        
        if result['missing']:
            print(f"\n  ❌ Missing: {len(result['missing'])}")
            for subject in result['missing']:
                print(f"    - {subject}")
        
        return result
    
    def test_single_image(self, image_path, expected_grades=None):
        """Test OCR on a single image."""
        start_time = datetime.now()
        
        # Extract grades
        extracted = self.extract_grades(image_path)
        
        if extracted is None:
            return None
        
        # Display results
        self.display_results(extracted, expected_grades)
        
        # Verify if expected grades provided
        result = None
        if expected_grades:
            result = self.verify_grades(extracted, expected_grades)
        
        # Store test result
        elapsed = (datetime.now() - start_time).total_seconds()
        test_record = {
            'image': image_path,
            'timestamp': start_time.isoformat(),
            'elapsed_seconds': elapsed,
            'extracted': extracted,
            'expected': expected_grades,
            'verification': result
        }
        self.test_results.append(test_record)
        
        print(f"\n⏱️  Processing time: {elapsed:.2f} seconds")
        
        return extracted
    
    def test_tolerance_levels(self, image_path, expected_grades):
        """Test different tolerance levels."""
        print(f"\n{'='*70}")
        print("TOLERANCE LEVEL TESTING")
        print(f"{'='*70}\n")
        
        tolerance_levels = [1.0, 2.0, 3.0, 5.0]
        
        # Extract once
        extracted = self.verifier.extract_grades_from_image(image_path)
        
        print(f"{'Tolerance':<12} {'Match':>8} {'Confidence':>12} {'Matched':>10}")
        print("-" * 50)
        
        for tol in tolerance_levels:
            temp_verifier = OCRGradeVerifier(tolerance=tol)
            result = temp_verifier.verify_grades(extracted, expected_grades)
            
            match_str = "✅ YES" if result['is_match'] else "❌ NO"
            print(f"  ±{tol:<10.1f} {match_str:>8} {result['confidence']:>11.1f}% {result['matched']:>4}/{result['total']:<4}")
    
    def export_results(self, output_dir="test_results"):
        """Export test results to JSON and CSV."""
        if not self.test_results:
            print("No results to export")
            return
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export JSON
        json_file = os.path.join(output_dir, f"ocr_test_{timestamp}.json")
        with open(json_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"\n✅ Results exported to: {json_file}")
        
        # Export CSV
        try:
            import csv
            csv_file = os.path.join(output_dir, f"ocr_test_{timestamp}.csv")
            
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Image', 'Subject', 'Extracted', 'Expected', 'Match', 'Confidence'])
                
                for record in self.test_results:
                    image = record['image']
                    extracted = record['extracted']
                    expected = record.get('expected', {})
                    verification = record.get('verification', {})
                    
                    for subject in extracted.keys():
                        writer.writerow([
                            image,
                            subject,
                            extracted.get(subject, ''),
                            expected.get(subject, ''),
                            verification.get('is_match', ''),
                            verification.get('confidence', '')
                        ])
            
            print(f"✅ CSV exported to: {csv_file}")
            
        except ImportError:
            print("⚠️  CSV export skipped (csv module not available)")


def main():
    """Main test function with menu."""
    
    print(f"\n{'='*70}")
    print("OCR GRADE VERIFIER - IMPROVED TEST SCRIPT")
    print(f"{'='*70}")
    
    # Initialize tester
    tester = OCRTester(tolerance=3.0)
    
    if not tester.initialize_verifier():
        print("\n❌ Cannot proceed without valid verifier")
        return
    
    # Default test image
    default_image = "shared_assets/static/images/mudanGirls_27.jpg"
    
    # Check if image path provided as argument
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = default_image
    
    # Sample expected grades (adjust based on your test image)
    expected_grades = {
        'filipino': 92.0,
        'english': 87.0,
        'science': 91.0,
        'mathematics': 89.0,
        'araling_panlipunan': 93.0,
        'edukasyon_sa_pagpapakatao': 91.0,  # ESP
        'edukasyon_pangkabuhayan': 93.0,     # EPK
        'mapeh': 86.0
    }
    
    # Ask user what to test
    print(f"\n{'='*70}")
    print("TEST OPTIONS")
    print(f"{'='*70}\n")
    print(f"1. Extract grades only (no verification)")
    print(f"2. Extract and verify against expected grades")
    print(f"3. Test different tolerance levels")
    print(f"4. Custom test (enter grades manually)")
    
    choice = input("\nSelect option (1-4) [default: 2]: ").strip() or "2"
    
    if choice == "1":
        # Extract only
        tester.test_single_image(image_path)
        
    elif choice == "2":
        # Extract and verify
        tester.test_single_image(image_path, expected_grades)
        
    elif choice == "3":
        # Tolerance testing
        tester.test_single_image(image_path, expected_grades)
        tester.test_tolerance_levels(image_path, expected_grades)
        
    elif choice == "4":
        # Custom verification
        extracted = tester.extract_grades(image_path)
        
        if extracted:
            print(f"\n{'='*70}")
            print("MANUAL VERIFICATION")
            print(f"{'='*70}\n")
            print("Enter expected grades (press Enter to skip subject):\n")
            
            custom_expected = {}
            for subject in extracted.keys():
                value = input(f"  {subject}: ").strip()
                if value:
                    try:
                        custom_expected[subject] = float(value)
                    except ValueError:
                        print(f"    ⚠️  Invalid number, skipping")
            
            if custom_expected:
                tester.display_results(extracted, custom_expected)
                tester.verify_grades(extracted, custom_expected)
    
    # Export results
    export = input("\n💾 Export results to file? (y/n) [default: n]: ").strip().lower()
    if export == 'y':
        tester.export_results()
    
    print(f"\n{'='*70}")
    print("✅ TEST COMPLETE")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)