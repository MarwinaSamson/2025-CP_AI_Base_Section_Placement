import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'section_placement_system.settings')
django.setup()

from enrollment_app.models import Student
from enrollment_app.services.recommendation_service import _map_session_to_ml_features
from TRAINING_ARC.placement_recommender import PlacementRecommender
from django.conf import settings
import shap

lrn = '126108180066'
student = Student.objects.get(lrn=lrn)

academic_data = {}
if hasattr(student, 'academic_data'):
    ad = student.academic_data
    academic_data = {
        'overall_average': ad.overall_average,
        'mathematics': ad.mathematics,
        'science': ad.science,
        'english': ad.english,
        'filipino': ad.filipino,
        'araling_panlipunan': ad.araling_panlipunan,
        'mapeh': ad.mapeh,
        'edukasyon_pangkabuhayan': ad.edukasyon_pangkabuhayan,
        'edukasyon_sa_pagpapakatao': ad.edukasyon_sa_pagpapakatao,
    }

survey_data = {}
if hasattr(student, 'survey_data'):
    sv = student.survey_data
    survey_data = {
        'enjoyed_subjects': sv.enjoyed_subjects or [],
        'difficulty_areas': sv.difficulty_areas or [],
    }

student_data = {}
if hasattr(student, 'student_data'):
    sd = student.student_data
    student_data = {
        'is_sped': sd.is_sped,
        'is_working_student': sd.is_working_student,
        'gender': sd.gender,
        'date_of_birth': sd.date_of_birth,
    }

recommender = PlacementRecommender(model_path=str(settings.BASE_DIR / 'TRAINING_ARC' / 'models'))
if recommender.load_model():
    features_df = _map_session_to_ml_features(academic_data, survey_data, student_data)
    print("\nFeatures used for prediction:", features_df.columns.tolist())
    model = recommender.model
    explainer = shap.Explainer(model, feature_perturbation='interventional')
    shap_values = explainer(features_df, check_additivity=False)
    for idx, program in enumerate(model.classes_):
        print(f"\nFeature contributions for {program} probability:")
        # Collect all features and their SHAP values
        feature_contribs = [
            (feature, value, shap_val)
            for feature, value, shap_val in zip(features_df.columns, features_df.iloc[0], shap_values.values[0][idx])
        ]
        # Sort by absolute contribution (strongest first)
        feature_contribs.sort(key=lambda x: abs(x[2]), reverse=True)
        for feature, value, shap_val in feature_contribs:
            print(f"{feature}: value={value}, contribution={shap_val:.4f}")
else:
    print("ERROR: Could not load ML model!")
