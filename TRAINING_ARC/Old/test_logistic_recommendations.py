
import pandas as pd
from placement_recommender_logistic import PlacementRecommenderLogistic


print(" TESTING LOGISTIC REGRESSION PLACEMENT RECOMMENDATION SYSTEM")


# Initialize recommender
recommender = PlacementRecommenderLogistic()

# Load model
if not recommender.load_model():
    print(" Please run train_logistic_model.py first!")
    exit()



print(" TEST 1: STE PROFILE")
print("   High grades (90+), loves science/math, has science awards")


ste_student = pd.DataFrame([{
    'age': 12, 'gender': 1, 'learning_style': 2, 'study_hours_daily': 4,
    'support_person': 1, 'assignment_completion': 1, 'handle_difficulty': 1,
    'enjoy_math': 1, 'enjoy_science': 1, 'enjoy_english': 1, 'enjoy_filipino': 1,
    'enjoy_arpan': 1, 'enjoy_mapeh': 0, 'enjoy_tle': 0,
    'preferred_program': 1,  
    'motivation_level': 3,
    'enjoy_science_experiments': 1, 'enjoy_reading': 1, 'enjoy_handson_activities': 1,
    'enjoy_sports': 0, 'enjoy_arts': 0, 'enjoy_language_related_activities': 0,
    'foreign_language_interest': 0, 'competition_participation': 1,
    'device_availability': 1, 'internet_access': 1,
    'absences_count': 1, 'absence_reason': 0,
    'family_income_help': 1, 'school_participation': 1, 'received_awards': 1,
    'award_highest_honors': 1, 'award_high_honors': 0, 'award_with_honors': 0,
    'award_best_science': 1, 'award_best_math': 1, 'award_best_english': 0,
    'award_conduct': 1, 'achiever_award': 1,
    'difficulty_reading': 0, 'difficulty_writing': 0, 'difficulty_math': 0,
    'difficulty_focusing': 0, 'difficulty_social_interaction': 0,
    'extra_support_recommended': 0, 'quiet_study_place': 1,
    'distance_from_school': 1, 'travel_difficulty': 0,
    'grade_math': 95, 'grade_science': 96, 'grade_english': 92,
    'grade_filipino': 91, 'grade_arpan': 90, 'grade_mapeh': 90,
    'average_grade_tle': 91, 'grade_esp': 93, 'grade_6_final_average': 93
}])

recommendations = recommender.recommend(ste_student)
recommender.display(recommendations, student_id="STE Profile Student")


print(" TEST 2: SPFL PROFILE")
print("   Good grades, loves languages, foreign language interest")


spfl_student = pd.DataFrame([{
    'age': 12, 'gender': 0, 'learning_style': 1, 'study_hours_daily': 3,
    'support_person': 1, 'assignment_completion': 1, 'handle_difficulty': 1,
    'enjoy_math': 0, 'enjoy_science': 0, 'enjoy_english': 1, 'enjoy_filipino': 1,
    'enjoy_arpan': 1, 'enjoy_mapeh': 1, 'enjoy_tle': 0,
    'preferred_program': 2,  
    'motivation_level': 3,
    'enjoy_science_experiments': 0, 'enjoy_reading': 1, 'enjoy_handson_activities': 0,
    'enjoy_sports': 0, 'enjoy_arts': 1, 'enjoy_language_related_activities': 1,
    'foreign_language_interest': 1,  
    'competition_participation': 1,
    'device_availability': 1, 'internet_access': 1,
    'absences_count': 1, 'absence_reason': 0,
    'family_income_help': 1, 'school_participation': 1, 'received_awards': 1,
    'award_highest_honors': 0, 'award_high_honors': 1, 'award_with_honors': 0,
    'award_best_science': 0, 'award_best_math': 0, 'award_best_english': 1,
    'award_conduct': 1, 'achiever_award': 1,
    'difficulty_reading': 0, 'difficulty_writing': 0, 'difficulty_math': 1,
    'difficulty_focusing': 0, 'difficulty_social_interaction': 0,
    'extra_support_recommended': 0, 'quiet_study_place': 1,
    'distance_from_school': 1, 'travel_difficulty': 0,
    'grade_math': 85, 'grade_science': 84, 'grade_english': 94,
    'grade_filipino': 95, 'grade_arpan': 90, 'grade_mapeh': 91,
    'average_grade_tle': 88, 'grade_esp': 92, 'grade_6_final_average': 89
}])

recommendations = recommender.recommend(spfl_student)
recommender.display(recommendations, student_id="SPFL Profile Student")


print(" TEST 3: SPTVE PROFILE")
print("   Enjoys hands-on activities, TLE, practical skills")


