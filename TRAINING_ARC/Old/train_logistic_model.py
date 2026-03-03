
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, confusion_matrix
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import warnings
warnings.filterwarnings('ignore')


print(" STUDENT PLACEMENT RECOMMENDATION SYSTEM - Logistic Regression")



print("\n Step 1: Loading Data...")

CSV_PATH = 'dataset/TRAINING_Student_Placement_Data.csv'

if not os.path.exists(CSV_PATH):
    print(f"    File not found: {CSV_PATH}")
    print("   Please place your CSV file in the 'dataset' folder.")
    exit()

df = pd.read_csv(CSV_PATH)
print(f"    Loaded {len(df)} students, {len(df.columns)} columns")

# Placement mapping
PLACEMENT_MAP = {
    1: 'STE',
    2: 'SPFL',
    3: 'SPTVE',
    4: 'Top-5 Regular',
    5: 'Hetero'
}

print(f"\n    Class Distribution:")
for code, name in PLACEMENT_MAP.items():
    count = len(df[df['actual_placement'] == code])
    pct = (count / len(df)) * 100
    print(f"      {code} ({name}): {count} students ({pct:.1f}%)")


print("\n  Step 2: Preparing Features...")

X = df.drop(columns=['student_id', 'actual_placement'])
y = df['actual_placement']

# Impute missing values
imputer = SimpleImputer(strategy='median')
X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=X.columns, index=X.index)

# Feature Engineering
enjoy_cols = ['enjoy_math', 'enjoy_science', 'enjoy_english', 'enjoy_filipino', 
              'enjoy_arpan', 'enjoy_mapeh', 'enjoy_tle']
X_imputed['total_subjects_enjoyed'] = X_imputed[enjoy_cols].sum(axis=1)

difficulty_cols = ['difficulty_reading', 'difficulty_writing', 'difficulty_math', 
                   'difficulty_focusing', 'difficulty_social_interaction']
X_imputed['total_difficulties'] = X_imputed[difficulty_cols].sum(axis=1)

award_cols = ['award_highest_honors', 'award_high_honors', 'award_with_honors',
              'award_best_science', 'award_best_math', 'award_best_english',
              'award_conduct', 'achiever_award']
X_imputed['total_awards'] = X_imputed[award_cols].sum(axis=1)

grade_cols = ['grade_math', 'grade_science', 'grade_english', 'grade_filipino',
              'grade_arpan', 'grade_mapeh', 'average_grade_tle', 'grade_esp']
X_imputed['meets_ste_criteria'] = (X_imputed[grade_cols] >= 90).all(axis=1).astype(int)

print(f"    Features prepared: {X_imputed.shape[1]} total")


print("\n  Step 3: Splitting Data...")

X_train, X_test, y_train, y_test = train_test_split(
    X_imputed, y, test_size=0.2, random_state=42, stratify=y
)
print(f"    Training: {len(X_train)} | Testing: {len(X_test)}")


print("\n  Step 4: Balancing Classes with SMOTE...")

smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

print(f"   Before: {dict(y_train.value_counts().sort_index())}")
print(f"   After:  {dict(pd.Series(y_train_balanced).value_counts().sort_index())}")


print("\n Step 5: Standardizing Features...")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_balanced)
X_test_scaled = scaler.transform(X_test)

print("    Features standardized (mean=0, std=1)")

print("\n Step 6: Training Logistic Regression Model...")

# Logistic Regression parameters for multi-class classification
model = LogisticRegression(
    
    solver='lbfgs',             # Good solver for multinomial
    max_iter=1000,              # Enough iterations for convergence
    C=1.0,                      # Regularization strength (inverse)
    random_state=42,
    n_jobs=-1,                  # Use all CPU cores
    verbose=0
)

model.fit(X_train_scaled, y_train_balanced)
print("    Logistic Regression model trained!")

print("\n Step 7: Evaluating Model...")

y_pred = model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

print(f"    Accuracy: {accuracy*100:.2f}%")
print(f"    F1-Score: {f1:.4f}")

