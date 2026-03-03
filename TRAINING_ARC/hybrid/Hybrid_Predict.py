"""
================================================================================
SPARK SYSTEM — Hybrid Model: New Student Prediction Interface
================================================================================

DESCRIPTION:
    This script loads the trained Hybrid Two-Stage ML Framework (Ridge + XGBoost)
    and accepts input data for one or more new Grade 6 students. It then outputs:

        Stage 1 → Predicted G7 Q1 average for each of the 5 programs
        Stage 2 → Top program recommendation (XGBoost classification)

    Additionally, it produces:
        • A formatted recommendation report printed to the console
        • An optional per-student recommendation card saved as PNG

USAGE:
    ① Run Hybrid_TwoStage_Framework.py first to generate 'hybrid_models/'
    ② Fill in the student data in the INPUT SECTION at the bottom of this file
    ③ Run:  python Hybrid_Predict.py

    — OR —
    Run interactively:  python Hybrid_Predict.py --interactive
    The script will prompt you for each field one by one.

REQUIREMENTS:
    Same environment as Hybrid_TwoStage_Framework.py
    (scikit-learn, xgboost, imbalanced-learn, pandas, numpy, matplotlib)
================================================================================
"""

import os
import sys
import warnings
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import joblib
warnings.filterwarnings('ignore')

from sklearn.impute import SimpleImputer

# ==============================================================================
# SECTION 1: CONSTANTS (must match training script exactly)
# ==============================================================================

PROGRAM_MAP = {
    1: 'STE',
    2: 'SPFL',
    3: 'SPTVE',
    4: 'TOP-5',
    5: 'HETERO'
}

PROGRAM_COLORS = {
    1: '#2E86AB',
    2: '#A23B72',
    3: '#F18F01',
    4: '#C73E1D',
    5: '#3B1F2B'
}

PROGRAM_DESCRIPTIONS = {
    1: 'Science, Technology & Engineering',
    2: 'Special Program in Foreign Language',
    3: 'Special Program in Technical-Vocational Education',
    4: 'Top 5 / Academic Excellence Track',
    5: 'Heterogeneous / General Program'
}

SUITABILITY_THRESHOLD = {
    1: 85,
    2: 85,
    3: 85,
    4: 85,
    5: 75
}

STE_ELIGIBILITY_SUBJECTS = ['grade_math', 'grade_science', 'grade_english']
STE_ELIGIBILITY_MIN_GRADE = 83

LABEL_OFFSET = 1   # XGBoost was trained with labels {0,1,2,3,4}

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
    'has_valid_preference'    # engineered feature — added during training
]

FEATURES = G6_ACADEMIC + NON_ACADEMIC

