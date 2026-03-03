"""
================================================================================
SPARK SYSTEM — Ridge Regression Prediction & Recommendation
Interactive Testing Script
================================================================================

HOW TO USE:
    1. Run ridge_training.py first to train and save models.
    2. Run this script:  python3 ridge_predict.py
    3. Enter the student's data when prompted.
    4. The system will:
        - Check STE eligibility based on Grade 6 Math, Science, English.
        - Predict Grade 7 Q1 average for each of the 5 programs using trained
          Ridge regression models.
        - Apply suitability thresholds.
        - Display Top 3 recommended programs with explanation.
        - Compare with the student's preferred program.
        - Generate a visual report (PNG).

REQUIRES:
    - ridge_models/ folder (created by ridge_training.py)
    - Libraries: pandas, numpy, matplotlib, joblib, scikit-learn
================================================================================
"""

import os
import sys
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import warnings
warnings.filterwarnings('ignore')

MODELS_DIR = 'ridge_models'

def load_models():
    """Load trained Ridge models, classifier, and config."""
    required = [
        'config.pkl', 'classifier.pkl',
        'ridge_STE.pkl', 'ridge_SPFL.pkl',
        'ridge_SPTVE.pkl', 'ridge_TOP-5.pkl',
        'ridge_HETERO.pkl'
    ]
    for f in required:
        if not os.path.exists(os.path.join(MODELS_DIR, f)):
            print(f"\n  ❌ ERROR: '{MODELS_DIR}/{f}' not found.")
            print("     Please run ridge_training.py first.")
            sys.exit(1)

    config = joblib.load(f'{MODELS_DIR}/config.pkl')
    classifier = joblib.load(f'{MODELS_DIR}/classifier.pkl')
    regressors = {}
    for p, name in config['PROGRAM_MAP'].items():
        fname = f'{MODELS_DIR}/ridge_{name}.pkl'
        regressors[p] = joblib.load(fname)
    return config, classifier, regressors

