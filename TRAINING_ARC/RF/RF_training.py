
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from scipy.stats import mstats
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score,
                              accuracy_score, precision_score, recall_score,
                              f1_score, confusion_matrix, classification_report)
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder


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


SUITABILITY_THRESHOLD = {
    1: 85,   # STE
    2: 85,   # SPFL
    3: 85,   # SPTVE
    4: 85,   # TOP-5 Regular
    5: 75    # HETERO
}

STE_ELIGIBILITY_SUBJECTS = ['grade_math', 'grade_science', 'grade_english']
STE_ELIGIBILITY_MIN_GRADE = 83


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

# Program-exclusive subjects
G7_EXCLUSIVE = {
    1: 'q1_g7research',         # STE only
    2: 'q1_g7_foreign_language', # SPFL only
    3: 'q1_g7_tve'              # SPTVE only
}


def get_program_subjects(program_id):
    subjects = G7_COMMON_SUBJECTS.copy()
    if program_id in G7_EXCLUSIVE:
        subjects.append(G7_EXCLUSIVE[program_id])
    return subjects

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("=" * 70)
print("  SPARK SYSTEM — Section Placement Prediction")
print("  Capstone Project | ML Training Pipeline")
print("=" * 70)


print("\n[STEP 1] Loading dataset...")

df = pd.read_csv('../SPARK_DATASET.csv')

print(f"  → Dataset loaded: {df.shape[0]} students, {df.shape[1]} columns")
print(f"  → Program distribution:")
for p, name in PROGRAM_MAP.items():
    count = (df['actual_placement'] == p).sum()
    print(f"     {name:10s}: {count} students")

print("\n[STEP 2] Data Preprocessing...")


df['has_valid_preference'] = df['preferred_program'].apply(
    lambda x: 1 if x in [1.0, 2.0, 3.0, 4.0, 5.0] else 0
)
# Add to NON_ACADEMIC features
NON_ACADEMIC.append('has_valid_preference')
FEATURES.append('has_valid_preference')

flagged = (df['has_valid_preference'] == 0).sum()
print(f"  → Flagged {flagged} students with out-of-scope preferred program (OHSP/SNEd)")


print("  → Imputing non-academic missing values (mode imputation)...")

non_academic_imputer = SimpleImputer(strategy='most_frequent')
df[NON_ACADEMIC] = non_academic_imputer.fit_transform(df[NON_ACADEMIC])

missing_non_academic = df[NON_ACADEMIC].isnull().sum().sum()
print(f"     Remaining NaN in non-academic columns: {missing_non_academic}")


print("  → Confirmed: Program-exclusive G7 subjects are structurally NaN for")
print("    other programs — no imputation needed for these.")

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
    mask = df['actual_placement'] == prog_id
    before = df.loc[mask, col].isnull().sum()
    group_mean = df.loc[mask, col].mean()
    df.loc[mask, col] = df.loc[mask, col].fillna(group_mean)
    after = df.loc[mask, col].isnull().sum()
    print(f"     {PROGRAM_MAP[prog_id]} - {col:30s}: {before} NaN → {after} NaN")

# Fix student_061 final grade mismatch (verified during audit)
student_061_mask = df['student_id'] == 'student_061'
if student_061_mask.any():
    computed = df.loc[student_061_mask, G7_COMMON_SUBJECTS].mean(axis=1).values[0]
    df.loc[student_061_mask, 'q1_g7_final_grade'] = round(computed, 3)
    print(f"  → Fixed student_061 final grade: corrected to computed average {computed:.3f}")

print(f"  → Preprocessing complete. Final NaN check:")
remaining_nan = df[G7_COMMON_SUBJECTS + ['q1_g7_final_grade']].isnull().sum().sum()
print(f"     Total remaining NaN in G7 grades: {remaining_nan}")

\
print("\n[STEP 3] Outlier Detection and Treatment...")

"""
OUTLIER STRATEGY:
- Statistical detection using IQR (Interquartile Range) method
- Winsorization applied to cap extreme values at 5th and 95th percentile
  within each program group to prevent cross-program contamination
- Most critical case: student_071's Science grade of 39.6 in HETERO
  (confirmed real data, but extreme outlier that would skew regression)
"""

def detect_outliers_iqr(series, multiplier=1.5):
    """Detect outliers using IQR method."""
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR
    return series[(series < lower) | (series > upper)]

# --- Plot 1: Outlier Detection Visualization ---
fig, axes = plt.subplots(2, 4, figsize=(18, 10))
fig.suptitle('Grade 7 Q1 Grades — Outlier Detection (Before Winsorization)',
             fontsize=15, fontweight='bold', y=1.01)

all_outliers_found = {}