# Human-readable labels for interactive prompts
FIELD_PROMPTS = {
    # ── Grade 6 Academic ──
    'grade_math':             ('Grade 6 Mathematics grade',           60, 100),
    'grade_science':          ('Grade 6 Science grade',               60, 100),
    'grade_english':          ('Grade 6 English grade',               60, 100),
    'grade_filipino':         ('Grade 6 Filipino grade',              60, 100),
    'grade_arpan':            ('Grade 6 ARPAN grade',                 60, 100),
    'grade_mapeh':            ('Grade 6 MAPEH grade',                 60, 100),
    'average_grade_tle':      ('Grade 6 TLE average grade',           60, 100),
    'grade_esp':              ('Grade 6 ESP grade',                   60, 100),
    # grade_6_final_average is auto-computed — not prompted

    # ── Personal / Demographic ──
    'age':                    ('Age (years)',                          10, 15),
    'gender':                 ('Gender (0=Female, 1=Male)',            0, 1),
    'learning_style':         ('Learning style\n   1=Visual  2=Auditory  3=Kinesthetic  4=Read/Write', 1, 4),
    'study_hours_daily':      ('Daily study hours (1=<1hr  2=1-2hrs  3=2-3hrs  4=>3hrs)',              1, 4),
    'support_person':         ('Main support person\n   1=Parent  2=Sibling  3=Tutor  4=Self',         1, 4),
    'assignment_completion':  ('Assignment completion rate\n   1=Rarely  2=Sometimes  3=Usually  4=Always', 1, 4),
    'handle_difficulty':      ('Handles academic difficulty\n   1=Gives up  2=Seeks help  3=Persists independently', 1, 3),

    # ── Subject Enjoyment ──
    'enjoy_math':             ('Enjoys Math? (0=No, 1=Yes)',           0, 1),
    'enjoy_science':          ('Enjoys Science? (0=No, 1=Yes)',        0, 1),
    'enjoy_english':          ('Enjoys English? (0=No, 1=Yes)',        0, 1),
    'enjoy_filipino':         ('Enjoys Filipino? (0=No, 1=Yes)',       0, 1),
    'enjoy_arpan':            ('Enjoys ARPAN? (0=No, 1=Yes)',          0, 1),
    'enjoy_mapeh':            ('Enjoys MAPEH? (0=No, 1=Yes)',          0, 1),
    'enjoy_tle':              ('Enjoys TLE? (0=No, 1=Yes)',            0, 1),

    # ── Motivation & Interests ──
    'motivation_level':       ('Motivation level (1=Low  2=Moderate  3=High)', 1, 3),
    'enjoy_science_experiments': ('Enjoys science experiments? (0=No, 1=Yes)', 0, 1),
    'enjoy_reading':          ('Enjoys reading? (0=No, 1=Yes)',        0, 1),
    'enjoy_handson_activities': ('Enjoys hands-on activities? (0=No, 1=Yes)', 0, 1),
    'enjoy_sports':           ('Enjoys sports? (0=No, 1=Yes)',         0, 1),
    'enjoy_arts':             ('Enjoys arts? (0=No, 1=Yes)',           0, 1),
    'enjoy_language_related_activities': ('Enjoys language activities? (0=No, 1=Yes)', 0, 1),
    'foreign_language_interest': ('Foreign language interest\n   1=None  2=Low  3=Moderate  4=High', 1, 4),
    'competition_participation': ('Joined academic competitions? (0=No, 1=Yes)', 0, 1),

    # ── Resources ──
    'device_availability':    ('Device availability\n   1=None  2=Shared  3=Own device', 1, 3),
    'internet_access':        ('Internet access\n   1=None  2=Limited  3=Reliable',      1, 3),
    'absences_count':         ('Number of absences this school year', 0, 60),
    'family_income_help':     ('Family income support (0=No, 1=Yes)',  0, 1),
    'school_participation':   ('School/extracurricular participation\n   1=None  2=Low  3=Moderate  4=Active', 1, 4),

    # ── Awards ──
    'received_awards':        ('Received any academic awards? (0=No, 1=Yes)', 0, 1),
    'award_highest_honors':   ('With Highest Honors award? (0=No, 1=Yes)',    0, 1),
    'award_high_honors':      ('With High Honors award? (0=No, 1=Yes)',       0, 1),
    'award_with_honors':      ('With Honors award? (0=No, 1=Yes)',            0, 1),
    'award_best_science':     ('Best in Science award? (0=No, 1=Yes)',        0, 1),
    'award_best_math':        ('Best in Math award? (0=No, 1=Yes)',           0, 1),
    'award_best_english':     ('Best in English award? (0=No, 1=Yes)',        0, 1),
    'award_conduct':          ('Best in Conduct award? (0=No, 1=Yes)',        0, 1),
    'achiever_award':         ('Achiever award? (0=No, 1=Yes)',               0, 1),

    # ── Learning Challenges ──
    'difficulty_reading':     ('Reading difficulty? (0=No, 1=Yes)',           0, 1),
    'difficulty_writing':     ('Writing difficulty? (0=No, 1=Yes)',           0, 1),
    'difficulty_math':        ('Math difficulty? (0=No, 1=Yes)',              0, 1),
    'difficulty_focusing':    ('Focusing difficulty? (0=No, 1=Yes)',          0, 1),
    'difficulty_social_interaction': ('Social interaction difficulty? (0=No, 1=Yes)', 0, 1),
    'extra_support_recommended': ('Extra support recommended? (0=No, 1=Yes)', 0, 1),
    'quiet_study_place':      ('Has quiet place to study? (0=No, 1=Yes)',     0, 1),

    # ── Logistics ──
    'distance_from_school':   ('Distance from school\n   1=<1km  2=1-3km  3=3-5km  4=>5km', 1, 4),
    'travel_difficulty':      ('Travel difficulty? (0=No, 1=Yes)',            0, 1),

    # ── Preference ──
    'preferred_program':      ('Preferred program (1=STE  2=SPFL  3=SPTVE  4=TOP-5  5=HETERO  6=OHSP  7=SNEd)', 1, 7),
}