# ==============================================================================
# INPUT QUESTION DEFINITIONS (same as in RF_predict.py)
# ==============================================================================
def build_questions():
    """Return ordered list of input questions."""
    questions = [
        ('student_name',  'Student Name',          'text',   None,        'Full name'),
        ('age',           'Age',                   'int',    (11, 18),    'Typical range: 11-13'),
        ('gender',        'Gender',                'choice', {0: 'Male', 1: 'Female'}, ''),
        ('grade_math',         'Grade 6 — Mathematics',         'float', (60, 100), ''),
        ('grade_science',      'Grade 6 — Science',             'float', (60, 100), ''),
        ('grade_english',      'Grade 6 — English',             'float', (60, 100), ''),
        ('grade_filipino',     'Grade 6 — Filipino',            'float', (60, 100), ''),
        ('grade_arpan',        'Grade 6 — Araling Panlipunan',  'float', (60, 100), ''),
        ('grade_mapeh',        'Grade 6 — MAPEH',               'float', (60, 100), ''),
        ('average_grade_tle',  'Grade 6 — TLE',                 'float', (60, 100), ''),
        ('grade_esp',          'Grade 6 — ESP',                 'float', (60, 100), ''),
        ('preferred_program', 'Preferred Program', 'choice', {
            1: 'STE  (Science, Technology & Engineering)',
            2: 'SPFL (Special Program in Foreign Language)',
            3: 'SPTVE(Special Program in Tech-Voc Education)',
            4: 'TOP-5 Regular Section',
            5: 'HETERO (Regular Section)',
            6: 'OHSP / SNEd (not in system scope)'
        }, ''),
        ('learning_style', 'Learning Style', 'choice', {
            1: 'Visual', 2: 'Auditory', 3: 'Reading/Writing', 4: 'Kinesthetic', 5: 'Mixed'
        }, ''),
        ('study_hours_daily', 'Study Hours Per Day', 'choice', {
            1: '<1 hour', 2: '1-2 hours', 3: '2-3 hours', 4: '>3 hours'
        }, ''),
        ('motivation_level', 'Motivation Level', 'choice', {
            1: 'Low', 2: 'Average', 3: 'High'
        }, ''),
        ('assignment_completion', 'Assignment Completion', 'choice', {
            1: 'Rarely', 2: 'Sometimes', 3: 'Usually', 4: 'Always'
        }, ''),
        ('handle_difficulty', 'Handles Difficulty', 'choice', {
            1: 'Gives up', 2: 'Needs encouragement', 3: 'Tries independently', 4: 'Seeks help'
        }, ''),
        ('support_person', 'Support at Home', 'choice', {
            1: 'Parent', 2: 'Sibling', 3: 'Tutor', 4: 'Friend', 5: 'No support'
        }, ''),
        ('family_income_help', 'Family Income', 'choice', {
            1: 'Low', 2: 'Middle', 3: 'High'
        }, ''),
        ('device_availability', 'Device Availability', 'choice', {
            1: 'None', 2: 'Shared', 3: 'Personal'
        }, ''),
        ('internet_access', 'Internet Access', 'choice', {
            1: 'No internet', 2: 'Occasional', 3: 'Stable'
        }, ''),
        ('distance_from_school', 'Distance from School', 'choice', {
            1: 'Very near', 2: 'Near', 3: 'Far', 4: 'Very far'
        }, ''),
        ('travel_difficulty', 'Travel Difficulty', 'choice', {
            1: 'No difficulty', 2: 'Sometimes', 3: 'Very difficult'
        }, ''),
        ('absences_count', 'Absences in G6', 'choice', {
            1: '0-5 days', 2: '6-10 days', 3: '11-15 days', 4: '>15 days'
        }, ''),
        ('absence_reason', 'Primary Absence Reason', 'choice', {
            1: 'Illness', 2: 'Family matters', 3: 'Work', 4: 'Distance', 5: 'No absences'
        }, ''),
        ('enjoy_math',                     'Enjoys Mathematics?',                  'yesno', None, ''),
        ('enjoy_science',                  'Enjoys Science?',                      'yesno', None, ''),
        ('enjoy_english',                  'Enjoys English?',                      'yesno', None, ''),
        ('enjoy_filipino',                 'Enjoys Filipino?',                     'yesno', None, ''),
        ('enjoy_arpan',                    'Enjoys Araling Panlipunan?',           'yesno', None, ''),
        ('enjoy_mapeh',                    'Enjoys MAPEH?',                        'yesno', None, ''),
        ('enjoy_tle',                      'Enjoys TLE?',                          'yesno', None, ''),
        ('enjoy_science_experiments',      'Enjoys Science Experiments?',          'yesno', None, ''),
        ('enjoy_reading',                  'Enjoys Reading?',                      'yesno', None, ''),
        ('enjoy_handson_activities',       'Enjoys Hands-on Activities?',          'yesno', None, ''),
        ('enjoy_sports',                   'Enjoys Sports?',                       'yesno', None, ''),
        ('enjoy_arts',                     'Enjoys Arts?',                         'yesno', None, ''),
        ('enjoy_language_related_activities', 'Enjoys Language-related Activities?','yesno', None, ''),
        ('foreign_language_interest',      'Interest in Foreign Language', 'choice', {
            1: 'Very interested', 2: 'Somewhat', 3: 'Not interested'
        }, ''),
        ('school_participation', 'School Participation', 'choice', {
            1: 'Low', 2: 'Average', 3: 'Active'
        }, ''),
        ('competition_participation', 'Participated in Competitions?',     'yesno', None, ''),
        ('received_awards',           'Received any Awards in G6?',        'yesno', None, ''),
        ('award_highest_honors',      'Award: Highest Honors?',            'yesno', None, ''),
        ('award_high_honors',         'Award: High Honors?',               'yesno', None, ''),
        ('award_with_honors',         'Award: With Honors?',               'yesno', None, ''),
        ('award_best_science',        'Award: Best in Science?',           'yesno', None, ''),
        ('award_best_math',           'Award: Best in Math?',              'yesno', None, ''),
        ('award_best_english',        'Award: Best in English?',           'yesno', None, ''),
        ('award_conduct',             'Award: Best in Conduct?',           'yesno', None, ''),
        ('achiever_award',            'Award: Achiever Award?',            'yesno', None, ''),
        ('difficulty_reading',            'Difficulty in Reading?',            'yesno', None, ''),
        ('difficulty_writing',            'Difficulty in Writing?',            'yesno', None, ''),
        ('difficulty_math',               'Difficulty in Math?',               'yesno', None, ''),
        ('difficulty_focusing',           'Difficulty Focusing?',              'yesno', None, ''),
        ('difficulty_social_interaction', 'Difficulty with Social Interaction?','yesno', None, ''),
        ('extra_support_recommended',     'Extra Support Recommended?',        'yesno', None, ''),
        ('quiet_study_place',             'Quiet Study Place at Home?',      'choice', {
            0: 'No', 1: 'Sometimes', 2: 'Usually', 3: 'Always'
        }, ''),
    ]
    return questions

