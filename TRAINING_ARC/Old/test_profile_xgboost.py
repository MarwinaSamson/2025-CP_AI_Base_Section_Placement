import pandas as pd
import joblib
import os

# Configuration
MODEL_DIR = 'models/xgboost'
PLACEMENT_MAP = {1: 'STE', 2: 'SPFL', 3: 'SPTVE', 4: 'Top-5 Regular', 5: 'Hetero'}


print("TESTING XGBOOST PLACEMENT RECOMMENDATION SYSTEM")



# Load Model and Components

print("\nLoading model...")

model_path = f'{MODEL_DIR}/placement_xgboost_model.pkl'
imputer_path = f'{MODEL_DIR}/imputer.pkl'
features_path = f'{MODEL_DIR}/feature_names.pkl'

if not all(os.path.exists(p) for p in [model_path, imputer_path, features_path]):
    print("Model files not found. Please run training first!")
    exit()

model = joblib.load(model_path)
imputer = joblib.load(imputer_path)
feature_names = joblib.load(features_path)

print("Model loaded successfully")

def prepare_features(df):
    X = df.copy()
    
    X_imputed = pd.DataFrame(
        imputer.transform(X),
        columns=X.columns,
        index=X.index
    )
    
    enjoy_cols = ['enjoy_math', 'enjoy_science', 'enjoy_english', 'enjoy_filipino',
                  'enjoy_arpan', 'enjoy_mapeh', 'enjoy_tle']
    difficulty_cols = ['difficulty_reading', 'difficulty_writing', 'difficulty_math',
                       'difficulty_focusing', 'difficulty_social_interaction']
    award_cols = ['award_highest_honors', 'award_high_honors', 'award_with_honors',
                  'award_best_science', 'award_best_math', 'award_best_english',
                  'award_conduct', 'achiever_award']
    grade_cols = ['grade_math', 'grade_science', 'grade_english', 'grade_filipino',
                  'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp']
    
    X_imputed['total_subjects_enjoyed'] = X_imputed[enjoy_cols].sum(axis=1)
    X_imputed['total_difficulties'] = X_imputed[difficulty_cols].sum(axis=1)
    X_imputed['total_awards'] = X_imputed[award_cols].sum(axis=1)
    X_imputed['meets_ste_criteria'] = (X_imputed[grade_cols] >= 90).all(axis=1).astype(int)
    
    return X_imputed[feature_names]

def get_recommendations(student_data):
    X = prepare_features(student_data)
    probabilities = model.predict_proba(X)[0]
    results = [(PLACEMENT_MAP[i+1], prob) for i, prob in enumerate(probabilities)]
    results.sort(key=lambda x: x[1], reverse=True)
    return results

def display_recommendations(recommendations, student_id):
    print(f"\nStudent: {student_id}")
    print("-" * 50)
    print("Recommendations:")
    for rank, (name, prob) in enumerate(recommendations, 1):
        marker = " <-- Best Fit" if rank == 1 else ""
        print(f"  {rank}. {name:15} {prob*100:6.2f}%{marker}")
    print("-" * 50)

# TESTING 


print("TESTING  STUDENT PROFILES")



import pandas as pd

import pandas as pd

# Student 300
import pandas as pd

student = pd.DataFrame([{
   'age': 12, 
    'gender': 1, 
    'learning_style': 3, # Mixed/Kinaesthetic common for TLE
    'study_hours_daily': 2,
    'support_person': 1, 
    'assignment_completion': 2, 
    'handle_difficulty': 2,
    'enjoy_math': 0, 
    'enjoy_science': 0, 
    'enjoy_english': 0, 
    'enjoy_filipino': 0,
    'enjoy_arpan': 0, 
    'enjoy_mapeh': 1, 
    'enjoy_tle': 1, # Specifically interested in TLE
    'preferred_program': 4, # Assuming 4 corresponds to a technical/vocational track
    'motivation_level': 3,
    'enjoy_science_experiments': 0, 
    'enjoy_reading': 0, 
    'enjoy_handson_activities': 1, # TLE students usually prefer hands-on work
    'enjoy_sports': 1, 
    'enjoy_arts': 1, 
    'enjoy_language_related_activities': 0,
    'foreign_language_interest': 0, 
    'competition_participation': 1,
    'device_availability': 1, 
    'internet_access': 1,
    'absences_count': 1, 
    'absence_reason': 1,
    'family_income_help': 2, 
    'school_participation': 2, 
    'received_awards': 0,
    'award_highest_honors': 0, 
    'award_high_honors': 0, 
    'award_with_honors': 0,
    'award_best_science': 0, 
    'award_best_math': 0, 
    'award_best_english': 0,
    'award_conduct': 1, 
    'achiever_award': 0,
    'difficulty_reading': 0, 
    'difficulty_writing': 0, 
    'difficulty_math': 0,
    'difficulty_focusing': 0, 
    'difficulty_social_interaction': 0,
    'extra_support_recommended': 0, 
    'quiet_study_place': 1,
    'distance_from_school': 2, 
    'travel_difficulty': 1,
    'grade_math': 83.0, 
    'grade_science': 84.0, 
    'grade_english': 82.0,
    'grade_filipino': 85.0, 
    'grade_arpan': 85.0, 
    'grade_mapeh': 88.0,
    'average_grade_tle': 90.0, # Higher grade in TLE to show interest/skill
    'grade_esp': 86.0, 
    'grade_6_final_average': 85.0 # Set to exactly 85
}])

recommendations = get_recommendations(student)
display_recommendations(recommendations, " Profile Student")