sptve_student = pd.DataFrame([{
    'age': 13, 'gender': 1, 'learning_style': 3, 'study_hours_daily': 2,
    'support_person': 2, 'assignment_completion': 2, 'handle_difficulty': 2,
    'enjoy_math': 0, 'enjoy_science': 0, 'enjoy_english': 0, 'enjoy_filipino': 0,
    'enjoy_arpan': 0, 'enjoy_mapeh': 1, 'enjoy_tle': 1,  
    'preferred_program': 3,
    'motivation_level': 2,
    'enjoy_science_experiments': 0, 'enjoy_reading': 0, 'enjoy_handson_activities': 1,
    'enjoy_sports': 1, 'enjoy_arts': 0, 'enjoy_language_related_activities': 0,
    'foreign_language_interest': 0, 'competition_participation': 0,
    'device_availability': 1, 'internet_access': 1,
    'absences_count': 2, 'absence_reason': 1,
    'family_income_help': 2, 'school_participation': 1, 'received_awards': 0,
    'award_highest_honors': 0, 'award_high_honors': 0, 'award_with_honors': 0,
    'award_best_science': 0, 'award_best_math': 0, 'award_best_english': 0,
    'award_conduct': 0, 'achiever_award': 0,
    'difficulty_reading': 1, 'difficulty_writing': 1, 'difficulty_math': 1,
    'difficulty_focusing': 0, 'difficulty_social_interaction': 0,
    'extra_support_recommended': 1, 'quiet_study_place': 0,
    'distance_from_school': 2, 'travel_difficulty': 1,
    'grade_math': 82, 'grade_science': 83, 'grade_english': 81,
    'grade_filipino': 84, 'grade_arpan': 85, 'grade_mapeh': 88,
    'average_grade_tle': 92,  
    'grade_esp': 86, 'grade_6_final_average': 85
}])

recommendations = recommender.recommend(sptve_student)
recommender.display(recommendations, student_id="SPTVE Profile Student")


print(" TEST 4: TOP-5 REGULAR PROFILE")
print("   Good grades (85-89), balanced interests, no special program preference")


top5_student = pd.DataFrame([{
    'age': 12, 'gender': 0, 'learning_style': 2, 'study_hours_daily': 3,
    'support_person': 1, 'assignment_completion': 1, 'handle_difficulty': 2,
    'enjoy_math': 1, 'enjoy_science': 1, 'enjoy_english': 1, 'enjoy_filipino': 1,
    'enjoy_arpan': 1, 'enjoy_mapeh': 1, 'enjoy_tle': 1,
    'preferred_program': 4, 
    'motivation_level': 2,
    'enjoy_science_experiments': 1, 'enjoy_reading': 1, 'enjoy_handson_activities': 1,
    'enjoy_sports': 1, 'enjoy_arts': 1, 'enjoy_language_related_activities': 0,
    'foreign_language_interest': 0, 'competition_participation': 0,
    'device_availability': 1, 'internet_access': 1,
    'absences_count': 1, 'absence_reason': 0,
    'family_income_help': 1, 'school_participation': 1, 'received_awards': 1,
    'award_highest_honors': 0, 'award_high_honors': 0, 'award_with_honors': 1,
    'award_best_science': 0, 'award_best_math': 0, 'award_best_english': 0,
    'award_conduct': 1, 'achiever_award': 0,
    'difficulty_reading': 0, 'difficulty_writing': 0, 'difficulty_math': 0,
    'difficulty_focusing': 0, 'difficulty_social_interaction': 0,
    'extra_support_recommended': 0, 'quiet_study_place': 1,
    'distance_from_school': 1, 'travel_difficulty': 0,
    'grade_math': 87, 'grade_science': 86, 'grade_english': 88,
    'grade_filipino': 87, 'grade_arpan': 88, 'grade_mapeh': 89,
    'average_grade_tle': 87, 'grade_esp': 88, 'grade_6_final_average': 87
}])

recommendations = recommender.recommend(top5_student)
recommender.display(recommendations, student_id="Top-5 Regular Profile Student")


print(" TEST 5: HETERO PROFILE")
print("   Average grades (75-82), some difficulties, needs support")


hetero_student = pd.DataFrame([{
    'age': 13, 'gender': 1, 'learning_style': 3, 'study_hours_daily': 1,
    'support_person': 3, 'assignment_completion': 3, 'handle_difficulty': 3,
    'enjoy_math': 0, 'enjoy_science': 0, 'enjoy_english': 0, 'enjoy_filipino': 0,
    'enjoy_arpan': 0, 'enjoy_mapeh': 1, 'enjoy_tle': 1,
    'preferred_program': 5,  
    'motivation_level': 1,
    'enjoy_science_experiments': 0, 'enjoy_reading': 0, 'enjoy_handson_activities': 1,
    'enjoy_sports': 1, 'enjoy_arts': 0, 'enjoy_language_related_activities': 0,
    'foreign_language_interest': 0, 'competition_participation': 0,
    'device_availability': 0, 'internet_access': 0,
    'absences_count': 3, 'absence_reason': 2,
    'family_income_help': 3, 'school_participation': 0, 'received_awards': 0,
    'award_highest_honors': 0, 'award_high_honors': 0, 'award_with_honors': 0,
    'award_best_science': 0, 'award_best_math': 0, 'award_best_english': 0,
    'award_conduct': 0, 'achiever_award': 0,
    'difficulty_reading': 1, 'difficulty_writing': 1, 'difficulty_math': 1,
    'difficulty_focusing': 1, 'difficulty_social_interaction': 0,
    'extra_support_recommended': 1, 'quiet_study_place': 0,
    'distance_from_school': 3, 'travel_difficulty': 1,
    'grade_math': 77, 'grade_science': 78, 'grade_english': 76,
    'grade_filipino': 79, 'grade_arpan': 80, 'grade_mapeh': 82,
    'average_grade_tle': 81, 'grade_esp': 80, 'grade_6_final_average': 79
}])

recommendations = recommender.recommend(hetero_student)
recommender.display(recommendations, student_id="Hetero Profile Student")