# ==============================================================================
# INPUT COLLECTION (same as in RF_predict.py)
# ==============================================================================
def section_header(title):
    print(f"\n  {'─' * 60}\n  {title}\n  {'─' * 60}")

def ask_yesno(label):
    while True:
        ans = input(f"  {label} [1=Yes / 0=No]: ").strip()
        if ans in ['0', '1']:
            return int(ans)
        print("     ⚠  Please enter 1 or 0.")

def ask_choice(label, options):
    print(f"  {label}:")
    for k, v in options.items():
        print(f"      {k} — {v}")
    valid = [str(k) for k in options.keys()]
    while True:
        ans = input(f"     Enter choice ({'/'.join(valid)}): ").strip()
        if ans in valid:
            return int(ans)
        print(f"     ⚠  Choose from: {', '.join(valid)}")

def ask_float(label, lo, hi):
    while True:
        ans = input(f"  {label} ({lo}–{hi}): ").strip()
        try:
            val = float(ans)
            if lo <= val <= hi:
                return val
            print(f"     ⚠  Value must be between {lo} and {hi}.")
        except ValueError:
            print("     ⚠  Enter a valid number.")

def ask_int(label, lo, hi):
    while True:
        ans = input(f"  {label} ({lo}–{hi}): ").strip()
        try:
            val = int(ans)
            if lo <= val <= hi:
                return val
            print(f"     ⚠  Value must be between {lo} and {hi}.")
        except ValueError:
            print("     ⚠  Enter a whole number.")

def ask_text(label):
    while True:
        ans = input(f"  {label}: ").strip()
        if ans:
            return ans
        print("     ⚠  Cannot be empty.")

def collect_student_data():
    print("\n" + "=" * 66)
    print("  SPARK SYSTEM (Ridge) — New Student Data Entry")
    print("=" * 66)
    questions = build_questions()
    student_data = {}
    sections = {
        'student_name':      '📋  BASIC INFORMATION',
        'grade_math':        '📚  GRADE 6 ACADEMIC GRADES',
        'preferred_program': '🎯  PREFERRED PROGRAM',
        'learning_style':    '🧠  LEARNING PROFILE',
        'support_person':    '🏠  BACKGROUND & SUPPORT',
        'enjoy_math':        '💡  INTERESTS & ENJOYMENT',
        'school_participation': '🏆  PARTICIPATION & AWARDS',
        'difficulty_reading':'⚠️   LEARNING DIFFICULTIES',
    }
    current_section = None
    for key, label, qtype, valid, hint in questions:
        if key in sections:
            section_header(sections[key])
        if qtype == 'text':
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

def compute_g6_average(data):
    g6_cols = [
        'grade_math', 'grade_science', 'grade_english', 'grade_filipino',
        'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp'
    ]
    return round(np.mean([data[c] for c in g6_cols]), 3)

