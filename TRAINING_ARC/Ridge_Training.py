"""
================================================================================
SPARK SYSTEM — Ridge Regression Training Pipeline
Student Placement Prediction & Program Recommendation
================================================================================

This script trains:
    - 5 separate Ridge regression models (one per program) to predict Grade 7
      Q1 final average from Grade 6 grades and non‑academic features.
    - 1 Logistic Regression classifier that combines the 5 predicted averages
      with original features to recommend the most suitable program.

All trained models and configuration are saved in the 'ridge_models/' folder.
Evaluation plots and metrics are generated for comparison with other algorithms.
================================================================================
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from sklearn.linear_model import RidgeCV, Ridge, LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score,
                             accuracy_score, precision_score, recall_score,
                             f1_score, confusion_matrix, classification_report)
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.stats import mstats

# ==============================================================================
# CONSTANTS & CONFIGURATION
# ==============================================================================

PROGRAM_MAP = {
    1: 'STE',
    2: 'SPFL',
    3: 'SPTVE',
    4: 'TOP-5',
    5: 'HETERO'
}

PROGRAM_COLORS = {
    1: '#2E86AB',   # Blue
    2: '#A23B72',   # Purple
    3: '#F18F01',   # Orange
    4: '#C73E1D',   # Red
    5: '#3B1F2B'    # Dark
}

# Suitability thresholds for predicted Grade 7 average
SUITABILITY_THRESHOLD = {
    1: 85,   # STE
    2: 85,   # SPFL
    3: 85,   # SPTVE
    4: 85,   # TOP-5
    5: 75    # HETERO
}

# Hard STE eligibility: Grade 6 Math, Science, English must all be >= 83
STE_ELIGIBILITY_SUBJECTS = ['grade_math', 'grade_science', 'grade_english']
STE_ELIGIBILITY_MIN_GRADE = 83

# Feature groups (copied from original code)
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

FEATURES = G6_ACADEMIC + NON_ACADEMIC

G7_COMMON_SUBJECTS = [
    'q1_g7_filipino', 'q1_g7_english', 'q1_g7_math', 'q1_g7_science',
    'q1_g7_arpan', 'q1_g7_tle', 'q1_g7_mapeh', 'q1_g7_esp'
]

G7_EXCLUSIVE = {
    1: 'q1_g7research',          # STE only
    2: 'q1_g7_foreign_language', # SPFL only
    3: 'q1_g7_tve'               # SPTVE only
}

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_program_subjects(program_id):
    """Return list of Grade 7 subjects for a given program (common + exclusive)."""
    subjects = G7_COMMON_SUBJECTS.copy()
    if program_id in G7_EXCLUSIVE:
        subjects.append(G7_EXCLUSIVE[program_id])
    return subjects

def detect_outliers_iqr(series, multiplier=1.5):
    """Detect outliers using IQR method (for visualisation only)."""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR
    return series[(series < lower) | (series > upper)]

# ==============================================================================
# STEP 1: LOAD DATA
# ==============================================================================
print("=" * 70)
print("  SPARK SYSTEM — Ridge Regression Training Pipeline")
print("=" * 70)
print("\n[STEP 1] Loading dataset...")
df = pd.read_csv('DATASET/SPARK_DATASET.csv')
print(f"  → Dataset loaded: {df.shape[0]} students, {df.shape[1]} columns")

# ==============================================================================
# STEP 2: PREPROCESSING
# ==============================================================================
print("\n[STEP 2] Data Preprocessing...")

# Flag out‑of‑scope preferred programs (OHSP/SNEd)
df['has_valid_preference'] = df['preferred_program'].apply(
    lambda x: 1 if x in [1.0, 2.0, 3.0, 4.0, 5.0] else 0
)
NON_ACADEMIC.append('has_valid_preference')
FEATURES.append('has_valid_preference')

# Impute non‑academic missing values with mode
non_acad_imputer = SimpleImputer(strategy='most_frequent')
df[NON_ACADEMIC] = non_acad_imputer.fit_transform(df[NON_ACADEMIC])

# Compute Grade 6 final average (if not already present)
df['grade_6_final_average'] = df[G6_ACADEMIC[:8]].mean(axis=1)

# Impute Grade 7 common subjects with program‑specific mean
for col in G7_COMMON_SUBJECTS + ['q1_g7_final_grade']:
    df[col] = df.groupby('actual_placement')[col].transform(
        lambda x: x.fillna(x.mean())
    )

# Impute program‑exclusive subjects within the same program
for prog_id, col in G7_EXCLUSIVE.items():
    mask = df['actual_placement'] == prog_id
    group_mean = df.loc[mask, col].mean()
    df.loc[mask, col] = df.loc[mask, col].fillna(group_mean)

# Fix student_061 final grade mismatch (as in original)
student_061_mask = df['student_id'] == 'student_061'
if student_061_mask.any():
    computed = df.loc[student_061_mask, G7_COMMON_SUBJECTS].mean(axis=1).values[0]
    df.loc[student_061_mask, 'q1_g7_final_grade'] = round(computed, 3)
    print("  → Fixed student_061 final grade.")

print("  → Preprocessing complete.")

# ==============================================================================
# STEP 3: OUTLIER TREATMENT (Winsorization per program)
# ==============================================================================
print("\n[STEP 3] Outlier Treatment (Winsorization)...")

winsorized_count = 0
for col in G7_COMMON_SUBJECTS:
    for p in [1, 2, 3, 4, 5]:
        mask = df['actual_placement'] == p
        prog_data = df.loc[mask, col]
        lower = prog_data.quantile(0.05)
        upper = prog_data.quantile(0.95)
        before = df.loc[mask, col].copy()
        df.loc[mask, col] = df.loc[mask, col].clip(lower=lower, upper=upper)
        winsorized_count += (before != df.loc[mask, col]).sum()
print(f"  → Winsorization applied: {winsorized_count} values adjusted.")

# ==============================================================================
# STEP 4: STAGE 1 — RIDGE REGRESSION (5‑Loop Grade Prediction)
# ==============================================================================
print("\n" + "=" * 70)
print("  STAGE 1: RIDGE REGRESSION — Grade Prediction (5‑Loop)")
print("=" * 70)

reg_models = {}          # trained models per program
reg_metrics = {}         # evaluation metrics per program
coef_importances = {}    # feature coefficients (absolute) for importance
all_program_preds = {}   # predictions for every student (used in Stage 2)

# Alpha candidates for RidgeCV
alphas = [0.1, 1.0, 10.0, 100.0, 1000.0]

for loop, (prog_id, prog_name) in enumerate(PROGRAM_MAP.items(), 1):
    print(f"\n  ── Loop {loop}/5: Training Ridge for {prog_name} ──")

    # Filter data for this program
    prog_df = df[df['actual_placement'] == prog_id].copy()
    if len(prog_df) == 0:
        print(f"     WARNING: No samples for {prog_name}. Skipping.")
        continue

    X = prog_df[FEATURES].copy()
    y = prog_df['q1_g7_final_grade'].copy()

    # Impute any remaining missing values in features (use mean)
    feat_imputer = SimpleImputer(strategy='mean')
    X_imputed = feat_imputer.fit_transform(X)
    X_imputed = pd.DataFrame(X_imputed, columns=FEATURES)

    # Train/test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X_imputed, y, test_size=0.2, random_state=RANDOM_STATE
    )

    # Ridge regression with built‑in CV to choose alpha
    ridge = RidgeCV(alphas=alphas, store_cv_values=True)
    ridge.fit(X_train, y_train)
    best_alpha = ridge.alpha_

    # Predictions
    y_pred = ridge.predict(X_test)

    # Evaluation
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    # Cross‑validation (5‑fold) on the whole program dataset
    cv_scores = cross_val_score(ridge, X_imputed, y, cv=5, scoring='r2')

    # Store model and metadata
    reg_models[prog_id] = {
        'model': ridge,
        'imputer': feat_imputer,
        'subjects': get_program_subjects(prog_id),
        'best_alpha': best_alpha
    }
    reg_metrics[prog_id] = {
        'R2': round(r2, 4),
        'MAE': round(mae, 4),
        'RMSE': round(rmse, 4),
        'CV_R2_Mean': round(cv_scores.mean(), 4),
        'CV_R2_Std': round(cv_scores.std(), 4),
        'n_train': len(X_train),
        'n_test': len(X_test),
        'best_alpha': best_alpha
    }

    # Feature importance = absolute coefficients (averaged over CV folds)
    # RidgeCV doesn't expose coef_ directly (it uses the last fold). We'll refit with best alpha on full data.
    final_ridge = Ridge(alpha=best_alpha)
    final_ridge.fit(X_imputed, y)
    coef_series = pd.Series(np.abs(final_ridge.coef_), index=FEATURES).sort_values(ascending=False)
    coef_importances[prog_id] = coef_series

    # Predict for all students (using the full‑data model)
    X_all = df[FEATURES].copy()
    X_all_imp = feat_imputer.transform(X_all)
    all_program_preds[prog_id] = final_ridge.predict(X_all_imp)

    print(f"     Best alpha: {best_alpha:.2f}")
    print(f"     R²:   {r2:.4f}  (CV mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f})")
    print(f"     MAE:  {mae:.4f}")
    print(f"     RMSE: {rmse:.4f}")

print("\n  ✓ All 5 regression models trained.")

# ==============================================================================
# STEP 5: SUITABILITY SCORING (Bridge to Classification)
# ==============================================================================
print("\n[STEP 5] Computing Suitability Scores...")

suit_df = pd.DataFrame()
suit_df['student_id'] = df['student_id']
suit_df['actual_placement'] = df['actual_placement']
suit_df['preferred_program'] = df['preferred_program']
suit_df['has_valid_preference'] = df['has_valid_preference']
suit_df['g6_final_average'] = df['grade_6_final_average']
suit_df['g6_math'] = df['grade_math']
suit_df['g6_science'] = df['grade_science']
suit_df['g6_english'] = df['grade_english']

# STE eligibility (hard rule)
suit_df['ste_g6_eligible'] = (
    (df['grade_math'].values >= STE_ELIGIBILITY_MIN_GRADE) &
    (df['grade_science'].values >= STE_ELIGIBILITY_MIN_GRADE) &
    (df['grade_english'].values >= STE_ELIGIBILITY_MIN_GRADE)
).astype(int)

suit_df['ste_ineligible_reason'] = df.apply(
    lambda row: ', '.join([
        f'{subj.replace("grade_", "").upper()} ({row[subj]:.0f}<83)'
        for subj in STE_ELIGIBILITY_SUBJECTS
        if row[subj] < STE_ELIGIBILITY_MIN_GRADE
    ]) if any(row[s] < STE_ELIGIBILITY_MIN_GRADE for s in STE_ELIGIBILITY_SUBJECTS)
    else 'Eligible',
    axis=1
)

# Suitability per program
for prog_id, prog_name in PROGRAM_MAP.items():
    pred_col = f'pred_avg_{prog_name}'
    suit_col = f'suitable_{prog_name}'
    margin_col = f'margin_{prog_name}'

    suit_df[pred_col] = all_program_preds[prog_id].round(3)

    grade_ok = suit_df[pred_col] >= SUITABILITY_THRESHOLD[prog_id]
    if prog_id == 1:  # STE
        suit_df[suit_col] = (grade_ok & (suit_df['ste_g6_eligible'] == 1)).astype(int)
    else:
        suit_df[suit_col] = grade_ok.astype(int)

    suit_df[margin_col] = (suit_df[pred_col] - SUITABILITY_THRESHOLD[prog_id]).round(3)

# Top‑3 recommendations (suitable first, then predicted avg)
def top3_recommendations(row):
    progs = list(PROGRAM_MAP.keys())
    pred_cols = [f'pred_avg_{PROGRAM_MAP[p]}' for p in progs]
    suit_cols = [f'suitable_{PROGRAM_MAP[p]}' for p in progs]
    scores = [(p, row[suit_cols[i]], row[pred_cols[i]]) for i, p in enumerate(progs)]
    scores.sort(key=lambda x: (x[1], x[2]), reverse=True)
    return [s[0] for s in scores[:3]]

suit_df['top3_recommendations'] = suit_df.apply(top3_recommendations, axis=1)
suit_df['top1_recommendation'] = suit_df['top3_recommendations'].apply(lambda x: x[0])

# Suitability rates
print("  → Suitability rates:")
for prog_id, prog_name in PROGRAM_MAP.items():
    rate = suit_df[f'suitable_{prog_name}'].mean() * 100
    print(f"     {prog_name:10s}: {rate:.1f}%")

# ==============================================================================
# STEP 6: STAGE 2 — LOGISTIC REGRESSION CLASSIFICATION
# ==============================================================================
print("\n" + "=" * 70)
print("  STAGE 2: LOGISTIC REGRESSION — Program Recommendation")
print("=" * 70)

# Build feature set: original FEATURES + 5 predicted averages
clf_features = FEATURES + [f'pred_avg_{PROGRAM_MAP[p]}' for p in PROGRAM_MAP]

X_clf = pd.DataFrame()
for feat in FEATURES:
    X_clf[feat] = df[feat].values
for prog_id, prog_name in PROGRAM_MAP.items():
    X_clf[f'pred_avg_{prog_name}'] = all_program_preds[prog_id]

y_clf = df['actual_placement'].values

# Impute any remaining NaN in classification features
clf_imputer = SimpleImputer(strategy='mean')
X_clf_imputed = clf_imputer.fit_transform(X_clf)

# Train/test split (stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X_clf_imputed, y_clf, test_size=0.2, random_state=RANDOM_STATE, stratify=y_clf
)

# Scale features for logistic regression (important for coefficients)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Logistic Regression with multinomial, balanced class weights
logreg = LogisticRegression(
    multi_class='multinomial',
    solver='lbfgs',
    class_weight='balanced',
    max_iter=1000,
    random_state=RANDOM_STATE
)
logreg.fit(X_train_scaled, y_train)

# Predictions
y_pred = logreg.predict(X_test_scaled)
y_proba = logreg.predict_proba(X_test_scaled)

# Evaluation metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='macro', zero_division=0)
recall = recall_score(y_test, y_pred, average='macro', zero_division=0)
f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)

# Cross‑validation (stratified)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_scores = cross_val_score(logreg, X_clf_imputed, y_clf, cv=cv, scoring='f1_macro')

print(f"\n  Classification Results:")
print(f"  Accuracy:  {accuracy:.4f}")
print(f"  Precision: {precision:.4f} (macro)")
print(f"  Recall:    {recall:.4f} (macro)")
print(f"  F1-Score:  {f1:.4f} (macro)")
print(f"  CV F1 (mean ± std): {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Per‑class metrics
clf_report = classification_report(
    y_test, y_pred,
    target_names=list(PROGRAM_MAP.values()),
    output_dict=True
)

# Feature importance (absolute coefficients averaged over classes)
coef_matrix = np.abs(logreg.coef_).mean(axis=0)
clf_importance = pd.Series(coef_matrix, index=clf_features).sort_values(ascending=False)

# ==============================================================================
# STEP 7: GENERATE EVALUATION PLOTS (selected key plots)
# ==============================================================================
print("\n[STEP 7] Generating evaluation plots...")

# Plot 1: Regression metrics (R², MAE, RMSE) per program
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle('Ridge Regression — Evaluation Metrics per Program', fontsize=14, fontweight='bold')

prog_names = list(PROGRAM_MAP.values())
colors = list(PROGRAM_COLORS.values())

# R²
r2_vals = [reg_metrics[p]['R2'] for p in PROGRAM_MAP]
axes[0].bar(prog_names, r2_vals, color=colors, alpha=0.85, edgecolor='white')
axes[0].set_title('R² Score', fontweight='bold')
axes[0].set_ylim(0, 1)
for i, v in enumerate(r2_vals):
    axes[0].text(i, v+0.02, f'{v:.3f}', ha='center', fontsize=9, fontweight='bold')
axes[0].grid(axis='y', alpha=0.3)

# MAE
mae_vals = [reg_metrics[p]['MAE'] for p in PROGRAM_MAP]
axes[1].bar(prog_names, mae_vals, color=colors, alpha=0.85, edgecolor='white')
axes[1].set_title('MAE (grade points)', fontweight='bold')
for i, v in enumerate(mae_vals):
    axes[1].text(i, v+0.02, f'{v:.3f}', ha='center', fontsize=9, fontweight='bold')
axes[1].grid(axis='y', alpha=0.3)

# RMSE
rmse_vals = [reg_metrics[p]['RMSE'] for p in PROGRAM_MAP]
axes[2].bar(prog_names, rmse_vals, color=colors, alpha=0.85, edgecolor='white')
axes[2].set_title('RMSE (grade points)', fontweight='bold')
for i, v in enumerate(rmse_vals):
    axes[2].text(i, v+0.02, f'{v:.3f}', ha='center', fontsize=9, fontweight='bold')
axes[2].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('ridge_plot_01_regression_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: ridge_plot_01_regression_metrics.png")

# Plot 2: CV R² with error bars
fig, ax = plt.subplots(figsize=(10, 6))
cv_means = [reg_metrics[p]['CV_R2_Mean'] for p in PROGRAM_MAP]
cv_stds  = [reg_metrics[p]['CV_R2_Std'] for p in PROGRAM_MAP]
ax.bar(prog_names, cv_means, yerr=cv_stds, color=colors, alpha=0.85,
       edgecolor='white', error_kw=dict(ecolor='black', capsize=5))
ax.axhline(0.7, color='green', linestyle='--', alpha=0.7, label='Good (0.7)')
ax.axhline(0.5, color='orange', linestyle='--', alpha=0.7, label='Acceptable (0.5)')
ax.set_title('5‑Fold Cross‑Validation R² per Program', fontsize=13, fontweight='bold')
ax.set_ylabel('R²')
ax.legend()
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('ridge_plot_02_cv_r2.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: ridge_plot_02_cv_r2.png")

# Plot 3: Top 10 feature coefficients for each program (absolute values)
fig, axes = plt.subplots(1, 5, figsize=(22, 8))
fig.suptitle('Top 10 Feature Coefficients (Absolute) — Ridge Regression per Program',
             fontsize=14, fontweight='bold')
for idx, (prog_id, prog_name) in enumerate(PROGRAM_MAP.items()):
    ax = axes[idx]
    top10 = coef_importances[prog_id].head(10)
    clean_names = [f.replace('grade_', 'G6 ').replace('_', ' ').title() for f in top10.index]
    ax.barh(range(len(top10)), top10.values, color=PROGRAM_COLORS[prog_id], alpha=0.85, edgecolor='white')
    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(clean_names, fontsize=8)
    ax.invert_yaxis()
    ax.set_title(prog_name, fontweight='bold', fontsize=10, color=PROGRAM_COLORS[prog_id])
    ax.set_xlabel('Coefficient Magnitude')
    ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('ridge_plot_03_coefficient_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: ridge_plot_03_coefficient_importance.png")

# Plot 4: Confusion Matrix (classification)
fig, ax = plt.subplots(figsize=(8, 7))
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=list(PROGRAM_MAP.values()),
            yticklabels=list(PROGRAM_MAP.values()),
            ax=ax, linewidths=0.5, linecolor='white',
            annot_kws={'size': 12, 'weight': 'bold'})
ax.set_title('Confusion Matrix — Logistic Regression', fontsize=13, fontweight='bold')
ax.set_xlabel('Predicted Program')
ax.set_ylabel('Actual Program')
plt.tight_layout()
plt.savefig('ridge_plot_04_confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: ridge_plot_04_confusion_matrix.png")

# Plot 5: Classification metrics per class
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle('Logistic Regression — Per‑Class Metrics', fontsize=14, fontweight='bold')
for i, metric in enumerate(['precision', 'recall', 'f1-score']):
    vals = [clf_report[name][metric] for name in prog_names]
    axes[i].bar(prog_names, vals, color=colors, alpha=0.85, edgecolor='white')
    axes[i].set_title(metric.capitalize(), fontweight='bold')
    axes[i].set_ylim(0, 1.1)
    for j, v in enumerate(vals):
        axes[i].text(j, v+0.02, f'{v:.3f}', ha='center', fontsize=9, fontweight='bold')
    axes[i].grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('ridge_plot_05_classification_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: ridge_plot_05_classification_metrics.png")

# Plot 6: Feature importance for classifier (top 15)
fig, ax = plt.subplots(figsize=(12, 8))
top15 = clf_importance.head(15)
clean_names = [f.replace('grade_', 'G6 ').replace('pred_avg_', 'Pred ')
               .replace('_', ' ').title() for f in top15.index]
colors_imp = ['#C73E1D' if 'Pred' in n else '#2E86AB' for n in clean_names]
ax.barh(range(len(top15)), top15.values, color=colors_imp, alpha=0.85, edgecolor='white')
ax.set_yticks(range(len(top15)))
ax.set_yticklabels(clean_names, fontsize=9)
ax.invert_yaxis()
ax.set_title('Top 15 Feature Importances (|Coefficient|) — Logistic Regression',
             fontsize=13, fontweight='bold')
ax.set_xlabel('Average Absolute Coefficient')
red_patch = mpatches.Patch(color='#C73E1D', label='Predicted G7 Avg')
blue_patch = mpatches.Patch(color='#2E86AB', label='Original Features')
ax.legend(handles=[red_patch, blue_patch], fontsize=10)
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('ridge_plot_06_classifier_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: ridge_plot_06_classifier_importance.png")

# ==============================================================================
# STEP 8: SAVE MODELS, CONFIG, AND METRICS
# ==============================================================================
print("\n[STEP 8] Saving trained models and configuration...")
import joblib
import os

models_dir = 'ridge_models'
os.makedirs(models_dir, exist_ok=True)

# Save regression models
for prog_id, prog_name in PROGRAM_MAP.items():
    model_data = {
        'model': reg_models[prog_id]['model'],
        'imputer': reg_models[prog_id]['imputer'],
        'subjects': reg_models[prog_id]['subjects'],
        'best_alpha': reg_models[prog_id]['best_alpha'],
        'program_id': prog_id,
        'program_name': prog_name
    }
    joblib.dump(model_data, f'{models_dir}/ridge_{prog_name}.pkl')

# Save classification model and scaler
clf_data = {
    'model': logreg,
    'imputer': clf_imputer,
    'scaler': scaler,
    'clf_features': clf_features
}
joblib.dump(clf_data, f'{models_dir}/classifier.pkl')

# Save configuration and constants
config = {
    'FEATURES': FEATURES,
    'G6_ACADEMIC': G6_ACADEMIC,
    'NON_ACADEMIC': NON_ACADEMIC,
    'G7_COMMON_SUBJECTS': G7_COMMON_SUBJECTS,
    'G7_EXCLUSIVE': G7_EXCLUSIVE,
    'PROGRAM_MAP': PROGRAM_MAP,
    'PROGRAM_COLORS': PROGRAM_COLORS,
    'SUITABILITY_THRESHOLD': SUITABILITY_THRESHOLD,
    'STE_ELIGIBILITY_SUBJECTS': STE_ELIGIBILITY_SUBJECTS,
    'STE_ELIGIBILITY_MIN_GRADE': STE_ELIGIBILITY_MIN_GRADE,
    'clf_features': clf_features
}
joblib.dump(config, f'{models_dir}/config.pkl')

# Save metrics for later comparison
reg_metrics_df = pd.DataFrame(reg_metrics).T
reg_metrics_df.index = [PROGRAM_MAP[p] for p in reg_metrics_df.index]
reg_metrics_df.to_csv('ridge_regression_metrics.csv')

clf_metrics_df = pd.DataFrame(clf_report).T
clf_metrics_df.to_csv('ridge_classification_metrics.csv')

suit_df.to_csv('ridge_suitability_scores.csv', index=False)

print(f"  → Models saved in '{models_dir}/'")
print("  → Metrics saved as CSV files.")

print("\n" + "=" * 70)
print("  RIDGE TRAINING PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 70)