# ==============================================================================
# SECTION 2: MODEL LOADER
# ==============================================================================

def load_models(models_dir='hybrid_models'):
    """Load all trained models from the hybrid_models/ directory."""
    if not os.path.exists(models_dir):
        print(f"\n  ✗ ERROR: '{models_dir}/' not found.")
        print("  → Please run Hybrid_TwoStage_Framework.py first to train and save the models.\n")
        sys.exit(1)

    ridge_models = {}
    for prog_id, prog_name in PROGRAM_MAP.items():
        path = os.path.join(models_dir, f'ridge_{prog_name}.pkl')
        if not os.path.exists(path):
            print(f"  ✗ Missing model: {path}")
            sys.exit(1)
        ridge_models[prog_id] = joblib.load(path)

    clf_path = os.path.join(models_dir, 'xgboost_classifier.pkl')
    if not os.path.exists(clf_path):
        print(f"  ✗ Missing classifier: {clf_path}")
        sys.exit(1)
    clf_bundle = joblib.load(clf_path)

    return ridge_models, clf_bundle

# ==============================================================================
# SECTION 3: PREDICTION PIPELINE
# ==============================================================================

def predict_student(student_data: dict, ridge_models: dict, clf_bundle: dict) -> dict:
    """
    Run the full two-stage prediction for a single student.

    Parameters
    ----------
    student_data : dict
        Must contain all keys in FEATURES (plus 'preferred_program').
    ridge_models : dict
        {prog_id: {'model': Ridge, 'imputer': SimpleImputer, ...}}
    clf_bundle : dict
        {'model': XGBClassifier, 'scaler': StandardScaler,
         'imputer': SimpleImputer, 'clf_features': list, 'label_offset': int}

    Returns
    -------
    dict with keys:
        predicted_averages  — {prog_id: float}
        suitability         — {prog_id: bool}
        ste_eligible        — bool
        ste_ineligible_reason — str
        recommended_program — int (prog_id)
        probabilities       — {prog_id: float}
        top3               — [(prog_id, probability), ...]
        g6_final_average    — float
    """
    results = {}

    # ── Derive grade_6_final_average from the 8 subject grades
    g6_subjects = G6_ACADEMIC[:8]
    g6_avg = np.mean([student_data[s] for s in g6_subjects])
    student_data['grade_6_final_average'] = round(g6_avg, 3)
    results['g6_final_average'] = g6_avg

    # ── Engineer has_valid_preference
    pref = student_data.get('preferred_program', 0)
    student_data['has_valid_preference'] = 1 if pref in [1, 2, 3, 4, 5] else 0

    # ── Verify STE hard eligibility
    ste_eligible = all(
        student_data[s] >= STE_ELIGIBILITY_MIN_GRADE
        for s in STE_ELIGIBILITY_SUBJECTS
    )
    results['ste_eligible'] = ste_eligible
    if not ste_eligible:
        failed = [
            f"{s.replace('grade_', '').upper()} ({student_data[s]:.0f}<{STE_ELIGIBILITY_MIN_GRADE})"
            for s in STE_ELIGIBILITY_SUBJECTS
            if student_data[s] < STE_ELIGIBILITY_MIN_GRADE
        ]
        results['ste_ineligible_reason'] = ', '.join(failed)
    else:
        results['ste_ineligible_reason'] = 'Eligible'

    # ── Build base feature vector (shape: 1 × n_features)
    X_base = pd.DataFrame([{f: student_data.get(f, np.nan) for f in FEATURES}])

    # ──────────────────────────────────────────────────────────────────
    # STAGE 1: Ridge Regression — predict G7 Q1 average per program
    # ──────────────────────────────────────────────────────────────────
    predicted_averages = {}
    suitability = {}

    for prog_id, prog_name in PROGRAM_MAP.items():
        m       = ridge_models[prog_id]
        imputer = m['imputer']
        model   = m['model']

        X_imp  = imputer.transform(X_base)
        pred   = float(model.predict(X_imp)[0])
        pred   = round(pred, 2)
        predicted_averages[prog_id] = pred

        # Suitability check
        grade_ok = pred >= SUITABILITY_THRESHOLD[prog_id]
        if prog_id == 1:   # STE requires hard eligibility in addition
            suitability[prog_id] = grade_ok and ste_eligible
        else:
            suitability[prog_id] = grade_ok

    results['predicted_averages'] = predicted_averages
    results['suitability'] = suitability

    # ──────────────────────────────────────────────────────────────────
    # STAGE 2: XGBoost Classification — recommend best program
    # ──────────────────────────────────────────────────────────────────
    xgb_model   = clf_bundle['model']
    scaler      = clf_bundle['scaler']
    clf_imputer = clf_bundle['imputer']
    clf_features = clf_bundle['clf_features']
    label_offset = clf_bundle['label_offset']

    # Augment: original features + 5 predicted averages
    X_aug = X_base.copy()
    for prog_id, prog_name in PROGRAM_MAP.items():
        X_aug[f'pred_avg_{prog_name}'] = predicted_averages[prog_id]

    # Ensure column order matches training
    X_aug = X_aug[clf_features]

    # Impute → Scale → Predict
    X_aug_imp    = clf_imputer.transform(X_aug)
    X_aug_scaled = scaler.transform(X_aug_imp)

    proba_raw = xgb_model.predict_proba(X_aug_scaled)[0]

    probabilities = {
        pid: round(float(proba_raw[pid - label_offset]), 4)
        for pid in PROGRAM_MAP
    }

    # ── All programs ranked by XGBoost confidence (raw, no filter yet)
    all_ranked = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)

    # ── SUITABILITY GATE ──────────────────────────────────────────────
    # XGBoost ranks programs by statistical similarity to historical
    # cohorts, but a student should only be recommended a program they
    # are academically projected to thrive in (Stage 1 threshold gate).
    #
    # Rule: the final recommendation must come from the set of programs
    # where suitability[prog_id] is True (predicted avg >= threshold AND
    # STE hard-eligibility if applicable).
    #
    # Fallback: if NO program clears the gate, recommend HETERO (id=5)
    # because it has the lowest threshold (75) and is the general
    # catch-all program by institutional design.

    suitable_ranked = [
        (pid, prob) for pid, prob in all_ranked
        if suitability[pid]
    ]

    if suitable_ranked:
        final_recommendation = suitable_ranked[0][0]   # highest XGBoost confidence among suitable
        gate_applied = False
    else:
        final_recommendation = 5   # HETERO fallback
        gate_applied = True

    # Top-3 for display: only suitable programs (honest & actionable)
    top3 = suitable_ranked[:3] if suitable_ranked else [(5, probabilities[5])]

    results['recommended_program'] = final_recommendation
    results['probabilities']       = probabilities
    results['all_ranked']          = all_ranked      # raw XGBoost ranking kept for transparency
    results['top3']                = top3
    results['gate_applied']        = gate_applied

    return results

