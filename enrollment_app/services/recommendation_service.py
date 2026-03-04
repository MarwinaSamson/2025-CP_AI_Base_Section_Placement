"""
Program Recommendation Service
Now supports ML-based recommendations using Hybrid Two-Stage Model
(Ridge Regression + XGBoost Classifier) from TRAINING_ARC.placement_recommender_hybrid
with a safe fallback to rule-based logic if the ML models are unavailable.
"""

from coordinator_app.models import Qualified_for_ste
from django.conf import settings
import pandas as pd

try:
    
    from TRAINING_ARC.placement_recommender_hybrid import HybridPlacementRecommender
    _ML_AVAILABLE = True
except Exception:
    HybridPlacementRecommender = None
    _ML_AVAILABLE = False


class ProgramRecommendationEngine:
    """
    Engine to generate program recommendations based on academic and non-academic criteria
    """
    
    # Program definitions with their requirements
    PROGRAMS = {
        'STE': {
            'name': 'Science, Technology, Engineering',
            'academic_rule': 'avg_90_above_85_subjects_dost_passed',
            'non_academic_rule': 'interested_science_math_english_active_studious_smart',
        },
        'SPFL': {
            'name': 'Specialized in Foreign Languages',
            'academic_rule': 'avg_90_above_85_subjects_no_dost',
            'non_academic_rule': 'interested_english_foreign_language_arts_tourism_active_studious',
        },
        'SPTVE': {
            'name': 'Specialized in Technology, Vocational & English',
            'academic_rule': 'avg_90_above_85_subjects_no_dost',
            'non_academic_rule': 'interested_english_technology_arts_crafts_creative_studious_smart_artistic',
        },
        'SNED L': {
            'name': 'Special Needs Education Program',
            'academic_rule': 'all_students_with_disability',
            'non_academic_rule': 'has_disability',
        },
        'OHSP': {
            'name': 'Out-of-School Youth Program',
            'academic_rule': 'working_student',
            'non_academic_rule': 'working_student',
        },
        'REGULAR': {
            'name': 'Regular Program',
            'academic_rule': 'avg_89_below',
            'non_academic_rule': 'average_student_not_studious_not_smart',
        },
    }
    
    def __init__(self, student_lrn, academic_data, survey_data, student_data):
        """
        Initialize recommendation engine with student data
        
        Args:
            student_lrn: Student's LRN
            academic_data: Dictionary containing academic information
            survey_data: Dictionary containing survey/non-academic information
            student_data: Dictionary containing basic student information
        """
        self.student_lrn = student_lrn
        self.academic_data = academic_data or {}
        self.survey_data = survey_data or {}
        self.student_data = student_data or {}
        self.recommendations = []
        
    def generate_recommendations(self):
        """
        Generate program recommendations based on academic and non-academic rules
        
        Returns:
            List of recommendations sorted by rank (best first)
        """
        self._evaluate_all_programs()
        self._rank_recommendations()
        return self.recommendations
    
    def _evaluate_all_programs(self):
        """Evaluate each program against academic and non-academic rules"""
        
        # Evaluate academic criteria
        academic_scores = self._evaluate_academic_criteria()
        
        # Evaluate non-academic criteria
        non_academic_scores = self._evaluate_non_academic_criteria()
        
        # Create recommendations
        for program_code, program_info in self.PROGRAMS.items():
            academic_score = academic_scores.get(program_code, 0)
            non_academic_score = non_academic_scores.get(program_code, 0)
            
            # Only include programs that qualify (at least 50% criteria met)
            if academic_score > 0 or non_academic_score > 0:
                recommendation = {
                    'program_code': program_code,
                    'program_name': program_info['name'],
                    'academic_score': academic_score,
                    'non_academic_score': non_academic_score,
                    'overall_score': (academic_score + non_academic_score) / 2,
                    'criteria_met': self._get_criteria_met(program_code, academic_score, non_academic_score),
                    'total_criteria': self._get_total_criteria(program_code),
                    'percentage_match': self._calculate_percentage_match(program_code, academic_score, non_academic_score),
                    'special_checks': self._get_special_checks(program_code),
                }
                self.recommendations.append(recommendation)
    
    def _evaluate_academic_criteria(self):
        """Evaluate academic rules for each program"""
        scores = {}
        
        average_grade = float(self.academic_data.get('overall_average', 0))
        dost_exam_result = self.academic_data.get('dost_exam_result', '').lower().strip()
        
        # Get minimum grade per subject
        grades = [
            float(self.academic_data.get('mathematics', 0) or 0),
            float(self.academic_data.get('araling_panlipunan', 0) or 0),
            float(self.academic_data.get('english', 0) or 0),
            float(self.academic_data.get('edukasyon_sa_pagpapakatao', 0) or 0),
            float(self.academic_data.get('science', 0) or 0),
            float(self.academic_data.get('edukasyon_pangkabuhayan', 0) or 0),
            float(self.academic_data.get('filipino', 0) or 0),
            float(self.academic_data.get('mapeh', 0) or 0),
        ]
        
        valid_grades = [g for g in grades if g > 0]
        min_grade = min(valid_grades) if valid_grades else 0
        all_subjects_85_above = all(g >= 85 for g in valid_grades) if valid_grades else False
        
        # Rule 1: STE - avg 90+, all subjects 85+, DOST passed
        if average_grade >= 90 and all_subjects_85_above and dost_exam_result == 'passed':
            scores['STE'] = 100
        
        # Rule 2: SPFL/SPTVE - avg 90+, all subjects 85+, DOST not passed
        if average_grade >= 90 and all_subjects_85_above and dost_exam_result != 'passed':
            scores['SPFL'] = 90
            scores['SPTVE'] = 90
        
        # Rule 3: REGULAR - avg 89 and below, DOST not passed
        if average_grade <= 89:
            scores['REGULAR'] = 80
        
        # Disability and working student rules
        is_pwd = self.student_data.get('is_sped', False)
        is_working = self.student_data.get('is_working_student', False)
        
        if is_pwd:
            scores['SNED L'] = 100
        
        if is_working:
            scores['OHSP'] = 100
        
        return scores
    
    def _evaluate_non_academic_criteria(self):
        """Evaluate non-academic (survey) rules for each program"""
        scores = {}
        
        # Extract survey attributes
        interests = self._parse_interests()
        characteristics = self._parse_characteristics()
        disability_status = self.student_data.get('is_sped', False)
        working_status = self.student_data.get('is_working_student', False)
        
        # STE criteria: interested in science, math, English + active + studious + smart
        ste_criteria = [
            'science' in interests,
            'math' in interests or 'mathematics' in interests,
            'english' in interests,
            characteristics.get('active', False),
            characteristics.get('studious', False),
            characteristics.get('smart', False),
        ]
        scores['STE'] = (sum(ste_criteria) / len(ste_criteria)) * 100 if ste_criteria else 0
        
        # SPFL criteria: interested in English, foreign language, arts, tourism + active + studious
        spfl_criteria = [
            'english' in interests,
            'foreign language' in interests or 'language' in interests,
            'arts' in interests,
            'tourism' in interests,
            characteristics.get('active', False),
            characteristics.get('studious', False),
        ]
        scores['SPFL'] = (sum(spfl_criteria) / len(spfl_criteria)) * 100 if spfl_criteria else 0
        
        # SPTVE criteria: interested in English, technology, arts, crafts + creative + studious + smart + artistic
        sptve_criteria = [
            'english' in interests,
            'technology' in interests or 'tech' in interests,
            'arts' in interests,
            'crafts' in interests,
            characteristics.get('creative', False),
            characteristics.get('studious', False),
            characteristics.get('smart', False),
            characteristics.get('artistic', False),
        ]
        scores['SPTVE'] = (sum(sptve_criteria) / len(sptve_criteria)) * 100 if sptve_criteria else 0
        
        # SNED L: has disability
        if disability_status:
            scores['SNED L'] = 100
        
        # OHSP: working student
        if working_status:
            scores['OHSP'] = 100
        
        # REGULAR: average student, not studious, not smart/active
        regular_criteria = [
            not characteristics.get('studious', True),
            not characteristics.get('smart', True),
            not characteristics.get('active', True),
        ]
        if sum(regular_criteria) >= 2:
            scores['REGULAR'] = 80
        
        return scores
    
    def _parse_interests(self):
        """Extract student interests from survey data"""
        interests = []
        
        # Map survey fields to interests
        interest_fields = {
            'interested_science': 'science',
            'interested_math': 'math',
            'interested_english': 'english',
            'interested_technology': 'technology',
            'interested_arts': 'arts',
            'interested_foreign_language': 'foreign language',
            'interested_tourism': 'tourism',
            'interested_crafts': 'crafts',
        }
        
        for field, interest in interest_fields.items():
            if self.survey_data.get(field) in [True, 'Yes', 'yes', 'true', 'True']:
                interests.append(interest)
        
        # Also check the interested_program field
        interested_program = self.survey_data.get('interested_program', '').lower()
        if interested_program:
            interests.append(interested_program)
        
        return interests
    
    def _parse_characteristics(self):
        """Extract student characteristics from survey data"""
        characteristics = {}
        
        # Map survey fields to characteristics
        characteristic_fields = {
            'is_active': 'active',
            'is_studious': 'studious',
            'is_smart': 'smart',
            'is_creative': 'creative',
            'is_artistic': 'artistic',
            'potential_genius': 'active',  # Active means potential genius
        }
        
        for field, char in characteristic_fields.items():
            value = self.survey_data.get(field)
            characteristics[char] = value in [True, 'Yes', 'yes', 'true', 'True']
        
        return characteristics
    
    def _get_criteria_met(self, program_code, academic_score, non_academic_score):
        """Get list of criteria met for a program"""
        criteria_met = []
        
        if academic_score > 0:
            criteria_met.append('Academic Requirements')
        
        if non_academic_score > 0:
            criteria_met.append('Non-Academic/Survey Requirements')
        
        return criteria_met
    
    def _get_total_criteria(self, program_code):
        """Get total number of criteria for a program"""
        criteria_map = {
            'STE': 6,  # 3 academic + 3 non-academic
            'SPFL': 5,  # 2 academic + 3 non-academic
            'SPTVE': 5,  # 2 academic + 3 non-academic
            'SNED L': 2,  # 1 academic + 1 non-academic
            'OHSP': 2,  # 1 academic + 1 non-academic
            'REGULAR': 2,  # 1 academic + 1 non-academic
        }
        return criteria_map.get(program_code, 1)
    
    def _calculate_percentage_match(self, program_code, academic_score, non_academic_score):
        """Calculate percentage of criteria met"""
        if academic_score > 0 or non_academic_score > 0:
            return round((academic_score + non_academic_score) / 2)
        return 0
    
    def _get_special_checks(self, program_code):
        """Get special checks required for a program"""
        special_checks = []
        
        if program_code == 'STE':
            special_checks.append({
                'type': 'database_verification',
                'description': 'Verify student in Qualified_for_ste table for DOST exam',
                'required': True,
            })
        
        return special_checks
    
    def _rank_recommendations(self):
        """
        Rank recommendations based on percentage match
        Rank 1: Meets all key components (100%)
        Rank 2: Meets 80% of components
        Rank 3+: Follow accordingly
        """
        # Sort by overall score (descending)
        self.recommendations.sort(key=lambda x: x['overall_score'], reverse=True)
        
        # Assign ranks
        for i, rec in enumerate(self.recommendations, 1):
            rec['rank'] = i
            
            # Determine if this is a strong recommendation
            percentage = rec['percentage_match']
            if percentage == 100:
                rec['recommendation_level'] = 'Strong (Meets all criteria)'
            elif percentage >= 80:
                rec['recommendation_level'] = 'Good (Meets 80% of criteria)'
            elif percentage >= 50:
                rec['recommendation_level'] = 'Fair (Meets 50% of criteria)'
            else:
                rec['recommendation_level'] = 'Weak (Meets <50% criteria)'
    
    def check_ste_qualification(self):
        """
        Check if student is qualified for STE program
        Returns: (is_qualified: bool, record: Qualified_for_ste or None)
        """
        try:
            qualified_record = Qualified_for_ste.objects.get(student_lrn=self.student_lrn)
            is_qualified = qualified_record.status == 'qualified'
            return is_qualified, qualified_record
        except Qualified_for_ste.DoesNotExist:
            return False, None
    
    def get_recommendation_summary(self):
        """
        Get a summary of recommendations for display
        """
        if not self.recommendations:
            return {
                'status': 'no_recommendations',
                'message': 'Unable to generate recommendations. Please ensure all data is complete.',
                'recommendations': []
            }
        
        # Get top 3 recommendations
        top_recommendations = self.recommendations[:3]
        
        return {
            'status': 'success',
            'message': 'Program recommendations generated successfully.',
            'recommendations': top_recommendations,
            'total_recommendations': len(self.recommendations),
            'all_recommendations': self.recommendations,
        }


