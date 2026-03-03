
from matplotlib.pylab import f
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

print(" STUDENT PLACEMENT RECOMMENDATION SYSTEM")



# STEP 1: LOAD DATA

print("\n Step 1: Loading Data...")

CSV_PATH = 'dataset/TRAINING_Student_Placement_Data.csv'

if not os.path.exists(CSV_PATH):
    print(f"   File not found: {CSV_PATH}")
    print("   Please place your CSV file in the 'dataset' folder.")
    exit()

df = pd.read_csv(CSV_PATH)
print(f"    Loaded {len(df)} students, {len(df.columns)} columns")

# Placement mapping
PLACEMENT_MAP = {
    1: 'STE',
    2: 'SPFL',
    3: 'SPTVE',
    4: 'Top-5 Regular',
    5: 'Hetero'
}

print(f"\n    Class Distribution:")
for code, name in PLACEMENT_MAP.items():
    count = len(df[df['actual_placement'] == code])
    pct = (count / len(df)) * 100
    print(f"      {code} ({name}): {count} students ({pct:.1f}%)")


# STEP 2: PREPARE FEATURES AND TARGET

print("\n Step 2: Preparing Features...")

X = df.drop(columns=['student_id', 'actual_placement'])
y = df['actual_placement']

# Impute missing values
imputer = SimpleImputer(strategy='median')
X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=X.columns, index=X.index)

# Feature Engineering
enjoy_cols = ['enjoy_math', 'enjoy_science', 'enjoy_english', 'enjoy_filipino', 
              'enjoy_arpan', 'enjoy_mapeh', 'enjoy_tle']
X_imputed['total_subjects_enjoyed'] = X_imputed[enjoy_cols].sum(axis=1)

difficulty_cols = ['difficulty_reading', 'difficulty_writing', 'difficulty_math', 
                   'difficulty_focusing', 'difficulty_social_interaction']
X_imputed['total_difficulties'] = X_imputed[difficulty_cols].sum(axis=1)

award_cols = ['award_highest_honors', 'award_high_honors', 'award_with_honors',
              'award_best_science', 'award_best_math', 'award_best_english',
              'award_conduct', 'achiever_award']
X_imputed['total_awards'] = X_imputed[award_cols].sum(axis=1)

grade_cols = ['grade_math', 'grade_science', 'grade_english', 'grade_filipino',
              'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp']
X_imputed['meets_ste_criteria'] = (X_imputed[grade_cols] >= 90).all(axis=1).astype(int)

print(f"   Features prepared: {X_imputed.shape[1]} total")


# STEP 3: TRAIN-TEST SPLIT

print("\n  Step 3: Splitting Data...")

X_train, X_test, y_train, y_test = train_test_split(
    X_imputed, y, test_size=0.2, random_state=42, stratify=y
)
print(f"   Training: {len(X_train)} | Testing: {len(X_test)}")


# STEP 4: APPLY SMOTE

print("\n  Step 4: Balancing Classes with SMOTE...")

smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

print(f"   Before: {dict(y_train.value_counts().sort_index())}")
print(f"   After:  {dict(pd.Series(y_train_balanced).value_counts().sort_index())}")


# STEP 5: TRAIN RANDOM FOREST (Best for Recommendations)

print("\n Step 5: Training Random Forest Model...")

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train_balanced, y_train_balanced)
print("    Model trained!")

# STEP 6: EVALUATE MODEL

print("\n Step 6: Evaluating Model...")

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"   Accuracy: {accuracy*100:.2f}%")
print(f"   F1-Score: {f1:.4f}")

# STEP 7: SAVE MODEL AND COMPONENTS

print("\n Step 7: Saving Model...")

os.makedirs('models', exist_ok=True)

joblib.dump(model, 'models/placement_recommendation_model.pkl')
joblib.dump(imputer, 'models/imputer.pkl')
joblib.dump(list(X_imputed.columns), 'models/feature_names.pkl')

print("   Saved: models/placement_recommendation_model.pkl")
print("   Saved: models/imputer.pkl")
print("   Saved: models/feature_names.pkl")

