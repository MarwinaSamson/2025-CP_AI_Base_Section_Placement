"""
================================================================================
SPARK SYSTEM — Hybrid Two-Stage Machine Learning Framework
Integrating Ridge Regression (Grade Prediction) + XGBoost (Program Classification)
================================================================================

RESEARCH CONTEXT:
    This script implements a hybrid two-stage machine learning pipeline designed
    for the SPARK Grade 7 Section Placement System. Based on experimental findings:
        • Ridge Regression yields superior performance for grade prediction (regression)
        • Gradient Boosting (XGBoost) yields superior performance for program
          classification (multi-class classification)

    The hybrid architecture leverages both strengths simultaneously:
        Stage 1 → Ridge Regression predicts G7 Q1 average per program per student
        Stage 2 → XGBoost uses original features + Stage-1 predictions to classify
                  the most suitable program placement

    This design prevents data leakage at every boundary and ensures full
    reproducibility, making it suitable for inclusion in a thesis or
    peer-reviewed manuscript.

METHODOLOGY:
    • Five Ridge Regression models (one per program) trained independently
    • Predicted averages from Stage 1 are appended to the original feature matrix
    • SMOTE (Synthetic Minority Oversampling Technique) is applied exclusively
      on the training partition to address class imbalance without leakage
    • XGBoost classifier trained on the augmented, balanced training set

OUTPUT FILES:
    Regression Plots      : hybrid_reg_01_actual_vs_predicted.png
                            hybrid_reg_02_residual_distribution.png
                            hybrid_reg_03_residual_vs_fitted.png
    Classification Plots  : hybrid_clf_01_confusion_matrix.png
                            hybrid_clf_02_feature_importance.png
                            hybrid_clf_03_roc_curve.png
    Metrics CSV           : hybrid_regression_metrics.csv
                            hybrid_classification_metrics.csv

ACADEMIC REFERENCES:
    Tibshirani, R. (1996). Regression shrinkage and selection via the lasso.
    Chen, T., & Guestrin, C. (2016). XGBoost: A scalable tree boosting system.
    Chawla, N. V. et al. (2002). SMOTE: Synthetic minority over-sampling technique.
================================================================================
"""

# ==============================================================================
# SECTION 0: IMPORT LIBRARIES
# ==============================================================================

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')   # Non-interactive backend for server/script environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
warnings.filterwarnings('ignore')

from sklearn.linear_model import RidgeCV, Ridge
from sklearn.preprocessing import StandardScaler, label_binarize
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc
)
from sklearn.impute import SimpleImputer

from imblearn.over_sampling import SMOTE   # pip install imbalanced-learn
import xgboost as xgb                      # pip install xgboost

print("=" * 72)
print("  SPARK SYSTEM — Hybrid Two-Stage ML Framework")
print("  Ridge Regression  +  XGBoost  +  SMOTE")
print("=" * 72)

# ==============================================================================
# SECTION 1: CONSTANTS & CONFIGURATION
# ==============================================================================

PROGRAM_MAP = {
    1: 'STE',
    2: 'SPFL',
    3: 'SPTVE',
    4: 'TOP-5',
    5: 'HETERO'
}

PROGRAM_COLORS = {
    1: '#2E86AB',   # Blue  — STE
    2: '#A23B72',   # Purple — SPFL
    3: '#F18F01',   # Orange — SPTVE
    4: '#C73E1D',   # Red   — TOP-5
    5: '#3B1F2B'    # Dark  — HETERO
}

# Suitability thresholds (consistent with Ridge_Training.py)
SUITABILITY_THRESHOLD = {
    1: 85,   # STE
    2: 85,   # SPFL
    3: 85,   # SPTVE
    4: 85,   # TOP-5
    5: 75    # HETERO — lower threshold reflects heterogeneous cohort
}

# Hard eligibility rule for STE (G6 Math, Science, English must all be ≥ 83)
STE_ELIGIBILITY_SUBJECTS = ['grade_math', 'grade_science', 'grade_english']
STE_ELIGIBILITY_MIN_GRADE = 83

# Feature definitions (replicated from Ridge_Training.py for parity)
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
    'distance_from_school', 'travel_difficulty'
]

G7_COMMON_SUBJECTS = [
    'q1_g7_filipino', 'q1_g7_english', 'q1_g7_math', 'q1_g7_science',
    'q1_g7_arpan', 'q1_g7_tle', 'q1_g7_mapeh', 'q1_g7_esp'
]

G7_EXCLUSIVE = {
    1: 'q1_g7research',
    2: 'q1_g7_foreign_language',
    3: 'q1_g7_tve'
}