for idx, col in enumerate(G7_COMMON_SUBJECTS):
    ax = axes[idx // 4][idx % 4]
    subject_name = col.replace('q1_g7_', '').replace('_', ' ').upper()

    data_by_program = []
    labels = []
    outlier_info = {}

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

    colors = list(PROGRAM_COLORS.values())
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # Highlight outliers
    for i, (prog_data, label) in enumerate(zip(data_by_program, labels)):
        if label in outlier_info:
            for val in outlier_info[label]:
                ax.annotate(f'★{val:.1f}', xy=(i+1, val),
                            fontsize=7, color='red', ha='center',
                            fontweight='bold')

    ax.set_title(subject_name, fontweight='bold', fontsize=10)
    ax.set_xlabel('Program', fontsize=8)
    ax.set_ylabel('Grade', fontsize=8)
    ax.tick_params(axis='x', labelsize=7)
    ax.axhline(y=75, color='orange', linestyle='--', alpha=0.5, linewidth=1)
    ax.axhline(y=85, color='green', linestyle='--', alpha=0.5, linewidth=1)
    ax.grid(axis='y', alpha=0.3)

# Legend
orange_line = mpatches.Patch(color='orange', alpha=0.5, label='75 threshold (HETERO)')
green_line = mpatches.Patch(color='green', alpha=0.5, label='85 threshold (Special/TOP-5)')
star_patch = mpatches.Patch(color='red', label='★ Detected Outlier')
fig.legend(handles=[orange_line, green_line, star_patch],
           loc='lower center', ncol=3, fontsize=9, bbox_to_anchor=(0.5, -0.02))

plt.tight_layout()
plt.savefig('plot_01_outlier_detection.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_01_outlier_detection.png")
print(f"  → Outlier groups detected: {len(all_outliers_found)}")

# --- Apply Winsorization per program group ---
"""
WINSORIZATION:
- Caps extreme values at the 5th and 95th percentile WITHIN each program group
- This preserves the relative distribution while preventing extreme values
  from disproportionately influencing regression model weights
- Applied per-program to avoid cross-program mean contamination
"""

df_before_wins = df[G7_COMMON_SUBJECTS].copy()

winsorized_count = 0
for col in G7_COMMON_SUBJECTS:
    for p in [1, 2, 3, 4, 5]:
        mask = df['actual_placement'] == p
        prog_data = df.loc[mask, col]
        lower_p = prog_data.quantile(0.05)
        upper_p = prog_data.quantile(0.95)
        before_vals = df.loc[mask, col].copy()
        df.loc[mask, col] = df.loc[mask, col].clip(lower=lower_p, upper=upper_p)
        changed = (before_vals != df.loc[mask, col]).sum()
        winsorized_count += changed

print(f"  → Winsorization applied: {winsorized_count} values adjusted")

# --- Plot 2: Before vs After Winsorization ---
fig, axes = plt.subplots(2, 4, figsize=(18, 10))
fig.suptitle('Grade 7 Q1 Grades — Before vs After Winsorization',
             fontsize=15, fontweight='bold')

for idx, col in enumerate(G7_COMMON_SUBJECTS):
    ax = axes[idx // 4][idx % 4]
    subject_name = col.replace('q1_g7_', '').replace('_', ' ').upper()

    before_data = df_before_wins[col].dropna()
    after_data = df[col].dropna()

    ax.hist(before_data, bins=20, alpha=0.5, color='#E63946', label='Before',
            edgecolor='white', linewidth=0.5)
    ax.hist(after_data, bins=20, alpha=0.5, color='#2A9D8F', label='After',
            edgecolor='white', linewidth=0.5)

    ax.axvline(before_data.min(), color='red', linestyle=':', alpha=0.7,
               linewidth=1.5, label=f'Min before: {before_data.min():.1f}')
    ax.axvline(after_data.min(), color='green', linestyle=':', alpha=0.7,
               linewidth=1.5, label=f'Min after: {after_data.min():.1f}')

    ax.set_title(subject_name, fontweight='bold', fontsize=10)
    ax.set_xlabel('Grade', fontsize=8)
    ax.set_ylabel('Count', fontsize=8)
    ax.legend(fontsize=6)
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('plot_02_winsorization.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_02_winsorization.png")

\
print("\n[STEP 4] Generating EDA visualizations...")

# --- Plot 3: Grade 6 Average Distribution by Program ---
fig, ax = plt.subplots(figsize=(12, 6))
for p, name in PROGRAM_MAP.items():
    data = df[df['actual_placement'] == p]['grade_6_final_average']
    ax.hist(data, bins=15, alpha=0.6, label=f'{name} (n={len(data)})',
            color=PROGRAM_COLORS[p], edgecolor='white')

ax.axvline(85, color='black', linestyle='--', linewidth=2,
           label='85 Threshold')
ax.set_title('Grade 6 Final Average Distribution by Program',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Grade 6 Final Average', fontsize=12)
ax.set_ylabel('Number of Students', fontsize=12)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_03_g6_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_03_g6_distribution.png")

# --- Plot 4: Grade 7 Final Grade Distribution by Program ---
fig, ax = plt.subplots(figsize=(12, 6))
for p, name in PROGRAM_MAP.items():
    data = df[df['actual_placement'] == p]['q1_g7_final_grade']
    ax.hist(data, bins=15, alpha=0.6, label=f'{name} (n={len(data)})',
            color=PROGRAM_COLORS[p], edgecolor='white')

ax.axvline(85, color='black', linestyle='--', linewidth=2,
           label='85 Suitability Threshold')
ax.axvline(75, color='gray', linestyle='--', linewidth=2,
           label='75 HETERO Threshold')
ax.set_title('Grade 7 Q1 Final Grade Distribution by Program',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Grade 7 Q1 Final Grade', fontsize=12)
ax.set_ylabel('Number of Students', fontsize=12)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_04_g7_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_04_g7_distribution.png")

# --- Plot 5: Grade 6 vs Grade 7 Scatter per Program ---
fig, axes = plt.subplots(1, 5, figsize=(20, 5))
fig.suptitle('Grade 6 Final Average vs Grade 7 Q1 Final Grade by Program',
             fontsize=13, fontweight='bold')

for idx, (p, name) in enumerate(PROGRAM_MAP.items()):
    ax = axes[idx]
    prog_df = df[df['actual_placement'] == p]
    ax.scatter(prog_df['grade_6_final_average'], prog_df['q1_g7_final_grade'],
               color=PROGRAM_COLORS[p], alpha=0.6, edgecolors='white', s=40)

    # Trend line
    x = prog_df['grade_6_final_average'].dropna()
    y = prog_df['q1_g7_final_grade'].dropna()
    if len(x) > 1:
        z = np.polyfit(x, y, 1)
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
plt.savefig('plot_05_g6_vs_g7_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_05_g6_vs_g7_scatter.png")

# --- Plot 6: Subject-level Grade 7 averages per program ---
fig, ax = plt.subplots(figsize=(14, 7))
subject_labels = [s.replace('q1_g7_', '').replace('_', '\n').upper()
                  for s in G7_COMMON_SUBJECTS]
x = np.arange(len(G7_COMMON_SUBJECTS))
width = 0.15

for i, (p, name) in enumerate(PROGRAM_MAP.items()):
    prog_df = df[df['actual_placement'] == p]
    means = [prog_df[col].mean() for col in G7_COMMON_SUBJECTS]
    bars = ax.bar(x + i * width, means, width, label=name,
                  color=PROGRAM_COLORS[p], alpha=0.85, edgecolor='white')

ax.axhline(85, color='green', linestyle='--', linewidth=1.5,
           alpha=0.7, label='85 Threshold')
ax.axhline(75, color='orange', linestyle='--', linewidth=1.5,
           alpha=0.7, label='75 Threshold')
ax.set_xticks(x + width * 2)
ax.set_xticklabels(subject_labels, fontsize=9)
ax.set_title('Average Grade 7 Q1 Grades by Subject and Program',
             fontsize=14, fontweight='bold')
ax.set_ylabel('Average Grade', fontsize=12)
ax.set_ylim(70, 100)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_06_g7_subject_averages.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_06_g7_subject_averages.png")


print("\n" + "=" * 70)
print("  STAGE 1: RANDOM FOREST REGRESSION — Grade Prediction (5-Loop)")
print("=" * 70)

"""
THE 5-LOOP PROCESS (Professor's Requirement):
    For each of the 5 programs, we train a separate regression model.
    Each model learns: "Given a student's Grade 6 grades and non-academic
    background, what Grade 7 grades would they get IF placed in this program?"

    This is the core insight: instead of asking "which program does this
    student look like?", we ask "how well would this student PERFORM in
    each program?" — then recommend based on predicted performance.

MODEL: RandomForestRegressor
WHY:
    - Handles mixed features (grades + categorical survey data) without scaling
    - Robust to small per-program sample sizes (min 22 students)
    - Captures non-linear relationships between interests and grades
    - Built-in feature importance for thesis explanation
    - Less prone to overfitting than single decision trees
"""

regression_models = {}      # Store trained models
regression_metrics = {}     # Store evaluation metrics
feature_importances_reg = {} # Store feature importances

# Store predictions for all programs (used in classification stage)
all_program_predictions = {}

for loop_num, (program_id, program_name) in enumerate(PROGRAM_MAP.items(), 1):

    print(f"\n  ── Loop {loop_num}/5: Training Regression Model for {program_name} ──")

    # ── Step A: Filter training data to only students in this program ──
    prog_df = df[df['actual_placement'] == program_id].copy()
    subjects_for_program = get_program_subjects(program_id)

    print(f"     Training samples: {len(prog_df)} students in {program_name}")
    print(f"     Prediction targets: {len(subjects_for_program)} subjects "
          f"({'+ ' + G7_EXCLUSIVE[program_id].replace('q1_g7_','').upper() if program_id in G7_EXCLUSIVE else 'common only'})")

    # ── Step B: Prepare features (X) and targets (y) ──
    X = prog_df[FEATURES].copy()
    y_subjects = prog_df[subjects_for_program].copy()
    y_final = prog_df['q1_g7_final_grade'].copy()

    # Simple imputation for any remaining NaN in features
    feat_imputer = SimpleImputer(strategy='mean')
    X_imputed = feat_imputer.fit_transform(X)
    X_imputed = pd.DataFrame(X_imputed, columns=FEATURES)

    # ── Step C: Train/Test Split ──
    # Note: Small sample sizes per program; use 80/20 split
    X_train, X_test, y_train_final, y_test_final = train_test_split(
        X_imputed, y_final,
        test_size=0.2, random_state=RANDOM_STATE
    )

    # Also split subject-level targets
    y_train_subj = y_subjects.iloc[X_train.index] if hasattr(X_train.index, '__iter__') else y_subjects
    y_test_subj = y_subjects.iloc[X_test.index] if hasattr(X_test.index, '__iter__') else y_subjects

    # ── Step D: Train RandomForest Regressor for FINAL GRADE ──
    rf_reg = RandomForestRegressor(
        n_estimators=200,       # 200 trees for stable predictions
        max_depth=8,            # Prevent overfitting on small datasets
        min_samples_split=3,    # Minimum 3 samples to split a node
        min_samples_leaf=2,     # Minimum 2 samples per leaf
        max_features='sqrt',    # Use sqrt of features at each split
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    rf_reg.fit(X_train, y_train_final)

    # ── Step E: Evaluate ──
    y_pred = rf_reg.predict(X_test)

    r2  = r2_score(y_test_final, y_pred)
    mae = mean_absolute_error(y_test_final, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test_final, y_pred))

    # Cross-validation for robustness (important for small samples)
    cv_scores = cross_val_score(rf_reg, X_imputed, y_final,
                                cv=5, scoring='r2',
                                error_score='raise')

    regression_models[program_id] = {
        'model': rf_reg,
        'imputer': feat_imputer,
        'subjects': subjects_for_program
    }

    regression_metrics[program_id] = {
        'R2': round(r2, 4),
        'MAE': round(mae, 4),
        'RMSE': round(rmse, 4),
        'CV_R2_Mean': round(cv_scores.mean(), 4),
        'CV_R2_Std': round(cv_scores.std(), 4),
        'n_train': len(X_train),
        'n_test': len(X_test)
    }

    feature_importances_reg[program_id] = pd.Series(
        rf_reg.feature_importances_, index=FEATURES
    ).sort_values(ascending=False)

    # Store predictions for ALL students (for classification stage)
    X_all_imputed = feat_imputer.transform(df[FEATURES])
    all_program_predictions[program_id] = rf_reg.predict(X_all_imputed)

    print(f"     R²:   {r2:.4f}  (CV mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f})")
    print(f"     MAE:  {mae:.4f} grade points")
    print(f"     RMSE: {rmse:.4f} grade points")

print("\n  ✓ All 5 regression models trained successfully.")


print("\n[STEP 5] Generating regression evaluation plots...")

# --- Plot 7: Regression Metrics Summary ---
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle('Stage 1 — Regression Model Evaluation Metrics\n(Grade 7 Prediction per Program)',
             fontsize=13, fontweight='bold')

programs = list(PROGRAM_MAP.values())
colors = list(PROGRAM_COLORS.values())

# R² scores
r2_vals = [regression_metrics[p]['R2'] for p in PROGRAM_MAP]
bars = axes[0].bar(programs, r2_vals, color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)
axes[0].set_title('R² Score (Higher = Better)', fontweight='bold')
axes[0].set_ylabel('R² Value')
axes[0].set_ylim(0, 1)
axes[0].axhline(0.7, color='green', linestyle='--', alpha=0.7, label='Good (0.7)')
axes[0].axhline(0.5, color='orange', linestyle='--', alpha=0.7, label='Acceptable (0.5)')
axes[0].legend(fontsize=8)
for bar, val in zip(bars, r2_vals):
    axes[0].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
axes[0].grid(axis='y', alpha=0.3)

# MAE scores
mae_vals = [regression_metrics[p]['MAE'] for p in PROGRAM_MAP]
bars = axes[1].bar(programs, mae_vals, color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)
axes[1].set_title('MAE (Lower = Better)', fontweight='bold')
axes[1].set_ylabel('Mean Absolute Error (grade points)')
for bar, val in zip(bars, mae_vals):
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
axes[1].grid(axis='y', alpha=0.3)

# RMSE scores
rmse_vals = [regression_metrics[p]['RMSE'] for p in PROGRAM_MAP]
bars = axes[2].bar(programs, rmse_vals, color=colors, alpha=0.85, edgecolor='white', linewidth=1.5)
axes[2].set_title('RMSE (Lower = Better)', fontweight='bold')
axes[2].set_ylabel('Root Mean Squared Error (grade points)')
for bar, val in zip(bars, rmse_vals):
    axes[2].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                 f'{val:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
axes[2].grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('plot_07_regression_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_07_regression_metrics.png")

# --- Plot 8: Feature Importance for each regression model ---
fig, axes = plt.subplots(1, 5, figsize=(22, 8))
fig.suptitle('Top 10 Feature Importances — Regression Models per Program',
             fontsize=13, fontweight='bold')

for idx, (p, name) in enumerate(PROGRAM_MAP.items()):
    ax = axes[idx]
    top10 = feature_importances_reg[p].head(10)
    clean_names = [f.replace('grade_', 'G6 ').replace('q1_g7_', 'G7 ')
                   .replace('_', ' ').title() for f in top10.index]
    bars = ax.barh(range(len(top10)), top10.values,
                   color=PROGRAM_COLORS[p], alpha=0.85, edgecolor='white')
    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(clean_names, fontsize=7)
    ax.invert_yaxis()
    ax.set_title(f'{name}', fontweight='bold', fontsize=10, color=PROGRAM_COLORS[p])
    ax.set_xlabel('Importance', fontsize=8)
    ax.grid(axis='x', alpha=0.3)

plt.tight_layout()
plt.savefig('plot_08_feature_importance_regression.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_08_feature_importance_regression.png")

# --- Plot 9: CV R² scores with error bars ---
fig, ax = plt.subplots(figsize=(10, 6))
cv_means = [regression_metrics[p]['CV_R2_Mean'] for p in PROGRAM_MAP]
cv_stds  = [regression_metrics[p]['CV_R2_Std'] for p in PROGRAM_MAP]

bars = ax.bar(programs, cv_means, yerr=cv_stds, color=colors, alpha=0.85,
              edgecolor='white', linewidth=1.5,
              error_kw=dict(ecolor='black', capsize=5, linewidth=2))

ax.axhline(0.7, color='green', linestyle='--', alpha=0.7, linewidth=2,
           label='Good threshold (R²=0.7)')
ax.axhline(0.5, color='orange', linestyle='--', alpha=0.7, linewidth=2,
           label='Acceptable threshold (R²=0.5)')

for bar, val, std in zip(bars, cv_means, cv_stds):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + std + 0.01,
            f'{val:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.set_title('5-Fold Cross-Validation R² Scores per Program Model\n(Error bars = ±1 std)',
             fontsize=13, fontweight='bold')
ax.set_ylabel('Cross-Validated R²', fontsize=12)
ax.set_ylim(0, 1.1)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_09_cv_r2_scores.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_09_cv_r2_scores.png")

# ==============================================================================
# SECTION 8: SUITABILITY SCORING (Bridge between Stage 1 and Stage 2)
# ==============================================================================
print("\n[STEP 6] Computing Suitability Scores...")

"""
SUITABILITY SCORING LOGIC (Professor's Requirement):
    After predicting grades in all 5 programs, we check if the predicted
    grade meets the threshold for each program.

    Threshold rules:
    - STE, SPFL, SPTVE, TOP-5: Predicted average must be ≥ 85
    - HETERO: Predicted average must be ≥ 75

    STE HARD ELIGIBILITY PRE-CHECK (school policy):
    - Before even checking the predicted grade threshold, a student must
      have Grade 6 Math ≥ 83, Science ≥ 83, AND English ≥ 83.
    - If ANY of these three Grade 6 grades is below 83, the student is
      immediately marked INELIGIBLE for STE — even if their predicted
      Grade 7 average in STE would be 95.
    - This is a non-negotiable school policy rule, not a model decision.
    - Reason: STE requires demonstrated STEM aptitude at Grade 6 level
      BEFORE the student can be considered for the program.

    This answers the professor's question: "Why should we recommend
    this student to Program A if their predicted grade is only 75?"
    And also: "Why is this student not recommended for STE even though
    their predicted average is high?" — because eligibility gates apply first.

    The suitability score combines:
    1. STE eligibility pre-check (Grade 6 Math/Science/English ≥ 83)
    2. Whether the predicted grade threshold is met
    3. How far above/below the threshold the prediction falls (margin)
"""

# Build suitability dataframe
suitability_data = pd.DataFrame()
suitability_data['student_id'] = df['student_id'].values
suitability_data['actual_placement'] = df['actual_placement'].values
suitability_data['preferred_program'] = df['preferred_program'].values
suitability_data['has_valid_preference'] = df['has_valid_preference'].values
suitability_data['g6_final_average'] = df['grade_6_final_average'].values
suitability_data['g6_math'] = df['grade_math'].values
suitability_data['g6_science'] = df['grade_science'].values
suitability_data['g6_english'] = df['grade_english'].values

# ── STE ELIGIBILITY PRE-CHECK ──────────────────────────────────────────────────
# Evaluate each student: do they meet the Grade 6 subject minimums for STE?
# All three subjects (Math, Science, English) must be ≥ 83.
suitability_data['ste_g6_eligible'] = (
    (df['grade_math'].values >= STE_ELIGIBILITY_MIN_GRADE) &
    (df['grade_science'].values >= STE_ELIGIBILITY_MIN_GRADE) &
    (df['grade_english'].values >= STE_ELIGIBILITY_MIN_GRADE)
).astype(int)

# Track which specific subjects caused ineligibility (for explanation output)
suitability_data['ste_ineligible_reason'] = df.apply(
    lambda row: ', '.join([
        f'{subj.replace("grade_", "").upper()} ({row[subj]:.0f}<83)'
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

# Breakdown of what caused ineligibility
ineligible_df = suitability_data[suitability_data['ste_g6_eligible'] == 0]
if len(ineligible_df) > 0:
    math_fail    = (df['grade_math']    < STE_ELIGIBILITY_MIN_GRADE).sum()
    science_fail = (df['grade_science'] < STE_ELIGIBILITY_MIN_GRADE).sum()
    english_fail = (df['grade_english'] < STE_ELIGIBILITY_MIN_GRADE).sum()
    print(f"     Below 83 in Math:    {math_fail} students")
    print(f"     Below 83 in Science: {science_fail} students")
    print(f"     Below 83 in English: {english_fail} students")

# ── SUITABILITY SCORING FOR ALL PROGRAMS ──────────────────────────────────────
for p, name in PROGRAM_MAP.items():
    pred_col   = f'pred_avg_{name}'
    suit_col   = f'suitable_{name}'
    margin_col = f'margin_{name}'

    suitability_data[pred_col] = all_program_predictions[p].round(3)

    # Base suitability: predicted grade meets program threshold
    grade_threshold_met = (
        suitability_data[pred_col] >= SUITABILITY_THRESHOLD[p]
    )

    if p == 1:  # STE — apply BOTH the grade threshold AND the eligibility pre-check
        suitability_data[suit_col] = (
            grade_threshold_met & (suitability_data['ste_g6_eligible'] == 1)
        ).astype(int)
    else:
        suitability_data[suit_col] = grade_threshold_met.astype(int)

    suitability_data[margin_col] = (
        suitability_data[pred_col] - SUITABILITY_THRESHOLD[p]
    ).round(3)

# Determine Top 3 recommendations per student
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
            row[f'suitable_{PROGRAM_MAP[p]}'],   # 1 if suitable, 0 if not
            row[pred_avg_cols[p]]                # predicted average as tiebreaker
        ),
        reverse=True
    )
    return sorted_programs[:3]

suitability_data['top3_recommendations'] = suitability_data.apply(
    get_top3_recommendations, axis=1
)
suitability_data['top1_recommendation'] = suitability_data['top3_recommendations'].apply(
    lambda x: x[0]
)

print(f"\n  → Suitability scores computed for {len(suitability_data)} students")

# Suitability rate per program
print("  → Suitability rates (students meeting ALL criteria):")
for p, name in PROGRAM_MAP.items():
    suit_rate = suitability_data[f'suitable_{name}'].mean() * 100
    extra = " (grade threshold + G6 eligibility)" if p == 1 else " (grade threshold only)"
    print(f"     {name:10s}: {suit_rate:.1f}% of all students are predicted suitable{extra}")

# ==============================================================================
# SECTION 9: STAGE 2 — RANDOM FOREST CLASSIFICATION (Program Recommendation)
# ==============================================================================
print("\n" + "=" * 70)
print("  STAGE 2: RANDOM FOREST CLASSIFICATION — Program Recommendation")
print("=" * 70)

"""
CLASSIFICATION MODEL:
    Input:  Predicted Grade 7 averages from all 5 regression models
            + original Grade 6 grades + non-academic features
    Output: Recommended program (1-5)
    Target: actual_placement (what program the student was actually placed in)

MODEL: RandomForestClassifier
WHY:
    - Same algorithm family as regression stage (consistent methodology)
    - Handles imbalanced classes (HETERO=298 vs SPTVE=44) better than
      single decision trees
    - Provides feature importance showing which predicted grades matter most
    - class_weight='balanced' addresses class imbalance
"""

# Build classification features: original features + 5 predicted averages
clf_features = FEATURES + [f'pred_avg_{PROGRAM_MAP[p]}' for p in PROGRAM_MAP]

X_clf = pd.DataFrame()
for feat in FEATURES:
    X_clf[feat] = df[feat].values

for p, name in PROGRAM_MAP.items():
    X_clf[f'pred_avg_{name}'] = all_program_predictions[p]

y_clf = df['actual_placement'].values

# Impute any remaining NaN in clf features
clf_imputer = SimpleImputer(strategy='mean')
X_clf_imputed = clf_imputer.fit_transform(X_clf)

# Train/Test Split (stratified to handle class imbalance)
X_train_clf, X_test_clf, y_train_clf, y_test_clf = train_test_split(
    X_clf_imputed, y_clf,
    test_size=0.2,
    random_state=RANDOM_STATE,
    stratify=y_clf
)

print(f"\n  Training samples: {len(X_train_clf)}")
print(f"  Test samples:     {len(X_test_clf)}")

# Train RandomForest Classifier
rf_clf = RandomForestClassifier(
    n_estimators=300,           # More trees for stable classification
    max_depth=10,
    min_samples_split=3,
    min_samples_leaf=2,
    max_features='sqrt',
    class_weight='balanced',    # Handles HETERO class imbalance
    random_state=RANDOM_STATE,
    n_jobs=-1
)

rf_clf.fit(X_train_clf, y_train_clf)
y_pred_clf = rf_clf.predict(X_test_clf)

# Evaluation
clf_accuracy  = accuracy_score(y_test_clf, y_pred_clf)
clf_precision = precision_score(y_test_clf, y_pred_clf, average='macro', zero_division=0)
clf_recall    = recall_score(y_test_clf, y_pred_clf, average='macro', zero_division=0)
clf_f1        = f1_score(y_test_clf, y_pred_clf, average='macro', zero_division=0)

# Per-class metrics
clf_report = classification_report(
    y_test_clf, y_pred_clf,
    target_names=list(PROGRAM_MAP.values()),
    output_dict=True
)

# Cross-validation
cv_clf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
cv_clf_scores = cross_val_score(rf_clf, X_clf_imputed, y_clf,
                                cv=cv_clf, scoring='f1_macro')

print(f"\n  ── Classification Results ──")
print(f"  Accuracy:  {clf_accuracy:.4f}")
print(f"  Precision: {clf_precision:.4f} (macro)")
print(f"  Recall:    {clf_recall:.4f} (macro)")
print(f"  F1-Score:  {clf_f1:.4f} (macro)")
print(f"  CV F1 (mean ± std): {cv_clf_scores.mean():.4f} ± {cv_clf_scores.std():.4f}")

# Feature importance for classifier
clf_feature_importance = pd.Series(
    rf_clf.feature_importances_, index=clf_features
).sort_values(ascending=False)

# ==============================================================================
# SECTION 10: CLASSIFICATION EVALUATION PLOTS
# ==============================================================================
print("\n[STEP 7] Generating classification evaluation plots...")

# --- Plot 10: Confusion Matrix ---
fig, ax = plt.subplots(figsize=(9, 7))
cm = confusion_matrix(y_test_clf, y_pred_clf)
cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

sns.heatmap(cm_normalized, annot=True, fmt='.2f', cmap='Blues',
            xticklabels=list(PROGRAM_MAP.values()),
            yticklabels=list(PROGRAM_MAP.values()),
            ax=ax, linewidths=0.5, linecolor='white',
            annot_kws={'size': 12, 'weight': 'bold'})

ax.set_title('Confusion Matrix — Program Classification\n(Normalized by Actual Class)',
             fontsize=13, fontweight='bold')
ax.set_ylabel('Actual Program', fontsize=12)
ax.set_xlabel('Predicted Program', fontsize=12)
plt.tight_layout()
plt.savefig('plot_10_confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_10_confusion_matrix.png")

# --- Plot 11: Classification Metrics per Program ---
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle('Stage 2 — Classification Metrics per Program',
             fontsize=13, fontweight='bold')

metric_names = ['precision', 'recall', 'f1-score']
metric_titles = ['Precision', 'Recall', 'F1-Score']

for ax_idx, (metric, title) in enumerate(zip(metric_names, metric_titles)):
    ax = axes[ax_idx]
    vals = [clf_report[name][metric] for name in PROGRAM_MAP.values()
            if name in clf_report]
    bars = ax.bar(list(PROGRAM_MAP.values()), vals,
                  color=list(PROGRAM_COLORS.values()),
                  alpha=0.85, edgecolor='white', linewidth=1.5)
    ax.set_title(f'{title} per Program', fontweight='bold')
    ax.set_ylabel(title)
    ax.set_ylim(0, 1.1)
    ax.axhline(0.8, color='green', linestyle='--', alpha=0.5,
               label='Good (0.8)')
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                f'{val:.3f}', ha='center', va='bottom',
                fontsize=9, fontweight='bold')
    ax.legend(fontsize=8)
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('plot_11_classification_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_11_classification_metrics.png")

# --- Plot 12: Overall Classification Metrics Summary ---
fig, ax = plt.subplots(figsize=(8, 6))
overall_metrics = {
    'Accuracy': clf_accuracy,
    'Precision\n(Macro)': clf_precision,
    'Recall\n(Macro)': clf_recall,
    'F1-Score\n(Macro)': clf_f1,
    'CV F1\n(Macro)': cv_clf_scores.mean()
}

bar_colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']
bars = ax.bar(overall_metrics.keys(), overall_metrics.values(),
              color=bar_colors, alpha=0.85, edgecolor='white', linewidth=1.5)

ax.axhline(0.8, color='green', linestyle='--', linewidth=2,
           alpha=0.7, label='Good threshold (0.8)')
ax.axhline(0.6, color='orange', linestyle='--', linewidth=2,
           alpha=0.7, label='Acceptable threshold (0.6)')

for bar, val in zip(bars, overall_metrics.values()):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
            f'{val:.4f}', ha='center', va='bottom',
            fontsize=11, fontweight='bold')

ax.set_title('Overall Classification Evaluation Metrics\n(Program Recommendation)',
             fontsize=13, fontweight='bold')
ax.set_ylabel('Score', fontsize=12)
ax.set_ylim(0, 1.15)
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_12_overall_classification_metrics.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_12_overall_classification_metrics.png")

# --- Plot 13: Feature Importance for Classifier ---
fig, ax = plt.subplots(figsize=(12, 8))
top15_clf = clf_feature_importance.head(15)
clean_names_clf = [f.replace('grade_', 'G6 ').replace('q1_g7_', 'G7 ')
                   .replace('pred_avg_', 'Predicted ').replace('_', ' ').title()
                   for f in top15_clf.index]

bar_colors_imp = ['#C73E1D' if 'Predicted' in n else '#2E86AB' for n in clean_names_clf]
bars = ax.barh(range(len(top15_clf)), top15_clf.values,
               color=bar_colors_imp, alpha=0.85, edgecolor='white')
ax.set_yticks(range(len(top15_clf)))
ax.set_yticklabels(clean_names_clf, fontsize=10)
ax.invert_yaxis()
ax.set_title('Top 15 Feature Importances — Classification Model\n(Red = Predicted Grade Features)',
             fontsize=13, fontweight='bold')
ax.set_xlabel('Feature Importance', fontsize=12)

red_patch = mpatches.Patch(color='#C73E1D', alpha=0.85,
                            label='Predicted G7 Avg (from Regression)')
blue_patch = mpatches.Patch(color='#2E86AB', alpha=0.85,
                             label='Original Features (G6/Non-academic)')
ax.legend(handles=[red_patch, blue_patch], fontsize=10)
ax.grid(axis='x', alpha=0.3)
plt.tight_layout()
plt.savefig('plot_13_feature_importance_classifier.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_13_feature_importance_classifier.png")

# --- Plot 14: Suitability Heatmap ---
fig, ax = plt.subplots(figsize=(10, 6))
suit_rates = {}
for p, name in PROGRAM_MAP.items():
    by_actual = []
    for actual_p in [1, 2, 3, 4, 5]:
        sub = suitability_data[suitability_data['actual_placement'] == actual_p]
        rate = sub[f'suitable_{name}'].mean() * 100
        by_actual.append(rate)
    suit_rates[name] = by_actual

suit_df = pd.DataFrame(suit_rates, index=list(PROGRAM_MAP.values()))
sns.heatmap(suit_df, annot=True, fmt='.1f', cmap='RdYlGn',
            ax=ax, linewidths=0.5, linecolor='white',
            annot_kws={'size': 11, 'weight': 'bold'},
            vmin=0, vmax=100)
ax.set_title('Suitability Rate (%) — Actual vs Predicted Program\n'
             '(% of students meeting grade threshold for each program)',
             fontsize=12, fontweight='bold')
ax.set_xlabel('Predicted Suitable For Program', fontsize=11)
ax.set_ylabel('Actual Placed In Program', fontsize=11)
plt.tight_layout()
plt.savefig('plot_14_suitability_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_14_suitability_heatmap.png")

# --- Plot 14b: STE Eligibility Breakdown ---
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
fig.suptitle('STE Grade 6 Eligibility Analysis\n'
             '(All 3 subjects must be ≥ 83 for STE recommendation)',
             fontsize=13, fontweight='bold')

ste_subjects = {
    'grade_math':    'Math',
    'grade_science': 'Science',
    'grade_english': 'English'
}

for idx, (col, label) in enumerate(ste_subjects.items()):
    ax = axes[idx]
    eligible   = (df[col] >= STE_ELIGIBILITY_MIN_GRADE).sum()
    ineligible = (df[col] <  STE_ELIGIBILITY_MIN_GRADE).sum()

    bars = ax.bar(['Eligible\n(≥83)', 'Ineligible\n(<83)'],
                  [eligible, ineligible],
                  color=['#2A9D8F', '#E63946'],
                  alpha=0.85, edgecolor='white', linewidth=1.5,
                  width=0.5)

    for bar, val in zip(bars, [eligible, ineligible]):
        pct = val / len(df) * 100
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 2,
                f'{val}\n({pct:.1f}%)',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_title(f'G6 {label}', fontweight='bold', fontsize=12)
    ax.set_ylabel('Number of Students', fontsize=10)
    ax.set_ylim(0, len(df) * 1.15)
    ax.axhline(len(df), color='gray', linestyle='--', alpha=0.3)
    ax.grid(axis='y', alpha=0.3)

    # Per-program breakdown as annotation
    prog_lines = []
    for p, pname in PROGRAM_MAP.items():
        prog_df = df[df['actual_placement'] == p]
        elig_p = (prog_df[col] >= STE_ELIGIBILITY_MIN_GRADE).sum()
        prog_lines.append(f'{pname}: {elig_p}/{len(prog_df)}')
    ax.text(0.98, 0.97, '\n'.join(prog_lines),
            transform=ax.transAxes, fontsize=7,
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.4))

plt.tight_layout()
plt.savefig('plot_14b_ste_eligibility.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_14b_ste_eligibility.png")

# ==============================================================================
# SECTION 11: COMPLETE METRICS SUMMARY TABLE
# ==============================================================================
print("\n" + "=" * 70)
print("  COMPLETE EVALUATION METRICS SUMMARY")
print("=" * 70)

print("\n── STAGE 1: REGRESSION METRICS (Grade Prediction per Program) ──")
print(f"{'Program':<12} {'R²':>8} {'MAE':>8} {'RMSE':>8} {'CV R²':>10} {'N Train':>8}")
print("-" * 60)
for p, name in PROGRAM_MAP.items():
    m = regression_metrics[p]
    print(f"{name:<12} {m['R2']:>8.4f} {m['MAE']:>8.4f} {m['RMSE']:>8.4f} "
          f"{m['CV_R2_Mean']:>8.4f}±{m['CV_R2_Std']:.3f} {m['n_train']:>8}")

print("\n── STAGE 2: CLASSIFICATION METRICS (Program Recommendation) ──")
print(f"  Overall Accuracy:     {clf_accuracy:.4f}")
print(f"  Macro Precision:      {clf_precision:.4f}")
print(f"  Macro Recall:         {clf_recall:.4f}")
print(f"  Macro F1-Score:       {clf_f1:.4f}")
print(f"  CV F1 (mean ± std):   {cv_clf_scores.mean():.4f} ± {cv_clf_scores.std():.4f}")

print("\n  Per-Program Classification Metrics:")
print(f"  {'Program':<12} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
print("  " + "-" * 50)
for name in PROGRAM_MAP.values():
    if name in clf_report:
        r = clf_report[name]
        print(f"  {name:<12} {r['precision']:>10.4f} {r['recall']:>10.4f} "
              f"{r['f1-score']:>10.4f} {int(r['support']):>10}")

# ==============================================================================
# SECTION 12: SAMPLE RECOMMENDATION OUTPUT
# ==============================================================================
print("\n" + "=" * 70)
print("  SAMPLE: System Recommendation for 3 Students")
print("=" * 70)

def generate_recommendation(student_row, models_dict, reg_metrics):
    """
    Generate a full recommendation for one student.
    This is what your system's output function should look like.

    STE eligibility is checked BEFORE grade threshold for STE recommendations.
    """
    sid    = student_row['student_id']
    actual = PROGRAM_MAP[student_row['actual_placement']]
    pref   = student_row['preferred_program']
    has_pref = student_row['has_valid_preference']

    print(f"\n  Student: {sid}")
    print(f"  Grade 6 Final Average : {student_row['g6_final_average']:.2f}")
    print(f"  Grade 6 Math          : {student_row['g6_math']:.0f}  "
          f"{'✅' if student_row['g6_math'] >= STE_ELIGIBILITY_MIN_GRADE else '❌ (below 83 — STE ineligible)'}")
    print(f"  Grade 6 Science       : {student_row['g6_science']:.0f}  "
          f"{'✅' if student_row['g6_science'] >= STE_ELIGIBILITY_MIN_GRADE else '❌ (below 83 — STE ineligible)'}")
    print(f"  Grade 6 English       : {student_row['g6_english']:.0f}  "
          f"{'✅' if student_row['g6_english'] >= STE_ELIGIBILITY_MIN_GRADE else '❌ (below 83 — STE ineligible)'}")

    ste_eligible = student_row['ste_g6_eligible'] == 1
    print(f"  STE G6 Eligibility    : {'✅ ELIGIBLE' if ste_eligible else '❌ INELIGIBLE — ' + student_row['ste_ineligible_reason']}")
    print(f"  Actual Placement      : {actual}")

    if has_pref and not pd.isna(pref):
        print(f"  Preferred Program     : {PROGRAM_MAP.get(int(pref), 'Unknown')}")
    else:
        print("  Preferred Program     : OHSP/SNEd (out of scope)")
    print()

    # Get predicted averages for all programs
    pred_avgs = {}
    for p, name in PROGRAM_MAP.items():
        pred_avgs[p] = student_row[f'pred_avg_{name}']

    # Rank using the same logic as get_top3_recommendations
    ranked = sorted(
        pred_avgs.items(),
        key=lambda x: (
            student_row[f'suitable_{PROGRAM_MAP[x[0]]}'],
            x[1]
        ),
        reverse=True
    )

    print(f"  {'Program':<12} {'Pred Avg':>10} {'Threshold':>10} "
          f"{'G6 Elig':>10} {'Suitable':>10}")
    print(f"  " + "-" * 58)
    for p, avg in ranked:
        thresh = SUITABILITY_THRESHOLD[p]

        if p == 1:  # STE
            elig_str = '✅' if ste_eligible else '❌'
            grade_ok = avg >= thresh
            suitable_str = '✅ YES' if (grade_ok and ste_eligible) else '❌ NO'
            if not ste_eligible:
                suitable_str += ' (G6 ineligible)'
            elif not grade_ok:
                suitable_str += ' (grade)'
        else:
            elig_str  = 'N/A'
            grade_ok  = avg >= thresh
            suitable_str = '✅ YES' if grade_ok else '❌ NO'

        marker = ' ◄ TOP 3' if ranked.index((p, avg)) < 3 else ''
        print(f"  {PROGRAM_MAP[p]:<12} {avg:>10.2f} {thresh:>10} "
              f"{elig_str:>10} {suitable_str:>10}{marker}")

    top3 = [p for p, _ in ranked[:3]]
    print(f"\n  📌 TOP 3 RECOMMENDATIONS: "
          f"{', '.join([PROGRAM_MAP[p] for p in top3])}")

    # STE-specific note if ineligible
    if not ste_eligible and 1 not in top3:
        reason = student_row['ste_ineligible_reason']
        print(f"  ℹ️  STE excluded: Grade 6 subject requirement not met "
              f"({reason})")

    if has_pref and not pd.isna(pref):
        pref_p = int(pref)
        if pref_p in top3:
            print(f"  ✅ Preferred program ({PROGRAM_MAP[pref_p]}) is in Top 3 — MATCH")
        else:
            pred_for_pref  = pred_avgs.get(pref_p, 0)
            thresh_for_pref = SUITABILITY_THRESHOLD[pref_p]
            print(f"  ⚠️  Preferred program ({PROGRAM_MAP[pref_p]}) is NOT in Top 3")

            # Explain STE specifically if that was the preference
            if pref_p == 1 and not ste_eligible:
                reason = student_row['ste_ineligible_reason']
                print(f"     Reason: Does not meet STE Grade 6 eligibility requirement.")
                print(f"     Failed subject(s): {reason}")
                print(f"     The student must have Grade 6 Math, Science, AND English ≥ 83 "
                      f"to qualify for STE.")
            else:
                print(f"     Predicted grade if placed in {PROGRAM_MAP[pref_p]}: "
                      f"{pred_for_pref:.2f} (threshold: {thresh_for_pref})")
                if pred_for_pref < thresh_for_pref:
                    diff = thresh_for_pref - pred_for_pref
                    print(f"     Reason: Predicted grade is {diff:.2f} points below "
                          f"the {thresh_for_pref} threshold for {PROGRAM_MAP[pref_p]}")

# Show sample recommendations:
# Student 0   — likely high performer (STE/SPFL range)
# Student 80  — mid-range performer
# Student 300 — HETERO range
# + one student who PREFERS STE but is G6-ineligible
sample_indices = [0, 80, 300]
ste_pref_ineligible = suitability_data[
    (suitability_data['preferred_program'] == 1) &
    (suitability_data['ste_g6_eligible'] == 0)
]
if len(ste_pref_ineligible) > 0:
    sample_indices.append(ste_pref_ineligible.index[0])
    print("\n  (4th sample: student who prefers STE but is G6-ineligible)")

for idx in sample_indices:
    if idx < len(suitability_data):
        generate_recommendation(suitability_data.iloc[idx],
                                regression_models, regression_metrics)

# ==============================================================================
# SECTION 13: FINAL SUMMARY PLOT — Dashboard
# ==============================================================================
print("\n[STEP 8] Generating final summary dashboard...")

fig = plt.figure(figsize=(18, 12))
fig.suptitle('SPARK System — Complete Model Evaluation Dashboard',
             fontsize=16, fontweight='bold', y=1.01)

# Subplot layout
gs = fig.add_gridspec(3, 4, hspace=0.45, wspace=0.4)

# 1. R² per program
ax1 = fig.add_subplot(gs[0, 0])
r2_vals = [regression_metrics[p]['R2'] for p in PROGRAM_MAP]
ax1.bar(programs, r2_vals, color=colors, alpha=0.85, edgecolor='white')
ax1.set_title('Regression R²', fontweight='bold', fontsize=10)
ax1.set_ylim(0, 1)
ax1.axhline(0.7, color='green', linestyle='--', alpha=0.6, linewidth=1)
ax1.tick_params(axis='x', labelsize=7)
[ax1.text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
 for i, v in enumerate(r2_vals)]
ax1.grid(axis='y', alpha=0.3)

# 2. MAE per program
ax2 = fig.add_subplot(gs[0, 1])
mae_vals = [regression_metrics[p]['MAE'] for p in PROGRAM_MAP]
ax2.bar(programs, mae_vals, color=colors, alpha=0.85, edgecolor='white')
ax2.set_title('Regression MAE', fontweight='bold', fontsize=10)
ax2.tick_params(axis='x', labelsize=7)
[ax2.text(i, v + 0.01, f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
 for i, v in enumerate(mae_vals)]
ax2.grid(axis='y', alpha=0.3)

# 3. RMSE per program
ax3 = fig.add_subplot(gs[0, 2])
rmse_vals = [regression_metrics[p]['RMSE'] for p in PROGRAM_MAP]
ax3.bar(programs, rmse_vals, color=colors, alpha=0.85, edgecolor='white')
ax3.set_title('Regression RMSE', fontweight='bold', fontsize=10)
ax3.tick_params(axis='x', labelsize=7)
[ax3.text(i, v + 0.01, f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
 for i, v in enumerate(rmse_vals)]
ax3.grid(axis='y', alpha=0.3)

# 4. Overall classification metrics
ax4 = fig.add_subplot(gs[0, 3])
clf_metrics_vals = [clf_accuracy, clf_precision, clf_recall, clf_f1]
clf_metrics_labels = ['Accuracy', 'Precision', 'Recall', 'F1']
ax4.bar(clf_metrics_labels, clf_metrics_vals,
        color=['#264653','#2A9D8F','#E9C46A','#E76F51'], alpha=0.85, edgecolor='white')
ax4.set_title('Classification Metrics', fontweight='bold', fontsize=10)
ax4.set_ylim(0, 1.1)
ax4.axhline(0.8, color='green', linestyle='--', alpha=0.6, linewidth=1)
ax4.tick_params(axis='x', labelsize=8)
[ax4.text(i, v + 0.02, f'{v:.2f}', ha='center', fontsize=8, fontweight='bold')
 for i, v in enumerate(clf_metrics_vals)]
ax4.grid(axis='y', alpha=0.3)

# 5. Confusion Matrix (smaller)
ax5 = fig.add_subplot(gs[1, :2])
cm = confusion_matrix(y_test_clf, y_pred_clf)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=list(PROGRAM_MAP.values()),
            yticklabels=list(PROGRAM_MAP.values()),
            ax=ax5, linewidths=0.5, linecolor='white',
            annot_kws={'size': 10, 'weight': 'bold'})
ax5.set_title('Confusion Matrix (Counts)', fontweight='bold', fontsize=10)
ax5.set_xlabel('Predicted', fontsize=9)
ax5.set_ylabel('Actual', fontsize=9)
ax5.tick_params(labelsize=8)

# 6. Sample distribution
ax6 = fig.add_subplot(gs[1, 2:])
program_counts = df['actual_placement'].value_counts().sort_index()
pcolors = [PROGRAM_COLORS[p] for p in program_counts.index]
wedges, texts, autotexts = ax6.pie(
    program_counts.values,
    labels=[PROGRAM_MAP[p] for p in program_counts.index],
    autopct='%1.1f%%',
    colors=pcolors,
    startangle=90,
    pctdistance=0.75
)
for autotext in autotexts:
    autotext.set_fontsize(8)
    autotext.set_fontweight('bold')
ax6.set_title('Dataset Distribution by Program', fontweight='bold', fontsize=10)

# 7. G6 vs G7 correlation per program
ax7 = fig.add_subplot(gs[2, :2])
for p, name in PROGRAM_MAP.items():
    prog_df = df[df['actual_placement'] == p]
    ax7.scatter(prog_df['grade_6_final_average'],
                prog_df['q1_g7_final_grade'],
                color=PROGRAM_COLORS[p], alpha=0.4, s=20, label=name)

ax7.axhline(85, color='green', linestyle='--', alpha=0.5, linewidth=1)
ax7.axvline(85, color='green', linestyle='--', alpha=0.5, linewidth=1)
ax7.set_title('G6 Avg vs G7 Q1 Final Grade', fontweight='bold', fontsize=10)
ax7.set_xlabel('Grade 6 Final Average', fontsize=9)
ax7.set_ylabel('Grade 7 Q1 Final Grade', fontsize=9)
ax7.legend(fontsize=7, ncol=2)
ax7.grid(alpha=0.3)

# 8. CV scores
ax8 = fig.add_subplot(gs[2, 2:])
cv_means = [regression_metrics[p]['CV_R2_Mean'] for p in PROGRAM_MAP]
cv_stds  = [regression_metrics[p]['CV_R2_Std'] for p in PROGRAM_MAP]
ax8.bar(programs, cv_means, yerr=cv_stds, color=colors, alpha=0.85,
        edgecolor='white',
        error_kw=dict(ecolor='black', capsize=4, linewidth=1.5))
ax8.set_title('CV R² per Program Model', fontweight='bold', fontsize=10)
ax8.set_ylim(0, 1.1)
ax8.axhline(0.7, color='green', linestyle='--', alpha=0.6, linewidth=1)
ax8.tick_params(axis='x', labelsize=7)
[ax8.text(i, v + s + 0.02, f'{v:.2f}', ha='center', fontsize=7, fontweight='bold')
 for i, (v, s) in enumerate(zip(cv_means, cv_stds))]
ax8.grid(axis='y', alpha=0.3)

plt.savefig('plot_15_dashboard.png', dpi=150, bbox_inches='tight')
plt.close()
print("  → Saved: plot_15_dashboard.png")

# ==============================================================================
# SECTION 14: SAVE ALL OUTPUTS
# ==============================================================================
print("\n[STEP 9] Saving outputs...")

# Save suitability scores
suitability_data.drop(columns=['top3_recommendations'], errors='ignore').to_csv(
    'suitability_scores.csv', index=False
)
print("  → Saved: suitability_scores.csv")

# Save regression metrics
reg_metrics_df = pd.DataFrame(regression_metrics).T
reg_metrics_df.index = [PROGRAM_MAP[p] for p in reg_metrics_df.index]
reg_metrics_df.to_csv('regression_metrics.csv')
print("  → Saved: regression_metrics.csv")

# Save classification report
clf_df = pd.DataFrame(clf_report).T
clf_df.to_csv('classification_metrics.csv')
print("  → Saved: classification_metrics.csv")

# ==============================================================================
# SAVE TRAINED MODELS FOR USE IN TESTING/PREDICTION SCRIPT
# ==============================================================================
import joblib, os

models_dir = 'spark_models'
os.makedirs(models_dir, exist_ok=True)

# Save all 5 regression models
for p, name in PROGRAM_MAP.items():
    model_data = {
        'model':    regression_models[p]['model'],
        'imputer':  regression_models[p]['imputer'],
        'subjects': regression_models[p]['subjects'],
        'program_id':   p,
        'program_name': name
    }
    joblib.dump(model_data, f'{models_dir}/regression_{name}.pkl')

# Save classification model
clf_data = {
    'model':        rf_clf,
    'imputer':      clf_imputer,
    'clf_features': clf_features
}
joblib.dump(clf_data, f'{models_dir}/classifier.pkl')

# Save feature list and constants for the prediction script
config = {
    'FEATURES':               FEATURES,
    'G6_ACADEMIC':            G6_ACADEMIC,
    'NON_ACADEMIC':           NON_ACADEMIC,
    'G7_COMMON_SUBJECTS':     G7_COMMON_SUBJECTS,
    'G7_EXCLUSIVE':           G7_EXCLUSIVE,
    'PROGRAM_MAP':            PROGRAM_MAP,
    'PROGRAM_COLORS':         PROGRAM_COLORS,
    'SUITABILITY_THRESHOLD':  SUITABILITY_THRESHOLD,
    'STE_ELIGIBILITY_SUBJECTS':  STE_ELIGIBILITY_SUBJECTS,
    'STE_ELIGIBILITY_MIN_GRADE': STE_ELIGIBILITY_MIN_GRADE,
    'clf_features':           clf_features
}
joblib.dump(config, f'{models_dir}/config.pkl')

print(f"  → Saved: {models_dir}/regression_STE.pkl")
print(f"  → Saved: {models_dir}/regression_SPFL.pkl")
print(f"  → Saved: {models_dir}/regression_SPTVE.pkl")
print(f"  → Saved: {models_dir}/regression_TOP-5.pkl")
print(f"  → Saved: {models_dir}/regression_HETERO.pkl")
print(f"  → Saved: {models_dir}/classifier.pkl")
print(f"  → Saved: {models_dir}/config.pkl")
print(f"  ✓ Models saved — ready for spark_predict.py")

print("\n" + "=" * 70)
print("  SPARK TRAINING PIPELINE COMPLETE")
print("=" * 70)
print(f"  Total plots generated: 16")
print(f"  Models trained:        6 (5 regression + 1 classification)")
print(f"  Students processed:    {len(df)}")
print("=" * 70)
