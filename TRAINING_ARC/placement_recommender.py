"""
================================================================================
🎓 PLACEMENT RECOMMENDATION MODULE
================================================================================
Use this module to get placement recommendations for new students.

Usage:
    from placement_recommender import PlacementRecommender
    
    recommender = PlacementRecommender()
    recommender.load_model()
    
    recommendations = recommender.recommend(student_data)
    recommender.display(recommendations)
================================================================================
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
        print("\n" + "═" * 60)
        if student_id:
            print(f"    PLACEMENT RECOMMENDATIONS FOR: {student_id}")
        else:
            print("    PLACEMENT RECOMMENDATIONS")
        print("═" * 60)
        
        print("\n   We recommend these placements:\n")
        
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
        
        print("\n" + "─" * 60)
        
        # Primary recommendation
        best = recommendations[0]
        print(f"\n    PRIMARY RECOMMENDATION: {best['placement_full']}")
        print(f"      Match Score: {best['percentage']}")
        print("\n" + "═" * 60)
    
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


# ============================================================================
# STANDALONE USAGE EXAMPLE
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("🎓 PLACEMENT RECOMMENDER - Test Mode")
    print("=" * 60)
    
    # Initialize recommender
    recommender = PlacementRecommender()
    
    # Load model
    if not recommender.load_model():
        print("Please train the model first using train_recommendation_model.py")
        exit()
    
    # Create a test student
    test_student = pd.DataFrame([{
   'age': 13,
    'gender': 0,
    'learning_style': 5,
    'study_hours_daily': 4,
    'support_person': 1,
    'assignment_completion': 1,
    'handle_difficulty': 3,
    'enjoy_math': 1,
    'enjoy_science': 0,
    'enjoy_english': 0,
    'enjoy_filipino': 0,
    'enjoy_arpan': 0,
    'enjoy_mapeh': 0,
    'enjoy_tle': 0,
    'preferred_program': 4,
    'motivation_level': 3,
    'enjoy_science_experiments': 0,
    'enjoy_reading': 0,
    'enjoy_handson_activities': 1,
    'enjoy_sports': 0,
    'enjoy_arts': 0,
    'enjoy_language_related_activities': 0,
    'foreign_language_interest': 2,
    'competition_participation': 1,
    'device_availability': 2,
    'internet_access': 3,
    'absences_count': 1,
    'absence_reason': 5,
    'family_income_help': 3,
    'school_participation': 1,
    'received_awards': 0,
    'award_highest_honors': 0,
    'award_high_honors': 0,
    'award_with_honors': 0,
    'award_best_science': 0,
    'award_best_math': 0,
    'award_best_english': 0,
    'award_conduct': 0,
    'achiever_award': 1,
    'difficulty_reading': 0,
    'difficulty_writing': 0,
    'difficulty_math': 0,
    'difficulty_focusing': 1,
    'difficulty_social_interaction': 0,
    'extra_support_recommended': 1,
    'quiet_study_place': 1,
    'distance_from_school': 1,
    'travel_difficulty': 3,
    'grade_math': 85,
    'grade_science': 86,
    'grade_english': 86,
    'grade_filipino': 86,
    'grade_arpan': 87,
    'grade_mapeh': 87,
    'average_grade_tle': 88,
    'grade_esp': 88,
    'grade_6_final_average': 86
    }])
    
    # Get recommendations
    recommendations = recommender.recommend(test_student)
    
    # Display
    recommender.display(recommendations, student_id="Test Student (STE Profile)")
    
    # Also show as dictionary (for API usage)
    print("\n API Output Format:")
    print("-" * 40)
    result = recommender.get_recommendation_dict(test_student)
    print(f"   Primary: {result['primary_recommendation']}")
    print(f"   Score: {result['primary_match_score']*100:.2f}%")