def _map_session_to_ml_features(academic_data: dict, survey_data: dict, student_data: dict) -> pd.DataFrame:
    """
    Map existing session dictionaries to ML feature columns expected by the
    TRAINING_ARC model. Uses reasonable defaults where data is not present.
    """
    academic_data = academic_data or {}
    survey_data = survey_data or {}
    student_data = student_data or {}

    # Helpers
    def _yes(val):
        return val in [True, 'Yes', 'yes', 'true', 'True', 1]
    
    def _safe_str(val):
        """Safely convert value to lowercase string, handling None and int"""
        if val is None or val == '':
            return ''
        return str(val).lower()

    enjoyed_subjects = set((survey_data.get('enjoyed_subjects') or []))
    enjoyed_activities = set((survey_data.get('enjoyed_activities') or []))
    difficulty_areas = set((survey_data.get('difficulty_areas') or []))

    # Gender mapping - safely handle both string and int values
    gender_raw = student_data.get('gender') or survey_data.get('gender')
    if isinstance(gender_raw, int):
        gender_val = gender_raw if gender_raw in [0, 1, 2] else 0
    else:
        gender_str = _safe_str(gender_raw)
        gender_map = {'male': 1, 'female': 0, 'other': 2}
        gender_val = gender_map.get(gender_str, 0)

    # Learning style/study hours mapping (basic buckets)
    ls_map = {
        'visual': 1, 'auditory': 2, 'reading': 3, 'kinesthetic': 4,
        'mixed': 5
    }
    learning_style_val = ls_map.get(_safe_str(survey_data.get('learning_style')), 5)

    sh_map = {
        'less than 1 hour': 1, '1-2 hours': 2, '3-4 hours': 3, '5+ hours': 4
    }
    study_hours_val = sh_map.get(_safe_str(survey_data.get('study_hours')), 2)

    # Schoolwork support person
    sp_map = {
        'parents': 1, 'siblings': 2, 'self': 3, 'teacher/tutor': 4
    }
    support_person_val = sp_map.get(_safe_str(survey_data.get('schoolwork_support')), 1)

    # Assignment completion & handling difficulty
    ac_map = {'always on time': 1, 'often on time': 2, 'rarely on time': 3}
    assignment_completion_val = ac_map.get(_safe_str(survey_data.get('assignments_on_time')), 2)

    hd_map = {'seek help': 1, 'try again': 2, 'give up': 3}
    handle_difficulty_val = hd_map.get(_safe_str(survey_data.get('handle_difficult_lessons')), 2)

    # Enjoyed subjects
    enjoy_math = 1 if 'Math' in enjoyed_subjects else 0
    enjoy_science = 1 if 'Science' in enjoyed_subjects else 0
    enjoy_english = 1 if 'English' in enjoyed_subjects else 0
    enjoy_filipino = 1 if 'Filipino' in enjoyed_subjects else 0
    enjoy_arpan = 1 if ('Araling Panlipunan' in enjoyed_subjects or 'ArPan' in enjoyed_subjects) else 0
    enjoy_mapeh = 1 if 'MAPEH' in enjoyed_subjects else 0
    enjoy_tle = 1 if ('TLE' in enjoyed_subjects or 'Edukasyon Pangkabuhayan' in enjoyed_subjects) else 0

    # Preferred program mapping
    pp_map = {'ste': 1, 'spfl': 2, 'sptve': 3, 'regular': 4, 'hetero': 5}
    preferred_program_val = pp_map.get(_safe_str(survey_data.get('interested_program')), 4)

    # Motivation level (simple heuristic)
    motivation_level_val = 3 if survey_data.get('program_motivation') else 2

    # Enjoyed activities
    enjoy_science_experiments = 1 if 'Science Experiments' in enjoyed_activities else 0
    enjoy_reading = 1 if 'Reading' in enjoyed_activities else 0
    enjoy_handson_activities = 1 if ('Hands-on Activities' in enjoyed_activities or 'TLE Activities' in enjoyed_activities) else 0
    enjoy_sports = 1 if 'Sports' in enjoyed_activities else 0
    enjoy_arts = 1 if 'Arts' in enjoyed_activities else 0
    enjoy_language_related_activities = 1 if ('Language Activities' in enjoyed_activities or 'Foreign Language' in enjoyed_subjects) else 0
    foreign_language_interest = 1 if ('Foreign Language' in enjoyed_subjects or _safe_str(survey_data.get('interested_program')) == 'spfl') else 0

    # Tech access
    da_map = {'none': 0, 'phone': 1, 'tablet': 2, 'computer': 3}
    device_availability_val = da_map.get(_safe_str(survey_data.get('device_availability')), 1)
    ia_map = {'none': 0, 'limited': 1, 'mobile data': 2, 'wifi': 3}
    internet_access_val = ia_map.get(_safe_str(survey_data.get('internet_access')), 1)

    # Attendance/responsibility
    try:
        absences_count_val = int((survey_data.get('absences') or '0').split()[0])
    except Exception:
        absences_count_val = 1
    absence_reason_val = 1 if survey_data.get('absence_reason') else 0

    # Participation
    school_participation_val = 1 if _yes(survey_data.get('participation')) else 0

    # Awards (not captured; default to 0 unless survey mentions)
    received_awards = 1 if 'Awards' in enjoyed_activities else 0
    award_highest_honors = 0
    award_high_honors = 0
    award_with_honors = 0
    award_best_science = 0
    award_best_math = 0
    award_best_english = 0
    award_conduct = 0
    achiever_award = 0

    # Difficulties
    difficulty_reading = 1 if 'Reading' in difficulty_areas else 0
    difficulty_writing = 1 if 'Writing' in difficulty_areas else 0
    difficulty_math = 1 if ('Math' in difficulty_areas or 'Mathematics' in difficulty_areas) else 0
    difficulty_focusing = 1 if 'Focusing' in difficulty_areas else 0
    difficulty_social_interaction = 1 if ('Social Interaction' in difficulty_areas or 'Social' in difficulty_areas) else 0

    extra_support_recommended = 1 if _yes(survey_data.get('extra_support')) else 0

    # Environment
    quiet_study_place = 1 if _yes(survey_data.get('quiet_place')) else 0
    distance_from_school = 1  # Simplify to near
    travel_difficulty = 1 if _yes(survey_data.get('travel_difficulty')) else 0

    # Compute age from date_of_birth if available
    age_val = None
    dob = student_data.get('date_of_birth')
    if dob:
        try:
            from datetime import date
            today = date.today()
            age_val = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except Exception:
            age_val = survey_data.get('age') or 12
    else:
        age_val = survey_data.get('age') or 12

    # Map grades
    def _num(val):
        try:
            return float(val) if val is not None and val != '' else None
        except Exception:
            return None

    grade_math = _num(academic_data.get('mathematics'))
    grade_science = _num(academic_data.get('science'))
    grade_english = _num(academic_data.get('english'))
    grade_filipino = _num(academic_data.get('filipino'))
    grade_arpan = _num(academic_data.get('araling_panlipunan'))
    grade_mapeh = _num(academic_data.get('mapeh'))
    average_grade_tle = _num(academic_data.get('edukasyon_pangkabuhayan'))
    grade_esp = _num(academic_data.get('edukasyon_sa_pagpapakatao'))
    grade_6_final_average = academic_data.get('overall_average') or 0

    # Build single-row dataframe
    row = {
        'age': age_val,
        'gender': gender_val,
        'learning_style': learning_style_val,
        'study_hours_daily': study_hours_val,
        'support_person': support_person_val,
        'assignment_completion': assignment_completion_val,
        'handle_difficulty': handle_difficulty_val,
        'enjoy_math': enjoy_math,
        'enjoy_science': enjoy_science,
        'enjoy_english': enjoy_english,
        'enjoy_filipino': enjoy_filipino,
        'enjoy_arpan': enjoy_arpan,
        'enjoy_mapeh': enjoy_mapeh,
        'enjoy_tle': enjoy_tle,
        'preferred_program': preferred_program_val,
        'motivation_level': motivation_level_val,
        'enjoy_science_experiments': enjoy_science_experiments,
        'enjoy_reading': enjoy_reading,
        'enjoy_handson_activities': enjoy_handson_activities,
        'enjoy_sports': enjoy_sports,
        'enjoy_arts': enjoy_arts,
        'enjoy_language_related_activities': enjoy_language_related_activities,
        'foreign_language_interest': foreign_language_interest,
        'competition_participation': 0,
        'device_availability': device_availability_val,
        'internet_access': internet_access_val,
        'absences_count': absences_count_val,
        'absence_reason': absence_reason_val,
        'family_income_help': 1,
        'school_participation': school_participation_val,
        'received_awards': received_awards,
        'award_highest_honors': award_highest_honors,
        'award_high_honors': award_high_honors,
        'award_with_honors': award_with_honors,
        'award_best_science': award_best_science,
        'award_best_math': award_best_math,
        'award_best_english': award_best_english,
        'award_conduct': award_conduct,
        'achiever_award': achiever_award,
        'difficulty_reading': difficulty_reading,
        'difficulty_writing': difficulty_writing,
        'difficulty_math': difficulty_math,
        'difficulty_focusing': difficulty_focusing,
        'difficulty_social_interaction': difficulty_social_interaction,
        'extra_support_recommended': extra_support_recommended,
        'quiet_study_place': quiet_study_place,
        'distance_from_school': distance_from_school,
        'travel_difficulty': travel_difficulty,
        'grade_math': grade_math,
        'grade_science': grade_science,
        'grade_english': grade_english,
        'grade_filipino': grade_filipino,
        'grade_arpan': grade_arpan,
        'grade_mapeh': grade_mapeh,
        'average_grade_tle': average_grade_tle,
        'grade_esp': grade_esp,
        'grade_6_final_average': grade_6_final_average,
    }

    return pd.DataFrame([row])