# ==============================================================================
# SECTION 4: CONSOLE REPORT
# ==============================================================================

def print_report(student_name: str, student_data: dict, results: dict):
    """Print a formatted recommendation report to the console."""
    sep = "═" * 68
    thin = "─" * 68

    print(f"\n{sep}")
    print(f"  SPARK SYSTEM — STUDENT RECOMMENDATION REPORT")
    print(f"{sep}")
    print(f"  Student : {student_name}")
    print(f"  G6 Final Average : {results['g6_final_average']:.2f}")
    print(f"  STE Eligibility  : {'✓ ELIGIBLE' if results['ste_eligible'] else '✗ INELIGIBLE — ' + results['ste_ineligible_reason']}")
    print(f"{thin}")

    # ── Stage 1 table ────────────────────────────────────────────────
    print("\n  ── STAGE 1: Predicted G7 Q1 Averages ──\n")
    print(f"  {'Program':<10}  {'Predicted Avg':>14}  {'Threshold':>10}  {'Suitable?':>10}")
    print(f"  {'─'*55}")
    for prog_id, prog_name in PROGRAM_MAP.items():
        pred    = results['predicted_averages'][prog_id]
        thresh  = SUITABILITY_THRESHOLD[prog_id]
        suit    = '✓ Yes' if results['suitability'][prog_id] else '✗ No'
        marker  = ' ◄ STE Ineligible' if (prog_id == 1 and not results['ste_eligible']) else ''
        print(f"  {prog_name:<10}  {pred:>14.2f}  {thresh:>10}  {suit:>10}{marker}")

    # ── Stage 2: raw XGBoost ranking (transparency) ──────────────────
    print(f"\n{thin}")
    print("\n  ── STAGE 2: XGBoost Raw Ranking (before suitability gate) ──\n")
    print(f"  {'Rank':<6}  {'Program':<10}  {'Confidence':>12}  {'Suitable?':>10}  {'Gate':>8}")
    print(f"  {'─'*55}")
    for rank, (prog_id, prob) in enumerate(results['all_ranked'], 1):
        prog_name = PROGRAM_MAP[prog_id]
        suit_bool = results['suitability'][prog_id]
        suit_str  = '✓ Yes' if suit_bool else '✗ No'
        gate_str  = '✓ Pass' if suit_bool else '✗ Blocked'
        print(f"  #{rank:<5}  {prog_name:<10}  {prob*100:>10.1f}%  {suit_str:>10}  {gate_str:>8}")

    # ── Stage 2: filtered recommendation ─────────────────────────────
    print(f"\n{thin}")
    print("\n  ── STAGE 2: Suitable Program Recommendations (after suitability gate) ──\n")

    if results['gate_applied']:
        print("  ⚠  No program met the suitability threshold.")
        print("     Defaulting to HETERO as the general program.\n")

    top3 = results['top3']
    medals = ['🥇', '🥈', '🥉']
    for rank, (prog_id, prob) in enumerate(top3):
        prog_name = PROGRAM_MAP[prog_id]
        prog_desc = PROGRAM_DESCRIPTIONS[prog_id]
        pred_avg  = results['predicted_averages'][prog_id]
        thresh    = SUITABILITY_THRESHOLD[prog_id]
        bar_len   = int(prob * 40)
        bar       = '█' * bar_len + '░' * (40 - bar_len)
        print(f"  {medals[rank]}  {prog_name:<8} — {prog_desc}")
        print(f"      XGBoost Confidence : {prob*100:5.1f}%  [{bar}]")
        print(f"      Predicted G7 Avg   : {pred_avg:.2f}  (threshold: {thresh})")
        print()

    rec_prog = results['recommended_program']
    print(f"{thin}")
    print(f"\n  ✅  RECOMMENDED PROGRAM : {PROGRAM_MAP[rec_prog]}")
    print(f"      {PROGRAM_DESCRIPTIONS[rec_prog]}")
    print(f"      XGBoost Confidence   : {results['probabilities'][rec_prog]*100:.1f}%")
    print(f"      Predicted G7 Average : {results['predicted_averages'][rec_prog]:.2f}  "
          f"(threshold: {SUITABILITY_THRESHOLD[rec_prog]})")
    print(f"\n{sep}\n")