# STEP 8: DEMONSTRATION - RECOMMENDATION OUTPUT

def get_placement_recommendation(model, student_data, top_n=5):
    """
    Get placement recommendations with match percentages.
    
    Returns a list of tuples: [(placement_name, probability, rank), ...]
    """
    # Get probabilities for each class
    probabilities = model.predict_proba(student_data)[0]
    
    # Get class labels from model
    classes = model.classes_
    
    # Create list of (class, probability) and sort by probability
    placements = ['STE', 'SPFL', 'SPTVE', 'Top-5 Regular', 'Hetero']
    
    # Map model classes to placement names
    results = []
    for i, prob in enumerate(probabilities):
        class_label = classes[i]
        placement_name = PLACEMENT_MAP.get(class_label, f"Class {class_label}")
        results.append((placement_name, prob, class_label))
    
    # Sort by probability (highest first)
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:top_n]


def display_recommendation(recommendations, student_id=None):
    """
    Display recommendations in a nice format.
    """
    print("\n" + "─" * 60)
    if student_id:
        print(f"   Student: {student_id}")
        print("─" * 60)
    
    print("\n    RECOMMENDED PLACEMENTS:")
    print("   " + "─" * 55)
    
    for rank, (name, prob, class_label) in enumerate(recommendations, 1):
        # Create visual bar
        bar_length = int(prob * 30)
        bar = "█" * bar_length
        
        # Add label
        if rank == 1:
            label = " Best Fit"
        elif rank == 2:
            label = "   2nd Choice"
        elif rank == 3:
            label = "   3rd Choice"
        else:
            label = ""
        
        print(f"      {rank}. {name:15} {prob*100:6.2f}%  {bar} {label}")
    
    print("   " + "─" * 55)
    
    # Show best recommendation
    best = recommendations[0]
    print(f"\n    PRIMARY RECOMMENDATION: {best[0]} ({best[1]*100:.1f}% match)")


# Test with sample students from test set
print("\nTesting with 3 sample students:\n")

for i in range(3):
    sample = X_test.iloc[[i]]
    actual = y_test.iloc[i]
    
    recommendations = get_placement_recommendation(model, sample)
    
    print(f"\n{'='*60}")
    print(f"   STUDENT {i+1}")
    print(f"   Actual Placement: {PLACEMENT_MAP[actual]}")
    display_recommendation(recommendations)
    
    # Check if correct
    predicted = recommendations[0][2]
    if predicted == actual:
        print("    Model's top recommendation matches actual placement!")
    else:
        print(f"   Actual placement was {PLACEMENT_MAP[actual]}")


# STEP 9: SAVE THE RECOMMENDATION FUNCTION



