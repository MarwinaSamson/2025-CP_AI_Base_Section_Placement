"""
================================================================================
SPARK SYSTEM — Student Prediction & Program Recommendation
Gradient Boosting Algorithm | Interactive Testing Script
================================================================================

HOW TO USE:
    1. Run GBR_training.py first — it saves trained models to gbr_models/.
    2. Run this script:  python3 GBR_predict.py
    3. Answer each prompt to enter a new student's data.
    4. The system will:
        - Check STE eligibility (Grade 6 Math, Science, English ≥ 83)
        - Loop through all 5 programs and predict Grade 7 grades using
          Gradient Boosting regression
        - Apply suitability thresholds (≥85 special, ≥75 HETERO)
        - Recommend Top 3 programs with scores and margin analysis
        - Compare against the student's preferred program
        - Generate a visual PNG report saved to disk

ALGORITHM: Gradient Boosting (XGBoost/LightGBM equivalent via sklearn)
    - Each program prediction uses a separate GBR model trained in GBR_training.py
    - Program recommendation uses a GradientBoostingClassifier
    - Both models use the same feature set as the RF baseline (RF_predict.py)
    - Predictions are clamped to [60, 100] — the valid grade range

REQUIREMENTS:
    - gbr_models/ folder must exist (created by GBR_training.py)
    - Libraries: pandas, numpy, matplotlib, joblib, scikit-learn
================================================================================
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')    # Non-interactive backend — safe for all environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# SECTION 1: LOAD TRAINED MODELS AND CONFIG
# ==============================================================================

MODELS_DIR = 'gbr_models'

def load_models():
    """
    Load all trained Gradient Boosting models and shared config from disk.
    Exits with a clear error message if GBR_training.py has not been run yet.
    """
    required = [
        'config.pkl', 'classifier.pkl',
        'regression_STE.pkl', 'regression_SPFL.pkl',
        'regression_SPTVE.pkl', 'regression_TOP-5.pkl',
        'regression_HETERO.pkl'
    ]
    for f in required:
        if not os.path.exists(os.path.join(MODELS_DIR, f)):
            print(f"\n  ❌ ERROR: '{MODELS_DIR}/{f}' not found.")
            print("     Please run GBR_training.py first to train and save models.")
            sys.exit(1)

    config     = joblib.load(f'{MODELS_DIR}/config.pkl')
    classifier = joblib.load(f'{MODELS_DIR}/classifier.pkl')
    regressors = {}
    for p, name in config['PROGRAM_MAP'].items():
        fname          = f'{MODELS_DIR}/regression_{name}.pkl'
        regressors[p]  = joblib.load(fname)

    return config, classifier, regressors

# ==============================================================================
# SECTION 2: INPUT QUESTION DEFINITIONS
# (Identical to RF_predict.py — same questions, same order, same encoding)
# ==============================================================================

def build_questions():
    """
    Returns ordered list of all input questions.
    Format: (key, display_label, input_type, valid_values_or_range, hint)

    input_type:
        'int'    — integer within numeric range
        'float'  — decimal within numeric range
        'choice' — must pick from option dict
        'yesno'  — enter 1 (Yes) or 0 (No)
        'text'   — free text (student name only)
    """
    questions = [
        # ── BASIC INFO ────────────────────────────────────────────────────────
        ('student_name', 'Student Name', 'text',   None,     'Full name'),
        ('age',          'Age',          'int',     (11, 18), 'Typical range: 11-13 for Grade 7'),
        ('gender', 'Gender', 'choice', {
            0: 'Male',
            1: 'Female'
        }, ''),

        # ── GRADE 6 ACADEMIC GRADES ───────────────────────────────────────────
        ('grade_math',        'Grade 6 — Mathematics',        'float', (60, 100), 'Numerical grade'),
        ('grade_science',     'Grade 6 — Science',            'float', (60, 100), 'Numerical grade'),
        ('grade_english',     'Grade 6 — English',            'float', (60, 100), 'Numerical grade'),
        ('grade_filipino',    'Grade 6 — Filipino',           'float', (60, 100), 'Numerical grade'),
        ('grade_arpan',       'Grade 6 — Araling Panlipunan', 'float', (60, 100), 'Numerical grade'),
        ('grade_mapeh',       'Grade 6 — MAPEH',              'float', (60, 100), 'Numerical grade'),
        ('average_grade_tle', 'Grade 6 — TLE',                'float', (60, 100), 'Numerical grade'),
        ('grade_esp',         'Grade 6 — ESP',                'float', (60, 100), 'Numerical grade'),

        # ── PREFERRED PROGRAM ─────────────────────────────────────────────────
        ('preferred_program', 'Preferred Program', 'choice', {
            1: 'STE   (Science, Technology & Engineering)',
            2: 'SPFL  (Special Program in Foreign Language)',
            3: 'SPTVE (Special Program in Tech-Voc Education)',
            4: 'TOP-5 Regular Section',
            5: 'HETERO (Regular Section)',
            6: 'OHSP / SNEd (not in system scope)'
        }, "Student's preferred program"),

        # ── NON-ACADEMIC — LEARNING PROFILE ──────────────────────────────────
        ('learning_style', 'Learning Style', 'choice', {
            1: 'Visual   (learns best through images/charts)',
            2: 'Auditory (learns best through listening)',
            3: 'Reading/Writing (learns best through text)',
            4: 'Kinesthetic (learns best through hands-on)',
            5: 'Mixed'
        }, ''),
        ('study_hours_daily', 'Study Hours Per Day', 'choice', {
            1: 'Less than 1 hour',
            2: '1-2 hours',
            3: '2-3 hours',
            4: 'More than 3 hours'
        }, ''),
        ('motivation_level', 'Motivation Level', 'choice', {
            1: 'Low',
            2: 'Average',
            3: 'High'
        }, ''),
        ('assignment_completion', 'Assignment Completion Rate', 'choice', {
            1: 'Rarely completes',
            2: 'Sometimes completes',
            3: 'Usually completes',
            4: 'Always completes'
        }, ''),
        ('handle_difficulty', 'How does the student handle difficulty?', 'choice', {
            1: 'Gives up easily',
            2: 'Needs encouragement',
            3: 'Tries independently',
            4: 'Seeks help and persists'
        }, ''),

        # ── NON-ACADEMIC — SUPPORT & BACKGROUND ──────────────────────────────
        ('support_person', 'Who supports the student at home?', 'choice', {
            1: 'Parent/Guardian',
            2: 'Sibling',
            3: 'Tutor',
            4: 'Friend',
            5: 'No support'
        }, ''),
        ('family_income_help', 'Family Income Level', 'choice', {
            1: 'Low',
            2: 'Middle',
            3: 'High'
        }, ''),
        ('device_availability', 'Device Availability for Studies', 'choice', {
            1: 'No device',
            2: 'Shared device',
            3: 'Personal device'
        }, ''),
        ('internet_access', 'Internet Access', 'choice', {
            1: 'No internet',
            2: 'Occasional access',
            3: 'Stable internet'
        }, ''),
        ('distance_from_school', 'Distance from School', 'choice', {
            1: 'Very near (walking distance)',
            2: 'Near (short ride)',
            3: 'Far (long commute)',
            4: 'Very far'
        }, ''),
        ('travel_difficulty', 'Difficulty Traveling to School', 'choice', {
            1: 'No difficulty',
            2: 'Sometimes difficult',
            3: 'Very difficult'
        }, ''),
        ('absences_count', 'Absences in Grade 6', 'choice', {
            1: '0-5 days',
            2: '6-10 days',
            3: '11-15 days',
            4: 'More than 15 days'
        }, ''),
        ('absence_reason', 'Primary Reason for Absences', 'choice', {
            1: 'Illness',
            2: 'Family matters',
            3: 'Work/helping family',
            4: 'Distance/transportation',
            5: 'No absences / not applicable'
        }, ''),

        # ── NON-ACADEMIC — INTERESTS ──────────────────────────────────────────
        ('enjoy_math',                        'Enjoys Mathematics?',                    'yesno', None, ''),
        ('enjoy_science',                     'Enjoys Science?',                        'yesno', None, ''),
        ('enjoy_english',                     'Enjoys English?',                        'yesno', None, ''),
        ('enjoy_filipino',                    'Enjoys Filipino?',                       'yesno', None, ''),
        ('enjoy_arpan',                       'Enjoys Araling Panlipunan?',             'yesno', None, ''),
        ('enjoy_mapeh',                       'Enjoys MAPEH?',                          'yesno', None, ''),
        ('enjoy_tle',                         'Enjoys TLE?',                            'yesno', None, ''),
        ('enjoy_science_experiments',         'Enjoys Science Experiments?',            'yesno', None, ''),
        ('enjoy_reading',                     'Enjoys Reading?',                        'yesno', None, ''),
        ('enjoy_handson_activities',          'Enjoys Hands-on Activities?',            'yesno', None, ''),
        ('enjoy_sports',                      'Enjoys Sports?',                         'yesno', None, ''),
        ('enjoy_arts',                        'Enjoys Arts?',                           'yesno', None, ''),
        ('enjoy_language_related_activities', 'Enjoys Language-related Activities?',    'yesno', None, ''),
        ('foreign_language_interest', 'Interest in Learning Foreign Language', 'choice', {
            1: 'Very Interested',
            2: 'Somewhat Interested',
            3: 'Not Interested'
        }, ''),

        # ── NON-ACADEMIC — PARTICIPATION & AWARDS ────────────────────────────
        ('school_participation', 'School Participation Level', 'choice', {
            1: 'Low',
            2: 'Average',
            3: 'Active'
        }, ''),
        ('competition_participation', 'Participated in Competitions?',   'yesno', None, ''),
        ('received_awards',           'Received any Awards in Grade 6?', 'yesno', None, ''),
        ('award_highest_honors',      'Award: Highest Honors?',          'yesno', None, ''),
        ('award_high_honors',         'Award: High Honors?',             'yesno', None, ''),
        ('award_with_honors',         'Award: With Honors?',             'yesno', None, ''),
        ('award_best_science',        'Award: Best in Science?',         'yesno', None, ''),
        ('award_best_math',           'Award: Best in Math?',            'yesno', None, ''),
        ('award_best_english',        'Award: Best in English?',         'yesno', None, ''),
        ('award_conduct',             'Award: Best in Conduct?',         'yesno', None, ''),
        ('achiever_award',            'Award: Achiever Award?',          'yesno', None, ''),

        # ── NON-ACADEMIC — DIFFICULTIES ──────────────────────────────────────
        ('difficulty_reading',            'Has difficulty in Reading?',              'yesno', None, ''),
        ('difficulty_writing',            'Has difficulty in Writing?',              'yesno', None, ''),
        ('difficulty_math',               'Has difficulty in Math?',                 'yesno', None, ''),
        ('difficulty_focusing',           'Has difficulty Focusing in class?',       'yesno', None, ''),
        ('difficulty_social_interaction', 'Has difficulty with Social Interaction?', 'yesno', None, ''),
        ('extra_support_recommended',     'Was extra support recommended?',          'yesno', None, ''),
        ('quiet_study_place', 'Has a quiet place to study at home?', 'choice', {
            0: 'No quiet place',
            1: 'Sometimes quiet',
            2: 'Usually quiet',
            3: 'Always quiet'
        }, ''),
    ]
    return questions

# ==============================================================================
# SECTION 3: INPUT COLLECTION
# (Identical helper functions to RF_predict.py)
# ==============================================================================

def section_header(title):
    print(f"\n  {'─' * 60}")
    print(f"  {title}")
    print(f"  {'─' * 60}")

def ask_yesno(label):
    while True:
        ans = input(f"  {label} [1=Yes / 0=No]: ").strip()
        if ans in ['0', '1']:
            return int(ans)
        print("     ⚠  Please enter 1 (Yes) or 0 (No).")

def ask_choice(label, options):
    print(f"  {label}:")
    for k, v in options.items():
        print(f"      {k} — {v}")
    valid = [str(k) for k in options.keys()]
    while True:
        ans = input(f"     Enter choice ({'/'.join(valid)}): ").strip()
        if ans in valid:
            return int(ans)
        print(f"     ⚠  Please choose from: {', '.join(valid)}")

def ask_float(label, lo, hi):
    while True:
        ans = input(f"  {label} ({lo}–{hi}): ").strip()
        try:
            val = float(ans)
            if lo <= val <= hi:
                return val
            print(f"     ⚠  Please enter a value between {lo} and {hi}.")
        except ValueError:
            print("     ⚠  Please enter a valid number.")

def ask_int(label, lo, hi):
    while True:
        ans = input(f"  {label} ({lo}–{hi}): ").strip()
        try:
            val = int(ans)
            if lo <= val <= hi:
                return val
            print(f"     ⚠  Please enter a whole number between {lo} and {hi}.")
        except ValueError:
            print("     ⚠  Please enter a whole number.")

def ask_text(label):
    while True:
        ans = input(f"  {label}: ").strip()
        if ans:
            return ans
        print("     ⚠  This field cannot be empty.")

def collect_student_data():
    """
    Walk the user through all input questions grouped by section.
    Returns a dict of {feature_name: value} plus student_name.
    Identical question set to RF_predict.py — ensures comparable input.
    """
    print("\n" + "=" * 66)
    print("  SPARK SYSTEM — New Student Data Entry")
    print("  Algorithm: Gradient Boosting")
    print("  Answer each question. Type the number for choice questions.")
    print("=" * 66)

    questions    = build_questions()
    student_data = {}

    sections = {
        'student_name':         '📋  BASIC INFORMATION',
        'grade_math':           '📚  GRADE 6 ACADEMIC GRADES',
        'preferred_program':    '🎯  PREFERRED PROGRAM',
        'learning_style':       '🧠  LEARNING PROFILE',
        'support_person':       '🏠  BACKGROUND & SUPPORT',
        'enjoy_math':           '💡  INTERESTS & ENJOYMENT',
        'school_participation': '🏆  PARTICIPATION & AWARDS',
        'difficulty_reading':   '⚠️   LEARNING DIFFICULTIES',
    }

    for (key, label, qtype, valid, hint) in questions:
        if key in sections:
            section_header(sections[key])

        if   qtype == 'text':
            student_data[key] = ask_text(label)
        elif qtype == 'yesno':
            student_data[key] = ask_yesno(label)
        elif qtype == 'choice':
            student_data[key] = ask_choice(label, valid)
        elif qtype == 'float':
            lo, hi = valid
            student_data[key] = ask_float(label, lo, hi)
        elif qtype == 'int':
            lo, hi = valid
            student_data[key] = ask_int(label, lo, hi)

    return student_data

# ==============================================================================
# SECTION 4: COMPUTE GRADE 6 FINAL AVERAGE
# ==============================================================================

def compute_g6_average(data):
    """Compute Grade 6 final average from the 8 subject grades."""
    g6_cols = [
        'grade_math', 'grade_science', 'grade_english', 'grade_filipino',
        'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp'
    ]
    return round(np.mean([data[c] for c in g6_cols]), 3)

# ==============================================================================
# SECTION 5: GRADIENT BOOSTING PREDICTION ENGINE
# ==============================================================================

def predict_for_student(student_data, config, classifier, regressors):
    """
    Runs the 5-loop Gradient Boosting prediction for one student.
    Returns a results dict with predicted grades, suitability, and
    the classifier recommendation — in the same format as RF_predict.py.

    KEY DIFFERENCE FROM RF:
        Gradient Boosting regression models may produce slightly different
        predicted averages due to their sequential (vs parallel) tree building.
        The suitability logic, Top 3 ranking, and STE eligibility check are
        IDENTICAL to the RF pipeline — enabling direct comparison.
    """
    PROGRAM_MAP               = config['PROGRAM_MAP']
    FEATURES                  = config['FEATURES']
    SUITABILITY_THRESHOLD     = config['SUITABILITY_THRESHOLD']
    STE_ELIGIBILITY_SUBJECTS  = config['STE_ELIGIBILITY_SUBJECTS']
    STE_ELIGIBILITY_MIN_GRADE = config['STE_ELIGIBILITY_MIN_GRADE']
    clf_features              = config['clf_features']

    # ── Build feature vector ────────────────────────────────────────────────
    student_data['grade_6_final_average'] = compute_g6_average(student_data)
    student_data['has_valid_preference']  = (
        1 if student_data.get('preferred_program', 6) in [1, 2, 3, 4, 5] else 0
    )

    feat_row   = {f: student_data.get(f, 0) for f in FEATURES}
    X_student  = pd.DataFrame([feat_row])

    # ── STE Eligibility Pre-check ───────────────────────────────────────────
    ste_eligible = all(
        student_data.get(subj, 0) >= STE_ELIGIBILITY_MIN_GRADE
        for subj in STE_ELIGIBILITY_SUBJECTS
    )
    ste_failed_subjects = [
        f"{s.replace('grade_','').upper()} "
        f"({student_data.get(s,0):.0f} < {STE_ELIGIBILITY_MIN_GRADE})"
        for s in STE_ELIGIBILITY_SUBJECTS
        if student_data.get(s, 0) < STE_ELIGIBILITY_MIN_GRADE
    ]

    # ── 5-LOOP: Gradient Boosting Grade Prediction per Program ──────────────
    program_results   = {}
    pred_avgs_for_clf = {}

    for p, name in PROGRAM_MAP.items():
        reg_data  = regressors[p]
        gbr_model = reg_data['model']
        imputer   = reg_data['imputer']
        subjects  = reg_data['subjects']

        # Impute then predict
        X_imputed           = imputer.transform(X_student[FEATURES])
        predicted_final_avg = float(gbr_model.predict(X_imputed)[0])
        # Clamp to valid grade range [60, 100]
        predicted_final_avg = round(min(max(predicted_final_avg, 60), 100), 2)

        # Estimate per-subject grades (same approximation as RF_predict.py)
        subject_preds = {subj: round(predicted_final_avg, 2) for subj in subjects}

        # Suitability check
        grade_threshold_met = predicted_final_avg >= SUITABILITY_THRESHOLD[p]
        if p == 1:   # STE: grade threshold + G6 eligibility
            is_suitable = grade_threshold_met and ste_eligible
        else:
            is_suitable = grade_threshold_met

        margin = round(predicted_final_avg - SUITABILITY_THRESHOLD[p], 2)

        program_results[p] = {
            'name':          name,
            'predicted_avg': predicted_final_avg,
            'subject_preds': subject_preds,
            'subjects':      subjects,
            'threshold':     SUITABILITY_THRESHOLD[p],
            'grade_ok':      grade_threshold_met,
            'is_suitable':   is_suitable,
            'margin':        margin,
        }
        pred_avgs_for_clf[f'pred_avg_{name}'] = predicted_final_avg

    # ── Gradient Boosting Classification: Program Recommendation ────────────
    clf_model   = classifier['model']
    clf_imputer = classifier['imputer']

    clf_row = {f: student_data.get(f, 0) for f in FEATURES}
    clf_row.update(pred_avgs_for_clf)

    X_clf      = pd.DataFrame([[clf_row.get(f, 0) for f in clf_features]],
                              columns=clf_features)
    X_clf_imp  = clf_imputer.transform(X_clf)

    clf_pred    = int(clf_model.predict(X_clf_imp)[0])
    clf_proba   = clf_model.predict_proba(X_clf_imp)[0]
    clf_classes = clf_model.classes_
    proba_dict  = {int(c): round(float(prob), 4)
                   for c, prob in zip(clf_classes, clf_proba)}

    # ── Rank programs: suitable first, then by predicted average ────────────
    ranked_programs = sorted(
        program_results.keys(),
        key=lambda p: (
            int(program_results[p]['is_suitable']),
            program_results[p]['predicted_avg']
        ),
        reverse=True
    )
    top3 = ranked_programs[:3]

    return {
        'student_data':           student_data,
        'g6_avg':                 student_data['grade_6_final_average'],
        'ste_eligible':           ste_eligible,
        'ste_failed':             ste_failed_subjects,
        'program_results':        program_results,
        'ranked':                 ranked_programs,
        'top3':                   top3,
        'clf_pred':               clf_pred,
        'clf_proba':              proba_dict,
        'pred_avgs':              pred_avgs_for_clf,
        'PROGRAM_MAP':            PROGRAM_MAP,
        'SUITABILITY_THRESHOLD':  SUITABILITY_THRESHOLD,
        'STE_ELIGIBILITY_MIN_GRADE': STE_ELIGIBILITY_MIN_GRADE,
        'STE_ELIGIBILITY_SUBJECTS':  STE_ELIGIBILITY_SUBJECTS,
    }

# ==============================================================================
# SECTION 6: CONSOLE DISPLAY
# (Identical output format to RF_predict.py — enables side-by-side comparison)
# ==============================================================================

def display_results_console(result):
    """Print the detailed Gradient Boosting recommendation to the terminal."""
    sd          = result['student_data']
    name        = sd.get('student_name', 'Student')
    PROGRAM_MAP = result['PROGRAM_MAP']
    prog_res    = result['program_results']
    top3        = result['top3']
    pref        = sd.get('preferred_program', 6)
    has_pref    = sd.get('has_valid_preference', 0)

    print("\n" + "=" * 66)
    print(f"  SPARK RECOMMENDATION REPORT  [Gradient Boosting]")
    print(f"  Student: {name}")
    print("=" * 66)

    # ── Grade 6 Summary ─────────────────────────────────────────────────────
    print(f"\n  Grade 6 Final Average  : {result['g6_avg']:.3f}")
    print(f"  STE G6 Eligibility     : ", end='')
    if result['ste_eligible']:
        print(f"✅ ELIGIBLE (Math, Science, English all ≥ "
              f"{result['STE_ELIGIBILITY_MIN_GRADE']})")
    else:
        print(f"❌ INELIGIBLE")
        for reason in result['ste_failed']:
            print(f"     ✗ {reason}")

    if has_pref and pref in [1, 2, 3, 4, 5]:
        print(f"  Preferred Program      : {PROGRAM_MAP[pref]}")
    else:
        print("  Preferred Program      : OHSP/SNEd (out of system scope)")

    # ── 5-Loop Predicted Grades Table ───────────────────────────────────────
    print(f"\n  {'─' * 62}")
    print(f"  {'PROGRAM':<12} {'PRED AVG':>10} {'THRESHOLD':>10} "
          f"{'G6 ELIG':>9} {'SUITABLE':>10}  RANK")
    print(f"  {'─' * 62}")

    for rank, p in enumerate(result['ranked'], 1):
        r      = prog_res[p]
        suit   = "✅ YES" if r['is_suitable'] else "❌ NO"
        if p == 1:
            elig_str = "✅" if result['ste_eligible'] else "❌"
            if not result['ste_eligible']:
                suit = "❌ NO (G6)"
        else:
            elig_str = "N/A"
        top_tag = f"  ◄ #{rank} TOP 3" if rank <= 3 else ""
        print(f"  {r['name']:<12} {r['predicted_avg']:>10.2f} "
              f"{r['threshold']:>10} {elig_str:>9} {suit:>10}{top_tag}")

    # ── Top 3 Recommendations ───────────────────────────────────────────────
    print(f"\n  {'═' * 62}")
    print(f"  📌  TOP 3 RECOMMENDED PROGRAMS  [Gradient Boosting]:")
    print(f"  {'═' * 62}")

    medal = ['🥇', '🥈', '🥉']
    for i, p in enumerate(top3):
        r = prog_res[p]
        print(f"\n  {medal[i]}  #{i+1} — {r['name']}")
        print(f"      Predicted Grade 7 Q1 Average : {r['predicted_avg']:.2f}")
        print(f"      Suitability Threshold        : ≥ {r['threshold']}")
        margin_str = (f"+{r['margin']:.2f} above threshold"
                      if r['margin'] >= 0
                      else f"{r['margin']:.2f} below threshold")
        print(f"      Margin                       : {margin_str}")

        if p == 1:
            if result['ste_eligible']:
                print(f"      Why suitable: Student meets Grade 6 STE eligibility "
                      f"and predicted G7 average of {r['predicted_avg']:.2f} "
                      f"meets the {r['threshold']} threshold.")
            else:
                print(f"      ⚠  Note: STE is in Top 3 by predicted grade but "
                      f"student does NOT meet G6 eligibility requirements.")
                for reason in result['ste_failed']:
                    print(f"         ✗ {reason}")
        else:
            if r['is_suitable']:
                print(f"      Why suitable: Predicted average of "
                      f"{r['predicted_avg']:.2f} meets the "
                      f"{r['threshold']} threshold for {r['name']}.")
            else:
                print(f"      ⚠  Note: Predicted grade ({r['predicted_avg']:.2f}) "
                      f"is below the {r['threshold']} threshold. "
                      f"Included as best available option.")

    # ── Preferred Program Comparison ────────────────────────────────────────
    print(f"\n  {'─' * 62}")
    if has_pref and pref in [1, 2, 3, 4, 5]:
        pref_name = PROGRAM_MAP[pref]
        if pref in top3:
            rank = top3.index(pref) + 1
            print(f"  ✅  Preferred program ({pref_name}) matches "
                  f"recommendation #{rank} — GREAT FIT!")
        else:
            r_pref = prog_res[pref]
            print(f"  ⚠️   Preferred program ({pref_name}) is NOT in the Top 3.")
            print(f"      Predicted average if placed in {pref_name}: "
                  f"{r_pref['predicted_avg']:.2f}")
            if pref == 1 and not result['ste_eligible']:
                print(f"      Primary reason: Grade 6 eligibility not met.")
                for reason in result['ste_failed']:
                    print(f"        ✗ {reason}")
            elif not r_pref['grade_ok']:
                diff = r_pref['threshold'] - r_pref['predicted_avg']
                print(f"      Reason: Predicted grade is {diff:.2f} points below the "
                      f"{r_pref['threshold']} threshold required for {pref_name}.")
    else:
        print("  ℹ️   No preferred program within system scope (OHSP/SNEd selected).")
        print("      Recommendations are based entirely on predicted performance.")

    print(f"\n  {'─' * 62}")
    print(f"  Gradient Boosting Classifier  : {PROGRAM_MAP[result['clf_pred']]}")
    print(f"  (Direct classification — may differ from grade-based Top 1)")
    print(f"  {'─' * 62}\n")

# ==============================================================================
# SECTION 7: VISUAL REPORT GENERATION
# ==============================================================================

def generate_visual_report(result, output_filename=None):
    """
    Creates a comprehensive visual recommendation report (PNG).
    Identical layout to RF_predict.py — enables side-by-side visual comparison.
    """
    sd                    = result['student_data']
    name                  = sd.get('student_name', 'Student')
    PROGRAM_MAP           = result['PROGRAM_MAP']
    SUITABILITY_THRESHOLD = result['SUITABILITY_THRESHOLD']
    prog_res              = result['program_results']
    top3                  = result['top3']
    ranked                = result['ranked']
    pref                  = sd.get('preferred_program', 6)
    has_pref              = sd.get('has_valid_preference', 0)

    COLORS = {
        1: '#2E86AB', 2: '#A23B72', 3: '#F18F01',
        4: '#C73E1D', 5: '#3B1F2B'
    }
    SUITABLE_COLOR   = '#2A9D8F'
    UNSUITABLE_COLOR = '#E63946'

    fig = plt.figure(figsize=(16, 18))
    fig.patch.set_facecolor('#F8F9FA')

    gs = gridspec.GridSpec(4, 2, figure=fig,
                           hspace=0.45, wspace=0.35,
                           top=0.93, bottom=0.04,
                           left=0.07, right=0.97)

    # ── Title ────────────────────────────────────────────────────────────────
    fig.text(0.5, 0.97,
             'SPARK System — Program Recommendation Report  [Gradient Boosting]',
             ha='center', va='top', fontsize=16, fontweight='bold', color='#1A1A2E')
    fig.text(0.5, 0.945,
             f'Student: {name}  |  Grade 6 Average: {result["g6_avg"]:.3f}  '
             f'|  STE Eligible: {"✓ YES" if result["ste_eligible"] else "✗ NO"}',
             ha='center', va='top', fontsize=11, color='#555555')

    # ── Plot A: Predicted Grade 7 Averages per Program ────────────────────────
    ax_a = fig.add_subplot(gs[0, :])
    programs_ordered = [PROGRAM_MAP[p] for p in ranked]
    preds_ordered    = [prog_res[p]['predicted_avg'] for p in ranked]
    thresholds       = [prog_res[p]['threshold']     for p in ranked]
    bar_colors       = [SUITABLE_COLOR if prog_res[p]['is_suitable']
                        else UNSUITABLE_COLOR for p in ranked]

    bars = ax_a.bar(programs_ordered, preds_ordered,
                    color=bar_colors, alpha=0.88,
                    edgecolor='white', linewidth=2, width=0.55)

    # Threshold line per bar
    for i, (p, thr) in enumerate(zip(ranked, thresholds)):
        ax_a.plot([i - 0.28, i + 0.28], [thr, thr],
                  color='black', linewidth=2, linestyle='--', alpha=0.7)

    # Value labels
    for bar, val, p in zip(bars, preds_ordered, ranked):
        tag = '✅' if prog_res[p]['is_suitable'] else '❌'
        ax_a.text(bar.get_x() + bar.get_width() / 2.,
                  bar.get_height() + 0.3,
                  f'{val:.2f} {tag}',
                  ha='center', va='bottom', fontsize=10, fontweight='bold',
                  color='#1A1A2E')

    # Gold border for Top 3
    for i, p in enumerate(ranked[:3]):
        idx = ranked.index(p)
        ax_a.get_children()[idx].set_edgecolor('#FFD700')
        ax_a.get_children()[idx].set_linewidth(3)

    ax_a.set_title('Predicted Grade 7 Q1 Average per Program\n'
                   '(Green = Suitable | Red = Not Suitable | Gold border = Top 3 | '
                   'Dashed line = Threshold)',
                   fontsize=11, fontweight='bold', pad=10)
    ax_a.set_ylabel('Predicted Average Grade', fontsize=10)
    ax_a.set_ylim(60, 105)
    ax_a.axhline(85, color='#2E86AB', linestyle=':', alpha=0.4, linewidth=1)
    ax_a.axhline(75, color='#F18F01', linestyle=':', alpha=0.4, linewidth=1)
    ax_a.grid(axis='y', alpha=0.25)
    ax_a.set_facecolor('#FFFFFF')

    # ── Plot B: Grade 6 Subject Grades ──────────────────────────────────────
    ax_b = fig.add_subplot(gs[1, 0])
    g6_subjects = {
        'Math':     sd.get('grade_math', 0),
        'Science':  sd.get('grade_science', 0),
        'English':  sd.get('grade_english', 0),
        'Filipino': sd.get('grade_filipino', 0),
        'AP':       sd.get('grade_arpan', 0),
        'MAPEH':    sd.get('grade_mapeh', 0),
        'TLE':      sd.get('average_grade_tle', 0),
        'ESP':      sd.get('grade_esp', 0),
    }
    STE_SUBJECTS = ['Math', 'Science', 'English']
    g6_colors    = [('#2E86AB' if val >= 83 else '#E63946')
                    if subj in STE_SUBJECTS else '#6C757D'
                    for subj, val in g6_subjects.items()]

    bars_b = ax_b.bar(g6_subjects.keys(), g6_subjects.values(),
                      color=g6_colors, alpha=0.88,
                      edgecolor='white', linewidth=1.5)
    ax_b.axhline(83, color='#2E86AB', linestyle='--', linewidth=1.5,
                 alpha=0.7, label='STE min (83)')
    ax_b.axhline(85, color='green',   linestyle='--', linewidth=1.5,
                 alpha=0.5, label='Excellent (85)')
    ax_b.axhline(75, color='orange',  linestyle='--', linewidth=1.5,
                 alpha=0.5, label='Passing (75)')
    for bar, val in zip(bars_b, g6_subjects.values()):
        ax_b.text(bar.get_x() + bar.get_width() / 2.,
                  bar.get_height() + 0.3,
                  f'{val:.0f}', ha='center', va='bottom',
                  fontsize=8, fontweight='bold')
    ax_b.set_title('Grade 6 Subject Grades\n'
                   '(Blue = meets STE min | Red = below STE min)',
                   fontsize=10, fontweight='bold')
    ax_b.set_ylabel('Grade', fontsize=9)
    ax_b.set_ylim(60, 108)
    ax_b.legend(fontsize=7, loc='lower right')
    ax_b.tick_params(axis='x', labelsize=8)
    ax_b.grid(axis='y', alpha=0.25)
    ax_b.set_facecolor('#FFFFFF')

    # ── Plot C: GBR Classifier Probability ──────────────────────────────────
    ax_c = fig.add_subplot(gs[1, 1])
    proba        = result['clf_proba']
    prob_programs = [PROGRAM_MAP[p] for p in sorted(proba.keys())]
    prob_vals    = [proba[p] * 100 for p in sorted(proba.keys())]
    prob_colors  = [COLORS.get(p, '#999') for p in sorted(proba.keys())]

    bars_c = ax_c.bar(prob_programs, prob_vals,
                      color=prob_colors, alpha=0.88,
                      edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars_c, prob_vals):
        ax_c.text(bar.get_x() + bar.get_width() / 2.,
                  bar.get_height() + 0.5,
                  f'{val:.1f}%', ha='center', va='bottom',
                  fontsize=9, fontweight='bold')
    ax_c.set_title('Gradient Boosting Classifier\nProgram Probability (%)',
                   fontsize=10, fontweight='bold')
    ax_c.set_ylabel('Probability (%)', fontsize=9)
    ax_c.set_ylim(0, 115)
    ax_c.tick_params(axis='x', labelsize=8)
    ax_c.grid(axis='y', alpha=0.25)
    ax_c.set_facecolor('#FFFFFF')

    # ── Plot D: Suitability Margin ───────────────────────────────────────────
    ax_d = fig.add_subplot(gs[2, 0])
    margins       = [prog_res[p]['margin']     for p in ranked]
    margin_colors = [SUITABLE_COLOR if m >= 0 else UNSUITABLE_COLOR
                     for m in margins]

    bars_d = ax_d.barh(programs_ordered, margins,
                       color=margin_colors, alpha=0.88,
                       edgecolor='white', linewidth=1.5)
    ax_d.axvline(0, color='black', linewidth=1.5)
    for bar, val in zip(bars_d, margins):
        xpos = val + 0.1 if val >= 0 else val - 0.1
        ha   = 'left' if val >= 0 else 'right'
        ax_d.text(xpos, bar.get_y() + bar.get_height() / 2.,
                  f'{val:+.2f}', ha=ha, va='center',
                  fontsize=9, fontweight='bold')
    ax_d.set_title('Grade Margin from Threshold\n(+ = above  |  − = below)',
                   fontsize=10, fontweight='bold')
    ax_d.set_xlabel('Points above/below threshold', fontsize=9)
    ax_d.grid(axis='x', alpha=0.25)
    ax_d.set_facecolor('#FFFFFF')

    # ── Plot E: Top 3 Summary Card ───────────────────────────────────────────
    ax_e = fig.add_subplot(gs[2, 1])
    ax_e.set_facecolor('#FFFFFF')
    ax_e.axis('off')

    medal_colors = ['#FFD700', '#C0C0C0', '#CD7F32']
    medals       = ['🥇 RANK 1', '🥈 RANK 2', '🥉 RANK 3']
    y_positions  = [0.88, 0.58, 0.28]

    for i, p in enumerate(top3):
        r    = prog_res[p]
        ypos = y_positions[i]
        rect = mpatches.FancyBboxPatch(
            (0.02, ypos - 0.10), 0.96, 0.22,
            boxstyle="round,pad=0.02",
            linewidth=2,
            edgecolor=medal_colors[i],
            facecolor=COLORS.get(p, '#CCCCCC'),
            alpha=0.15,
            transform=ax_e.transAxes
        )
        ax_e.add_patch(rect)
        ax_e.text(0.05, ypos + 0.07, medals[i],
                  transform=ax_e.transAxes,
                  fontsize=9, fontweight='bold',
                  color=medal_colors[i], va='center')
        ax_e.text(0.05, ypos - 0.01, r['name'],
                  transform=ax_e.transAxes,
                  fontsize=12, fontweight='bold',
                  color=COLORS.get(p, '#333'), va='center')
        suit_str = '✅ Suitable' if r['is_suitable'] else '⚠ Below threshold'
        ax_e.text(0.55, ypos + 0.03,
                  f"Pred Avg: {r['predicted_avg']:.2f}",
                  transform=ax_e.transAxes,
                  fontsize=10, fontweight='bold', color='#1A1A2E', va='center')
        ax_e.text(0.55, ypos - 0.06, suit_str,
                  transform=ax_e.transAxes,
                  fontsize=8, va='center', fontweight='bold',
                  color=SUITABLE_COLOR if r['is_suitable'] else UNSUITABLE_COLOR)

    ax_e.set_title('Top 3 Recommended Programs', fontsize=10, fontweight='bold', pad=8)
    ax_e.set_xlim(0, 1)
    ax_e.set_ylim(0, 1)

    # ── Plot F: Preferred Program Comparison ────────────────────────────────
    ax_f = fig.add_subplot(gs[3, :])
    ax_f.set_facecolor('#FFFFFF')
    ax_f.axis('off')

    if has_pref and pref in [1, 2, 3, 4, 5]:
        pref_name  = PROGRAM_MAP[pref]
        r_pref     = prog_res[pref]
        pref_rank  = ranked.index(pref) + 1
        in_top3    = pref in top3

        title_color = SUITABLE_COLOR if in_top3 else UNSUITABLE_COLOR
        status_text = (
            f"✅  Preferred program ({pref_name}) is in Top 3 — Rank #{pref_rank}"
            if in_top3 else
            f"⚠️   Preferred program ({pref_name}) is NOT in Top 3 (Rank #{pref_rank})"
        )

        ax_f.text(0.5, 0.90, 'Preferred Program Analysis',
                  transform=ax_f.transAxes,
                  ha='center', fontsize=11, fontweight='bold', color='#1A1A2E')
        ax_f.text(0.5, 0.72, status_text,
                  transform=ax_f.transAxes,
                  ha='center', fontsize=10, fontweight='bold', color=title_color)

        if not in_top3:
            if pref == 1 and not result['ste_eligible']:
                reason = "Does not meet Grade 6 STE eligibility (Math/Science/English ≥ 83)"
                for fail in result['ste_failed']:
                    reason += f"\n  ✗ {fail}"
            else:
                diff   = r_pref['threshold'] - r_pref['predicted_avg']
                reason = (f"Predicted grade ({r_pref['predicted_avg']:.2f}) is "
                          f"{diff:.2f} pts below the {r_pref['threshold']} threshold "
                          f"required for {pref_name}.")
            ax_f.text(0.5, 0.42, f"Reason: {reason}",
                      transform=ax_f.transAxes,
                      ha='center', fontsize=9, color='#333333',
                      style='italic', wrap=True)
            ax_f.text(0.5, 0.18,
                      f"The system recommends {PROGRAM_MAP[top3[0]]} as the best fit, "
                      f"with a predicted average of {prog_res[top3[0]]['predicted_avg']:.2f}.",
                      transform=ax_f.transAxes,
                      ha='center', fontsize=9, color='#1A1A2E')
    else:
        ax_f.text(0.5, 0.60,
                  "Preferred program is OHSP/SNEd — outside this system's scope.\n"
                  "Recommendations above are based entirely on predicted performance.",
                  transform=ax_f.transAxes,
                  ha='center', fontsize=10, color='#555555', style='italic')

    # ── Save ─────────────────────────────────────────────────────────────────
    safe_name = name.replace(' ', '_').replace('/', '-')
    if output_filename is None:
        output_filename = f'gbr_recommendation_{safe_name}.png'
    plt.savefig(output_filename, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    plt.close()
    return output_filename

# ==============================================================================
# SECTION 8: MAIN — RUN THE PREDICTION SYSTEM
# ==============================================================================

def main():
    print("\n" + "=" * 66)
    print("  SPARK SYSTEM — Student Placement Prediction")
    print("  Algorithm: Gradient Boosting (XGBoost/LightGBM equivalent)")
    print("  Loading trained models from gbr_models/ ...")
    print("=" * 66)

    config, classifier, regressors = load_models()

    print("  ✓ Gradient Boosting models loaded successfully.")
    print(f"  ✓ Regression  : 5 GBR models ({', '.join(config['PROGRAM_MAP'].values())})")
    print(f"  ✓ Classifier  : GradientBoostingClassifier")
    print(f"  ✓ Features    : {len(config['FEATURES'])} input features")

    while True:
        student_data = collect_student_data()

        print("\n  Processing... predicting Grade 7 performance "
              "across all 5 programs using Gradient Boosting...")
        result = predict_for_student(student_data, config, classifier, regressors)

        display_results_console(result)

        print("  Generating visual report...")
        report_file = generate_visual_report(result)
        print(f"  ✓ Visual report saved: {report_file}")

        print("\n" + "─" * 66)
        again = input("  Predict for another student? [y/n]: ").strip().lower()
        if again not in ['y', 'yes']:
            print("\n  Thank you for using SPARK System (Gradient Boosting). Goodbye!\n")
            break

if __name__ == '__main__':
    main()