def _apply_special_program_inclusion(result: dict, is_working_student: bool, is_pwd: bool):
    """
    Apply special inclusion rules:
    - If student is a working student → ensure OHSP is in recommendations
    - If student is PWD/SPED → ensure SNED L is in recommendations
    
    These programs are added at the top of the list when applicable.
    """
    recommendations = result.get('recommendations', [])
    existing_codes = {rec['program_code'] for rec in recommendations}
    
    special_additions = []
    
    # Add OHSP if working student and not already present
    if is_working_student and 'OHSP' not in existing_codes:
        special_additions.append({
            'rank': 0,  # Will be adjusted after insertion
            'program_code': 'OHSP',
            'program_name': 'Out-of-School Youth Program',
            'percentage_match': 100,
            'recommendation_level': 'Strong (Working Student - Auto-included)',
            'criteria_met': ['Working Student Status'],
            'special_checks': [],
        })
    
    # Add SNED L if PWD and not already present
    if is_pwd and 'SNED L' not in existing_codes:
        special_additions.append({
            'rank': 0,  # Will be adjusted after insertion
            'program_code': 'SNED L',
            'program_name': 'Special Needs Education Program',
            'percentage_match': 100,
            'recommendation_level': 'Strong (PWD/SPED - Auto-included)',
            'criteria_met': ['PWD/SPED Status'],
            'special_checks': [],
        })
    
    # Insert special programs at the top of the list
    if special_additions:
        recommendations = special_additions + recommendations
        
        # Re-rank all recommendations
        for idx, rec in enumerate(recommendations, 1):
            rec['rank'] = idx
        
        result['recommendations'] = recommendations
        result['total_recommendations'] = len(recommendations)
        result['all_recommendations'] = recommendations
        
        # Update message to indicate special inclusion
        programs_added = [prog['program_code'] for prog in special_additions]
        result['message'] = f"Program recommendations generated. Auto-included: {', '.join(programs_added)} based on student status."
    
    return result