# Save a standalone recommendation module
recommendation_code = '''"""

 PLACEMENT RECOMMENDATION MODULE

Use this module to get placement recommendations for new students.

Usage:
    from placement_recommender import PlacementRecommender
    
    recommender = PlacementRecommender()
    recommender.load_model()
    
    recommendations = recommender.recommend(student_data)
    recommender.display(recommendations)

"""

import pandas as pd
import numpy as np
import joblib
import os

class PlacementRecommender:
    """
    Student Placement Recommendation System
    
    Provides placement recommendations with match percentages for all programs.
    """
    
    def __init__(self, model_path='models'):
        self.model_path = model_path
        self.model = None
        self.imputer = None
        self.feature_names = None
        
        self.PLACEMENT_MAP = {
            1: 'STE',
            2: 'SPFL',
            3: 'SPTVE',
            4: 'Top-5 Regular',
            5: 'Hetero'
        }
        
        self.PLACEMENT_FULL_NAMES = {
            1: 'STE (Science, Technology & Engineering)',
            2: 'SPFL (Special Program in Foreign Language)',
            3: 'SPTVE (Special Program in Technical Vocational Education)',
            4: 'Top-5 Regular Sections',
            5: 'Hetero Sections'
        }
    
    def load_model(self):
        """Load the trained model and preprocessors."""
        try:
            self.model = joblib.load(f'{self.model_path}/placement_recommendation_model.pkl')
            self.imputer = joblib.load(f'{self.model_path}/imputer.pkl')
            self.feature_names = joblib.load(f'{self.model_path}/feature_names.pkl')
            print(" Model loaded successfully!")
            return True
        except FileNotFoundError as e:
            print(f" Error loading model: {e}")
            return False
    
    def preprocess(self, student_data):
        """
        Preprocess student data before prediction.
        
        Args:
            student_data: DataFrame with student features
            
        Returns:
            Preprocessed DataFrame ready for prediction
        """
        df = student_data.copy()
        
        # Remove student_id if present
        if 'student_id' in df.columns:
            df = df.drop(columns=['student_id'])
        
        # Remove actual_placement if present
        if 'actual_placement' in df.columns:
            df = df.drop(columns=['actual_placement'])
        
        # Impute missing values
        df_imputed = pd.DataFrame(
            self.imputer.transform(df),
            columns=df.columns,
            index=df.index
        )
        
        # Add engineered features
        enjoy_cols = ['enjoy_math', 'enjoy_science', 'enjoy_english', 'enjoy_filipino', 
                      'enjoy_arpan', 'enjoy_mapeh', 'enjoy_tle']
        df_imputed['total_subjects_enjoyed'] = df_imputed[enjoy_cols].sum(axis=1)
        
        difficulty_cols = ['difficulty_reading', 'difficulty_writing', 'difficulty_math', 
                           'difficulty_focusing', 'difficulty_social_interaction']
        df_imputed['total_difficulties'] = df_imputed[difficulty_cols].sum(axis=1)
        
        award_cols = ['award_highest_honors', 'award_high_honors', 'award_with_honors',
                      'award_best_science', 'award_best_math', 'award_best_english',
                      'award_conduct', 'achiever_award']
        df_imputed['total_awards'] = df_imputed[award_cols].sum(axis=1)
        
        grade_cols = ['grade_math', 'grade_science', 'grade_english', 'grade_filipino',
                      'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp']
        df_imputed['meets_ste_criteria'] = (df_imputed[grade_cols] >= 90).all(axis=1).astype(int)
        
        return df_imputed
    
    def recommend(self, student_data, top_n=5):
        """
        Get placement recommendations for a student.
        
        Args:
            student_data: DataFrame with student features (single row)
            top_n: Number of recommendations to return (default: 5)
            
        Returns:
            List of tuples: [(placement_name, probability, class_label), ...]
        """
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Preprocess
        processed = self.preprocess(student_data)
        
        # Get probabilities
        probabilities = self.model.predict_proba(processed)[0]
        classes = self.model.classes_
        
        # Create results
        results = []
        for i, prob in enumerate(probabilities):
            class_label = classes[i]
            placement_name = self.PLACEMENT_MAP.get(class_label, f"Class {class_label}")
            results.append({
                'rank': 0,  # Will be set after sorting
                'placement': placement_name,
                'placement_full': self.PLACEMENT_FULL_NAMES.get(class_label, placement_name),
                'probability': prob,
                'percentage': f"{prob*100:.2f}%",
                'class_label': class_label
            })
        
        # Sort by probability
        results.sort(key=lambda x: x['probability'], reverse=True)
        
        # Add ranks
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return results[:top_n]
    
    def display(self, recommendations, student_id=None):
        """
        Display recommendations in a formatted output.
        
        Args:
            recommendations: List from recommend() method
            student_id: Optional student identifier
        """
        print("\\n" + "═" * 60)
        if student_id:
            print(f"    PLACEMENT RECOMMENDATIONS FOR: {student_id}")
        else:
            print("    PLACEMENT RECOMMENDATIONS")
       
        
        print("\\n   We recommend these placements:\\n")
        
        for rec in recommendations:
            # Create visual bar
            bar_length = int(rec['probability'] * 25)
            bar = "█" * bar_length
            
            # Add label
            if rec['rank'] == 1:
                label = "Best Fit"
            elif rec['rank'] == 2:
                label = "2nd Choice"
            elif rec['rank'] == 3:
                label = "3rd Choice"
            else:
                label = ""
            
            print(f"      {rec['rank']}. {rec['placement']:15} {rec['percentage']:>7}  {bar} {label}")
        
        print("\\n" + "─" * 60)
        
        # Primary recommendation
        best = recommendations[0]
        print(f"\\n    PRIMARY RECOMMENDATION: {best['placement_full']}")
        print(f"      Match Score: {best['percentage']}")
        print("\\n" + "═" * 60)
    
    def get_recommendation_dict(self, student_data):
        """
        Get recommendations as a dictionary (useful for APIs).
        
        Returns:
            Dictionary with recommendation data
        """
        recommendations = self.recommend(student_data)
        
        return {
            'primary_recommendation': recommendations[0]['placement'],
            'primary_match_score': recommendations[0]['probability'],
            'all_recommendations': recommendations
        }



# STANDALONE USAGE EXAMPLE

if __name__ == "__main__":
    print("=" * 60)
    print(" PLACEMENT RECOMMENDER - Test Mode")
    print("=" * 60)
    
    # Initialize recommender
    recommender = PlacementRecommender()
    
    # Load model
    if not recommender.load_model():
        print("Please train the model first using train_recommendation_model.py")
        exit()
    
    # Create a test student
    test_student = pd.DataFrame([{
        'age': 12,
        'gender': 1,
        'learning_style': 2,
        'study_hours_daily': 3,
        'support_person': 1,
        'assignment_completion': 1,
        'handle_difficulty': 1,
        'enjoy_math': 1,
        'enjoy_science': 1,
        'enjoy_english': 1,
        'enjoy_filipino': 1,
        'enjoy_arpan': 1,
        'enjoy_mapeh': 1,
        'enjoy_tle': 0,
        'preferred_program': 1,  # Prefers STE
        'motivation_level': 3,
        'enjoy_science_experiments': 1,
        'enjoy_reading': 1,
        'enjoy_handson_activities': 1,
        'enjoy_sports': 0,
        'enjoy_arts': 0,
        'enjoy_language_related_activities': 0,
        'foreign_language_interest': 0,
        'competition_participation': 1,
        'device_availability': 1,
        'internet_access': 1,
        'absences_count': 1,
        'absence_reason': 0,
        'family_income_help': 1,
        'school_participation': 1,
        'received_awards': 1,
        'award_highest_honors': 1,
        'award_high_honors': 0,
        'award_with_honors': 0,
        'award_best_science': 1,
        'award_best_math': 1,
        'award_best_english': 0,
        'award_conduct': 1,
        'achiever_award': 1,
        'difficulty_reading': 0,
        'difficulty_writing': 0,
        'difficulty_math': 0,
        'difficulty_focusing': 0,
        'difficulty_social_interaction': 0,
        'extra_support_recommended': 0,
        'quiet_study_place': 1,
        'distance_from_school': 1,
        'travel_difficulty': 0,
        'grade_math': 94,
        'grade_science': 95,
        'grade_english': 92,
        'grade_filipino': 91,
        'grade_arpan': 90,
        'grade_mapeh': 91,
        'average_grade_tle': 92,
        'grade_esp': 93,
        'grade_6_final_average': 92
    }])
    
    # Get recommendations
    recommendations = recommender.recommend(test_student)
    
    # Display
    recommender.display(recommendations, student_id="Test Student (STE Profile)")
    
    # Also show as dictionary (for API usage)
    print("\\n API Output Format:")
    print("-" * 40)
    result = recommender.get_recommendation_dict(test_student)
    print(f"   Primary: {result['primary_recommendation']}")
    print(f"   Score: {result['primary_match_score']*100:.2f}%")
'''

# Save the recommendation module
with open("placement_recommender.py", "w", encoding="utf-8") as f:
    f.write(recommendation_code)

print("    Saved: placement_recommender.py")


# FINAL SUMMARY



print(f"""
    Dataset: {len(df)} students

    Model Performance:
      - Accuracy: {accuracy*100:.2f}%
      - F1-Score: {f1:.4f}

    Saved Files:
      - models/placement_recommendation_model.pkl
      - models/imputer.pkl
      - models/feature_names.pkl
      - placement_recommender.py

""")


