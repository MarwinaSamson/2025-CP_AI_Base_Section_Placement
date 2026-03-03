"""
================================================================================
HYBRID PLACEMENT RECOMMENDER
================================================================================

Hybrid Two-Stage ML Framework for Section Placement

    Stage 1: Ridge Regression (5 models, one per program)
    └─ Predicts Grade 7 Q1 average for each program

    Stage 2: XGBoost Classifier (1 model)
    └─ Ranks programs by student fit and suitability

This module provides a drop-in replacement for the original PlacementRecommender,
using the same interface but with superior two-stage prediction logic.

USAGE:
    from TRAINING_ARC.placement_recommender_hybrid import HybridPlacementRecommender
    
    recommender = HybridPlacementRecommender(model_path='TRAINING_ARC/models/hybrid')
    if recommender.load_models():
        recommendations = recommender.recommend(student_data, top_n=5)
        for rec in recommendations:
            print(f"  {rec['placement']}: {rec['probability']:.1%} confidence")

================================================================================
"""

import os
import sys
import warnings
import numpy as np
import pandas as pd
import joblib

from sklearn.impute import SimpleImputer

warnings.filterwarnings('ignore')


class HybridPlacementRecommender:
    """
    Hybrid Two-Stage Placement Recommender.
    
    Compatible interface with PlacementRecommender but uses Ridge + XGBoost
    for better accuracy and explainability.
    """
    
    # Program mapping (for display/compatibility with signals.py)
    PLACEMENT_MAP = {
        1: 'STE',
        2: 'SPFL',
        3: 'SPTVE',
        4: 'Top-5 Regular',
        5: 'Hetero'
    }
    
    # File name mapping (actual model file names)
    PLACEMENT_FILE_MAP = {
        1: 'STE',
        2: 'SPFL',
        3: 'SPTVE',
        4: 'TOP-5',
        5: 'HETERO'
    }
    
    PLACEMENT_FULL_NAMES = {
        1: 'STE (Science, Technology & Engineering)',
        2: 'SPFL (Special Program in Foreign Language)',
        3: 'SPTVE (Special Program in Technical Vocational Education)',
        4: 'Top-5 Regular Sections',
        5: 'Hetero Sections'
    }
    
    # Suitability thresholds (Stage 1: minimum predicted average per program)
    SUITABILITY_THRESHOLD = {
        1: 85,
        2: 85,
        3: 85,
        4: 85,
        5: 75
    }
    
    # STE hard eligibility
    STE_ELIGIBILITY_SUBJECTS = ['grade_math', 'grade_science', 'grade_english']
    STE_ELIGIBILITY_MIN_GRADE = 83
    
    # All features (must match training data exactly)
    G6_ACADEMIC = [
        'grade_math', 'grade_science', 'grade_english', 'grade_filipino',
        'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp',
        'grade_6_final_average'
    ]
    
    NON_ACADEMIC = [
        'age', 'gender', 'learning_style', 'study_hours_daily', 'support_person',
        'assignment_completion', 'handle_difficulty', 'enjoy_math', 'enjoy_science',
        'enjoy_english', 'enjoy_filipino', 'enjoy_arpan', 'enjoy_mapeh', 'enjoy_tle',
        'motivation_level', 'enjoy_science_experiments', 'enjoy_reading',
        'enjoy_handson_activities', 'enjoy_sports', 'enjoy_arts',
        'enjoy_language_related_activities', 'foreign_language_interest',
        'competition_participation', 'device_availability', 'internet_access',
        'absences_count', 'family_income_help', 'school_participation',
        'received_awards', 'award_highest_honors', 'award_high_honors',
        'award_with_honors', 'award_best_science', 'award_best_math',
        'award_best_english', 'award_conduct', 'achiever_award',
        'difficulty_reading', 'difficulty_writing', 'difficulty_math',
        'difficulty_focusing', 'difficulty_social_interaction',
        'extra_support_recommended', 'quiet_study_place',
        'distance_from_school', 'travel_difficulty',
        'has_valid_preference'
    ]
    
    FEATURES = G6_ACADEMIC + NON_ACADEMIC
    
    def __init__(self, model_path='TRAINING_ARC/models/hybrid'):
        """
        Initialize the Hybrid Recommender.
        
        Args:
            model_path (str): Path to folder containing hybrid models
                            Default: TRAINING_ARC/models/hybrid
        """
        self.model_path = model_path
        self.ridge_models = {}
        self.clf_bundle = None
        self.loaded = False
    
    def load_models(self):
        """
        Load all trained Ridge regressors and XGBoost classifier.
        
        Returns:
            bool: True if all models loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.model_path):
                print(f"  ✗ ERROR: Model path '{self.model_path}' not found")
                return False
            
            # Load 5 Ridge regressors (one per program)
            for prog_id, file_name in self.PLACEMENT_FILE_MAP.items():
                model_file = os.path.join(self.model_path, f'ridge_{file_name}.pkl')
                if not os.path.exists(model_file):
                    print(f"  ✗ ERROR: Missing Ridge model: {model_file}")
                    return False
                
                self.ridge_models[prog_id] = joblib.load(model_file)
            
            # Load XGBoost classifier
            clf_file = os.path.join(self.model_path, 'xgboost_classifier.pkl')
            if not os.path.exists(clf_file):
                print(f"  ✗ ERROR: Missing XGBoost classifier: {clf_file}")
                return False
            
            self.clf_bundle = joblib.load(clf_file)
            self.loaded = True
            return True
            
        except Exception as e:
            print(f"  ✗ ERROR loading models: {e}")
            return False
    
    def load_model(self):
        """
        Alias for load_models() to maintain compatibility with PlacementRecommender.
        
        Returns:
            bool: True if loaded successfully
        """
        return self.load_models()
    
    def preprocess(self, student_data):
        """
        Preprocess student data for prediction.
        
        Args:
            student_data: pandas DataFrame with student features
            
        Returns:
            DataFrame ready for model input
        """
        # Ensure all required features are present
        for feature in self.FEATURES:
            if feature not in student_data.columns:
                student_data[feature] = np.nan
        
        # Return only required features in correct order
        return student_data[self.FEATURES]
    
    def recommend(self, student_data, top_n=5):
        """
        Generate placement recommendations using two-stage hybrid model.
        
        Args:
            student_data: DataFrame (single row) with student features
            top_n: Number of recommendations to return
            
        Returns:
            List of dicts with keys:
                - 'rank': rank (1-5)
                - 'placement': program name
                - 'probability': confidence score 0-1
                - 'placement_code': numeric code 1-5
                - 'predicted_average': Stage 1 prediction
                - 'suitable': bool
        """
        if not self.loaded:
            raise ValueError("Models not loaded. Call load_models() first.")
        
        try:
            # Ensure input is DataFrame
            if isinstance(student_data, dict):
                student_data = pd.DataFrame([student_data])
            
            # Make a copy to avoid modifying original
            X = student_data.copy()
            
            # Fill missing features with NaN (will be imputed)
            for feat in self.FEATURES:
                if feat not in X.columns:
                    X[feat] = np.nan
            
            # Calculate grade_6_final_average if not present
            if 'grade_6_final_average' not in X or pd.isna(X['grade_6_final_average'].iloc[0]):
                g6_subjects = self.G6_ACADEMIC[:8]
                g6_avg = X[[col for col in g6_subjects if col in X.columns]].mean(axis=1)
                X['grade_6_final_average'] = g6_avg
            
            # Engineer has_valid_preference
            if 'has_valid_preference' not in X.columns:
                X['has_valid_preference'] = 1
            
            # ──────────────────────────────────────────────────────────
            # STAGE 1: Ridge Regression
            # ──────────────────────────────────────────────────────────
            predicted_averages = {}
            suitability = {}
            
            for prog_id, prog_name in self.PLACEMENT_MAP.items():
                model_bundle = self.ridge_models[prog_id]
                
                # Extract imputer and model
                if isinstance(model_bundle, dict):
                    imputer = model_bundle.get('imputer')
                    model = model_bundle.get('model')
                else:
                    # For backward compatibility with joblib pickled bundles
                    imputer = getattr(model_bundle, 'imputer', SimpleImputer())
                    model = model_bundle
                
                # Predict
                X_prep = X[self.FEATURES].copy()
                if imputer:
                    X_imp = imputer.transform(X_prep)
                else:
                    X_imp = X_prep.fillna(X_prep.mean()).values
                
                pred = float(model.predict(X_imp)[0])
                pred = round(pred, 2)
                predicted_averages[prog_id] = pred
                
                # Suitability check
                grade_ok = pred >= self.SUITABILITY_THRESHOLD[prog_id]
                
                # STE requires hard eligibility
                if prog_id == 1:
                    ste_eligible = all(
                        X[s].iloc[0] is not None and X[s].iloc[0] >= self.STE_ELIGIBILITY_MIN_GRADE
                        for s in self.STE_ELIGIBILITY_SUBJECTS
                        if s in X.columns
                    )
                    suitability[prog_id] = grade_ok and ste_eligible
                else:
                    suitability[prog_id] = grade_ok
            
            # ──────────────────────────────────────────────────────────
            # STAGE 2: XGBoost Classification
            # ──────────────────────────────────────────────────────────
            xgb_model = self.clf_bundle.get('model')
            scaler = self.clf_bundle.get('scaler')
            clf_imputer = self.clf_bundle.get('imputer')
            clf_features = self.clf_bundle.get('clf_features')
            label_offset = self.clf_bundle.get('label_offset', 1)
            
            # Augment features with Stage 1 predictions
            X_aug = X[self.FEATURES].copy()
            for prog_id, prog_name in self.PLACEMENT_MAP.items():
                X_aug[f'pred_avg_{prog_name}'] = predicted_averages[prog_id]
            
            # Ensure columns match training order
            X_aug = X_aug[[col for col in clf_features if col in X_aug.columns]]
            
            # Fill any missing columns
            for col in clf_features:
                if col not in X_aug.columns:
                    X_aug[col] = 0
            
            X_aug = X_aug[clf_features]
            
            # Impute → Scale → Predict
            if clf_imputer:
                X_aug_imp = clf_imputer.transform(X_aug)
            else:
                X_aug_imp = X_aug.fillna(X_aug.mean()).values
            
            if scaler:
                X_aug_scaled = scaler.transform(X_aug_imp)
            else:
                X_aug_scaled = X_aug_imp
            
            proba_raw = xgb_model.predict_proba(X_aug_scaled)[0]
            
            # Map probabilities to program IDs
            probabilities = {
                pid: round(float(proba_raw[pid - label_offset]), 4)
                for pid in self.PLACEMENT_MAP
            }
            
            # ──────────────────────────────────────────────────────────
            # APPLY SUITABILITY GATE
            # ──────────────────────────────────────────────────────────
            # Only recommend programs where student is academically suitable
            # Fallback to HETERO (id=5) if no program clears the gate
            
            suitable_ranked = [
                (pid, probabilities[pid])
                for pid in sorted(self.PLACEMENT_MAP.keys(), 
                                 key=lambda x: probabilities[x], 
                                 reverse=True)
                if suitability[pid]
            ]
            
            if not suitable_ranked:
                # No program meets suitability gate, default to HETERO
                suitable_ranked = [(5, probabilities[5])]
            
            # Build results
            results = []
            for rank, (prog_id, prob) in enumerate(suitable_ranked[:top_n], 1):
                results.append({
                    'rank': rank,
                    'placement': self.PLACEMENT_MAP[prog_id],
                    'placement_code': prog_id,
                    'probability': prob,
                    'predicted_average': predicted_averages[prog_id],
                    'suitable': suitability[prog_id]
                })
            
            return results
        
        except Exception as e:
            print(f"  ✗ ERROR during prediction: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_recommendation_dict(self, student_data):
        """
        Get recommendations as a dictionary (useful for APIs).
        
        Args:
            student_data: DataFrame with student features
            
        Returns:
            Dictionary with recommendation data
        """
        recommendations = self.recommend(student_data)
        
        if recommendations:
            return {
                'model': 'Hybrid (Ridge + XGBoost)',
                'primary_recommendation': recommendations[0]['placement'],
                'primary_match_score': recommendations[0]['probability'],
                'all_recommendations': recommendations
            }
        else:
            return {
                'model': 'Hybrid (Ridge + XGBoost)',
                'primary_recommendation': 'Hetero',
                'primary_match_score': 0.5,
                'all_recommendations': []
            }
    
    def get_detailed_explanation(self, student_data, target_program_id=None):
        """
        Get detailed explanation of recommendations including all programs' predictions
        and top contributing factors.
        
        Args:
            student_data: DataFrame with student features (single row)
            target_program_id: Optional program ID to focus on (1-5)
            
        Returns:
            Dictionary with:
                - all_programs_stage1: Ridge regression predictions for all programs
                - all_programs_stage2: XGBoost confidences for all programs
                - top_factors: Top 10 feature importances for target program
                - predicted_averages: Dict of all programs' predicted G7 Q1 averages
        """
        try:
            if not self.loaded:
                return None
            
            # Ensure input is DataFrame
            if isinstance(student_data, dict):
                student_data = pd.DataFrame([student_data])
            
            X = student_data.copy()
            
            # Get all features prepared
            for feat in self.FEATURES:
                if feat not in X.columns:
                    X[feat] = np.nan
            
            # Calculate grade_6_final_average if not present
            if 'grade_6_final_average' not in X or pd.isna(X['grade_6_final_average'].iloc[0]):
                g6_subjects = self.G6_ACADEMIC[:8]
                g6_avg = X[[col for col in g6_subjects if col in X.columns]].mean(axis=1)
                X['grade_6_final_average'] = g6_avg
            
            if 'has_valid_preference' not in X.columns:
                X['has_valid_preference'] = 1
            
            # ── STAGE 1: Ridge Regression ──
            predicted_averages = {}
            stage1_results = []
            
            for prog_id, prog_name in self.PLACEMENT_MAP.items():
                model_bundle = self.ridge_models[prog_id]
                
                if isinstance(model_bundle, dict):
                    imputer = model_bundle.get('imputer')
                    model = model_bundle.get('model')
                else:
                    imputer = getattr(model_bundle, 'imputer', SimpleImputer())
                    model = model_bundle
                
                X_prep = X[self.FEATURES].copy()
                if imputer:
                    X_imp = imputer.transform(X_prep)
                else:
                    X_imp = X_prep.fillna(X_prep.mean()).values
                
                pred = float(model.predict(X_imp)[0])
                pred = round(pred, 2)
                predicted_averages[prog_id] = pred
                
                stage1_results.append({
                    'program_id': prog_id,
                    'program_name': prog_name,
                    'predicted_average': pred
                })
            
            # ── STAGE 2: XGBoost Classification ──
            xgb_model = self.clf_bundle.get('model')
            scaler = self.clf_bundle.get('scaler')
            clf_imputer = self.clf_bundle.get('imputer')
            clf_features = self.clf_bundle.get('clf_features')
            label_offset = self.clf_bundle.get('label_offset', 1)
            
            X_aug = X[self.FEATURES].copy()
            for prog_id, prog_name in self.PLACEMENT_MAP.items():
                X_aug[f'pred_avg_{prog_name}'] = predicted_averages[prog_id]
            
            X_aug = X_aug[[col for col in clf_features if col in X_aug.columns]]
            
            for col in clf_features:
                if col not in X_aug.columns:
                    X_aug[col] = 0
            
            X_aug = X_aug[clf_features]
            
            if clf_imputer:
                X_aug_imp = clf_imputer.transform(X_aug)
            else:
                X_aug_imp = X_aug.fillna(X_aug.mean()).values
            
            if scaler:
                X_aug_scaled = scaler.transform(X_aug_imp)
            else:
                X_aug_scaled = X_aug_imp
            
            proba_raw = xgb_model.predict_proba(X_aug_scaled)[0]
            
            probabilities = {
                pid: round(float(proba_raw[pid - label_offset]), 4)
                for pid in self.PLACEMENT_MAP
            }
            
            stage2_results = [
                {
                    'program_id': pid,
                    'program_name': self.PLACEMENT_MAP[pid],
                    'confidence': probabilities[pid],
                    'confidence_pct': int(round(probabilities[pid] * 100))
                }
                for pid in sorted(self.PLACEMENT_MAP.keys(), 
                                 key=lambda x: probabilities[x], 
                                 reverse=True)
            ]
            
            # ── Top 8 Contributing Factors ──
            top_factors = self._get_top_factors(student_data, X[self.FEATURES], target_program_id or 1)
            
            return {
                'stage1_all_programs': stage1_results,
                'stage2_all_programs': stage2_results,
                'predicted_averages': predicted_averages,
                'top_factors': top_factors
            }
        
        except Exception as e:
            print(f"[HYBRID] Error in get_detailed_explanation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_top_factors(self, student_data_orig, student_data_processed, program_id):
        """
        Get top 8 factors influencing recommendation for a specific program.
        
        Args:
            student_data_orig: Original student data dict
            student_data_processed: Processed DataFrame
            program_id: Program ID to analyze
            
        Returns:
            List of top 8 factors with their contribution
        """
        try:
            # Simple heuristic-based factor extraction from student data
            factors = []
            
            if isinstance(student_data_orig, pd.DataFrame):
                row = student_data_orig.iloc[0] if len(student_data_orig) > 0 else {}
            else:
                row = student_data_orig
            
            # Extract key academic factors
            academic_fields = {
                'grade_math': 'Math Grade',
                'grade_science': 'Science Grade',
                'grade_english': 'English Grade',
                'grade_6_final_average': 'Overall Average'
            }
            
            for field, label in academic_fields.items():
                if field in row:
                    val = row[field] if isinstance(row, dict) else row.get(field)
                    if val and not pd.isna(val):
                        factors.append({
                            'feature': label,
                            'value': f'{float(val):.1f}',
                            'type': 'academic'
                        })
            
            # Extract survey factors
            survey_fields = {
                'enjoy_math': 'Enjoys Mathematics',
                'enjoy_science': 'Enjoys Science',
                'enjoy_english': 'Enjoys English',
                'motivation_level': 'Motivation Level',
                'learning_style': 'Learning Style',
                'study_hours_daily': 'Daily Study Hours',
                'received_awards': 'Has Received Awards',
                'competition_participation': 'Joined Competitions'
            }
            
            for field, label in survey_fields.items():
                if field in row:
                    val = row[field] if isinstance(row, dict) else row.get(field)
                    if val and not pd.isna(val):
                        if isinstance(val, (int, float)):
                            display_val = 'Yes' if val == 1 else f'{int(val)}'
                        else:
                            display_val = str(val)
                        
                        factors.append({
                            'feature': label,
                            'value': display_val,
                            'type': 'survey'
                        })
            
            # Return top 10 factors
            return factors[:10]
        
        except Exception as e:
            print(f"[HYBRID] Error in _get_top_factors: {e}")
            return []

    def display(self, recommendations, student_id=None):
        """
        Display recommendations in a formatted way.
        
        Args:
            recommendations: List of recommendation dicts
            student_id: Optional student ID for logging
        """
        if student_id:
            print(f"\n  Recommendations for Student {student_id}:")
        else:
            print(f"\n  Recommendations:")
        
        for rec in recommendations:
            prog = rec['placement']
            prob = rec['probability']
            avg = rec.get('predicted_average', 'N/A')
            print(f"    {rec['rank']}. {prog:20s} {prob:6.1%} confidence (pred avg: {avg})")


if __name__ == '__main__':
    # Simple test
    recommender = HybridPlacementRecommender()
    if recommender.load_models():
        print("✓ Hybrid models loaded successfully")
    else:
        print("✗ Failed to load hybrid models")
