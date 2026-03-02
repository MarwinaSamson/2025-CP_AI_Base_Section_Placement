"""
================================================================================
SPARK SYSTEM — Section Placement and Recommendation
Gradient Boosting Algorithm | Training & Evaluation Script
Capstone Project | Grade 7 Section Placement Prediction System
================================================================================

STUDY CONTEXT:
    This script trains and evaluates Gradient Boosting models as an alternative
    to the Random Forest baseline to determine which algorithm performs best
    for the SPARK Grade 7 section placement system.

ALGORITHM: Gradient Boosting (sklearn GradientBoosting — XGBoost/LightGBM equivalent)
──────────────────────────────────────────────────────────────────────────────
    sklearn's GradientBoostingRegressor and GradientBoostingClassifier implement
    the identical GBDT (Gradient Boosted Decision Tree) algorithm used by
    XGBoost and LightGBM. The mathematical approach is the same:

        Iteration 1 : Train a shallow tree on the raw residuals.
        Iteration k : Train a new tree on the errors left by all prior trees.
        Final output: Weighted sum of all trees (learning_rate controls each
                      tree's contribution — prevents overfitting via shrinkage).

    XGBoost / LightGBM differ from sklearn only in:
        • Engineering optimizations (histogram binning, GPU support)
        • Distributed training support
        • Missing-value handling built-in

    For a capstone comparison study on 594 students, the mathematical results
    are directly comparable. The same hyperparameters (n_estimators, max_depth,
    learning_rate, subsample) produce equivalent outcomes.

WHY GRADIENT BOOSTING vs RANDOM FOREST:
    Random Forest   → builds trees in PARALLEL on random data subsets (bagging)
    Gradient Boost  → builds trees SEQUENTIALLY, each correcting prior errors
    Advantage       → GB typically achieves lower bias on structured tabular data
    Trade-off       → GB is more sensitive to hyperparameters and noisy data

TWO-STAGE MODEL ARCHITECTURE (same as RF baseline):
    Stage 1: Gradient Boosting REGRESSION  → Predict Grade 7 Q1 grades per program
    Stage 2: Gradient Boosting CLASSIFIER  → Recommend best-fit program

PROFESSOR'S REQUIREMENTS IMPLEMENTED:
    - Model loops 5 times (once per program) to predict grades
    - Suitability threshold: ≥85 for STE/SPFL/SPTVE/TOP-5, ≥75 for HETERO
    - STE HARD ELIGIBILITY: Grade 6 Math, Science, AND English must all be ≥83
    - Top 3 programs displayed with explanation
    - Preferred program comparison included

EVALUATION METRICS:
    Regression    : R², MAE, RMSE  +  5-fold Cross-Validated R²
    Classification: Accuracy, Precision, Recall, F1-Score, Confusion Matrix

OUTPUT FILES:
    Models : gbr_models/  (all trained models for GBR_predict.py)
    Plots  : plot_gbr_01 through plot_gbr_15
    CSV    : gbr_regression_metrics.csv
             gbr_classification_metrics.csv
             gbr_suitability_scores.csv

COMPARISON NOTE:
    Run this script alongside RF_training.py and compare outputs side-by-side.
    Both scripts use identical preprocessing, the same RANDOM_STATE=42 splits,
    and the same evaluation metrics — ensuring a fair algorithm comparison.
================================================================================
"""

# ==============================================================================
# SECTION 0: IMPORTS
# ==============================================================================
import os
import joblib
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')     # Non-interactive backend — safe for all environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
warnings.filterwarnings('ignore')

from sklearn.ensemble import GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score,
                              accuracy_score, precision_score, recall_score,
                              f1_score, confusion_matrix, classification_report)
from sklearn.impute import SimpleImputer

# ==============================================================================
# SECTION 1: CONSTANTS AND CONFIGURATION
# (Identical to RF_training.py — no changes to preserve preprocessing parity)
# ==============================================================================

PROGRAM_MAP = {
    1: 'STE',
    2: 'SPFL',
    3: 'SPTVE',
    4: 'TOP-5',
    5: 'HETERO'
}

PROGRAM_COLORS = {
    1: '#2E86AB',   # Blue     - STE
    2: '#A23B72',   # Purple   - SPFL
    3: '#F18F01',   # Orange   - SPTVE
    4: '#C73E1D',   # Red      - TOP-5
    5: '#3B1F2B'    # Dark     - HETERO
}

# Suitability threshold per program (professor's requirement)
SUITABILITY_THRESHOLD = {
    1: 85,   # STE
    2: 85,   # SPFL
    3: 85,   # SPTVE
    4: 85,   # TOP-5 Regular
    5: 75    # HETERO
}

# STE HARD ELIGIBILITY RULE (school policy — cannot be overridden by predicted grades)
# A student is INELIGIBLE for STE if ANY of these Grade 6 grades is below 83.
STE_ELIGIBILITY_SUBJECTS  = ['grade_math', 'grade_science', 'grade_english']
STE_ELIGIBILITY_MIN_GRADE = 83

# Grade 6 academic feature columns
G6_ACADEMIC = [
    'grade_math', 'grade_science', 'grade_english', 'grade_filipino',
    'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp',
    'grade_6_final_average'
]

# Non-academic survey feature columns
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
    'distance_from_school', 'travel_difficulty'
]

# All input features (combined — has_valid_preference appended in preprocessing)
FEATURES = G6_ACADEMIC + NON_ACADEMIC

# Grade 7 common target subjects (all programs)
G7_COMMON_SUBJECTS = [
    'q1_g7_filipino', 'q1_g7_english', 'q1_g7_math', 'q1_g7_science',
    'q1_g7_arpan', 'q1_g7_tle', 'q1_g7_mapeh', 'q1_g7_esp'
]

# Program-exclusive G7 subjects
G7_EXCLUSIVE = {
    1: 'q1_g7research',          # STE only
    2: 'q1_g7_foreign_language', # SPFL only
    3: 'q1_g7_tve'               # SPTVE only
}

def get_program_subjects(program_id):
    """Return list of G7 subjects relevant to this program."""
    subjects = G7_COMMON_SUBJECTS.copy()
    if program_id in G7_EXCLUSIVE:
        subjects.append(G7_EXCLUSIVE[program_id])
    return subjects

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("=" * 70)
print("  SPARK SYSTEM — Section Placement Prediction")
print("  Algorithm: Gradient Boosting (XGBoost/LightGBM equivalent)")
print("  Capstone Project | ML Training Pipeline")
print("=" * 70)

# ==============================================================================
# SECTION 2: LOAD DATA
# ==============================================================================
print("\n[STEP 1] Loading dataset...")

df = pd.read_csv('DATASET/SPARK_DATASET.csv')

print(f"  → Dataset loaded: {df.shape[0]} students, {df.shape[1]} columns")
print(f"  → Program distribution:")
for p, name in PROGRAM_MAP.items():
    count = (df['actual_placement'] == p).sum()
    print(f"     {name:10s}: {count} students")

# ==============================================================================
# SECTION 3: DATA PREPROCESSING
# (Line-for-line identical to RF_training.py — ensures fair algorithm comparison)
# ==============================================================================
print("\n[STEP 2] Data Preprocessing...")

# ------------------------------------------------------------------------------
# 3.1 — Fix preferred_program = 6 (students who preferred OHSP/SNEd)
# ------------------------------------------------------------------------------
# Students who preferred OHSP or SNEd are coded as 6.
# Since these programs are out of scope, we flag them instead of dropping.
df['has_valid_preference'] = df['preferred_program'].apply(
    lambda x: 1 if x in [1.0, 2.0, 3.0, 4.0, 5.0] else 0
)
NON_ACADEMIC.append('has_valid_preference')
FEATURES.append('has_valid_preference')