# ==============================================================================
# PREDICTION ENGINE
# ==============================================================================
def predict_for_student(student_data, config, classifier, regressors):
    PROGRAM_MAP = config['PROGRAM_MAP']
    FEATURES = config['FEATURES']
    G7_COMMON_SUBJECTS = config['G7_COMMON_SUBJECTS']
    G7_EXCLUSIVE = config['G7_EXCLUSIVE']
    SUITABILITY_THRESHOLD = config['SUITABILITY_THRESHOLD']
    STE_ELIGIBILITY_SUBJECTS = config['STE_ELIGIBILITY_SUBJECTS']
    STE_ELIGIBILITY_MIN_GRADE = config['STE_ELIGIBILITY_MIN_GRADE']
    clf_features = config['clf_features']

    # Add computed values
    student_data['grade_6_final_average'] = compute_g6_average(student_data)
    student_data['has_valid_preference'] = (
        1 if student_data.get('preferred_program', 6) in [1,2,3,4,5] else 0
    )

    # Build feature vector
    feat_row = {}
    for f in FEATURES:
        feat_row[f] = student_data.get(f, 0)
    X_student = pd.DataFrame([feat_row])

    # STE eligibility check
    ste_eligible = all(
        student_data.get(subj, 0) >= STE_ELIGIBILITY_MIN_GRADE
        for subj in STE_ELIGIBILITY_SUBJECTS
    )
    ste_failed = [
        f"{s.replace('grade_','').upper()} ({student_data.get(s,0):.0f} < {STE_ELIGIBILITY_MIN_GRADE})"
        for s in STE_ELIGIBILITY_SUBJECTS
        if student_data.get(s, 0) < STE_ELIGIBILITY_MIN_GRADE
    ]

    # 5‑loop predictions
    program_results = {}
    pred_avgs_for_clf = {}

    for p, name in PROGRAM_MAP.items():
        reg_data = regressors[p]
        model = reg_data['model']
        imputer = reg_data['imputer']
        subjects = reg_data['subjects']

        X_imp = imputer.transform(X_student[FEATURES])
        pred_avg = float(model.predict(X_imp)[0])
        pred_avg = round(min(max(pred_avg, 60), 100), 2)

        # Approximate per‑subject grades (use same predicted average)
        subject_preds = {subj: pred_avg for subj in subjects}

        grade_ok = pred_avg >= SUITABILITY_THRESHOLD[p]
        if p == 1:
            is_suitable = grade_ok and ste_eligible
        else:
            is_suitable = grade_ok

        margin = round(pred_avg - SUITABILITY_THRESHOLD[p], 2)

        program_results[p] = {
            'name': name,
            'predicted_avg': pred_avg,
            'subject_preds': subject_preds,
            'subjects': subjects,
            'threshold': SUITABILITY_THRESHOLD[p],
            'grade_ok': grade_ok,
            'is_suitable': is_suitable,
            'margin': margin,
        }
        pred_avgs_for_clf[f'pred_avg_{name}'] = pred_avg

    # Classification (Logistic Regression)
    clf_model = classifier['model']
    clf_imputer = classifier['imputer']
    clf_scaler = classifier['scaler']

    clf_row = {}
    for f in FEATURES:
        clf_row[f] = student_data.get(f, 0)
    for k, v in pred_avgs_for_clf.items():
        clf_row[k] = v

    X_clf = pd.DataFrame([[clf_row.get(f, 0) for f in clf_features]],
                         columns=clf_features)
    X_clf_imp = clf_imputer.transform(X_clf)
    X_clf_scaled = clf_scaler.transform(X_clf_imp)

    clf_pred = int(clf_model.predict(X_clf_scaled)[0])
    clf_proba = clf_model.predict_proba(X_clf_scaled)[0]
    proba_dict = {int(c): round(float(p), 4) for c, p in zip(clf_model.classes_, clf_proba)}

    # Rank programs: suitable first, then by predicted avg
    ranked = sorted(
        program_results.keys(),
        key=lambda p: (int(program_results[p]['is_suitable']), program_results[p]['predicted_avg']),
        reverse=True
    )
    top3 = ranked[:3]

    return {
        'student_data': student_data,
        'g6_avg': student_data['grade_6_final_average'],
        'ste_eligible': ste_eligible,
        'ste_failed': ste_failed,
        'program_results': program_results,
        'ranked': ranked,
        'top3': top3,
        'clf_pred': clf_pred,
        'clf_proba': proba_dict,
        'pred_avgs': pred_avgs_for_clf,
        'PROGRAM_MAP': PROGRAM_MAP,
        'SUITABILITY_THRESHOLD': SUITABILITY_THRESHOLD,
        'STE_ELIGIBILITY_MIN_GRADE': STE_ELIGIBILITY_MIN_GRADE,
        'STE_ELIGIBILITY_SUBJECTS': STE_ELIGIBILITY_SUBJECTS,
    }

