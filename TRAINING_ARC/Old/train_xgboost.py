import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import joblib
import os
import warnings
warnings.filterwarnings('ignore')

# Configuration
CSV_PATH = 'dataset/TRAINING_Student_Placement_Data.csv'
MODEL_DIR = 'models/xgboost'
PLACEMENT_MAP = {1: 'STE', 2: 'SPFL', 3: 'SPTVE', 4: 'Top-5 Regular', 5: 'Hetero'}


print("STUDENT PLACEMENT RECOMMENDATION SYSTEM - XGBoost")



# STEP 1: Load Data

print("\n[Step 1] Loading Data...")

if not os.path.exists(CSV_PATH):
    print(f"File not found: {CSV_PATH}")
    exit()

df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} students, {len(df.columns)} columns")

print("\nClass Distribution:")
for code, name in PLACEMENT_MAP.items():
    count = len(df[df['actual_placement'] == code])
    print(f"  {code} ({name}): {count} ({count/len(df)*100:.1f}%)")


# STEP 2: Prepare Features

print("\n[Step 2] Preparing Features...")

X = df.drop(columns=['student_id', 'actual_placement'])
y = df['actual_placement'] - 1

# Impute missing values
imputer = SimpleImputer(strategy='median')
X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=X.columns, index=X.index)

# Feature Engineering
enjoy_cols = ['enjoy_math', 'enjoy_science', 'enjoy_english', 'enjoy_filipino',
              'enjoy_arpan', 'enjoy_mapeh', 'enjoy_tle']
difficulty_cols = ['difficulty_reading', 'difficulty_writing', 'difficulty_math',
                   'difficulty_focusing', 'difficulty_social_interaction']
award_cols = ['award_highest_honors', 'award_high_honors', 'award_with_honors',
              'award_best_science', 'award_best_math', 'award_best_english',
              'award_conduct', 'achiever_award']
grade_cols = ['grade_math', 'grade_science', 'grade_english', 'grade_filipino',
              'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp']

X_imputed['total_subjects_enjoyed'] = X_imputed[enjoy_cols].sum(axis=1)
X_imputed['total_difficulties'] = X_imputed[difficulty_cols].sum(axis=1)
X_imputed['total_awards'] = X_imputed[award_cols].sum(axis=1)
X_imputed['meets_ste_criteria'] = (X_imputed[grade_cols] >= 90).all(axis=1).astype(int)

print(f"Features prepared: {X_imputed.shape[1]} total")


# STEP 3: Train-Test Split

print("\n[Step 3] Splitting Data...")

X_train, X_test, y_train, y_test = train_test_split(
    X_imputed, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Training: {len(X_train)} | Testing: {len(X_test)}")


# STEP 4: Apply SMOTE

print("\n[Step 4] Balancing Classes with SMOTE...")

smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

print(f"Before SMOTE: {len(X_train)} samples")
print(f"After SMOTE: {len(X_train_balanced)} samples")

# STEP 5: Train XGBoost Model

print("\n[Step 5] Training XGBoost Model...")

model = XGBClassifier(
    n_estimators=200,
    max_depth=8,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='multi:softprob',
    eval_metric='mlogloss',
    random_state=42,
    n_jobs=-1,
    tree_method='hist',
    enable_categorical=False
)

model.fit(X_train_balanced, y_train_balanced)
print("Model trained successfully")

# STEP 6: Evaluate Model

print("\n[Step 6] Evaluating Model...")

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"Accuracy: {accuracy*100:.2f}%")
print(f"F1-Score: {f1:.4f}")

print("\nClassification Report:")
print("-" * 50)
target_names = [PLACEMENT_MAP[i] for i in sorted(PLACEMENT_MAP.keys())]
print(classification_report(y_test, y_pred, target_names=target_names))

# STEP 7: Feature Importance

print("[Step 7] Feature Importance (Top 15)...")
print("-" * 50)

feature_importance = pd.DataFrame({
    'feature': X_imputed.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for _, row in feature_importance.head(15).iterrows():
    print(f"  {row['feature']:30} {row['importance']:.4f}")


# STEP 8: Save Model

print("\n[Step 8] Saving Model...")

os.makedirs(MODEL_DIR, exist_ok=True)

joblib.dump(model, f'{MODEL_DIR}/placement_xgboost_model.pkl')
joblib.dump(imputer, f'{MODEL_DIR}/imputer.pkl')
joblib.dump(list(X_imputed.columns), f'{MODEL_DIR}/feature_names.pkl')
feature_importance.to_csv(f'{MODEL_DIR}/feature_importance.csv', index=False)

print(f"Saved model and components to {MODEL_DIR}/")

# STEP 9: Demonstration

print("\n" + "=" * 60)
print("DEMONSTRATION: Sample Recommendation")


sample_student = X_test.iloc[[0]]
actual = y_test.iloc[0]

probabilities = model.predict_proba(sample_student)[0]
results = [(PLACEMENT_MAP[i+1], prob) for i, prob in enumerate(probabilities)]
results.sort(key=lambda x: x[1], reverse=True)

print("\nRecommendations:")
for rank, (name, prob) in enumerate(results, 1):
    print(f"  {rank}. {name:15} {prob*100:6.2f}%")

print(f"\nPrimary Recommendation: {results[0][0]} ({results[0][1]*100:.2f}%)")
print(f"Actual Placement: {PLACEMENT_MAP[actual+1]}")


# STEP 10: Cross-Validation

print("\n[Step 10] Cross-Validation...")

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_train_balanced, y_train_balanced, cv=cv, scoring='accuracy')

print(f"CV Scores: {cv_scores}")
print(f"Mean CV Accuracy: {cv_scores.mean()*100:.2f}% (+/- {cv_scores.std()*100:.2f}%)")

# Summary


print("TRAINING COMPLETE")
print(f"""
Results:
  - Test Accuracy: {accuracy*100:.2f}%
  - F1-Score: {f1:.4f}
  - CV Accuracy: {cv_scores.mean()*100:.2f}%

Saved Files:
  - {MODEL_DIR}/placement_xgboost_model.pkl
  - {MODEL_DIR}/imputer.pkl
  - {MODEL_DIR}/feature_names.pkl
  - {MODEL_DIR}/feature_importance.csv

Usage:
  model = joblib.load('{MODEL_DIR}/placement_xgboost_model.pkl')
  imputer = joblib.load('{MODEL_DIR}/imputer.pkl')
  predictions = model.predict(new_data)
""")