ALPHAS_RIDGE = [0.1, 1.0, 10.0, 100.0, 1000.0]  # CV alpha candidates

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# ==============================================================================
# SECTION 2: UTILITY FUNCTIONS
# ==============================================================================

def get_program_subjects(program_id):
    """Return the complete list of G7 subjects for a given program."""
    subjects = G7_COMMON_SUBJECTS.copy()
    if program_id in G7_EXCLUSIVE:
        subjects.append(G7_EXCLUSIVE[program_id])
    return subjects


def save_fig(filename, dpi=150):
    """Persist figure to disk and close to free memory."""
    plt.tight_layout()
    plt.savefig(filename, dpi=dpi, bbox_inches='tight')
    plt.close()
    print(f"  → Saved: {filename}")


# ==============================================================================
# SECTION 3: LOAD DATASET
# ==============================================================================
print("\n[STEP 1] Loading dataset...")

# Support running from any working directory
DATA_PATH = 'SPARK_DATASET.csv'
if not os.path.exists(DATA_PATH):
    DATA_PATH = '../SPARK_DATASET.csv'

df = pd.read_csv(DATA_PATH)
print(f"  → Loaded: {df.shape[0]} students × {df.shape[1]} features")

# ==============================================================================
# SECTION 4: DATA PREPROCESSING
# ==============================================================================
print("\n[STEP 2] Data Preprocessing...")

# ── 4a. Flag out-of-scope preferred programs (e.g., OHSP / SNEd → 0)
df['has_valid_preference'] = df['preferred_program'].apply(
    lambda x: 1 if x in [1.0, 2.0, 3.0, 4.0, 5.0] else 0
)
if 'has_valid_preference' not in NON_ACADEMIC:
    NON_ACADEMIC.append('has_valid_preference')

FEATURES = G6_ACADEMIC + NON_ACADEMIC   # combined feature list

# ── 4b. Impute non-academic features using mode (most frequent)
#        (fit on the full dataset before splitting; no target-leakage risk here
#         because non-academic features are not derived from the target)
non_acad_imputer = SimpleImputer(strategy='most_frequent')
df[NON_ACADEMIC] = non_acad_imputer.fit_transform(df[NON_ACADEMIC])

# ── 4c. Recompute Grade 6 final average from subject grades
df['grade_6_final_average'] = df[G6_ACADEMIC[:8]].mean(axis=1)

# ── 4d. Impute G7 subject grades using program-specific mean
#        This prevents cross-program contamination in imputation
for col in G7_COMMON_SUBJECTS + ['q1_g7_final_grade']:
    df[col] = df.groupby('actual_placement')[col].transform(
        lambda x: x.fillna(x.mean())
    )

for prog_id, col in G7_EXCLUSIVE.items():
    mask = df['actual_placement'] == prog_id
    group_mean = df.loc[mask, col].mean()
    df.loc[mask, col] = df.loc[mask, col].fillna(group_mean)

# ── 4e. Correct known data entry anomaly for student_061
student_061_mask = df['student_id'] == 'student_061'
if student_061_mask.any():
    computed = df.loc[student_061_mask, G7_COMMON_SUBJECTS].mean(axis=1).values[0]
    df.loc[student_061_mask, 'q1_g7_final_grade'] = round(computed, 3)
    print("  → Corrected student_061 final grade anomaly.")

# ── 4f. Winsorize G7 grade columns at [5th, 95th] percentile per program
#        to reduce influence of outliers without removing data
winsorized_count = 0
for col in G7_COMMON_SUBJECTS:
    for p in PROGRAM_MAP.keys():
        mask = df['actual_placement'] == p
        prog_data = df.loc[mask, col]
        lo, hi = prog_data.quantile(0.05), prog_data.quantile(0.95)
        before = df.loc[mask, col].copy()
        df.loc[mask, col] = df.loc[mask, col].clip(lower=lo, upper=hi)
        winsorized_count += (before != df.loc[mask, col]).sum()

print(f"  → Winsorization applied: {winsorized_count} values clamped.")
print("  → Preprocessing complete.")

# ==============================================================================
# SECTION 5: TRAIN-TEST SPLIT (Global — used for both stages)
# ==============================================================================
#
# DATA FLOW NOTE:
#   A single stratified 80/20 split is applied on the full dataset indices.
#   Stage 1 (Ridge) operates on program-specific sub-datasets but respects
#   the same proportional hold-out to avoid optimistic evaluation.
#   Stage 2 (XGBoost) uses the global split directly.
#
print("\n[STEP 3] Defining global train/test partition (80/20, stratified)...")

global_idx = df.index.to_numpy()
global_y   = df['actual_placement'].to_numpy()