# ==============================================================================
# SECTION 5: VISUALISATION — RECOMMENDATION CARD
# ==============================================================================

def save_recommendation_card(student_name: str, results: dict, filename: str = None):
    """
    Generate and save a visual recommendation card for the student.
    Suitable programs are shown in full colour; unsuitable ones are greyed out.
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#F8F9FA')
    fig.suptitle(
        f'SPARK Recommendation Card — {student_name}\n'
        f'G6 Final Average: {results["g6_final_average"]:.2f}  |  '
        f'Recommended: {PROGRAM_MAP[results["recommended_program"]]}',
        fontsize=13, fontweight='bold', y=1.02
    )

    prog_names  = list(PROGRAM_MAP.values())

    # ── Left: Predicted G7 Averages per Program ──────────────────────
    ax1 = axes[0]
    pred_vals = [results['predicted_averages'][p] for p in PROGRAM_MAP]

    # Colour: full colour if suitable, grey if not
    bar_colors_left = [
        PROGRAM_COLORS[p] if results['suitability'][p] else '#CCCCCC'
        for p in PROGRAM_MAP
    ]
    bars = ax1.bar(prog_names, pred_vals, color=bar_colors_left, alpha=0.88,
                   edgecolor='white', linewidth=1.2, width=0.55)

    # Per-program threshold lines
    for prog_id in PROGRAM_MAP:
        thresh = SUITABILITY_THRESHOLD[prog_id]
        ax1.axhline(thresh, color='red', linestyle='--', linewidth=0.8, alpha=0.4)

    ax1.set_ylim(max(0, min(pred_vals) - 10), min(100, max(pred_vals) + 8))
    ax1.set_ylabel('Predicted G7 Q1 Average', fontsize=11)
    ax1.set_title('Stage 1 — Predicted Grade per Program\n(grey = below threshold)', fontsize=11, fontweight='bold')
    ax1.grid(axis='y', alpha=0.25)
    ax1.set_facecolor('#FAFAFA')

    for bar, val, prog_id in zip(bars, pred_vals, PROGRAM_MAP.keys()):
        suit = results['suitability'][prog_id]
        icon = '✓' if suit else '✗'
        ax1.text(bar.get_x() + bar.get_width() / 2, val + 0.3,
                 f'{val:.1f}\n{icon}',
                 ha='center', va='bottom', fontsize=9, fontweight='bold',
                 color='#333333' if suit else '#999999')

    ax1.plot([], [], 'r--', linewidth=1, label='Suitability Threshold')
    ax1.legend(fontsize=8, loc='lower right')

    # ── Right: XGBoost Probabilities (only suitable programs shown) ───
    ax2 = axes[1]
    rec_prog = results['recommended_program']

    # Show all 5 but grey out unsuitable ones
    probs = [results['probabilities'][p] * 100 for p in PROGRAM_MAP]
    bar_colors_right = []
    for p in PROGRAM_MAP:
        if p == rec_prog:
            bar_colors_right.append('#FFD700')       # gold = recommended
        elif results['suitability'][p]:
            bar_colors_right.append(PROGRAM_COLORS[p])  # colour = suitable
        else:
            bar_colors_right.append('#CCCCCC')       # grey = unsuitable / gated out

    hbars = ax2.barh(prog_names[::-1], probs[::-1],
                     color=bar_colors_right[::-1], alpha=0.88,
                     edgecolor='white', linewidth=1.2, height=0.55)

    ax2.set_xlim(0, 115)
    ax2.set_xlabel('XGBoost Classification Confidence (%)', fontsize=11)
    ax2.set_title('Stage 2 — Program Probabilities\n(grey = blocked by suitability gate)', fontsize=11, fontweight='bold')
    ax2.grid(axis='x', alpha=0.25)
    ax2.set_facecolor('#FAFAFA')

    for bar, prob, prog_id in zip(hbars, probs[::-1], list(PROGRAM_MAP.keys())[::-1]):
        suit = results['suitability'][prog_id]
        label_color = '#333333' if suit else '#AAAAAA'
        ax2.text(prob + 0.8, bar.get_y() + bar.get_height() / 2,
                 f'{prob:.1f}%' + ('' if suit else ' ✗'),
                 va='center', fontsize=9, fontweight='bold', color=label_color)

    gold_patch = mpatches.Patch(color='#FFD700', label='Recommended')
    grey_patch = mpatches.Patch(color='#CCCCCC', label='Blocked (below threshold)')
    ax2.legend(handles=[gold_patch, grey_patch], fontsize=8, loc='lower right')

    plt.tight_layout()

    if filename is None:
        safe_name = student_name.replace(' ', '_').replace('/', '-')
        filename  = f'recommendation_{safe_name}.png'

    plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close()
    print(f"  → Recommendation card saved: {filename}")
    return filename

# ==============================================================================
# SECTION 6: INTERACTIVE INPUT MODE
# ==============================================================================

def get_float_input(prompt_label, lo, hi):
    """Prompt user for a float value within [lo, hi]."""
    while True:
        try:
            raw = input(f"  {prompt_label} [{lo}–{hi}]: ").strip()
            if raw == '':
                return np.nan
            val = float(raw)
            if lo <= val <= hi:
                return val
            print(f"    ⚠  Value must be between {lo} and {hi}. Try again.")
        except ValueError:
            print("    ⚠  Please enter a number.")

def collect_interactive():
    """Walk the user through all fields interactively."""
    print("\n" + "═"*68)
    print("  SPARK — Interactive Student Data Entry")
    print("  (Press ENTER to leave a field blank / use default)")
    print("═"*68)

    student_name = input("\n  Student name / ID: ").strip() or "New Student"

    data = {}

    # Grade 6 Academic subjects (prompted first)
    print("\n  ── Grade 6 Academic Grades ──")
    for field in G6_ACADEMIC[:8]:   # grade_6_final_average is computed
        label, lo, hi = FIELD_PROMPTS[field]
        data[field] = get_float_input(label, lo, hi)

    # Non-academic fields
    print("\n  ── Personal & Non-Academic Information ──")
    for field in NON_ACADEMIC:
        if field == 'has_valid_preference':
            continue   # computed from preferred_program
        label, lo, hi = FIELD_PROMPTS.get(
            field, (field.replace('_', ' ').title(), 0, 9)
        )
        data[field] = get_float_input(label, lo, hi)

    # Preferred program
    label, lo, hi = FIELD_PROMPTS['preferred_program']
    pref = get_float_input(label, lo, hi)
    data['preferred_program'] = pref

    return student_name, data


def collect_batch_from_csv(csv_path: str):
    """
    Load multiple students from a CSV file.
    The CSV must have a 'student_name' column plus all feature columns.
    Returns list of (name, data_dict) tuples.
    """
    df = pd.read_csv(csv_path)
    students = []
    for _, row in df.iterrows():
        name = str(row.get('student_name', row.get('student_id', 'Unknown')))
        data = {col: row[col] for col in row.index if col not in ('student_name', 'student_id')}
        students.append((name, data))
    return students


# ==============================================================================
# SECTION 7: MAIN ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='SPARK Hybrid Model — New Student Recommendation'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Prompt for student data field by field'
    )
    parser.add_argument(
        '--csv', '-c',
        type=str,
        default=None,
        help='Path to a CSV file with multiple students to predict'
    )
    parser.add_argument(
        '--models_dir', '-m',
        type=str,
        default='hybrid_models',
        help='Directory containing trained models (default: hybrid_models/)'
    )
    parser.add_argument(
        '--no_card',
        action='store_true',
        help='Skip saving recommendation card PNG'
    )
    args = parser.parse_args()

    print("\n" + "═"*68)
    print("  SPARK SYSTEM — Student Program Recommendation")
    print("  Hybrid Two-Stage Model  |  Ridge + XGBoost")
    print("═"*68)

    # ── Load models ──────────────────────────────────────────────────
    print(f"\n  Loading models from '{args.models_dir}/'...")
    ridge_models, clf_bundle = load_models(args.models_dir)
    print("  ✓ Models loaded successfully.")

    # ── Collect student data ─────────────────────────────────────────
    if args.csv:
        students = collect_batch_from_csv(args.csv)
        print(f"\n  → Loaded {len(students)} student(s) from '{args.csv}'")
    elif args.interactive:
        name, data = collect_interactive()
        students = [(name, data)]
    else:
        # ============================================================
        # MANUAL INPUT SECTION
        # ============================================================
        # Fill in the student data below.
        # All grade fields:  60–100
        # Binary fields (yes/no, awards, difficulties): 0 or 1
        # See FIELD_PROMPTS above for full value ranges.
        # ============================================================

       students = [
    # ── Student 2 ──────────────────────────────────────────────
    (
        "Maria Clara Santos",   # ← Student name
        {
            # Grade 6 Academic Grades (Range: 79-86)
            'grade_math':          79,
            'grade_science':       80,
            'grade_english':       85,
            'grade_filipino':      86,
            'grade_arpan':         82,
            'grade_mapeh':         84,
            'average_grade_tle':   81,
            'grade_esp':           85,
            # grade_6_final_average is computed automatically

            # Personal / Demographic
            'age':                 12,
            'gender':              2,        # 2=Female
            'learning_style':      2,        # 2=Auditory
            'study_hours_daily':   2,        # 1-2 hrs
            'support_person':      1,        # Parent
            'assignment_completion': 3,      # Most of the time
            'handle_difficulty':   2,        # Seeks help when stuck

            # Subject Enjoyment
            'enjoy_math':          0,
            'enjoy_science':       0,
            'enjoy_english':       1,
            'enjoy_filipino':      1,
            'enjoy_arpan':         0,
            'enjoy_mapeh':         1,
            'enjoy_tle':           1,

            # Motivation & Interests
            'motivation_level':    2,        # Moderate
            'enjoy_science_experiments': 0,
            'enjoy_reading':        1,
            'enjoy_handson_activities': 1,
            'enjoy_sports':         0,
            'enjoy_arts':           1,
            'enjoy_language_related_activities': 1,
            'foreign_language_interest': 1,
            'competition_participation': 0,

            # Resources
            'device_availability': 2,        # Shared device
            'internet_access':     2,        # Sometimes stable
            'absences_count':      5,
            'family_income_help':  1,
            'school_participation': 3,       # Participates often

            # Awards (Adjusted for grade range)
            'received_awards':     0,
            'award_highest_honors': 0,
            'award_high_honors':   0,
            'award_with_honors':   0,
            'award_best_science':  0,
            'award_best_math':     0,
            'award_best_english':  0,
            'award_conduct':       1,        # Good conduct award
            'achiever_award':      0,

            # Learning Challenges
            'difficulty_reading':  0,
            'difficulty_writing':  0,
            'difficulty_math':     1,        # Struggles with Math
            'difficulty_focusing': 1,        # Occasional focus issues
            'difficulty_social_interaction': 0,
            'extra_support_recommended': 1,
            'quiet_study_place':   1,

            # Logistics
            'distance_from_school': 1,      # < 1 km
            'travel_difficulty':   0,

            # Preference
            'preferred_program':   0,        # 0=Regular / RSEC
        }
    ),
]
        # ============================================================
        # END OF MANUAL INPUT SECTION
        # ============================================================

    # ── Run predictions ──────────────────────────────────────────────
    all_results = []
    for student_name, student_data in students:
        # Convert any pandas-typed values to plain Python floats
        clean_data = {k: float(v) if pd.notna(v) else np.nan
                      for k, v in student_data.items()}

        results = predict_student(clean_data, ridge_models, clf_bundle)
        print_report(student_name, clean_data, results)

        if not args.no_card:
            save_recommendation_card(student_name, results)

        all_results.append({
            'student':              student_name,
            'g6_final_average':     results['g6_final_average'],
            'ste_eligible':         results['ste_eligible'],
            'recommended_program':  PROGRAM_MAP[results['recommended_program']],
            'confidence_%':         round(results['probabilities'][results['recommended_program']] * 100, 2),
            **{f'pred_{PROGRAM_MAP[p]}': results['predicted_averages'][p] for p in PROGRAM_MAP},
            **{f'prob_{PROGRAM_MAP[p]}_%': round(results['probabilities'][p] * 100, 2) for p in PROGRAM_MAP},
        })

    # ── Save batch summary CSV if multiple students ───────────────────
    if len(all_results) > 1:
        out_df = pd.DataFrame(all_results)
        out_df.to_csv('spark_predictions.csv', index=False)
        print(f"\n  → Batch summary saved: spark_predictions.csv")

    print("\n  ✓ All predictions complete.\n")


if __name__ == '__main__':
    main()