"""
Program Recommendation Service
Handles program recommendations based on academic and non-academic data
following the defined business rules
"""

from coordinator_app.models import Qualified_for_ste


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


def generate_academic_recommendations(student_lrn, academic_data, survey_data, student_data):
    """
    Main function to generate recommendations
    
    Args:
        student_lrn: Student's LRN
        academic_data: Academic data dictionary
        survey_data: Survey/non-academic data dictionary
        student_data: Student data dictionary
    
    Returns:
        Dictionary with recommendations
    """
    engine = ProgramRecommendationEngine(
        student_lrn=student_lrn,
        academic_data=academic_data,
        survey_data=survey_data,
        student_data=student_data
    )
    
    engine.generate_recommendations()
    return engine.get_recommendation_summary()