train_idx, test_idx = train_test_split(
    global_idx, test_size=0.2,
    random_state=RANDOM_STATE, stratify=global_y
)

print(f"  → Train set: {len(train_idx)} samples | Test set: {len(test_idx)} samples")

# ==============================================================================
# SECTION 6: STAGE 1 — RIDGE REGRESSION (Grade Prediction per Program)
# ==============================================================================
print("\n" + "=" * 72)
print("  STAGE 1: RIDGE REGRESSION — G7 Q1 Grade Prediction")
print("=" * 72)
print("""
  Rationale:
    Ridge regression minimises the penalised loss:
        L(β) = ‖y - Xβ‖² + α‖β‖²
    The L2 penalty (α‖β‖²) shrinks coefficients, reducing variance while
    introducing controlled bias — ideal for the high-dimensional, collinear
    academic/non-academic feature space of the SPARK dataset.
    RidgeCV selects the optimal α via leave-one-out cross-validation.
""")

reg_models        = {}   # {prog_id: {'model': ..., 'imputer': ..., 'scaler': ...}}
reg_metrics       = {}   # {prog_id: {R2, MAE, RMSE, CV_R2_Mean, CV_R2_Std}}
all_program_preds = {}   # {prog_id: np.array of shape (n_students,)}

# Collect actual vs. predicted pairs for diagnostic plots
all_y_actual_list = []
all_y_pred_list   = []
all_program_labels = []

for prog_id, prog_name in PROGRAM_MAP.items():
    print(f"\n  ── Loop {prog_id}/5: Ridge for {prog_name} ──")

    prog_df = df[df['actual_placement'] == prog_id].copy()
    n_prog  = len(prog_df)
    if n_prog == 0:
        print(f"     WARNING: No samples for {prog_name}. Skipping.")
        continue

    X = prog_df[FEATURES].copy()
    y = prog_df['q1_g7_final_grade'].copy()

    # ── Impute any residual NaNs in X (mean strategy, fit on train only)
    feat_imputer = SimpleImputer(strategy='mean')

    # Identify train/test rows within this program
    prog_train_idx = [i for i in train_idx if i in prog_df.index]
    prog_test_idx  = [i for i in test_idx  if i in prog_df.index]

    # Fall back to random split if program has too few samples in either set
    if len(prog_train_idx) < 5 or len(prog_test_idx) < 2:
        prog_train_idx_local, prog_test_idx_local = train_test_split(
            prog_df.index.tolist(), test_size=0.2, random_state=RANDOM_STATE
        )
    else:
        prog_train_idx_local = prog_train_idx
        prog_test_idx_local  = prog_test_idx

    X_train_raw = X.loc[prog_train_idx_local]
    X_test_raw  = X.loc[prog_test_idx_local]
    y_train     = y.loc[prog_train_idx_local]
    y_test_prog = y.loc[prog_test_idx_local]

    # ── CRITICAL: fit imputer on training data ONLY to prevent leakage
    X_train_imp = feat_imputer.fit_transform(X_train_raw)
    X_test_imp  = feat_imputer.transform(X_test_raw)

    # ── RidgeCV: automatically selects best alpha via cross-validation
    ridge_cv = RidgeCV(alphas=ALPHAS_RIDGE)
    ridge_cv.fit(X_train_imp, y_train)
    best_alpha = ridge_cv.alpha_
    y_pred_test = ridge_cv.predict(X_test_imp)

    # ── Evaluation metrics
    r2   = r2_score(y_test_prog, y_pred_test)
    mae  = mean_absolute_error(y_test_prog, y_pred_test)
    rmse = np.sqrt(mean_squared_error(y_test_prog, y_pred_test))

    # 5-fold CV on entire program partition for generalisation estimate
    X_all_imp = feat_imputer.fit_transform(X)
    cv_r2 = cross_val_score(
        Ridge(alpha=best_alpha), X_all_imp, y, cv=5, scoring='r2'
    )

    reg_metrics[prog_id] = {
        'R2':         round(r2,            4),
        'MAE':        round(mae,           4),
        'RMSE':       round(rmse,          4),
        'CV_R2_Mean': round(cv_r2.mean(),  4),
        'CV_R2_Std':  round(cv_r2.std(),   4),
        'n_train':    len(X_train_imp),
        'n_test':     len(X_test_imp),
        'best_alpha': best_alpha
    }

    # ── Refit on full program data with best alpha for deployment-grade predictions
    #    These predictions are passed into Stage 2 as derived features
    final_ridge = Ridge(alpha=best_alpha)
    final_ridge.fit(X_all_imp, y)

    # ── Generate predictions for every student in the full dataset
    X_full_imp = feat_imputer.transform(df[FEATURES].copy())
    all_program_preds[prog_id] = final_ridge.predict(X_full_imp)

    reg_models[prog_id] = {
        'model':    final_ridge,
        'imputer':  feat_imputer,
        'subjects': get_program_subjects(prog_id),
        'alpha':    best_alpha
    }

    # Accumulate test actuals vs preds for aggregate diagnostics
    all_y_actual_list.extend(y_test_prog.tolist())
    all_y_pred_list.extend(y_pred_test.tolist())
    all_program_labels.extend([prog_name] * len(y_test_prog))

    print(f"     Best α: {best_alpha:.2f}")
    print(f"     R²:   {r2:.4f}  |  CV R² mean: {cv_r2.mean():.4f} ± {cv_r2.std():.4f}")
    print(f"     MAE:  {mae:.4f}  |  RMSE: {rmse:.4f}")