flagged = (df['has_valid_preference'] == 0).sum()
print(f"  → Flagged {flagged} students with out-of-scope preferred program (OHSP/SNEd)")

# ------------------------------------------------------------------------------
# 3.2 — NON-ACADEMIC missing value imputation (mode)
# WHAT:   Mode imputation for categorical/ordinal survey columns.
# WHY:    Survey data (Likert-scale, binary) has small missing counts (2-13).
#         Mode preserves the most common response pattern — appropriate for
#         ordinal survey data where the median/mode is the expected value.
# ------------------------------------------------------------------------------
print("  → Imputing non-academic missing values (mode imputation)...")

non_academic_imputer = SimpleImputer(strategy='most_frequent')
df[NON_ACADEMIC] = non_academic_imputer.fit_transform(df[NON_ACADEMIC])

missing_non_academic = df[NON_ACADEMIC].isnull().sum().sum()
print(f"     Remaining NaN in non-academic columns: {missing_non_academic}")

# ------------------------------------------------------------------------------
# 3.3 — GRADE 7 STRUCTURAL NaN (Not a problem — program-exclusive subjects)
# Program-exclusive subjects are NaN for other programs by design.
# NOT imputed — they are simply not used in those programs' models.
# ------------------------------------------------------------------------------
print("  → Confirmed: Program-exclusive G7 subjects are structurally NaN for")
print("    other programs — no imputation needed for these.")

# ------------------------------------------------------------------------------
# 3.4 — GRADE 7 COMMON SUBJECTS: Group Mean Imputation
# WHAT:   Fill missing Grade 7 grades with the mean of students in the SAME
#         placement group (not the overall mean).
# WHY:    Missing G7 grades are NOT missing at random — they depend on which
#         program the student is in. STE students average higher than HETERO.
#         Group mean preserves this between-program grade distinction.
# ------------------------------------------------------------------------------
print("  → Imputing Grade 7 common subjects (group mean imputation by program)...")

df_before_impute = df[G7_COMMON_SUBJECTS + ['q1_g7_final_grade']].copy()

for col in G7_COMMON_SUBJECTS + ['q1_g7_final_grade']:
    before_missing = df[col].isnull().sum()
    df[col] = df.groupby('actual_placement')[col].transform(
        lambda x: x.fillna(x.mean())
    )
    after_missing = df[col].isnull().sum()
    if before_missing > 0:
        print(f"     {col:30s}: {before_missing} NaN → {after_missing} NaN")

# Program-exclusive subject imputation (within-program only)
print("  → Imputing program-exclusive G7 subjects (within-program mean)...")
for prog_id, col in G7_EXCLUSIVE.items():
    mask       = df['actual_placement'] == prog_id
    before     = df.loc[mask, col].isnull().sum()
    group_mean = df.loc[mask, col].mean()
    df.loc[mask, col] = df.loc[mask, col].fillna(group_mean)
    after      = df.loc[mask, col].isnull().sum()
    print(f"     {PROGRAM_MAP[prog_id]} - {col:30s}: {before} NaN → {after} NaN")

# Fix student_061 final grade mismatch (verified data entry error)
student_061_mask = df['student_id'] == 'student_061'
if student_061_mask.any():
    computed = df.loc[student_061_mask, G7_COMMON_SUBJECTS].mean(axis=1).values[0]
    df.loc[student_061_mask, 'q1_g7_final_grade'] = round(computed, 3)
    print(f"  → Fixed student_061 final grade: corrected to computed average {computed:.3f}")

print(f"  → Preprocessing complete. Final NaN check:")
remaining_nan = df[G7_COMMON_SUBJECTS + ['q1_g7_final_grade']].isnull().sum().sum()
print(f"     Total remaining NaN in G7 grades: {remaining_nan}")

# ==============================================================================
# SECTION 4: OUTLIER DETECTION AND WINSORIZATION
# (Identical to RF_training.py — same data treatment for fair comparison)
# ==============================================================================
print("\n[STEP 3] Outlier Detection and Treatment...")

"""
OUTLIER STRATEGY:
- Statistical detection using IQR (Interquartile Range) method
- Winsorization applied to cap extreme values at 5th and 95th percentile
  WITHIN each program group (prevents cross-program contamination)
- Most critical case: student_071's Science grade of 39.6 in HETERO
"""

def detect_outliers_iqr(series, multiplier=1.5):
    """Detect outliers using IQR method."""
    Q1  = series.quantile(0.25)
    Q3  = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR
    return series[(series < lower) | (series > upper)]

# --- Plot GBR-01: Outlier Detection Visualization ---
fig, axes = plt.subplots(2, 4, figsize=(18, 10))
fig.suptitle('Grade 7 Q1 Grades — Outlier Detection (Before Winsorization)\n'
             '[Gradient Boosting Pipeline]',
             fontsize=14, fontweight='bold', y=1.01)

all_outliers_found = {}

