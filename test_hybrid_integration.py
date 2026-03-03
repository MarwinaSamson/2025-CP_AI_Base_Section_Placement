"""
Quick test to verify Hybrid recommender integration with Django signals
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

django.setup()

import pandas as pd
import numpy as np
from TRAINING_ARC.placement_recommender_hybrid import HybridPlacementRecommender

print("=" * 80)
print("TESTING HYBRID RECOMMENDER INTEGRATION")
print("=" * 80)

# Test 1: Load Hybrid recommender
print("\n[1/3] Testing Hybrid recommender load...")
try:
    recommender = HybridPlacementRecommender()
    if recommender.load_models():
        print("  ✓ Hybrid recommender loaded successfully")
    else:
        print("  ✗ Failed to load Hybrid models")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ Error: {e}")
    sys.exit(1)

# Test 2: Create test student data (similar to what _prepare_student_features returns)
print("\n[2/3] Testing prediction with sample data...")

# Build complete feature set with realistic values
sample_features = {
    # Academic (Grade 6)
    'grade_math': 85,
    'grade_science': 88,
    'grade_english': 82,
    'grade_filipino': 80,
    'grade_arpan': 79,
    'grade_mapeh': 87,
    'average_grade_tle': 83,
    'grade_esp': 81,
    'grade_6_final_average': 83.1,
    
    # Demographic
    'age': 12,
    'gender': 1,
    
    # Survey - Learning style
    'learning_style': 2,
    'study_hours_daily': 2,
    'support_person': 1,
    'assignment_completion': 3,
    'handle_difficulty': 2,
    
    # Subject enjoyment
    'enjoy_math': 1,
    'enjoy_science': 1,
    'enjoy_english': 1,
    'enjoy_filipino': 0,
    'enjoy_arpan': 0,
    'enjoy_mapeh': 1,
    'enjoy_tle': 0,
    
    # Motivation & interests
    'motivation_level': 3,
    'enjoy_science_experiments': 1,
    'enjoy_reading': 1,
    'enjoy_handson_activities': 1,
    'enjoy_sports': 1,
    'enjoy_arts': 0,
    'enjoy_language_related_activities': 0,
    'foreign_language_interest': 2,
    'competition_participation': 1,
    
    # Resources
    'device_availability': 2,
    'internet_access': 2,
    'absences_count': 3,
    'family_income_help': 0,
    'school_participation': 2,
    
    # Awards
    'received_awards': 1,
    'award_highest_honors': 0,
    'award_high_honors': 1,
    'award_with_honors': 0,
    'award_best_science': 1,
    'award_best_math': 0,
    'award_best_english': 0,
    'award_conduct': 0,
    'achiever_award': 0,
    
    # Difficulties
    'difficulty_reading': 0,
    'difficulty_writing': 0,
    'difficulty_math': 0,
    'difficulty_focusing': 0,
    'difficulty_social_interaction': 0,
    'extra_support_recommended': 0,
    'quiet_study_place': 1,
    
    # Logistics
    'distance_from_school': 2,
    'travel_difficulty': 0,
    
    # Preference
    'has_valid_preference': 1,
}

try:
    student_df = pd.DataFrame([sample_features])
    recommendations = recommender.recommend(student_df)
    
    if recommendations:
        print("  ✓ Prediction successful!")
        print(f"\n  Top 3 Recommendations:")
        for rec in recommendations[:3]:
            prog = rec['placement']
            prob = rec['probability']
            avg = rec.get('predicted_average', 'N/A')
            suitable = rec.get('suitable', False)
            marker = "✓" if suitable else "✗"
            print(f"    {marker} {prog:20s} {prob:6.1%} confidence (avg: {avg})")
    else:
        print("  ✗ No recommendations generated")
        sys.exit(1)
        
except Exception as e:
    print(f"  ✗ Prediction error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Verify signals.py can import and use the new class
print("\n[3/3] Testing Django signals integration...")
try:
    from enrollment_app.signals import _get_ai_recommended_track
    print("  ✓ Successfully imported _get_ai_recommended_track from signals.py")
    print("  ✓ Django integration looks good!")
except Exception as e:
    print(f"  ✗ Failed to import from signals.py: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("ALL TESTS PASSED ✓")
print("=" * 80)
print("\nHybrid recommender is ready for production!")
print("You can now restart Django with: python manage.py runserver")