print("\n  ✓ Stage 1 complete — all 5 Ridge Regression models trained.")

# ── Aggregate arrays for plotting
y_actual_all = np.array(all_y_actual_list)
y_pred_all   = np.array(all_y_pred_list)
residuals     = y_actual_all - y_pred_all

# ==============================================================================
# SECTION 7: STAGE 1 EVALUATION PLOTS
# ==============================================================================
print("\n[STEP 4] Generating Stage 1 (Regression) Visualizations...")

# ── Plot R1: Actual vs. Predicted (per program, colour-coded)
fig, ax = plt.subplots(figsize=(9, 7))
prog_label_arr = np.array(all_program_labels)
for prog_id, prog_name in PROGRAM_MAP.items():
    mask = prog_label_arr == prog_name
    if mask.sum() == 0:
        continue
    ax.scatter(y_actual_all[mask], y_pred_all[mask],
               color=PROGRAM_COLORS[prog_id], alpha=0.70,
               edgecolors='white', linewidths=0.4,
               s=55, label=prog_name, zorder=3)

# Perfect prediction reference line
lo_val = min(y_actual_all.min(), y_pred_all.min()) - 1
hi_val = max(y_actual_all.max(), y_pred_all.max()) + 1
ax.plot([lo_val, hi_val], [lo_val, hi_val], 'k--', linewidth=1.5,
        alpha=0.6, label='Perfect Prediction (y=x)')
