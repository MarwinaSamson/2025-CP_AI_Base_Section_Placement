import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, f1_score, confusion_matrix
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# Configuration
TEST_CSV_PATH = '../DATASET/TRAINING_Student_Placement_Data.csv'
MODEL_DIR = '../MODELS/xgboost'
PLACEMENT_MAP = {1: 'STE', 2: 'SPFL', 3: 'SPTVE', 4: 'Top-5 Regular', 5: 'Hetero'}

print("=" * 60)
print("STUDENT PLACEMENT MODEL - TESTING")
print("=" * 60)

# ----------------------------------------------------------------------------
# STEP 1: Load Model and Components
# ----------------------------------------------------------------------------
print("\n[Step 1] Loading Model...")

model_path = f'{MODEL_DIR}/placement_xgboost_model.pkl'
imputer_path = f'{MODEL_DIR}/imputer.pkl'
features_path = f'{MODEL_DIR}/feature_names.pkl'

if not all(os.path.exists(p) for p in [model_path, imputer_path, features_path]):
    print("Model files not found. Please run training first.")
    exit()

model = joblib.load(model_path)
imputer = joblib.load(imputer_path)
feature_names = joblib.load(features_path)

print("Model loaded successfully")

# ----------------------------------------------------------------------------
# STEP 2: Load Test Data
# ----------------------------------------------------------------------------
print("\n[Step 2] Loading Test Data...")

if not os.path.exists(TEST_CSV_PATH):
    print(f"File not found: {TEST_CSV_PATH}")
    exit()

df_test = pd.read_csv(TEST_CSV_PATH)
print(f"Loaded {len(df_test)} students")

print("\nClass Distribution:")
for code, name in PLACEMENT_MAP.items():
    count = len(df_test[df_test['actual_placement'] == code])
    print(f"  {code} ({name}): {count} ({count/len(df_test)*100:.1f}%)")

# ----------------------------------------------------------------------------
# STEP 3: Prepare Test Features
# ----------------------------------------------------------------------------
print("\n[Step 3] Preparing Features...")

X_test = df_test.drop(columns=['student_id', 'actual_placement'])
y_test = df_test['actual_placement'] - 1

# Impute missing values using the saved imputer
X_test_imputed = pd.DataFrame(
    imputer.transform(X_test),
    columns=X_test.columns,
    index=X_test.index
)

# Feature Engineering (must match training)
enjoy_cols = ['enjoy_math', 'enjoy_science', 'enjoy_english', 'enjoy_filipino',
              'enjoy_arpan', 'enjoy_mapeh', 'enjoy_tle']
difficulty_cols = ['difficulty_reading', 'difficulty_writing', 'difficulty_math',
                   'difficulty_focusing', 'difficulty_social_interaction']
award_cols = ['award_highest_honors', 'award_high_honors', 'award_with_honors',
              'award_best_science', 'award_best_math', 'award_best_english',
              'award_conduct', 'achiever_award']
grade_cols = ['grade_math', 'grade_science', 'grade_english', 'grade_filipino',
              'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp']

X_test_imputed['total_subjects_enjoyed'] = X_test_imputed[enjoy_cols].sum(axis=1)
X_test_imputed['total_difficulties'] = X_test_imputed[difficulty_cols].sum(axis=1)
X_test_imputed['total_awards'] = X_test_imputed[award_cols].sum(axis=1)
X_test_imputed['meets_ste_criteria'] = (X_test_imputed[grade_cols] >= 90).all(axis=1).astype(int)

# Ensure columns match training order
X_test_imputed = X_test_imputed[feature_names]

print(f"Features prepared: {X_test_imputed.shape[1]} total")

# ----------------------------------------------------------------------------
# STEP 4: Make Predictions
# ----------------------------------------------------------------------------
print("\n[Step 4] Making Predictions...")

y_pred = model.predict(X_test_imputed)
y_pred_proba = model.predict_proba(X_test_imputed)

print("Predictions complete")

# ----------------------------------------------------------------------------
# STEP 5: Evaluate Performance
# ----------------------------------------------------------------------------
print("\n[Step 5] Evaluation Results")
print("=" * 60)

accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"\nOverall Metrics:")
print(f"  Accuracy: {accuracy*100:.2f}%")
print(f"  F1-Score: {f1:.4f}")

print("\nClassification Report:")
print("-" * 60)
target_names = [PLACEMENT_MAP[i] for i in sorted(PLACEMENT_MAP.keys())]
print(classification_report(y_test, y_pred, target_names=target_names))

print("Confusion Matrix:")
print("-" * 60)
cm = confusion_matrix(y_test, y_pred)
cm_df = pd.DataFrame(cm, index=target_names, columns=target_names)
print(cm_df)

# ----------------------------------------------------------------------------
# STEP 6: Per-Class Analysis
# ----------------------------------------------------------------------------
print("\n[Step 6] Per-Class Analysis")
print("-" * 60)

for i, name in enumerate(target_names):
    mask = y_test == i
    if mask.sum() > 0:
        class_acc = (y_pred[mask] == i).sum() / mask.sum() * 100
        print(f"  {name:15} Accuracy: {class_acc:.2f}% ({mask.sum()} samples)")

# ----------------------------------------------------------------------------
# STEP 7: Sample Predictions
# ----------------------------------------------------------------------------
print("\n[Step 7] Sample Predictions (First 10)")
print("-" * 60)

for i in range(min(10, len(df_test))):
    student_id = df_test.iloc[i]['student_id']
    actual = PLACEMENT_MAP[y_test.iloc[i] + 1]
    predicted = PLACEMENT_MAP[y_pred[i] + 1]
    confidence = y_pred_proba[i].max() * 100
    match = "Correct" if y_test.iloc[i] == y_pred[i] else "Wrong"
    
    print(f"  Student {student_id}: Actual={actual:15} Predicted={predicted:15} "
          f"Conf={confidence:5.1f}%  [{match}]")

# ----------------------------------------------------------------------------
# STEP 8: Detailed Recommendation for Single Student
# ----------------------------------------------------------------------------
print("\n[Step 8] Detailed Recommendation Example")
print("=" * 60)

sample_idx = 0
student_id = df_test.iloc[sample_idx]['student_id']
actual = y_test.iloc[sample_idx]

print(f"\nStudent ID: {student_id}")
print(f"Actual Placement: {PLACEMENT_MAP[actual + 1]}")

print("\nRecommendations (ranked by confidence):")
probabilities = y_pred_proba[sample_idx]
results = [(PLACEMENT_MAP[i+1], prob) for i, prob in enumerate(probabilities)]
results.sort(key=lambda x: x[1], reverse=True)

for rank, (name, prob) in enumerate(results, 1):
    marker = " <-- Recommended" if rank == 1 else ""
    print(f"  {rank}. {name:15} {prob*100:6.2f}%{marker}")

# ----------------------------------------------------------------------------
# STEP 9: Save Results
# ----------------------------------------------------------------------------
print("\n[Step 9] Saving Results...")

results_df = df_test[['student_id', 'actual_placement']].copy()
results_df['predicted_placement'] = y_pred + 1
results_df['predicted_name'] = results_df['predicted_placement'].map(PLACEMENT_MAP)
results_df['actual_name'] = results_df['actual_placement'].map(PLACEMENT_MAP)
results_df['correct'] = results_df['actual_placement'] == results_df['predicted_placement']
results_df['confidence'] = y_pred_proba.max(axis=1)

# Add individual class probabilities
for i, name in enumerate(target_names):
    results_df[f'prob_{name}'] = y_pred_proba[:, i]

os.makedirs('results', exist_ok=True)
results_df.to_csv('results/test_predictions.csv', index=False)

print("Saved: results/test_predictions.csv")

# ----------------------------------------------------------------------------
# Summary
# ----------------------------------------------------------------------------
print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)
print(f"""
Results Summary:
  - Total Students Tested: {len(df_test)}
  - Correct Predictions: {(y_test == y_pred).sum()}
  - Wrong Predictions: {(y_test != y_pred).sum()}
  - Accuracy: {accuracy*100:.2f}%
  - F1-Score: {f1:.4f}

Output File:
  - results/test_predictions.csv
""")
print("=" * 60)