for idx, col in enumerate(G7_COMMON_SUBJECTS):
    ax           = axes[idx // 4][idx % 4]
    subject_name = col.replace('q1_g7_', '').replace('_', ' ').upper()

    data_by_program = []
    labels          = []
    outlier_info    = {}

    for p in [1, 2, 3, 4, 5]:
        prog_data = df[df['actual_placement'] == p][col].dropna()
        data_by_program.append(prog_data.values)
        labels.append(PROGRAM_MAP[p])
        outliers = detect_outliers_iqr(prog_data)
        if len(outliers) > 0:
            outlier_info[PROGRAM_MAP[p]] = outliers.values
            all_outliers_found[f"{PROGRAM_MAP[p]}-{col}"] = outliers

    bp = ax.boxplot(data_by_program, labels=labels, patch_artist=True,
                    medianprops=dict(color='red', linewidth=2))

    colors_list = list(PROGRAM_COLORS.values())
    for patch, color in zip(bp['boxes'], colors_list):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    for i, (prog_data, label) in enumerate(zip(data_by_program, labels)):
        if label in outlier_info:
            for val in outlier_info[label]:
                ax.annotate(f'★{val:.1f}', xy=(i + 1, val),
                            fontsize=7, color='red', ha='center', fontweight='bold')

    ax.set_title(subject_name, fontweight='bold', fontsize=10)
    ax.set_xlabel('Program', fontsize=8)
    ax.set_ylabel('Grade', fontsize=8)
    ax.tick_params(axis='x', labelsize=7)
    ax.axhline(y=75, color='orange', linestyle='--', alpha=0.5, linewidth=1)
    ax.axhline(y=85, color='green',  linestyle='--', alpha=0.5, linewidth=1)
    ax.grid(axis='y', alpha=0.3)

orange_line = mpatches.Patch(color='orange', alpha=0.5, label='75 threshold (HETERO)')
green_line  = mpatches.Patch(color='green',  alpha=0.5, label='85 threshold (Special/TOP-5)')
star_patch  = mpatches.Patch(color='red',              label='★ Detected Outlier')
fig.legend(handles=[orange_line, green_line, star_patch],
           loc='lower center', ncol=3, fontsize=9, bbox_to_anchor=(0.5, -0.02))

plt.tight_layout()
plt.savefig('plot_gbr_01_outlier_detection.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_01_outlier_detection.png")
print(f"  → Outlier groups detected: {len(all_outliers_found)}")

# --- Apply Winsorization per program group (5th–95th percentile) ---
"""
WINSORIZATION:
    Caps extreme values at the 5th and 95th percentile WITHIN each program group.
    Preserves the relative distribution while preventing extreme values from
    disproportionately influencing Gradient Boosting tree splits.
    Applied per-program to avoid cross-program mean contamination.
"""
df_before_wins = df[G7_COMMON_SUBJECTS].copy()

winsorized_count = 0
for col in G7_COMMON_SUBJECTS:
    for p in [1, 2, 3, 4, 5]:
        mask        = df['actual_placement'] == p
        prog_data   = df.loc[mask, col]
        lower_p     = prog_data.quantile(0.05)
        upper_p     = prog_data.quantile(0.95)
        before_vals = df.loc[mask, col].copy()
        df.loc[mask, col] = df.loc[mask, col].clip(lower=lower_p, upper=upper_p)
        changed     = (before_vals != df.loc[mask, col]).sum()
        winsorized_count += changed

print(f"  → Winsorization applied: {winsorized_count} values adjusted")

# --- Plot GBR-02: Before vs After Winsorization ---
fig, axes = plt.subplots(2, 4, figsize=(18, 10))
fig.suptitle('Grade 7 Q1 Grades — Before vs After Winsorization\n'
             '[Gradient Boosting Pipeline]',
             fontsize=14, fontweight='bold')

for idx, col in enumerate(G7_COMMON_SUBJECTS):
    ax           = axes[idx // 4][idx % 4]
    subject_name = col.replace('q1_g7_', '').replace('_', ' ').upper()
    before_data  = df_before_wins[col].dropna()
    after_data   = df[col].dropna()

    ax.hist(before_data, bins=20, alpha=0.5, color='#E63946', label='Before',
            edgecolor='white', linewidth=0.5)
    ax.hist(after_data,  bins=20, alpha=0.5, color='#2A9D8F', label='After',
            edgecolor='white', linewidth=0.5)
    ax.axvline(before_data.min(), color='red',   linestyle=':', alpha=0.7,
               linewidth=1.5, label=f'Min before: {before_data.min():.1f}')
    ax.axvline(after_data.min(),  color='green', linestyle=':', alpha=0.7,
               linewidth=1.5, label=f'Min after: {after_data.min():.1f}')
    ax.set_title(subject_name, fontweight='bold', fontsize=10)
    ax.set_xlabel('Grade', fontsize=8)
    ax.set_ylabel('Count', fontsize=8)
    ax.legend(fontsize=6)
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('plot_gbr_02_winsorization.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_02_winsorization.png")

# ==============================================================================
# SECTION 5: EXPLORATORY DATA ANALYSIS PLOTS
# ==============================================================================
print("\n[STEP 4] Generating EDA visualizations...")

# --- Plot GBR-03: Grade 6 Average Distribution by Program ---
fig, ax = plt.subplots(figsize=(12, 6))
for p, name in PROGRAM_MAP.items():
    data = df[df['actual_placement'] == p]['grade_6_final_average']
    ax.hist(data, bins=15, alpha=0.6, label=f'{name} (n={len(data)})',
            color=PROGRAM_COLORS[p], edgecolor='white')

ax.axvline(85, color='black', linestyle='--', linewidth=2, label='85 Threshold')
ax.set_title('Grade 6 Final Average Distribution by Program',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Grade 6 Final Average', fontsize=12)
ax.set_ylabel('Number of Students',    fontsize=12)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_gbr_03_g6_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_03_g6_distribution.png")

# --- Plot GBR-04: Grade 7 Final Grade Distribution by Program ---
fig, ax = plt.subplots(figsize=(12, 6))
for p, name in PROGRAM_MAP.items():
    data = df[df['actual_placement'] == p]['q1_g7_final_grade']
    ax.hist(data, bins=15, alpha=0.6, label=f'{name} (n={len(data)})',
            color=PROGRAM_COLORS[p], edgecolor='white')

ax.axvline(85, color='black', linestyle='--', linewidth=2,
           label='85 Suitability Threshold')
ax.axvline(75, color='gray',  linestyle='--', linewidth=2,
           label='75 HETERO Threshold')
ax.set_title('Grade 7 Q1 Final Grade Distribution by Program',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Grade 7 Q1 Final Grade', fontsize=12)
ax.set_ylabel('Number of Students',     fontsize=12)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_gbr_04_g7_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_04_g7_distribution.png")

# --- Plot GBR-05: Grade 6 vs Grade 7 Scatter per Program ---
fig, axes = plt.subplots(1, 5, figsize=(20, 5))
fig.suptitle('Grade 6 Final Average vs Grade 7 Q1 Final Grade by Program',
             fontsize=13, fontweight='bold')

for idx, (p, name) in enumerate(PROGRAM_MAP.items()):
    ax      = axes[idx]
    prog_df = df[df['actual_placement'] == p]
    ax.scatter(prog_df['grade_6_final_average'], prog_df['q1_g7_final_grade'],
               color=PROGRAM_COLORS[p], alpha=0.6, edgecolors='white', s=40)

    x = prog_df['grade_6_final_average'].dropna()
    y = prog_df['q1_g7_final_grade'].dropna()
    if len(x) > 1:
        z      = np.polyfit(x, y, 1)
        p_line = np.poly1d(z)
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, p_line(x_line), color='black', linewidth=2, linestyle='--')

    ax.axhline(SUITABILITY_THRESHOLD[p], color='red', linestyle=':', linewidth=1.5,
               label=f'Threshold: {SUITABILITY_THRESHOLD[p]}')
    ax.set_title(f'{name}\n(n={len(prog_df)})', fontweight='bold', fontsize=10)
    ax.set_xlabel('G6 Avg', fontsize=8)
    ax.set_ylabel('G7 Q1 Avg', fontsize=8)
    ax.legend(fontsize=7)
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('plot_gbr_05_g6_vs_g7_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_05_g6_vs_g7_scatter.png")

# --- Plot GBR-06: Subject-level Grade 7 averages per program ---
fig, ax = plt.subplots(figsize=(14, 7))
subject_labels = [s.replace('q1_g7_', '').replace('_', '\n').upper()
                  for s in G7_COMMON_SUBJECTS]
x     = np.arange(len(G7_COMMON_SUBJECTS))
width = 0.15

for i, (p, name) in enumerate(PROGRAM_MAP.items()):
    prog_df = df[df['actual_placement'] == p]
    means   = [prog_df[col].mean() for col in G7_COMMON_SUBJECTS]
    ax.bar(x + i * width, means, width, label=name,
           color=PROGRAM_COLORS[p], alpha=0.85, edgecolor='white')

ax.axhline(85, color='green',  linestyle='--', linewidth=1.5, alpha=0.7, label='85 Threshold')
ax.axhline(75, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='75 Threshold')
ax.set_xticks(x + width * 2)
ax.set_xticklabels(subject_labels, fontsize=9)
ax.set_title('Average Grade 7 Q1 Grades by Subject and Program',
             fontsize=14, fontweight='bold')
ax.set_ylabel('Average Grade', fontsize=12)
ax.set_ylim(70, 100)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_gbr_06_g7_subject_averages.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_06_g7_subject_averages.png")

# ==============================================================================
# SECTION 6: STAGE 1 — GRADIENT BOOSTING REGRESSION (THE 5-LOOP)
# ==============================================================================
print("\n" + "=" * 70)
print("  STAGE 1: GRADIENT BOOSTING REGRESSION — Grade Prediction (5-Loop)")
print("=" * 70)

"""
THE 5-LOOP PROCESS:
    For each of the 5 programs, we train a separate regression model.
    Each model answers: "What Grade 7 average would this student achieve
    IF placed in this specific program?"

    This is the core insight of the SPARK architecture: we simulate performance
    across all programs — then recommend based on predicted performance.

GRADIENT BOOSTING REGRESSOR HYPERPARAMETERS:
    n_estimators  = 200    → 200 sequential trees (same count as RF baseline)
    learning_rate = 0.08   → Shrinkage factor per tree.
                             Lower = more conservative, less overfit.
                             0.08 balances speed vs generalization.
    max_depth     = 4      → Shallow trees (RF baseline uses 8).
                             GB needs shallower trees because each tree only
                             corrects a fraction of the remaining error.
                             Deep trees in GB cause overfitting quickly.
    subsample     = 0.8    → Use 80% of training data per tree (stochastic GB).
                             Adds variance reduction — helps on small samples.
    min_samples_split = 3  → Same as RF baseline.
    min_samples_leaf  = 2  → Same as RF baseline — prevents single-sample leaves.

WHY GRADIENT BOOSTING FOR GRADE PREDICTION:
    - Sequential error correction typically achieves lower bias than RF on
      structured tabular data with ordinal features (grade scales)
    - Built-in regularization via learning_rate + subsample
    - Each new tree focuses exclusively on the hardest-to-predict students,
      improving accuracy on edge cases (borderline placements)
"""

regression_models   = {}      # Trained model objects
regression_metrics  = {}      # Evaluation metrics per program
feature_importances_reg = {}  # Feature importances per program
all_program_predictions = {}  # Predictions for all 594 students (for Stage 2)

for loop_num, (program_id, program_name) in enumerate(PROGRAM_MAP.items(), 1):

    print(f"\n  ── Loop {loop_num}/5: Training GBR Model for {program_name} ──")

    # ── Step A: Filter to students in this program ──────────────────────────
    prog_df              = df[df['actual_placement'] == program_id].copy()
    subjects_for_program = get_program_subjects(program_id)

    print(f"     Training samples : {len(prog_df)} students in {program_name}")
    print(f"     Prediction target: {len(subjects_for_program)} subjects "
          f"({'+ ' + G7_EXCLUSIVE[program_id].replace('q1_g7_','').upper() if program_id in G7_EXCLUSIVE else 'common only'})")

    # ── Step B: Prepare features (X) and target (y) ─────────────────────────
    X       = prog_df[FEATURES].copy()
    y_final = prog_df['q1_g7_final_grade'].copy()

    # Mean-impute any remaining NaN in features
    feat_imputer = SimpleImputer(strategy='mean')
    X_imputed    = feat_imputer.fit_transform(X)
    X_imputed    = pd.DataFrame(X_imputed, columns=FEATURES)

    # ── Step C: 80/20 Train/Test Split ──────────────────────────────────────
    # SAME RANDOM_STATE as RF_training.py → identical splits → fair comparison
    X_train, X_test, y_train, y_test = train_test_split(
        X_imputed, y_final, test_size=0.2, random_state=RANDOM_STATE
    )

    # ── Step D: Train Gradient Boosting Regressor ────────────────────────────
    gbr_reg = GradientBoostingRegressor(
        n_estimators=200,     # 200 sequential trees
        learning_rate=0.08,   # Shrinkage per tree — prevents overfitting
        max_depth=4,          # Shallow trees required for GB
        subsample=0.8,        # Stochastic GB — 80% of data per tree
        min_samples_split=3,  # Consistent with RF baseline
        min_samples_leaf=2,   # Consistent with RF baseline
        max_features='sqrt',  # Same feature sampling as RF
        random_state=RANDOM_STATE
    )

    gbr_reg.fit(X_train, y_train)

    # ── Step E: Evaluate ────────────────────────────────────────────────────
    y_pred = gbr_reg.predict(X_test)

    r2   = r2_score(y_test, y_pred)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    # 5-fold cross-validation (same as RF baseline for direct comparison)
    cv_scores = cross_val_score(
        gbr_reg, X_imputed, y_final,
        cv=5, scoring='r2', error_score='raise'
    )

    regression_models[program_id] = {
        'model':   gbr_reg,
        'imputer': feat_imputer,
        'subjects': subjects_for_program
    }

    regression_metrics[program_id] = {
        'R2':         round(r2, 4),
        'MAE':        round(mae, 4),
        'RMSE':       round(rmse, 4),
        'CV_R2_Mean': round(cv_scores.mean(), 4),
        'CV_R2_Std':  round(cv_scores.std(),  4),
        'n_train':    len(X_train),
        'n_test':     len(X_test)
    }

    feature_importances_reg[program_id] = pd.Series(
        gbr_reg.feature_importances_, index=FEATURES
    ).sort_values(ascending=False)

    # Predict for ALL 594 students (used in Stage 2 classifier)
    X_all_imputed = feat_imputer.transform(df[FEATURES])
    preds_all     = gbr_reg.predict(X_all_imputed)
    # Clamp to valid grade range [60, 100]
    all_program_predictions[program_id] = np.clip(preds_all, 60, 100)

    print(f"     R²:   {r2:.4f}  (CV mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f})")
    print(f"     MAE:  {mae:.4f} grade points")
    print(f"     RMSE: {rmse:.4f} grade points")

print("\n  ✓ All 5 Gradient Boosting regression models trained successfully.")

# ==============================================================================
# SECTION 7: REGRESSION EVALUATION PLOTS
# ==============================================================================
print("\n[STEP 5] Generating regression evaluation plots...")

programs = list(PROGRAM_MAP.values())
colors   = list(PROGRAM_COLORS.values())

# --- Plot GBR-07: Regression Metrics Summary (R², MAE, RMSE) ---
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle('Stage 1 — Gradient Boosting Regression Metrics\n'
             '(Grade 7 Q1 Prediction per Program)',
             fontsize=13, fontweight='bold')

# R² scores
r2_vals = [regression_metrics[p]['R2'] for p in PROGRAM_MAP]
bars = axes[0].bar(programs, r2_vals, color=colors, alpha=0.85,
                   edgecolor='white', linewidth=1.5)
axes[0].set_title('R² Score (Higher = Better)', fontweight='bold')
axes[0].set_ylabel('R² Value')
axes[0].set_ylim(0, 1)
axes[0].axhline(0.7, color='green',  linestyle='--', alpha=0.7, label='Good (0.7)')
axes[0].axhline(0.5, color='orange', linestyle='--', alpha=0.7, label='Acceptable (0.5)')
axes[0].legend(fontsize=8)
for bar, val in zip(bars, r2_vals):
    axes[0].text(bar.get_x() + bar.get_width() / 2.,
                 bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom',
                 fontsize=9, fontweight='bold')
axes[0].grid(axis='y', alpha=0.3)

# MAE scores
mae_vals = [regression_metrics[p]['MAE'] for p in PROGRAM_MAP]
bars = axes[1].bar(programs, mae_vals, color=colors, alpha=0.85,
                   edgecolor='white', linewidth=1.5)
axes[1].set_title('MAE (Lower = Better)', fontweight='bold')
axes[1].set_ylabel('Mean Absolute Error (grade points)')
for bar, val in zip(bars, mae_vals):
    axes[1].text(bar.get_x() + bar.get_width() / 2.,
                 bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom',
                 fontsize=9, fontweight='bold')
axes[1].grid(axis='y', alpha=0.3)

# RMSE scores
rmse_vals = [regression_metrics[p]['RMSE'] for p in PROGRAM_MAP]
bars = axes[2].bar(programs, rmse_vals, color=colors, alpha=0.85,
                   edgecolor='white', linewidth=1.5)
axes[2].set_title('RMSE (Lower = Better)', fontweight='bold')
axes[2].set_ylabel('Root Mean Squared Error (grade points)')
for bar, val in zip(bars, rmse_vals):
    axes[2].text(bar.get_x() + bar.get_width() / 2.,
                 bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom',
                 fontsize=9, fontweight='bold')
axes[2].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('plot_gbr_07_regression_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_07_regression_metrics.png")

# --- Plot GBR-08: Feature Importances per Regression Model ---
"""
GRADIENT BOOSTING FEATURE IMPORTANCE:
    Importance = total reduction in the loss function achieved by splits on
    this feature, summed across all trees and all splits.
    Higher = the feature is used more often and reduces error more effectively.
    Typically, GB concentrates importance on fewer features than RF (more greedy).
"""
fig, axes = plt.subplots(1, 5, figsize=(22, 8))
fig.suptitle('Top 10 Feature Importances — GBR Models per Program\n'
             '(Total loss reduction contributed by each feature)',
             fontsize=13, fontweight='bold')

for idx, (p, name) in enumerate(PROGRAM_MAP.items()):
    ax    = axes[idx]
    top10 = feature_importances_reg[p].head(10)
    clean = [f.replace('grade_', 'G6 ').replace('q1_g7_', 'G7 ')
              .replace('_', ' ').title() for f in top10.index]
    ax.barh(range(len(top10)), top10.values,
            color=PROGRAM_COLORS[p], alpha=0.85, edgecolor='white')
    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(clean, fontsize=7)
    ax.invert_yaxis()
    ax.set_title(f'{name}', fontweight='bold', fontsize=10, color=PROGRAM_COLORS[p])
    ax.set_xlabel('Importance', fontsize=8)
    ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('plot_gbr_08_feature_importance_regression.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_08_feature_importance_regression.png")

# --- Plot GBR-09: CV R² Scores with Error Bars ---
fig, ax = plt.subplots(figsize=(10, 6))
cv_means = [regression_metrics[p]['CV_R2_Mean'] for p in PROGRAM_MAP]
cv_stds  = [regression_metrics[p]['CV_R2_Std']  for p in PROGRAM_MAP]

bars = ax.bar(programs, cv_means, yerr=cv_stds, color=colors, alpha=0.85,
              edgecolor='white', linewidth=1.5,
              error_kw=dict(ecolor='black', capsize=5, linewidth=2))

ax.axhline(0.7, color='green',  linestyle='--', alpha=0.7, linewidth=2,
           label='Good threshold (R²=0.7)')
ax.axhline(0.5, color='orange', linestyle='--', alpha=0.7, linewidth=2,
           label='Acceptable threshold (R²=0.5)')

for bar, val, std in zip(bars, cv_means, cv_stds):
    ax.text(bar.get_x() + bar.get_width() / 2.,
            bar.get_height() + std + 0.01,
            f'{val:.3f}', ha='center', va='bottom',
            fontsize=10, fontweight='bold')

ax.set_title('5-Fold Cross-Validation R² — Gradient Boosting Regression\n'
             '(Error bars = ±1 std | Same 5-fold setup as RF baseline)',
             fontsize=13, fontweight='bold')
ax.set_ylabel('Cross-Validated R²', fontsize=12)
ax.set_ylim(0, 1.1)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_gbr_09_cv_r2_scores.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_09_cv_r2_scores.png")

# ==============================================================================
# SECTION 8: SUITABILITY SCORING (Bridge between Stage 1 and Stage 2)
# ==============================================================================
print("\n[STEP 6] Computing Suitability Scores...")

"""
SUITABILITY SCORING LOGIC (unchanged from RF baseline):
    After predicting grades in all 5 programs, we check whether the predicted
    grade meets the threshold for each program.

    Rules:
      - STE, SPFL, SPTVE, TOP-5 : Predicted average must be ≥ 85
      - HETERO                   : Predicted average must be ≥ 75

    STE HARD ELIGIBILITY PRE-CHECK (school policy — applied before threshold):
      A student must have Grade 6 Math ≥ 83, Science ≥ 83, AND English ≥ 83.
      If ANY of the three is below 83, the student is INELIGIBLE for STE —
      even if their predicted Grade 7 average in STE would be 95.
      This is a non-negotiable school policy, not a model output.
"""

suitability_data = pd.DataFrame()
suitability_data['student_id']          = df['student_id'].values
suitability_data['actual_placement']    = df['actual_placement'].values
suitability_data['preferred_program']   = df['preferred_program'].values
suitability_data['has_valid_preference']= df['has_valid_preference'].values
suitability_data['g6_final_average']    = df['grade_6_final_average'].values
suitability_data['g6_math']             = df['grade_math'].values
suitability_data['g6_science']          = df['grade_science'].values
suitability_data['g6_english']          = df['grade_english'].values

# ── STE Eligibility Pre-check ─────────────────────────────────────────────────
suitability_data['ste_g6_eligible'] = (
    (df['grade_math'].values    >= STE_ELIGIBILITY_MIN_GRADE) &
    (df['grade_science'].values >= STE_ELIGIBILITY_MIN_GRADE) &
    (df['grade_english'].values >= STE_ELIGIBILITY_MIN_GRADE)
).astype(int)

suitability_data['ste_ineligible_reason'] = df.apply(
    lambda row: ', '.join([
        f'{subj.replace("grade_","").upper()} ({row[subj]:.0f}<83)'
        for subj in STE_ELIGIBILITY_SUBJECTS
        if row[subj] < STE_ELIGIBILITY_MIN_GRADE
    ]) if any(row[s] < STE_ELIGIBILITY_MIN_GRADE for s in STE_ELIGIBILITY_SUBJECTS)
    else 'Eligible',
    axis=1
)

ste_eligible_count   = suitability_data['ste_g6_eligible'].sum()
ste_ineligible_count = len(suitability_data) - ste_eligible_count
print(f"  → STE eligibility check (G6 Math/Science/English ≥ 83):")
print(f"     Eligible:   {ste_eligible_count} students")
print(f"     Ineligible: {ste_ineligible_count} students")

if ste_ineligible_count > 0:
    math_fail    = (df['grade_math']    < STE_ELIGIBILITY_MIN_GRADE).sum()
    science_fail = (df['grade_science'] < STE_ELIGIBILITY_MIN_GRADE).sum()
    english_fail = (df['grade_english'] < STE_ELIGIBILITY_MIN_GRADE).sum()
    print(f"     Below 83 in Math:    {math_fail} students")
    print(f"     Below 83 in Science: {science_fail} students")
    print(f"     Below 83 in English: {english_fail} students")

# ── Suitability Scoring for all Programs ─────────────────────────────────────
for p, name in PROGRAM_MAP.items():
    pred_col   = f'pred_avg_{name}'
    suit_col   = f'suitable_{name}'
    margin_col = f'margin_{name}'

    suitability_data[pred_col] = all_program_predictions[p].round(3)

    grade_threshold_met = suitability_data[pred_col] >= SUITABILITY_THRESHOLD[p]

    if p == 1:   # STE: grade threshold + G6 eligibility pre-check
        suitability_data[suit_col] = (
            grade_threshold_met & (suitability_data['ste_g6_eligible'] == 1)
        ).astype(int)
    else:
        suitability_data[suit_col] = grade_threshold_met.astype(int)

    suitability_data[margin_col] = (
        suitability_data[pred_col] - SUITABILITY_THRESHOLD[p]
    ).round(3)

# Top 3 Recommendations per student (same ranking logic as RF baseline)
pred_avg_cols = {p: f'pred_avg_{PROGRAM_MAP[p]}' for p in PROGRAM_MAP}

def get_top3_recommendations(row):
    """
    Rank programs by:
      Priority 1 — Whether program is fully suitable (threshold + eligibility met)
      Priority 2 — Predicted average (higher is better)
    STE ineligible students are ranked last regardless of predicted grade.
    """
    sorted_programs = sorted(
        PROGRAM_MAP.keys(),
        key=lambda p: (
            row[f'suitable_{PROGRAM_MAP[p]}'],
            row[pred_avg_cols[p]]
        ),
        reverse=True
    )
    return sorted_programs[:3]

suitability_data['top3_recommendations'] = suitability_data.apply(
    get_top3_recommendations, axis=1
)
suitability_data['top1_recommendation']  = suitability_data[
    'top3_recommendations'
].apply(lambda x: x[0])

print(f"\n  → Suitability scores computed for {len(suitability_data)} students")
print("  → Suitability rates (students meeting ALL criteria):")
for p, name in PROGRAM_MAP.items():
    suit_rate = suitability_data[f'suitable_{name}'].mean() * 100
    extra = " (grade threshold + G6 eligibility)" if p == 1 else " (grade threshold only)"
    print(f"     {name:10s}: {suit_rate:.1f}% of all students are predicted suitable{extra}")

# --- Plot GBR-14: Suitability Heatmap ---
fig, ax = plt.subplots(figsize=(12, 7))
suit_cols = [f'suitable_{name}' for name in PROGRAM_MAP.values()]
suit_matrix = suitability_data[suit_cols].values.astype(float)
sns.heatmap(
    suit_matrix[:50],
    annot=False, cmap='RdYlGn', vmin=0, vmax=1,
    ax=ax,
    xticklabels=list(PROGRAM_MAP.values()),
    yticklabels=False,
    linewidths=0.3, linecolor='white'
)
ax.set_title('Suitability Map — First 50 Students × All Programs\n'
             '(Green = Suitable | Red = Not Suitable)',
             fontsize=12, fontweight='bold')
ax.set_xlabel('Program', fontsize=11)
ax.set_ylabel('Student (first 50)', fontsize=11)
plt.tight_layout()
plt.savefig('plot_gbr_14_suitability_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_14_suitability_heatmap.png")

# ==============================================================================
# SECTION 9: STAGE 2 — GRADIENT BOOSTING CLASSIFICATION (Program Recommendation)
# ==============================================================================
print("\n" + "=" * 70)
print("  STAGE 2: GRADIENT BOOSTING CLASSIFICATION — Program Recommendation")
print("=" * 70)

"""
CLASSIFICATION MODEL:
    Input : Predicted Grade 7 averages (from Stage 1) + G6 grades + non-academic
    Output: Recommended program (1–5)
    Target: actual_placement

GRADIENT BOOSTING CLASSIFIER HYPERPARAMETERS:
    n_estimators  = 300    → More trees for stable multi-class classification
    learning_rate = 0.08   → Same conservative rate as regression stage
    max_depth     = 4      → Shallow trees — essential for GB classification
    subsample     = 0.8    → Stochastic GB — reduces variance on imbalanced data
    min_samples_split = 3  → Consistent with RF baseline
    min_samples_leaf  = 2  → Consistent with RF baseline

CLASS IMBALANCE HANDLING:
    RandomForest used class_weight='balanced'.
    GradientBoostingClassifier does not support class_weight natively.
    Strategy: subsample=0.8 + shallow trees + StratifiedKFold evaluation
    reduces the impact of class imbalance. If F1 for minority classes (STE,
    SPTVE) is significantly lower than RF, consider applying SMOTE oversampling
    or switching to HistGradientBoostingClassifier which supports class_weight.
"""

# Build classification features: original features + 5 predicted averages
clf_features = FEATURES + [f'pred_avg_{PROGRAM_MAP[p]}' for p in PROGRAM_MAP]

X_clf = pd.DataFrame()
for feat in FEATURES:
    X_clf[feat] = df[feat].values
for p, name in PROGRAM_MAP.items():
    X_clf[f'pred_avg_{name}'] = all_program_predictions[p]

y_clf = df['actual_placement'].values

# Impute any remaining NaN in classification features
clf_imputer   = SimpleImputer(strategy='mean')
X_clf_imputed = clf_imputer.fit_transform(X_clf)

# Stratified split — same as RF baseline (identical RANDOM_STATE, test_size)
X_train_clf, X_test_clf, y_train_clf, y_test_clf = train_test_split(
    X_clf_imputed, y_clf,
    test_size=0.2, random_state=RANDOM_STATE, stratify=y_clf
)

print(f"\n  Training samples: {len(X_train_clf)}")
print(f"  Test samples:     {len(X_test_clf)}")

# Train Gradient Boosting Classifier
gbr_clf = GradientBoostingClassifier(
    n_estimators=300,     # 300 sequential trees (same count as RF baseline)
    learning_rate=0.08,   # Conservative shrinkage
    max_depth=4,          # Shallow trees for GB classification
    subsample=0.8,        # Stochastic GB — helps with class imbalance
    min_samples_split=3,
    min_samples_leaf=2,
    max_features='sqrt',
    random_state=RANDOM_STATE
)

gbr_clf.fit(X_train_clf, y_train_clf)
y_pred_clf = gbr_clf.predict(X_test_clf)

# Evaluation
clf_accuracy  = accuracy_score(y_test_clf, y_pred_clf)
clf_precision = precision_score(y_test_clf, y_pred_clf, average='macro', zero_division=0)
clf_recall    = recall_score(y_test_clf,    y_pred_clf, average='macro', zero_division=0)
clf_f1        = f1_score(y_test_clf,        y_pred_clf, average='macro', zero_division=0)

clf_report = classification_report(
    y_test_clf, y_pred_clf,
    target_names=list(PROGRAM_MAP.values()),
    output_dict=True
)

# 5-fold Stratified Cross-validation
cv_clf        = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_clf_scores = cross_val_score(gbr_clf, X_clf_imputed, y_clf,
                                cv=cv_clf, scoring='f1_macro')

print(f"\n  ── Gradient Boosting Classification Results ──")
print(f"  Accuracy:  {clf_accuracy:.4f}")
print(f"  Precision: {clf_precision:.4f} (macro)")
print(f"  Recall:    {clf_recall:.4f} (macro)")
print(f"  F1-Score:  {clf_f1:.4f} (macro)")
print(f"  CV F1 (mean ± std): {cv_clf_scores.mean():.4f} ± {cv_clf_scores.std():.4f}")

# Feature importance for classifier
clf_feature_importance = pd.Series(
    gbr_clf.feature_importances_, index=clf_features
).sort_values(ascending=False)

# ==============================================================================
# SECTION 10: CLASSIFICATION EVALUATION PLOTS
# ==============================================================================
print("\n[STEP 7] Generating classification evaluation plots...")

# --- Plot GBR-10: Confusion Matrix ---
fig, ax = plt.subplots(figsize=(9, 7))
cm            = confusion_matrix(y_test_clf, y_pred_clf)
cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

sns.heatmap(cm_normalized, annot=True, fmt='.2f', cmap='Blues',
            xticklabels=list(PROGRAM_MAP.values()),
            yticklabels=list(PROGRAM_MAP.values()),
            ax=ax, linewidths=0.5, linecolor='white',
            annot_kws={'size': 12, 'weight': 'bold'})

ax.set_title('Confusion Matrix — Gradient Boosting Classification\n'
             '(Normalized by Actual Class)',
             fontsize=13, fontweight='bold')
ax.set_ylabel('Actual Program',    fontsize=12)
ax.set_xlabel('Predicted Program', fontsize=12)
plt.tight_layout()
plt.savefig('plot_gbr_10_confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_10_confusion_matrix.png")

# --- Plot GBR-11: Classification Metrics per Program ---
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle('Stage 2 — Gradient Boosting Classification Metrics per Program',
             fontsize=13, fontweight='bold')

metric_names  = ['precision', 'recall', 'f1-score']
metric_titles = ['Precision',  'Recall',  'F1-Score']

for ax_idx, (metric, title) in enumerate(zip(metric_names, metric_titles)):
    ax   = axes[ax_idx]
    vals = [clf_report[name][metric]
            for name in PROGRAM_MAP.values() if name in clf_report]
    bars = ax.bar(list(PROGRAM_MAP.values()), vals,
                  color=list(PROGRAM_COLORS.values()),
                  alpha=0.85, edgecolor='white', linewidth=1.5)
    ax.set_title(f'{title} per Program', fontweight='bold')
    ax.set_ylabel(title)
    ax.set_ylim(0, 1.15)
    ax.axhline(0.8,  color='green',  linestyle='--', alpha=0.7, label='Good (0.8)')
    ax.axhline(0.6,  color='orange', linestyle='--', alpha=0.7, label='Acceptable (0.6)')
    ax.legend(fontsize=8)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2.,
                bar.get_height() + 0.01,
                f'{val:.3f}', ha='center', va='bottom',
                fontsize=9, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('plot_gbr_11_classification_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_11_classification_metrics.png")

# --- Plot GBR-12: Overall Classification Metrics ---
fig, ax = plt.subplots(figsize=(8, 6))
metric_labels = ['Accuracy', 'Precision\n(macro)', 'Recall\n(macro)', 'F1-Score\n(macro)']
metric_values = [clf_accuracy, clf_precision, clf_recall, clf_f1]
metric_colors = ['#264653', '#2A9D8F', '#E9C46A', '#E76F51']

bars = ax.bar(metric_labels, metric_values, color=metric_colors,
              alpha=0.85, edgecolor='white', linewidth=1.5, width=0.5)
ax.axhline(0.8, color='green',  linestyle='--', alpha=0.7, linewidth=2, label='Good (0.8)')
ax.axhline(0.6, color='orange', linestyle='--', alpha=0.7, linewidth=2, label='Acceptable (0.6)')
ax.set_title('Overall Classification Metrics — Gradient Boosting\n'
             f'(CV F1: {cv_clf_scores.mean():.4f} ± {cv_clf_scores.std():.4f})',
             fontsize=13, fontweight='bold')
ax.set_ylabel('Score', fontsize=12)
ax.set_ylim(0, 1.15)
ax.legend(fontsize=10)
for bar, val in zip(bars, metric_values):
    ax.text(bar.get_x() + bar.get_width() / 2.,
            bar.get_height() + 0.01,
            f'{val:.4f}', ha='center', va='bottom',
            fontsize=10, fontweight='bold')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_gbr_12_overall_classification.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_12_overall_classification.png")

# --- Plot GBR-13: Feature Importance — Classifier ---
fig, ax = plt.subplots(figsize=(12, 8))
top15 = clf_feature_importance.head(15)
clean = [f.replace('grade_', 'G6 ').replace('q1_g7_', 'G7 ')
          .replace('pred_avg_', 'Pred Avg ')
          .replace('_', ' ').title() for f in top15.index]

bars = ax.barh(range(len(top15)), top15.values,
               color='#A23B72', alpha=0.85, edgecolor='white')
ax.set_yticks(range(len(top15)))
ax.set_yticklabels(clean, fontsize=9)
ax.invert_yaxis()
ax.set_title('Top 15 Feature Importances — Gradient Boosting Classifier\n'
             '(Predicted averages from Stage 1 typically rank highest)',
             fontsize=12, fontweight='bold')
ax.set_xlabel('Importance (total loss reduction)', fontsize=10)
ax.grid(axis='x', alpha=0.3)
for bar, val in zip(bars, top15.values):
    ax.text(val + 0.001, bar.get_y() + bar.get_height() / 2.,
            f'{val:.4f}', va='center', fontsize=8, fontweight='bold')
plt.tight_layout()
plt.savefig('plot_gbr_13_feature_importance_classifier.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_13_feature_importance_classifier.png")

# ==============================================================================
# SECTION 11: ALGORITHM COMPARISON SUMMARY TABLE
# ==============================================================================
print("\n" + "=" * 70)
print("  GRADIENT BOOSTING EVALUATION SUMMARY")
print("=" * 70)

print(f"\n  {'REGRESSION RESULTS':}")
print(f"  {'Program':<10} {'R²':>8} {'MAE':>8} {'RMSE':>8} {'CV R²':>20}  N_train/N_test")
print("  " + "─" * 72)
for p, name in PROGRAM_MAP.items():
    m = regression_metrics[p]
    print(f"  {name:<10} {m['R2']:>8.4f} {m['MAE']:>8.4f} {m['RMSE']:>8.4f} "
          f"{m['CV_R2_Mean']:>+8.4f} ± {m['CV_R2_Std']:.4f}  "
          f"{m['n_train']}/{m['n_test']}")

avg_r2   = np.mean([regression_metrics[p]['R2']   for p in PROGRAM_MAP])
avg_mae  = np.mean([regression_metrics[p]['MAE']  for p in PROGRAM_MAP])
avg_rmse = np.mean([regression_metrics[p]['RMSE'] for p in PROGRAM_MAP])
avg_cv   = np.mean([regression_metrics[p]['CV_R2_Mean'] for p in PROGRAM_MAP])

print("  " + "─" * 72)
print(f"  {'AVERAGE':<10} {avg_r2:>8.4f} {avg_mae:>8.4f} {avg_rmse:>8.4f} "
      f"{avg_cv:>+8.4f}")

print(f"\n  {'CLASSIFICATION RESULTS':}")
print(f"  Accuracy  : {clf_accuracy:.4f}")
print(f"  Precision : {clf_precision:.4f} (macro)")
print(f"  Recall    : {clf_recall:.4f} (macro)")
print(f"  F1-Score  : {clf_f1:.4f} (macro)")
print(f"  CV F1     : {cv_clf_scores.mean():.4f} ± {cv_clf_scores.std():.4f}")
print(f"\n  Per-Program Classification Report:")
print(f"  {'Program':<10} {'Precision':>10} {'Recall':>8} {'F1-Score':>10} {'Support':>8}")
print("  " + "─" * 50)
for name in PROGRAM_MAP.values():
    if name in clf_report:
        r = clf_report[name]
        print(f"  {name:<10} {r['precision']:>10.4f} {r['recall']:>8.4f} "
              f"{r['f1-score']:>10.4f} {int(r['support']):>8}")

# ==============================================================================
# SECTION 12: FINAL SUMMARY DASHBOARD
# ==============================================================================
print("\n[STEP 8] Generating final summary dashboard...")

fig = plt.figure(figsize=(22, 16))
fig.suptitle('SPARK — Gradient Boosting Algorithm | Full Evaluation Dashboard',
             fontsize=16, fontweight='bold', y=0.99)

gs = fig.add_gridspec(3, 4, hspace=0.45, wspace=0.4)

# 1. R² per program
ax1 = fig.add_subplot(gs[0, 0])
ax1.bar(programs, r2_vals, color=colors, alpha=0.85, edgecolor='white')
ax1.set_title('Regression R²', fontweight='bold', fontsize=10)
ax1.set_ylim(-0.2, 1)
ax1.axhline(0.7, color='green', linestyle='--', alpha=0.6, linewidth=1)
ax1.axhline(0.0, color='gray',  linestyle='-',  alpha=0.3)
ax1.tick_params(axis='x', labelsize=7)
for i, v in enumerate(r2_vals):
    yoff = 0.02 if v >= 0 else -0.08
    ax1.text(i, v + yoff, f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)

# 2. MAE per program
ax2 = fig.add_subplot(gs[0, 1])
ax2.bar(programs, mae_vals, color=colors, alpha=0.85, edgecolor='white')
ax2.set_title('Regression MAE', fontweight='bold', fontsize=10)
ax2.tick_params(axis='x', labelsize=7)
for i, v in enumerate(mae_vals):
    ax2.text(i, v + 0.01, f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)

# 3. RMSE per program
ax3 = fig.add_subplot(gs[0, 2])
ax3.bar(programs, rmse_vals, color=colors, alpha=0.85, edgecolor='white')
ax3.set_title('Regression RMSE', fontweight='bold', fontsize=10)
ax3.tick_params(axis='x', labelsize=7)
for i, v in enumerate(rmse_vals):
    ax3.text(i, v + 0.01, f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
ax3.grid(axis='y', alpha=0.3)

# 4. Overall classification metrics
ax4 = fig.add_subplot(gs[0, 3])
clf_vals   = [clf_accuracy, clf_precision, clf_recall, clf_f1]
clf_labels = ['Accuracy', 'Precision', 'Recall', 'F1']
ax4.bar(clf_labels, clf_vals,
        color=['#264653', '#2A9D8F', '#E9C46A', '#E76F51'],
        alpha=0.85, edgecolor='white')
ax4.set_title('Classification Metrics', fontweight='bold', fontsize=10)
ax4.set_ylim(0, 1.1)
ax4.axhline(0.8, color='green', linestyle='--', alpha=0.6, linewidth=1)
ax4.tick_params(axis='x', labelsize=8)
for i, v in enumerate(clf_vals):
    ax4.text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=8, fontweight='bold')
ax4.grid(axis='y', alpha=0.3)

# 5. Confusion Matrix
ax5 = fig.add_subplot(gs[1, :2])
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=list(PROGRAM_MAP.values()),
            yticklabels=list(PROGRAM_MAP.values()),
            ax=ax5, linewidths=0.5, linecolor='white',
            annot_kws={'size': 10, 'weight': 'bold'})
ax5.set_title('Confusion Matrix (Counts)', fontweight='bold', fontsize=10)
ax5.set_xlabel('Predicted', fontsize=9)
ax5.set_ylabel('Actual', fontsize=9)
ax5.tick_params(labelsize=8)

# 6. Dataset distribution pie
ax6 = fig.add_subplot(gs[1, 2:])
program_counts = df['actual_placement'].value_counts().sort_index()
pcolors        = [PROGRAM_COLORS[p] for p in program_counts.index]
wedges, texts, autotexts = ax6.pie(
    program_counts.values,
    labels=[PROGRAM_MAP[p] for p in program_counts.index],
    autopct='%1.1f%%', colors=pcolors, startangle=90, pctdistance=0.75
)
for autotext in autotexts:
    autotext.set_fontsize(8)
    autotext.set_fontweight('bold')
ax6.set_title('Dataset Distribution by Program', fontweight='bold', fontsize=10)

# 7. G6 vs G7 scatter
ax7 = fig.add_subplot(gs[2, :2])
for p, name in PROGRAM_MAP.items():
    prog_df = df[df['actual_placement'] == p]
    ax7.scatter(prog_df['grade_6_final_average'], prog_df['q1_g7_final_grade'],
                color=PROGRAM_COLORS[p], alpha=0.4, s=20, label=name)
ax7.axhline(85, color='green', linestyle='--', alpha=0.5, linewidth=1)
ax7.axvline(85, color='green', linestyle='--', alpha=0.5, linewidth=1)
ax7.set_title('G6 Avg vs G7 Q1 Final Grade', fontweight='bold', fontsize=10)
ax7.set_xlabel('Grade 6 Final Average', fontsize=9)
ax7.set_ylabel('Grade 7 Q1 Final Grade', fontsize=9)
ax7.legend(fontsize=7, ncol=2)
ax7.grid(alpha=0.3)

# 8. CV R² with error bars
ax8 = fig.add_subplot(gs[2, 2:])
ax8.bar(programs, cv_means, yerr=cv_stds, color=colors, alpha=0.85,
        edgecolor='white',
        error_kw=dict(ecolor='black', capsize=4, linewidth=1.5))
ax8.set_title('CV R² per Program Model', fontweight='bold', fontsize=10)
ax8.set_ylim(-0.3, 1.1)
ax8.axhline(0.7, color='green', linestyle='--', alpha=0.6, linewidth=1)
ax8.axhline(0.0, color='gray',  linestyle='-',  alpha=0.3)
ax8.tick_params(axis='x', labelsize=7)
for i, (v, s) in enumerate(zip(cv_means, cv_stds)):
    yoff = s + 0.02 if v >= 0 else -(s + 0.08)
    ax8.text(i, v + yoff, f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
ax8.grid(axis='y', alpha=0.3)

plt.savefig('plot_gbr_15_dashboard.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_gbr_15_dashboard.png")

# ==============================================================================
# SECTION 13: SAVE CSV RESULTS
# ==============================================================================
print("\n[STEP 9] Saving outputs...")

# Suitability scores
suitability_data.drop(columns=['top3_recommendations'], errors='ignore').to_csv(
    'gbr_suitability_scores.csv', index=False
)
print("  → Saved: gbr_suitability_scores.csv")

# Regression metrics
reg_metrics_df = pd.DataFrame(regression_metrics).T
reg_metrics_df.index = [PROGRAM_MAP[p] for p in reg_metrics_df.index]
reg_metrics_df.to_csv('gbr_regression_metrics.csv')
print("  → Saved: gbr_regression_metrics.csv")

# Classification report
clf_df = pd.DataFrame(clf_report).T
clf_df.to_csv('gbr_classification_metrics.csv')
print("  → Saved: gbr_classification_metrics.csv")

# ==============================================================================
# SECTION 14: SAVE TRAINED MODELS FOR GBR_predict.py
# ==============================================================================
models_dir = 'gbr_models'
os.makedirs(models_dir, exist_ok=True)

# Save all 5 regression models
for p, name in PROGRAM_MAP.items():
    model_data = {
        'model':        regression_models[p]['model'],
        'imputer':      regression_models[p]['imputer'],
        'subjects':     regression_models[p]['subjects'],
        'program_id':   p,
        'program_name': name
    }
    joblib.dump(model_data, f'{models_dir}/regression_{name}.pkl')

# Save classification model
clf_data = {
    'model':        gbr_clf,
    'imputer':      clf_imputer,
    'clf_features': clf_features
}
joblib.dump(clf_data, f'{models_dir}/classifier.pkl')

# Save shared config for GBR_predict.py
config = {
    'FEATURES':                   FEATURES,
    'G6_ACADEMIC':                G6_ACADEMIC,
    'NON_ACADEMIC':               NON_ACADEMIC,
    'G7_COMMON_SUBJECTS':         G7_COMMON_SUBJECTS,
    'G7_EXCLUSIVE':               G7_EXCLUSIVE,
    'PROGRAM_MAP':                PROGRAM_MAP,
    'PROGRAM_COLORS':             PROGRAM_COLORS,
    'SUITABILITY_THRESHOLD':      SUITABILITY_THRESHOLD,
    'STE_ELIGIBILITY_SUBJECTS':   STE_ELIGIBILITY_SUBJECTS,
    'STE_ELIGIBILITY_MIN_GRADE':  STE_ELIGIBILITY_MIN_GRADE,
    'clf_features':               clf_features
}
joblib.dump(config, f'{models_dir}/config.pkl')

print(f"  → Saved: {models_dir}/regression_STE.pkl")
print(f"  → Saved: {models_dir}/regression_SPFL.pkl")
print(f"  → Saved: {models_dir}/regression_SPTVE.pkl")
print(f"  → Saved: {models_dir}/regression_TOP-5.pkl")
print(f"  → Saved: {models_dir}/regression_HETERO.pkl")
print(f"  → Saved: {models_dir}/classifier.pkl")
print(f"  → Saved: {models_dir}/config.pkl")
print(f"  ✓ Models saved — ready for GBR_predict.py")

print("\n" + "=" * 70)
print("  GRADIENT BOOSTING TRAINING PIPELINE COMPLETE")
print("=" * 70)
print(f"  Algorithm     : Gradient Boosting (XGBoost/LightGBM equivalent)")
print(f"  Plots generated: 15 (plot_gbr_01 → plot_gbr_15)")
print(f"  Models trained : 6 (5 regression + 1 classification)")
print(f"  Students       : {len(df)}")
print(f"  Avg R² (reg)   : {avg_r2:.4f}")
print(f"  Avg MAE (reg)  : {avg_mae:.4f} grade points")
print(f"  Clf Accuracy   : {clf_accuracy:.4f}")
print(f"  Clf Macro F1   : {clf_f1:.4f}")
print("=" * 70)
print("  COMPARISON GUIDE:")
print("  Compare gbr_regression_metrics.csv  vs  regression_metrics.csv")
print("  Compare gbr_classification_metrics.csv vs  classification_metrics.csv")
print("  Best algorithm = higher avg R² (regression) + higher CV F1 (classification)")
print("=" * 70)