ax.set_xlim(lo_val, hi_val)
ax.set_ylim(lo_val, hi_val)
ax.set_xlabel('Actual G7 Q1 Final Grade', fontsize=12)
ax.set_ylabel('Predicted G7 Q1 Final Grade', fontsize=12)
ax.set_title('Stage 1 — Actual vs. Predicted Grade\n(Ridge Regression per Program)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9, framealpha=0.85)
ax.grid(True, alpha=0.25)

# Annotate aggregate R²
r2_overall = r2_score(y_actual_all, y_pred_all)
ax.text(0.04, 0.95, f'Overall R² = {r2_overall:.4f}',
        transform=ax.transAxes, fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

save_fig('hybrid_reg_01_actual_vs_predicted.png')

# ── Plot R2: Residual Distribution (histogram + KDE)
fig, ax = plt.subplots(figsize=(9, 6))
ax.hist(residuals, bins=25, color='#2E86AB', alpha=0.65,
        edgecolor='white', density=True, label='Residuals')
# Overlay KDE curve
from scipy.stats import gaussian_kde
kde_x = np.linspace(residuals.min() - 1, residuals.max() + 1, 300)
kde = gaussian_kde(residuals, bw_method='scott')
ax.plot(kde_x, kde(kde_x), color='#C73E1D', linewidth=2, label='KDE')
ax.axvline(0, color='black', linestyle='--', linewidth=1.2,
           alpha=0.75, label='Zero Residual')
ax.set_xlabel('Residual (Actual − Predicted)', fontsize=12)
ax.set_ylabel('Density', fontsize=12)
ax.set_title('Stage 1 — Residual Distribution\n(Ridge Regression, All Programs)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.25)
# Annotate skewness and mean
from scipy.stats import skew
ax.text(0.98, 0.95,
        f'Mean: {residuals.mean():.3f}\nStd:  {residuals.std():.3f}\nSkew: {skew(residuals):.3f}',
        transform=ax.transAxes, fontsize=9,
        verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.85))

save_fig('hybrid_reg_02_residual_distribution.png')

# ── Plot R3: Residual vs. Fitted (homoscedasticity diagnostic)
fig, ax = plt.subplots(figsize=(9, 6))
for prog_id, prog_name in PROGRAM_MAP.items():
    mask = prog_label_arr == prog_name
    if mask.sum() == 0:
        continue
    ax.scatter(y_pred_all[mask], residuals[mask],
               color=PROGRAM_COLORS[prog_id], alpha=0.65,
               edgecolors='white', linewidths=0.4,
               s=50, label=prog_name, zorder=3)

ax.axhline(0, color='black', linestyle='--', linewidth=1.4, alpha=0.7)
# Smoothed trend line (LOWESS-style via rolling mean approximation)
sort_idx = np.argsort(y_pred_all)
window   = max(1, len(y_pred_all) // 10)
trend_x  = pd.Series(y_pred_all[sort_idx]).rolling(window, center=True).mean()
trend_y  = pd.Series(residuals[sort_idx]).rolling(window, center=True).mean()
ax.plot(trend_x, trend_y, color='red', linewidth=2, alpha=0.7,
        linestyle='-', label='Smoothed Trend')

ax.set_xlabel('Fitted (Predicted) Value', fontsize=12)
ax.set_ylabel('Residual (Actual − Predicted)', fontsize=12)
ax.set_title('Stage 1 — Residual vs. Fitted Plot\n(Homoscedasticity Diagnostic)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.25)

save_fig('hybrid_reg_03_residual_vs_fitted.png')

# ── Regression metrics summary table (per program)
print("\n  ── Stage 1 Summary Table ──")
print(f"  {'Program':<10}  {'R²':>7}  {'MAE':>7}  {'RMSE':>7}  {'CV R²(mean)':>12}  {'α':>8}")
print(f"  {'─'*60}")
for prog_id, prog_name in PROGRAM_MAP.items():
    if prog_id not in reg_metrics:
        continue
    m = reg_metrics[prog_id]
    print(f"  {prog_name:<10}  {m['R2']:>7.4f}  {m['MAE']:>7.4f}  {m['RMSE']:>7.4f}  "
          f"{m['CV_R2_Mean']:>10.4f}±{m['CV_R2_Std']:.3f}  {m['best_alpha']:>8.1f}")

# ==============================================================================
# SECTION 8: BUILD AUGMENTED FEATURE MATRIX (Bridge Stage 1 → Stage 2)
# ==============================================================================
#
# DATA FLOW:
#   The five Ridge models each produce a predicted G7 Q1 average for every
#   student — irrespective of the student's actual program.  These predictions
#   encode the model's belief about how well a student would perform IF placed
#   in each program.  They are stacked alongside the original features to form
#   a richer representation for the XGBoost classifier.
#
#   Augmented feature matrix X_augmented:
#       [G6 Academic (9) | Non-Academic (46+1) | pred_avg_STE (1) |
#        pred_avg_SPFL (1) | pred_avg_SPTVE (1) | pred_avg_TOP5 (1) |
#        pred_avg_HETERO (1)]
#
print("\n[STEP 5] Constructing augmented feature matrix (Stage 1 → Stage 2 bridge)...")

X_clf = df[FEATURES].copy()
for prog_id, prog_name in PROGRAM_MAP.items():
    col_name = f'pred_avg_{prog_name}'
    X_clf[col_name] = all_program_preds[prog_id]
    print(f"  → Appended '{col_name}' to feature matrix")

clf_features = list(X_clf.columns)
print(f"  → Augmented feature matrix: {X_clf.shape[1]} features total")

# Impute any residual NaNs
clf_imputer = SimpleImputer(strategy='mean')
X_clf_imp   = clf_imputer.fit_transform(X_clf)
y_clf       = df['actual_placement'].to_numpy()

# ==============================================================================
# SECTION 9: STAGE 2 — TRAIN/TEST SPLIT + SMOTE
# ==============================================================================
print("\n" + "=" * 72)
print("  STAGE 2: XGBoost CLASSIFIER — Program Placement Prediction")
print("=" * 72)
print("""
  Rationale (XGBoost):
    XGBoost (Extreme Gradient Boosting) builds an additive ensemble:
        F_k(x) = F_{k-1}(x) + η · f_k(x),   where f_k minimises:
        Σ [ L(yᵢ, ŷᵢ) ] + Ω(f_k)
    The regularisation term Ω prevents overfitting.  XGBoost's second-order
    Taylor expansion of the loss leads to faster convergence and typically
    superior performance on tabular structured data vs. standard GBM.

  Rationale (SMOTE):
    Class imbalance inflates majority-class accuracy while depressing
    recall of minority programs.  SMOTE synthesises new minority samples
    by interpolating between existing k-nearest neighbours in feature space,
    rather than merely duplicating existing samples (oversampling with
    replacement).  Crucially, SMOTE is applied ONLY to the training set
    to prevent synthetic samples from contaminating the evaluation partition.
""")

# ── Stratified split on augmented feature matrix
X_train_clf, X_test_clf, y_train_clf, y_test_clf = train_test_split(
    X_clf_imp, y_clf,
    test_size=0.2,
    random_state=RANDOM_STATE,
    stratify=y_clf
)
print(f"  Train set : {X_train_clf.shape[0]} samples | Test set: {X_test_clf.shape[0]} samples")
print(f"  Train class distribution: {dict(zip(*np.unique(y_train_clf, return_counts=True)))}")

# ── Scale features (StandardScaler fitted on training data ONLY)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_clf)
X_test_scaled  = scaler.transform(X_test_clf)    # apply same transform to test

# ── Apply SMOTE exclusively on the training partition
#    SMOTE creates synthetic samples for minority programs by interpolating
#    between neighbouring instances — preventing the imbalance from biasing
#    the classifier toward HETERO (likely the largest class).
smote = SMOTE(random_state=RANDOM_STATE, k_neighbors=5)
X_train_sm, y_train_sm = smote.fit_resample(X_train_scaled, y_train_clf)

print(f"\n  Before SMOTE: {dict(zip(*np.unique(y_train_clf, return_counts=True)))}")
print(f"  After  SMOTE: {dict(zip(*np.unique(y_train_sm, return_counts=True)))}")

# ==============================================================================
# SECTION 10: XGBOOST TRAINING
# ==============================================================================
print("\n[STEP 6] Training XGBoost Classifier...")

# XGBoost expects 0-indexed labels
label_encoder_offset = 1   # actual_placement ∈ {1,2,3,4,5} → shift to {0,1,2,3,4}
y_train_xgb = y_train_sm  - label_encoder_offset
y_test_xgb  = y_test_clf  - label_encoder_offset

xgb_clf = xgb.XGBClassifier(
    n_estimators     = 300,
    max_depth        = 5,
    learning_rate    = 0.05,
    subsample        = 0.8,
    colsample_bytree = 0.8,
    min_child_weight = 2,
    gamma            = 0.1,
    reg_alpha        = 0.1,    # L1 regularisation
    reg_lambda       = 1.0,    # L2 regularisation
    objective        = 'multi:softprob',
    num_class        = 5,
    use_label_encoder= False,
    eval_metric      = 'mlogloss',
    random_state     = RANDOM_STATE,
    n_jobs           = -1
)

xgb_clf.fit(
    X_train_sm, y_train_xgb,      # X_train_sm = SMOTE-resampled training set
    eval_set=[(X_test_scaled, y_test_xgb)],
    verbose=False
)

print("  → XGBoost training complete.")

# Predictions (shift labels back to original encoding {1,…,5})
y_pred_xgb_idx  = xgb_clf.predict(X_test_scaled)
y_proba_xgb     = xgb_clf.predict_proba(X_test_scaled)
y_pred_original = y_pred_xgb_idx + label_encoder_offset   # {1,2,3,4,5}

# ==============================================================================
# SECTION 11: STAGE 2 EVALUATION
# ==============================================================================
print("\n[STEP 7] Evaluating Stage 2 (Classification) Performance...")

accuracy  = accuracy_score(y_test_clf, y_pred_original)
precision = precision_score(y_test_clf, y_pred_original, average='macro', zero_division=0)
recall    = recall_score(y_test_clf, y_pred_original, average='macro', zero_division=0)
f1        = f1_score(y_test_clf, y_pred_original, average='macro', zero_division=0)

# Stratified 5-fold CV on the full (unsampled) augmented set
#   Note: SMOTE is not applied here for fair generalisation estimate;
#         CV provides an unbiased performance lower-bound.
cv_kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_f1 = cross_val_score(
    xgb.XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        objective='multi:softprob', num_class=5,
        use_label_encoder=False, eval_metric='mlogloss',
        random_state=RANDOM_STATE, n_jobs=-1
    ),
    X_clf_imp,
    y_clf - label_encoder_offset,
    cv=cv_kf,
    scoring='f1_macro'
)

clf_report_dict = classification_report(
    y_test_clf, y_pred_original,
    target_names=list(PROGRAM_MAP.values()),
    output_dict=True
)

print(f"\n  ── Stage 2 Classification Metrics ──")
print(f"  Accuracy  : {accuracy:.4f}")
print(f"  Precision : {precision:.4f}  (macro-avg)")
print(f"  Recall    : {recall:.4f}  (macro-avg)")
print(f"  F1-Score  : {f1:.4f}  (macro-avg)")
print(f"  CV F1     : {cv_f1.mean():.4f} ± {cv_f1.std():.4f}  (5-fold stratified)")
print()
print(classification_report(
    y_test_clf, y_pred_original,
    target_names=list(PROGRAM_MAP.values())
))

# ==============================================================================
# SECTION 12: STAGE 2 VISUALIZATIONS
# ==============================================================================
print("\n[STEP 8] Generating Stage 2 (Classification) Visualizations...")

prog_names = list(PROGRAM_MAP.values())
colors_list = list(PROGRAM_COLORS.values())

# ── Plot C1: Confusion Matrix Heatmap
fig, ax = plt.subplots(figsize=(8, 7))
cm = confusion_matrix(y_test_clf, y_pred_original)
sns.heatmap(
    cm, annot=True, fmt='d',
    cmap='Blues', ax=ax,
    xticklabels=prog_names,
    yticklabels=prog_names,
    linewidths=0.5, linecolor='white',
    annot_kws={'size': 12, 'weight': 'bold'}
)
ax.set_title('Stage 2 — Confusion Matrix\n(XGBoost Classifier + SMOTE)',
             fontsize=13, fontweight='bold')
ax.set_xlabel('Predicted Program', fontsize=12)
ax.set_ylabel('Actual Program', fontsize=12)

save_fig('hybrid_clf_01_confusion_matrix.png')

# ── Plot C2: XGBoost Feature Importance (top 20, gain-based)
feat_importance_gain = pd.Series(
    xgb_clf.get_booster().get_score(importance_type='gain'),
    name='Gain'
).sort_values(ascending=False)

# Map internal feature names (f0, f1, …) to actual feature names
feat_name_map = {f'f{i}': name for i, name in enumerate(clf_features)}
feat_importance_gain.index = [
    feat_name_map.get(f, f) for f in feat_importance_gain.index
]
top20 = feat_importance_gain.head(20)

fig, ax = plt.subplots(figsize=(11, 8))
bar_colors = [
    '#C73E1D' if 'pred_avg' in f else '#2E86AB'
    for f in top20.index
]
ax.barh(range(len(top20)), top20.values,
        color=bar_colors, alpha=0.87, edgecolor='white')
ax.set_yticks(range(len(top20)))
clean_labels = [
    f.replace('pred_avg_', 'Pred ')
     .replace('grade_', 'G6 ')
     .replace('_', ' ')
     .title()
    for f in top20.index
]
ax.set_yticklabels(clean_labels, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel('Feature Importance (Gain)', fontsize=12)
ax.set_title('Stage 2 — Top 20 XGBoost Feature Importances\n(Gain Metric)',
             fontsize=13, fontweight='bold')

red_patch  = mpatches.Patch(color='#C73E1D', label='Predicted G7 Avg (Stage 1 output)')
blue_patch = mpatches.Patch(color='#2E86AB', label='Original Features')
ax.legend(handles=[red_patch, blue_patch], fontsize=10, loc='lower right')
ax.grid(axis='x', alpha=0.25)

save_fig('hybrid_clf_02_feature_importance.png')

# ── Plot C3: One-vs-Rest ROC Curves per Program
#    Binarise labels for OvR computation
classes_orig = np.array(list(PROGRAM_MAP.keys()))   # [1,2,3,4,5]
y_test_bin   = label_binarize(y_test_clf, classes=classes_orig)

fig, ax = plt.subplots(figsize=(9, 7))
for i, (prog_id, prog_name) in enumerate(PROGRAM_MAP.items()):
    fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_proba_xgb[:, i])
    roc_auc = auc(fpr, tpr)
    ax.plot(fpr, tpr,
            color=PROGRAM_COLORS[prog_id],
            linewidth=2.0,
            label=f'{prog_name}  (AUC = {roc_auc:.3f})')

ax.plot([0, 1], [0, 1], 'k--', linewidth=1.2, alpha=0.6, label='Random Classifier')
ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.05])
ax.set_xlabel('False Positive Rate', fontsize=12)
ax.set_ylabel('True Positive Rate', fontsize=12)
ax.set_title('Stage 2 — One-vs-Rest ROC Curves\n(XGBoost Classifier)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=10, loc='lower right')
ax.grid(True, alpha=0.25)

save_fig('hybrid_clf_03_roc_curve.png')

# ── Plot C4: Per-class classification metrics bar chart
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Stage 2 — Per-Class Classification Metrics (XGBoost + SMOTE)',
             fontsize=13, fontweight='bold')
for idx, metric in enumerate(['precision', 'recall', 'f1-score']):
    vals = [clf_report_dict[pn][metric] for pn in prog_names]
    axes[idx].bar(prog_names, vals, color=colors_list, alpha=0.85, edgecolor='white')
    axes[idx].set_title(metric.capitalize(), fontweight='bold')
    axes[idx].set_ylim(0, 1.15)
    for j, v in enumerate(vals):
        axes[idx].text(j, v + 0.02, f'{v:.3f}',
                       ha='center', fontsize=9, fontweight='bold')
    axes[idx].grid(axis='y', alpha=0.25)
    axes[idx].set_xlabel('Program')
    axes[idx].set_ylabel(metric.capitalize())

save_fig('hybrid_clf_04_per_class_metrics.png')

# ==============================================================================
# SECTION 13: SAVE METRICS AS CSV
# ==============================================================================
print("\n[STEP 9] Saving metrics to CSV files...")

# Regression metrics
reg_df = pd.DataFrame(reg_metrics).T
reg_df.index = [PROGRAM_MAP[p] for p in reg_df.index]
reg_df.index.name = 'Program'
reg_df.to_csv('hybrid_regression_metrics.csv')
print("  → Saved: hybrid_regression_metrics.csv")

# Classification metrics
clf_df = pd.DataFrame(clf_report_dict).T
clf_df.index.name = 'Class'
clf_df.to_csv('hybrid_classification_metrics.csv')
print("  → Saved: hybrid_classification_metrics.csv")

# Summary card
summary = {
    'Stage': ['Stage 1 (Ridge)', 'Stage 2 (XGBoost + SMOTE)'],
    'Task':  ['Regression', 'Classification'],
    'Key Metric': [f'Avg R² = {np.mean([reg_metrics[p]["R2"] for p in reg_metrics]):.4f}',
                   f'Macro F1 = {f1:.4f}'],
    'CV Score': [f'{np.mean([reg_metrics[p]["CV_R2_Mean"] for p in reg_metrics]):.4f}',
                 f'{cv_f1.mean():.4f} ± {cv_f1.std():.4f}']
}
pd.DataFrame(summary).to_csv('hybrid_summary_card.csv', index=False)
print("  → Saved: hybrid_summary_card.csv")

# ==============================================================================
# SECTION 14: SAVE TRAINED MODELS
# ==============================================================================
print("\n[STEP 10] Saving trained models...")
import joblib

os.makedirs('hybrid_models', exist_ok=True)

for prog_id, prog_name in PROGRAM_MAP.items():
    if prog_id in reg_models:
        joblib.dump(reg_models[prog_id], f'hybrid_models/ridge_{prog_name}.pkl')

joblib.dump({
    'model':        xgb_clf,
    'scaler':       scaler,
    'imputer':      clf_imputer,
    'clf_features': clf_features,
    'label_offset': label_encoder_offset,
    'program_map':  PROGRAM_MAP
}, 'hybrid_models/xgboost_classifier.pkl')

print("  → All models saved in 'hybrid_models/'")

# ==============================================================================
# SECTION 15: FINAL SUMMARY PRINTOUT
# ==============================================================================
print("\n" + "=" * 72)
print("  HYBRID TWO-STAGE FRAMEWORK — COMPLETE SUMMARY")
print("=" * 72)

print("\n  ── STAGE 1: Ridge Regression (Grade Prediction) ──")
print(f"  {'Program':<10}  {'R²':>7}  {'MAE':>7}  {'RMSE':>7}  {'CV R²':>10}")
print(f"  {'─'*50}")
for prog_id, prog_name in PROGRAM_MAP.items():
    if prog_id not in reg_metrics:
        continue
    m = reg_metrics[prog_id]
    print(f"  {prog_name:<10}  {m['R2']:>7.4f}  {m['MAE']:>7.4f}  "
          f"{m['RMSE']:>7.4f}  {m['CV_R2_Mean']:>7.4f}±{m['CV_R2_Std']:.3f}")

print(f"\n  ── STAGE 2: XGBoost Classifier (Program Placement) ──")
print(f"  Accuracy  : {accuracy:.4f}")
print(f"  Precision : {precision:.4f}  (macro)")
print(f"  Recall    : {recall:.4f}  (macro)")
print(f"  F1-Score  : {f1:.4f}  (macro)")
print(f"  CV F1     : {cv_f1.mean():.4f} ± {cv_f1.std():.4f}")

print("\n  ── Output Files ──")
for fname in [
    'hybrid_reg_01_actual_vs_predicted.png',
    'hybrid_reg_02_residual_distribution.png',
    'hybrid_reg_03_residual_vs_fitted.png',
    'hybrid_clf_01_confusion_matrix.png',
    'hybrid_clf_02_feature_importance.png',
    'hybrid_clf_03_roc_curve.png',
    'hybrid_clf_04_per_class_metrics.png',
    'hybrid_regression_metrics.csv',
    'hybrid_classification_metrics.csv',
    'hybrid_summary_card.csv'
]:
    print(f"  {fname}")

print("\n" + "=" * 72)
print("  PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 72)