def _filter_by_highest_program_rule(ml_results: list, average_grade: float = 0) -> list:
    """
    Apply program visibility filtering based on highest probability rule.

    Rules:
    1. If the HIGHEST probability program is REGULAR (Top-5 Regular or Hetero),
       hide ALL specialized programs (STE, SPFL, SPTVE)
       EXCEPTION: If student's average grade >= 85, also include the top
       specialized program (highest probability among STE/SPFL/SPTVE)
    2. If the HIGHEST probability program is a specialized program (STE, SPFL, SPTVE),
       show ALL programs
    3. OHSP and SNED L are ALWAYS shown (exempt from this rule)
    4. For REGULAR sub-tracks:
       - Hetero is ALWAYS shown (default track for average students)
       - Top-5 Regular is only shown if probability >= 15% (for qualified students)

    Args:
        ml_results: List of ML recommendations with 'placement' and 'probability' keys
        average_grade: Student's overall average grade

    Returns:
        Filtered list of recommendations
    """
    if not ml_results:
        return ml_results

    # Define program categories
    REGULAR_TRACKS = {'Top-5 Regular', 'Hetero'}
    SPECIALIZED_PROGRAMS = {'STE', 'SPFL', 'SPTVE'}
    EXEMPT_PROGRAMS = {'OHSP', 'SNED L'}  # Always shown
    TOP5_MIN_THRESHOLD = 0.15  # 15% minimum probability to show Top-5
    GRADE_THRESHOLD_FOR_SPECIALIZED = 85  # Show top specialized program if avg >= this

    # Find the highest probability program
    highest_program = max(ml_results, key=lambda x: x.get('probability', 0))
    highest_placement = highest_program.get('placement', '')

    # If highest is a REGULAR track, filter out specialized programs
    if highest_placement in REGULAR_TRACKS:
        # If average grade >= 85, find the top specialized program to include
        top_specialized_placement = None
        if average_grade >= GRADE_THRESHOLD_FOR_SPECIALIZED:
            specialized_recs = [
                r for r in ml_results if r.get('placement', '') in SPECIALIZED_PROGRAMS
            ]
            if specialized_recs:
                top_specialized = max(specialized_recs, key=lambda x: x.get('probability', 0))
                top_specialized_placement = top_specialized.get('placement', '')

        filtered_results = []
        for rec in ml_results:
            placement = rec.get('placement', '')
            probability = rec.get('probability', 0)

            # Skip specialized programs EXCEPT the top one when avg >= 85
            if placement in SPECIALIZED_PROGRAMS:
                if placement == top_specialized_placement:
                    filtered_results.append(rec)
                continue

            # For Top-5 Regular: only show if probability >= 15%
            if placement == 'Top-5 Regular' and probability < TOP5_MIN_THRESHOLD:
                continue

            # Hetero is always shown, exempt programs always shown
            filtered_results.append(rec)

        return filtered_results

    # If highest is a specialized program or anything else, show all
    return ml_results


