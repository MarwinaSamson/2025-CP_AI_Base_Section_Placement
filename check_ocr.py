import sys
import os

def test_easyocr_installation():
    """Check if EasyOCR and dependencies are installed"""

    print("=" * 60)
    print("🔍 CHECKING EASYOCR INSTALLATION")
    print("=" * 60)
    print()

    # Check OpenCV
    print("1️⃣ Checking OpenCV (cv2)...")
    try:
        import cv2
        print(f"   ✅ OpenCV installed: {cv2.__version__}")
    except ImportError as e:
        print(f"   ❌ OpenCV NOT installed")
        print(f"   👉 Run: pip install opencv-python")
        return False

    # Check EasyOCR
    print("\n2️⃣ Checking EasyOCR...")
    try:
        import easyocr
        print(f"   ✅ EasyOCR installed")
    except ImportError:
        print(f"   ❌ EasyOCR NOT installed")
        print(f"   👉 Run: pip install easyocr")
        return False

    # Check NumPy
    print("\n3️⃣ Checking NumPy...")
    try:
        import numpy as np
        print(f"   ✅ NumPy installed: {np.__version__}")
    except ImportError:
        print(f"   ❌ NumPy NOT installed")
        print(f"   👉 Run: pip install numpy")
        return False

    # Test EasyOCR Reader
    print("\n4️⃣ Testing EasyOCR Reader initialization...")
    try:
        print("   ⏳ Creating reader (this may take a moment)...")
        reader = easyocr.Reader(['en'], gpu=False)
        print("   ✅ EasyOCR Reader initialized successfully!")
    except Exception as e:
        print(f"   ❌ Failed to initialize reader: {e}")
        return False

    print("\n" + "=" * 60)
    print("✅ ALL CHECKS PASSED! EasyOCR is ready.")
    print("=" * 60)
    return True


def test_with_report_card(image_path):
    """Test OCR with actual report card"""

    if not os.path.exists(image_path):
        print(f"\n❌ Image not found: {image_path}")
        return

    print("\n" + "=" * 60)
    print("📸 TESTING WITH REPORT CARD")
    print("=" * 60)
    print(f"Image: {image_path}\n")

    try:
        import cv2
        import easyocr
        
        print("📷 Loading image...")
        image = cv2.imread(image_path)
        if image is None:
            print("❌ Failed to load image")
            return

        h, w, _ = image.shape
        print(f"✅ Image loaded: {w}x{h} pixels")

        print("\n✂️ Cropping Final Grade columns...")
        cropped = image[int(h * 0.18):int(h * 0.75), int(w * 0.68):]
        print(f"✅ Cropped region: {cropped.shape}")

        print("\n🔍 Running OCR on cropped region...")
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(cropped, detail=1)

        print("\n" + "-" * 60)
        print("RAW OCR RESULTS:")
        print("-" * 60)
        for result in results:
            text, confidence = result[1], result[2]
            print(f"  Detected: {text} (Confidence: {confidence:.2f})")
        print("-" * 60)

        print("\n📊 Extracting final grades...")
        grade_dict = {}
        
        # Example subject list based on your report card structure
        subjects = ["Filipino", "English", "Mathematics", "Science", 
                    "Araling Panlipunan (EsP)", "Technology and Livelihood Education (TLE)", 
                    "MAPEH"]

        # Loop through detected text and extract valid grades
        for text in results:
            detected_text = text[1].strip()
            if detected_text.isdigit() and int(detected_text) <= 100:
                # Assume grade is next to the subject name
                if len(grade_dict) < len(subjects):
                    grade_dict[subjects[len(grade_dict)]] = int(detected_text)

        print("\n" + "-" * 60)
        print("EXTRACTED FINAL GRADES:")
        print("-" * 60)
        for subject, grade in grade_dict.items():
            print(f"  {subject}: {grade}")
        print("-" * 60)

        if grade_dict:
            formatted_grades = [f"{subject}={grade}" for subject, grade in grade_dict.items()]
            print("Formatted Final Grades: " + ", ".join(formatted_grades))
        else:
            print("⚠️ No grades were extracted.")

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    if test_easyocr_installation():
        print("\n" + "=" * 60)
        print("📋 NEXT STEPS:")
        print("=" * 60)
        print(f"1. To test with your report card, run:")
        print("   python test_easyocr.py path/to/report_card.jpg")
        print("=" * 60)

        if len(sys.argv) > 1:
            image_path = sys.argv[1]
            test_with_report_card(image_path)
        else:
            print("❌ No image path provided!")
    else:
        print("\n❌ Please fix the issues above before proceeding")
        sys.exit(1)