# ==============================================================================
# CONSOLE DISPLAY (similar to RF_predict.py)
# ==============================================================================
def display_results_console(result):
    sd = result['student_data']
    name = sd.get('student_name', 'Student')
    PROGRAM_MAP = result['PROGRAM_MAP']
    prog_res = result['program_results']
    top3 = result['top3']
    pref = sd.get('preferred_program', 6)
    has_pref = sd.get('has_valid_preference', 0)

    print("\n" + "=" * 66)
    print(f"  SPARK RECOMMENDATION REPORT (Ridge)")
    print(f"  Student: {name}")
    print("=" * 66)

    print(f"\n  Grade 6 Final Average  : {result['g6_avg']:.3f}")
    print(f"  STE G6 Eligibility     : ", end='')
    if result['ste_eligible']:
        print(f"✅ ELIGIBLE (Math/Science/English ≥ {result['STE_ELIGIBILITY_MIN_GRADE']})")
    else:
        print("❌ INELIGIBLE")
        for reason in result['ste_failed']:
            print(f"     ✗ {reason}")

    if has_pref and pref in PROGRAM_MAP:
        print(f"  Preferred Program      : {PROGRAM_MAP[pref]}")
    else:
        print("  Preferred Program      : OHSP/SNEd (out of scope)")

    # Table of predicted averages
    print(f"\n  {'─' * 62}")
    print(f"  {'PROGRAM':<12} {'PRED AVG':>10} {'THRESHOLD':>10} {'G6 ELIG':>9} {'SUITABLE':>10}  RANK")
    print(f"  {'─' * 62}")
    for rank, p in enumerate(result['ranked'], 1):
        r = prog_res[p]
        elig_str = "✅" if (p == 1 and result['ste_eligible']) else "N/A" if p != 1 else "❌"
        suit = "✅ YES" if r['is_suitable'] else "❌ NO"
        top_tag = f"  ◄ #{rank} TOP 3" if rank <= 3 else ""
        print(f"  {r['name']:<12} {r['predicted_avg']:>10.2f} {r['threshold']:>10} "
              f"{elig_str:>9} {suit:>10}{top_tag}")

    # Top 3 details
    print(f"\n  {'═' * 62}")
    print(f"  📌  TOP 3 RECOMMENDED PROGRAMS:")
    print(f"  {'═' * 62}")
    medals = ['🥇', '🥈', '🥉']
    for i, p in enumerate(top3):
        r = prog_res[p]
        print(f"\n  {medals[i]}  #{i+1} — {r['name']}")
        print(f"      Predicted Grade 7 Q1 Average : {r['predicted_avg']:.2f}")
        print(f"      Suitability Threshold        : ≥ {r['threshold']}")
        print(f"      Margin                       : {r['margin']:+.2f}")
        if p == 1:
            if result['ste_eligible']:
                print("      Why suitable: STE eligibility met + predicted grade meets threshold.")
            else:
                print("      ⚠  Note: STE in Top 3 by grade, but G6 eligibility not met.")
        else:
            if r['is_suitable']:
                print(f"      Why suitable: Predicted grade meets the {r['threshold']} threshold.")
            else:
                print(f"      ⚠  Note: Predicted grade below threshold; best available.")

    # Preferred program comparison
    print(f"\n  {'─' * 62}")
    if has_pref and pref in PROGRAM_MAP:
        pref_name = PROGRAM_MAP[pref]
        if pref in top3:
            rank = top3.index(pref) + 1
            print(f"  ✅  Preferred program ({pref_name}) matches recommendation #{rank}.")
        else:
            r_pref = prog_res[pref]
            print(f"  ⚠️   Preferred program ({pref_name}) is NOT in Top 3.")
            print(f"      Predicted average if placed there: {r_pref['predicted_avg']:.2f}")
            if pref == 1 and not result['ste_eligible']:
                print("      Reason: Does not meet G6 STE eligibility.")
                for reason in result['ste_failed']:
                    print(f"        ✗ {reason}")
            elif not r_pref['grade_ok']:
                diff = r_pref['threshold'] - r_pref['predicted_avg']
                print(f"      Reason: Predicted grade is {diff:.2f} points BELOW the "
                      f"{r_pref['threshold']} threshold.")
    else:
        print("  ℹ️   No preferred program within scope. Recommendations based on predictions.")

    print(f"\n  Classification Model Prediction : {PROGRAM_MAP[result['clf_pred']]}")
    print(f"  {'─' * 62}\n")