def _format_ml_recommendations(ml_results: list, student_lrn: str, detailed_breakdown=None, student_features=None):
    """
    Convert PlacementRecommender results to the existing UI-friendly structure.
    Maps ML placement names back to the system's program codes with regular_track for REGULAR variants.
    
    Args:
        ml_results: List of ML recommendation dicts from recommender
        student_lrn: Student LRN
        detailed_breakdown: Optional dict with stage1/stage2 scores and contributing factors
        student_features: Optional DataFrame with student features
    """
    formatted = []
    code_map = {
        'STE': ('STE', 'Science, Technology, Engineering', None),
        'SPFL': ('SPFL', 'Special Program in Foreign Language', None),
        'SPTVE': ('SPTVE', 'Special Program in Technical Vocational Education', None),
        'Top-5 Regular': ('REGULAR', 'Regular Program - Top 5', 'TOP5'),
        'Hetero': ('REGULAR', 'Regular Program - Hetero', 'HETERO'),
    }

    for idx, rec in enumerate(ml_results, 1):
        placement = rec['placement']
        prob = rec['probability']  # 0..1
        
        # Map placement to program_code, program_name, and optional regular_track
        if placement in code_map:
            code, name, track = code_map[placement]
        else:
            code, name, track = placement, placement, None

        # Recommendation level bucketing similar to rule-based
        pct = int(round(prob * 100))
        if pct >= 90:
            level = 'Strong (High ML match)'
        elif pct >= 70:
            level = 'Good (ML match)'
        elif pct >= 50:
            level = 'Fair (ML match)'
        else:
            level = 'Weak (ML match)'

        special_checks = []
        if code == 'STE':
            special_checks.append({
                'type': 'database_verification',
                'description': 'Verify student in Qualified_for_ste table for DOST exam',
                'required': True,
            })

        recommendation = {
            'rank': idx,
            'program_code': code,
            'program_name': name,
            'percentage_match': pct,
            'recommendation_level': level,
            'criteria_met': ['ML Probability-Based Recommendation'],
            'special_checks': special_checks,
        }
        
        # Add regular_track if this is a REGULAR variant (TOP5/HETERO)
        if track:
            recommendation['regular_track'] = track

        # Add detailed breakdown if available
        if detailed_breakdown:
            recommendation['breakdown'] = {
                'stage1_all_programs': detailed_breakdown.get('stage1_all_programs', []),
                'stage2_all_programs': detailed_breakdown.get('stage2_all_programs', []),
                'top_factors': detailed_breakdown.get('top_factors', [])
            }

        formatted.append(recommendation)

    # DEBUG: Log stage1 Ridge predictions
    if detailed_breakdown:
        s1 = detailed_breakdown.get('stage1_all_programs', [])
        s2 = detailed_breakdown.get('stage2_all_programs', [])
        if s1:
            print("DEBUG [_format_ml_recommendations]: ── Stage 1 (Ridge) Predicted G7 Q1 Average ──")
            for p in s1:
                print(f"  {p['program_name']:<25} predicted_avg = {p['predicted_average']:.2f}")
        if s2:
            print("DEBUG [_format_ml_recommendations]: ── Stage 2 (XGBoost) Confidence Scores ──")
            for p in s2:
                marker = ' ◄ TOP' if p == s2[0] else ''
                print(f"  {p['program_name']:<25} confidence = {p['confidence_pct']:>3}%  ({p['confidence']:.4f}){marker}")

    # Build lookup dicts for per-recommendation detail
    _s1_lookup = {}
    _s2_lookup = {}
    if detailed_breakdown:
        for p in detailed_breakdown.get('stage1_all_programs', []):
            _s1_lookup[p['program_name']] = p['predicted_average']
        for p in detailed_breakdown.get('stage2_all_programs', []):
            _s2_lookup[p['program_name']] = (p['confidence_pct'], p['confidence'])

    print(f"DEBUG [_format_ml_recommendations]: Returning {len(formatted)} recommendations:")
    for rec in formatted:
        code = rec.get('program_code')
        track = rec.get('regular_track')
        match = rec.get('percentage_match')

        # Find matching program name for lookup
        if code == 'REGULAR' and track == 'TOP5':
            prog_key = 'Top-5 Regular'
        elif code == 'REGULAR':
            prog_key = 'Hetero'
        else:
            prog_key = code

        pred_avg = _s1_lookup.get(prog_key)
        conf_info = _s2_lookup.get(prog_key)
        pred_str = f"ridge_pred={pred_avg:.2f}" if pred_avg is not None else "ridge_pred=N/A"
        conf_str = f"xgb_conf={conf_info[0]}% ({conf_info[1]:.4f})" if conf_info else "xgb_conf=N/A"

        print(f"  #{rec.get('rank')} {code} (track={track}): match={match}% | {pred_str} | {conf_str}")

    return {
        'status': 'success',
        'message': 'ML-based program recommendations generated successfully.',
        'recommendations': formatted,
        'total_recommendations': len(formatted),
        'all_recommendations': formatted,
        'breakdown': detailed_breakdown,
    }


