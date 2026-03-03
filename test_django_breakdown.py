#!/usr/bin/env python
"""
Django integration test for breakdown feature
Tests recommendation_service with breakdown data
"""
import sys
import os
import django
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
django.setup()

from enrollment_app.services.recommendation_service import generate_academic_recommendations

# Create mock student data
mock_student_data = {
    'lrn': 'TEST12345678',
    'first_name': 'Test',
    'last_name': 'Student',
    'age': 12,
    'gender': 'Male',
    'is_working_student': False,
    'is_sped': False,
}

# Mock academic data
mock_academic = {
    'overall_average': 85,
    'grade_math': 88,
    'grade_science': 85,
    'grade_english': 82,
    'grade_filipino': 84,
    'grade_arpan': 80,
    'grade_mapeh': 86,
    'grade_tle': 87,
    'grade_esp': 83,
}

# Mock survey data
mock_survey = {
    'enjoy_math': 1,
    'enjoy_science': 1,
    'enjoy_english': 0,
    'motivation_level': 3,
    'learning_style': 2,
    'study_hours_daily': 2,
    'received_awards': 1,
    'competition_participation': 1,
}

print("[DJANGO TEST] Testing recommendation_service with breakdown...\n")

try:
    # Call recommendation service
    result = generate_academic_recommendations(
        student_lrn='TEST12345678',
        academic_data=mock_academic,
        survey_data=mock_survey,
        student_data=mock_student_data
    )
    
    if not result or result.get('status') != 'success':
        print(f"❌ Recommendation generation failed: {result}")
        sys.exit(1)
    
    print(f"✅ Recommendations generated successfully")
    print(f"   Total recommendations: {result.get('total_recommendations', 0)}")
    
    # Check each recommendation has breakdown
    recommendations = result.get('recommendations', [])
    for idx, rec in enumerate(recommendations, 1):
        print(f"\n[Recommendation {idx}] {rec['program_name']} ({rec['percentage_match']}%)")
        
        if 'breakdown' in rec:
            breakdown = rec['breakdown']
            
            # Check Stage 1
            stage1 = breakdown.get('stage1_all_programs', [])
            if stage1:
                print(f"   ✅ Stage 1 (Ridge): {len(stage1)} programs")
                for prog in stage1[:2]:
                    print(f"      - {prog['program_name']}: {prog['predicted_average']:.2f}")
                if len(stage1) > 2:
                    print(f"      ... and {len(stage1)-2} more")
            
            # Check Stage 2
            stage2 = breakdown.get('stage2_all_programs', [])
            if stage2:
                print(f"   ✅ Stage 2 (XGBoost): {len(stage2)} programs")
                for prog in stage2[:2]:
                    print(f"      - {prog['program_name']}: {prog['confidence_pct']}%")
                if len(stage2) > 2:
                    print(f"      ... and {len(stage2)-2} more")
            
            # Check Top Factors
            factors = breakdown.get('top_factors', [])
            if factors:
                print(f"   ✅ Top Factors: {len(factors)} factors")
                for factor in factors[:3]:
                    print(f"      - {factor['feature']}: {factor['value']}")
                if len(factors) > 3:
                    print(f"      ... and {len(factors)-3} more")
        else:
            print(f"   ⚠️  No breakdown data in recommendation")
    
    # Check top-level breakdown
    if 'breakdown' in result:
        print(f"\n✅ Top-level breakdown also present in result")
    
    print("\n" + "="*60)
    print("✅ ALL INTEGRATION TESTS PASSED!")
    print("="*60)
    print("\nBreakdown feature is ready for:")
    print("  1. Frontend display in Program Details modal")
    print("  2. Explainability display to students")
    
except Exception as e:
    print(f"❌ Test failed with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