# ==============================================================================
# VISUAL REPORT (adapted for Ridge – same layout)
# ==============================================================================
def generate_visual_report(result, output_filename=None):
    sd = result['student_data']
    name = sd.get('student_name', 'Student')
    PROGRAM_MAP = result['PROGRAM_MAP']
    SUITABILITY_THRESHOLD = result['SUITABILITY_THRESHOLD']
    prog_res = result['program_results']
    top3 = result['top3']
    ranked = result['ranked']
    pref = sd.get('preferred_program', 6)
    has_pref = sd.get('has_valid_preference', 0)

    COLORS = {
        1: '#2E86AB', 2: '#A23B72', 3: '#F18F01',
        4: '#C73E1D', 5: '#3B1F2B'
    }
    SUITABLE_COLOR = '#2A9D8F'
    UNSUITABLE_COLOR = '#E63946'

    fig = plt.figure(figsize=(16, 18))
    fig.patch.set_facecolor('#F8F9FA')
    gs = gridspec.GridSpec(4, 2, figure=fig, hspace=0.45, wspace=0.35,
                           top=0.93, bottom=0.04, left=0.07, right=0.97)

    # Title
    fig.text(0.5, 0.97,
             f'SPARK System (Ridge) — Program Recommendation Report',
             ha='center', va='top', fontsize=18, fontweight='bold', color='#1A1A2E')
    fig.text(0.5, 0.945,
             f'Student: {name}  |  Grade 6 Average: {result["g6_avg"]:.3f}  '
             f'|  STE Eligible: {"✓ YES" if result["ste_eligible"] else "✗ NO"}',
             ha='center', va='top', fontsize=11, color='#555555')

    # Plot A: Predicted averages per program
    ax_a = fig.add_subplot(gs[0, :])
    prog_names = [PROGRAM_MAP[p] for p in ranked]
    preds = [prog_res[p]['predicted_avg'] for p in ranked]
    thresholds = [prog_res[p]['threshold'] for p in ranked]
    bar_colors = [SUITABLE_COLOR if prog_res[p]['is_suitable'] else UNSUITABLE_COLOR for p in ranked]
    bars = ax_a.bar(prog_names, preds, color=bar_colors, alpha=0.88,
                    edgecolor='white', linewidth=2, width=0.55)
    for i, (p, thr) in enumerate(zip(ranked, thresholds)):
        ax_a.plot([i-0.28, i+0.28], [thr, thr], color='black', linewidth=2, linestyle='--', alpha=0.7)
    for bar, val, p in zip(bars, preds, ranked):
        ax_a.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                  f'{val:.2f} {"✅" if prog_res[p]["is_suitable"] else "❌"}',
                  ha='center', va='bottom', fontsize=10, fontweight='bold')
    # Highlight top3 borders
    for i, p in enumerate(ranked[:3]):
        idx = ranked.index(p)
        ax_a.get_children()[idx].set_edgecolor('#FFD700')
        ax_a.get_children()[idx].set_linewidth(3)
    ax_a.set_title('Predicted Grade 7 Q1 Average per Program\n'
                   '(Green = Suitable | Red = Not Suitable | Gold border = Top 3)',
                   fontsize=11, fontweight='bold')
    ax_a.set_ylabel('Predicted Average')
    ax_a.set_ylim(60, 105)
    ax_a.axhline(85, color='#2E86AB', linestyle=':', alpha=0.4)
    ax_a.axhline(75, color='#F18F01', linestyle=':', alpha=0.4)
    ax_a.grid(axis='y', alpha=0.25)

    # Plot B: Grade 6 breakdown
    ax_b = fig.add_subplot(gs[1, 0])
    g6_subjects = {
        'Math': sd.get('grade_math',0), 'Science': sd.get('grade_science',0),
        'English': sd.get('grade_english',0), 'Filipino': sd.get('grade_filipino',0),
        'AP': sd.get('grade_arpan',0), 'MAPEH': sd.get('grade_mapeh',0),
        'TLE': sd.get('average_grade_tle',0), 'ESP': sd.get('grade_esp',0)
    }
    ste_subs = ['Math','Science','English']
    colors_b = ['#2E86AB' if (subj in ste_subs and val >= 83) else
                '#E63946' if (subj in ste_subs and val < 83) else '#6C757D'
                for subj, val in g6_subjects.items()]
    bars_b = ax_b.bar(g6_subjects.keys(), g6_subjects.values(),
                      color=colors_b, alpha=0.88, edgecolor='white')
    ax_b.axhline(83, color='#2E86AB', linestyle='--', linewidth=1.5, alpha=0.7, label='STE min (83)')
    ax_b.axhline(85, color='green', linestyle='--', alpha=0.5, label='Excellent (85)')
    ax_b.axhline(75, color='orange', linestyle='--', alpha=0.5, label='Passing (75)')
    for bar, val in zip(bars_b, g6_subjects.values()):
        ax_b.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                  f'{val:.0f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    ax_b.set_title('Grade 6 Subject Grades', fontsize=10, fontweight='bold')
    ax_b.set_ylabel('Grade')
    ax_b.legend(fontsize=7, loc='lower right')
    ax_b.grid(axis='y', alpha=0.25)

    # Plot C: Classification probabilities
    ax_c = fig.add_subplot(gs[1, 1])
    proba = result['clf_proba']
    progs = sorted(proba.keys())
    prob_vals = [proba[p]*100 for p in progs]
    prob_names = [PROGRAM_MAP[p] for p in progs]
    prob_colors = [COLORS.get(p, '#999') for p in progs]
    bars_c = ax_c.bar(prob_names, prob_vals, color=prob_colors, alpha=0.88, edgecolor='white')
    for bar, val in zip(bars_c, prob_vals):
        ax_c.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                  f'{val:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax_c.set_title('Classification Model\nProgram Probability (%)', fontsize=10, fontweight='bold')
    ax_c.set_ylabel('Probability (%)')
    ax_c.set_ylim(0, 115)
    ax_c.grid(axis='y', alpha=0.25)

    # Plot D: Margin bar chart
    ax_d = fig.add_subplot(gs[2, 0])
    margins = [prog_res[p]['margin'] for p in ranked]
    margin_colors = [SUITABLE_COLOR if m>=0 else UNSUITABLE_COLOR for m in margins]
    bars_d = ax_d.barh(prog_names, margins, color=margin_colors, alpha=0.88, edgecolor='white')
    ax_d.axvline(0, color='black', linewidth=1.5)
    for bar, val in zip(bars_d, margins):
        xpos = val + 0.1 if val>=0 else val - 0.1
        ha = 'left' if val>=0 else 'right'
        ax_d.text(xpos, bar.get_y()+bar.get_height()/2,
                  f'{val:+.2f}', ha=ha, va='center', fontsize=9, fontweight='bold')
    ax_d.set_title('Grade Margin from Threshold', fontsize=10, fontweight='bold')
    ax_d.set_xlabel('Points above/below threshold')
    ax_d.grid(axis='x', alpha=0.25)

    # Plot E: Top 3 summary card
    ax_e = fig.add_subplot(gs[2, 1])
    ax_e.axis('off')
    ax_e.set_facecolor('#FFFFFF')
    medal_colors = ['#FFD700', '#C0C0C0', '#CD7F32']
    medals = ['🥇 RANK 1', '🥈 RANK 2', '🥉 RANK 3']
    ypos = [0.88, 0.58, 0.28]
    for i, p in enumerate(top3):
        r = prog_res[p]
        rect = mpatches.FancyBboxPatch((0.02, ypos[i]-0.10), 0.96, 0.22,
                                        boxstyle='round,pad=0.02', linewidth=2,
                                        edgecolor=medal_colors[i],
                                        facecolor=COLORS.get(p, '#CCC'), alpha=0.15,
                                        transform=ax_e.transAxes)
        ax_e.add_patch(rect)
        ax_e.text(0.05, ypos[i]+0.07, medals[i], transform=ax_e.transAxes,
                  fontsize=9, fontweight='bold', color=medal_colors[i], va='center')
        ax_e.text(0.05, ypos[i]-0.01, r['name'], transform=ax_e.transAxes,
                  fontsize=12, fontweight='bold', color=COLORS.get(p, '#333'), va='center')
        ax_e.text(0.55, ypos[i]+0.03, f"Pred Avg: {r['predicted_avg']:.2f}",
                  transform=ax_e.transAxes, fontsize=10, fontweight='bold')
        suit_str = '✅ Suitable' if r['is_suitable'] else '⚠ Below threshold'
        ax_e.text(0.55, ypos[i]-0.06, suit_str, transform=ax_e.transAxes,
                  fontsize=8, color=SUITABLE_COLOR if r['is_suitable'] else UNSUITABLE_COLOR,
                  va='center', fontweight='bold')
    ax_e.set_title('Top 3 Recommended Programs', fontsize=10, fontweight='bold', pad=8)
    ax_e.set_xlim(0,1); ax_e.set_ylim(0,1)

    # Plot F: Preferred program comparison
    ax_f = fig.add_subplot(gs[3, :])
    ax_f.axis('off')
    ax_f.set_facecolor('#FFFFFF')
    if has_pref and pref in PROGRAM_MAP:
        pref_name = PROGRAM_MAP[pref]
        r_pref = prog_res[pref]
        pref_rank = ranked.index(pref)+1
        in_top3 = pref in top3
        status_text = f"✅ Preferred ({pref_name}) in Top 3 — Rank #{pref_rank}" if in_top3 else \
                      f"⚠️ Preferred ({pref_name}) NOT in Top 3 (Rank #{pref_rank})"
        ax_f.text(0.5, 0.90, 'Preferred Program Analysis', ha='center',
                  fontsize=11, fontweight='bold')
        ax_f.text(0.5, 0.72, status_text, ha='center', fontsize=10,
                  fontweight='bold', color=SUITABLE_COLOR if in_top3 else UNSUITABLE_COLOR)
        if not in_top3:
            if pref == 1 and not result['ste_eligible']:
                reason = "G6 STE eligibility not met: " + ', '.join(result['ste_failed'])
            else:
                diff = r_pref['threshold'] - r_pref['predicted_avg']
                reason = f"Predicted {r_pref['predicted_avg']:.2f} is {diff:.2f} below {r_pref['threshold']} threshold."
            ax_f.text(0.5, 0.42, f"Reason: {reason}", ha='center', fontsize=9, wrap=True)
            ax_f.text(0.5, 0.18, f"Best fit: {PROGRAM_MAP[top3[0]]} "
                      f"(pred. avg {prog_res[top3[0]]['predicted_avg']:.2f})",
                      ha='center', fontsize=9)
    else:
        ax_f.text(0.5, 0.60,
                  "Preferred program is OHSP/SNEd — outside scope.\n"
                  "Recommendations based solely on predicted performance.",
                  ha='center', fontsize=10, color='#555555', style='italic')

    # Save
    safe_name = name.replace(' ', '_').replace('/', '-')
    if output_filename is None:
        output_filename = f'recommendation_ridge_{safe_name}.png'
    plt.savefig(output_filename, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    return output_filename

# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("\n" + "=" * 66)
    print("  SPARK SYSTEM (Ridge) — Student Placement Prediction")
    print("  Loading trained Ridge models...")
    print("=" * 66)

    config, classifier, regressors = load_models()
    print("  ✓ Models loaded successfully.")

    while True:
        student_data = collect_student_data()
        print("\n  Processing... predicting across all programs...")
        result = predict_for_student(student_data, config, classifier, regressors)
        display_results_console(result)
        print("  Generating visual report...")
        report_file = generate_visual_report(result)
        print(f"  ✓ Visual report saved: {report_file}")
        again = input("\n  Predict for another student? [y/n]: ").strip().lower()
        if again not in ['y', 'yes']:
            print("\n  Thank you for using SPARK System. Goodbye!\n")
            break

if __name__ == '__main__':
    main()