def generate_academic_recommendations(student_lrn, academic_data, survey_data, student_data):
    """
    Generate recommendations using ML model when available; otherwise fallback
    to the existing rule-based engine.
    
    Special rules:
    - If student is a working student → automatically include OHSP
    - If student is PWD/SPED → automatically include SNED L
    """
    # Check for special conditions
    is_working_student = student_data.get('is_working_student', False)
    is_pwd = student_data.get('is_sped', False)
    
    result = None
    
    # Attempt ML first if available
    if _ML_AVAILABLE and HybridPlacementRecommender is not None:
        try:
            recommender = HybridPlacementRecommender(model_path=str(settings.BASE_DIR / 'TRAINING_ARC' / 'models' / 'hybrid'))
            if recommender.load_model():
                print(f"[RECOMMENDATION_SERVICE] ✓ HYBRID MODEL LOADED (Ridge + XGBoost)")
                features_df = _map_session_to_ml_features(academic_data, survey_data, student_data)

                # Print mapped input features
                print("[RECOMMENDATION_SERVICE] ── Input Features ──")
                for col in features_df.columns:
                    val = features_df[col].iloc[0]
                    print(f"  {col:<40} = {val}")

                ml_results = recommender.recommend(features_df, top_n=5)

                # Print raw ML results (before any filtering)
                print("[RECOMMENDATION_SERVICE] ── Raw ML Results (before filter) ──")
                for r in ml_results:
                    print(f"  {r['placement']:<25} probability={r['probability']:.4f}  ({int(round(r['probability']*100))}%)")

                # Apply program visibility filtering rule:
                # If REGULAR is highest probability, hide specialized programs
                # (but show top specialized if average grade >= 85)
                avg_grade = float(academic_data.get('overall_average', 0) or 0)
                ml_results = _filter_by_highest_program_rule(ml_results, avg_grade)

                # Print filtered ML results
                print(f"[RECOMMENDATION_SERVICE] ── After Filter (overall_avg={avg_grade}) ──")
                for r in ml_results:
                    print(f"  {r['placement']:<25} probability={r['probability']:.4f}  ({int(round(r['probability']*100))}%)")

                # Get detailed breakdown for explainability
                detailed_breakdown = recommender.get_detailed_explanation(features_df)

                result = _format_ml_recommendations(ml_results, student_lrn, detailed_breakdown, features_df)
        except Exception as e:
            # Log and fallback silently
            print(f"[RECOMMENDATION_SERVICE] ✗ ML recommendation failed, falling back to rules: {e}")

    # Fallback to rule-based engine if ML failed
    if result is None:
        engine = ProgramRecommendationEngine(
            student_lrn=student_lrn,
            academic_data=academic_data,
            survey_data=survey_data,
            student_data=student_data
        )
        engine.generate_recommendations()
        result = engine.get_recommendation_summary()
    
    # Apply special inclusion rules
    if result and result.get('status') == 'success':
        result = _apply_special_program_inclusion(result, is_working_student, is_pwd)
    
    return result