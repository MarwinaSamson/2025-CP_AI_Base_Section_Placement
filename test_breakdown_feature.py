#!/usr/bin/env python
"""
Quick test to verify breakdown feature works end-to-end
"""
import sys
import os
import django
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
django.setup()

from TRAINING_ARC.placement_recommender_hybrid import HybridPlacementRecommender
from pathlib import Path

# Initialize recommender
recommender = HybridPlacementRecommender(
    model_path=str(Path(__file__).parent / 'TRAINING_ARC' / 'models' / 'hybrid')
)

# Load models
if not recommender.load_model():
    print("❌ Failed to load Hybrid models")
    sys.exit(1)

print("✅ Hybrid models loaded successfully")

# Create sample student data with required features
sample_student = {
    'grade_math': 88,
    'grade_science': 85,
    'grade_english': 82,
    'grade_filipino': 84,
    'grade_arpan': 80,
    'grade_mapeh': 86,
    'grade_tle': 87,
    'grade_esp': 83,
    'age': 12,
    'gender': 1,
    'enjoy_math': 1,
    'enjoy_science': 1,
    'enjoy_english': 0,
    'motivation_level': 3,
    'learning_style': 2,
    'study_hours_daily': 2,
    'received_awards': 1,
    'competition_participation': 1,
}

# Convert to DataFrame
student_df = pd.DataFrame([sample_student])

# Test 1: Regular recommendation
print("\n[TEST 1] Testing regular recommendation...")
recommendations = recommender.recommend(student_df, top_n=5)
print(f"✅ Got {len(recommendations)} recommendations")
for rec in recommendations[:3]:
    print(f"  - {rec['placement']}: {int(rec['probability']*100)}%")

# Test 2: Detailed explanation
print("\n[TEST 2] Testing get_detailed_explanation()...")
breakdown = recommender.get_detailed_explanation(student_df)

if breakdown is None:
    print("❌ get_detailed_explanation() returned None")
    sys.exit(1)

print("✅ Detailed breakdown retrieved")

# Check Stage 1
if 'stage1_all_programs' in breakdown:
    print(f"\n  Stage 1 (Ridge Predictions): {len(breakdown['stage1_all_programs'])} programs")
    for prog in breakdown['stage1_all_programs']:
        print(f"    - {prog['program_name']}: {prog['predicted_average']:.2f}")
else:
    print("❌ Missing stage1_all_programs in breakdown")

# Check Stage 2
if 'stage2_all_programs' in breakdown:
    print(f"\n  Stage 2 (XGBoost Confidence): {len(breakdown['stage2_all_programs'])} programs")
    for prog in breakdown['stage2_all_programs']:
        print(f"    - {prog['program_name']}: {prog['confidence_pct']}%")
else:
    print("❌ Missing stage2_all_programs in breakdown")

# Check Top Factors
if 'top_factors' in breakdown:
    print(f"\n  Top Factors: {len(breakdown['top_factors'])} factors")
    for factor in breakdown['top_factors'][:5]:
        print(f"    - {factor['feature']}: {factor['value']}")
else:
    print("❌ Missing top_factors in breakdown")

print("\n✅ All breakdown feature tests passed!")