# Detailed classification report
print("\n   Classification Report:")
print("   " + "-" * 50)
report = classification_report(y_test, y_pred, target_names=[PLACEMENT_MAP[i] for i in sorted(PLACEMENT_MAP.keys())])
for line in report.split('\n'):
    if line.strip():
        print(f"   {line}")


print("\n Step 8: Analyzing Model Coefficients...")

# Get coefficients for each class
coefficients_df = pd.DataFrame(
    model.coef_,
    columns=X_imputed.columns,
    index=[PLACEMENT_MAP[i] for i in model.classes_]
)

print("\n   Top 10 Features for Each Placement:")
print("   " + "-" * 60)

for placement in coefficients_df.index:
    coef_series = coefficients_df.loc[placement].abs().sort_values(ascending=False)
    print(f"\n    {placement}:")
    for feature, value in coef_series.head(10).items():
        original_coef = coefficients_df.loc[placement, feature]
        direction = "↑" if original_coef > 0 else "↓"
        print(f"      {direction} {feature:30} {abs(original_coef):6.4f}")


print("\n Step 9: Saving Logistic Regression Model...")

os.makedirs('models/logistic', exist_ok=True)

joblib.dump(model, 'models/logistic/placement_logistic_model.pkl')
joblib.dump(scaler, 'models/logistic/scaler.pkl')
joblib.dump(imputer, 'models/logistic/imputer.pkl')
joblib.dump(list(X_imputed.columns), 'models/logistic/feature_names.pkl')
coefficients_df.to_csv('models/logistic/coefficients.csv')

print("    Saved: models/logistic/placement_logistic_model.pkl")
print("    Saved: models/logistic/scaler.pkl")
print("    Saved: models/logistic/imputer.pkl")
print("    Saved: models/logistic/feature_names.pkl")
print("    Saved: models/logistic/coefficients.csv")



print(" DEMONSTRATION: Logistic Regression Recommendation Output")


# Test with a sample student
sample_idx = X_test.index[0]
sample_student_scaled = X_test_scaled[[0]]
actual_placement = y_test.iloc[0]

# Get predictions
probabilities = model.predict_proba(sample_student_scaled)[0]
classes = model.classes_

# Create results
results = []
for i, prob in enumerate(probabilities):
    class_label = classes[i]
    placement_name = PLACEMENT_MAP.get(class_label, f"Class {class_label}")
    results.append((placement_name, prob, class_label))

# Sort by probability
results.sort(key=lambda x: x[1], reverse=True)

print("\n   RECOMMENDED PLACEMENTS:")
print("  " + "─" * 60)

for rank, (name, prob, class_label) in enumerate(results, 1):
    bar_length = int(prob * 30)
    bar = "█" * bar_length
    
    label = ""
    if rank == 1:
        label = "   Best Fit"
    elif rank == 2:
        label = "  2nd Choice"
    elif rank == 3:
        label = "  3rd Choice"
    
    print(f"     {rank}. {name:15} {prob*100:6.2f}%  {bar} {label}")

print("  " + "─" * 60)
print(f"\n    PRIMARY RECOMMENDATION: {results[0][0]}")
print(f"      Match Score: {results[0][1]*100:.2f}%")
print(f"\n    Actual Placement: {PLACEMENT_MAP[actual_placement]}")
if results[0][2] == actual_placement:
    print("   CORRECT! Model matches actual placement")
else:
    print("    Different from actual placement")


print(" Step 11: Cross-Validation...")


cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(model, X_train_scaled, y_train_balanced, cv=cv, scoring='accuracy')

print(f"\n   Cross-Validation Scores: {cv_scores}")
print(f"   Mean CV Accuracy: {cv_scores.mean()*100:.2f}%")
print(f"   Std CV Accuracy: {cv_scores.std()*100:.2f}%")



print(" LOGISTIC REGRESSION TRAINING COMPLETE - SUMMARY")


print(f"""
    Dataset: {len(df)} students

    Model Performance:
     - Test Accuracy: {accuracy*100:.2f}%
     - F1-Score: {f1:.4f}
     - CV Mean Accuracy: {cv_scores.mean()*100:.2f}%
   
""")

print(" READY FOR DEPLOYMENT!")

