# Guide: Integrating a New ML Model (e.g. Random Forest) into the SPARK System

## Overview of the Current Architecture

Before adding anything, understand the flow:

```
Student submits data
       ↓
enrollment_app/services/recommendation_service.py
       ↓  (imports)
TRAINING_ARC/placement_recommender_hybrid.py  ← HybridPlacementRecommender (Ridge + XGBoost)
       ↓  (fallback)
Rule-based logic inside ProgramRecommendationEngine
```

Your new model will slot in at the `TRAINING_ARC` level, and `recommendation_service.py` will be updated to call it.

---

## Step 1 — Prepare Your Training Script

Your codebase already has a working example: `TRAINING_ARC/RF/RF_training.py`. Use it as a reference.

Your training script must produce the same **input features** the hybrid model uses,
because downstream code expects that exact shape. The features are defined in
`TRAINING_ARC/placement_recommender_hybrid.py`:

- `G6_ACADEMIC` — 9 grade columns (`grade_math`, `grade_science`, `grade_english`,
  `grade_filipino`, `grade_arpan`, `grade_mapeh`, `average_grade_tle`, `grade_esp`,
  `grade_6_final_average`)
- `NON_ACADEMIC` — survey columns (`age`, `gender`, `learning_style`,
  `study_hours_daily`, `support_person`, `assignment_completion`, etc.)

> **Do not change or rename these feature columns.**
> Your new model must be trained on the same feature set so the service layer
> does not need to be rewritten.

---

## Step 2 — Train and Save the Model

At the end of your training script, save every artifact your recommender will need
at runtime using `joblib`:

```python
import joblib, os

SAVE_DIR = 'TRAINING_ARC/models/rf'   # create a dedicated folder per model type
os.makedirs(SAVE_DIR, exist_ok=True)

# Stage 1 — one regressor per program (mirrors how Ridge does it)
for prog_id, regressor in stage1_regressors.items():
    joblib.dump(regressor, f'{SAVE_DIR}/rf_regressor_{prog_id}.pkl')

# Stage 2 — one classifier for final ranking
joblib.dump(classifier,    f'{SAVE_DIR}/rf_classifier.pkl')

# Preprocessing artifacts — MUST save these too
joblib.dump(imputer,        f'{SAVE_DIR}/imputer.pkl')
joblib.dump(scaler,         f'{SAVE_DIR}/scaler.pkl')           # if used
joblib.dump(label_encoder,  f'{SAVE_DIR}/label_encoder.pkl')    # if used
joblib.dump(feature_cols,   f'{SAVE_DIR}/feature_columns.pkl')  # list of column names
```

> Save **every** object that was fit on training data.
> If you forget the imputer or scaler and try to fit them again at inference time,
> your predictions will be wrong.

---

## Step 3 — Create a New Recommender Class

Create a new file: `TRAINING_ARC/placement_recommender_rf.py`

Model it directly after `TRAINING_ARC/placement_recommender_hybrid.py`.
The class must expose exactly **these two public methods** so the service layer
does not need to change:

```python
class RFPlacementRecommender:

    def __init__(self, model_path='TRAINING_ARC/models/rf'):
        self.model_path   = model_path
        self.regressors   = {}     # Stage 1: one RF per program
        self.classifier   = None   # Stage 2: ranking classifier
        self.imputer      = None
        self.scaler       = None
        self.feature_cols = []
        self.is_loaded    = False

    def load_models(self) -> bool:
        """
        Load all saved artifacts.
        Return True on success, False on any failure.
        The caller (recommendation_service.py) checks this return value
        before calling recommend().
        """
        try:
            # load regressors, classifier, imputer, scaler, feature_cols ...
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"[RF] Failed to load models: {e}")
            return False

    def recommend(self, student_data: dict, top_n: int = 5) -> list:
        """
        Accept the same student_data dict shape the hybrid model receives.
        Return a list of dicts, each with at minimum:
            { 'placement': str, 'probability': float, 'rank': int }
        """
        ...
```

The `student_data` dict shape is already defined by who calls
`recommender.recommend()` in `enrollment_app/services/recommendation_service.py`.
Match that shape exactly — this is what all views and templates depend on.

---

## Step 4 — Register the New Model in `recommendation_service.py`

Open `enrollment_app/services/recommendation_service.py`.
At the top you will see the existing import block:

```python
try:
    from TRAINING_ARC.placement_recommender_hybrid import HybridPlacementRecommender
    _ML_AVAILABLE = True
except Exception:
    HybridPlacementRecommender = None
    _ML_AVAILABLE = False
```

**Option A — Replace the hybrid entirely with RF:**
Simply change the import to point at your new class.

**Option B — Add RF as an alternative and choose at runtime (recommended):**

```python
try:
    from TRAINING_ARC.placement_recommender_hybrid import HybridPlacementRecommender
    _HYBRID_AVAILABLE = True
except Exception:
    HybridPlacementRecommender = None
    _HYBRID_AVAILABLE = False

try:
    from TRAINING_ARC.placement_recommender_rf import RFPlacementRecommender
    _RF_AVAILABLE = True
except Exception:
    RFPlacementRecommender = None
    _RF_AVAILABLE = False

# Which model to use — driven by an environment variable so you can switch
# without redeploying code.
import os
_ACTIVE_MODEL = os.getenv('PLACEMENT_MODEL', 'hybrid')  # 'hybrid' | 'rf'
```

---

## Step 5 — Update the Instantiation Logic in the Service

Find where `HybridPlacementRecommender` is instantiated and wrap it in a factory:

```python
def _get_recommender():
    """
    Factory: returns the best available recommender, or None to trigger
    the rule-based fallback already present in ProgramRecommendationEngine.
    """
    if _ACTIVE_MODEL == 'rf' and _RF_AVAILABLE:
        rec = RFPlacementRecommender(model_path='TRAINING_ARC/models/rf')
        if rec.load_models():
            return rec

    if _HYBRID_AVAILABLE:
        rec = HybridPlacementRecommender(model_path='TRAINING_ARC/models/hybrid')
        if rec.load_models():
            return rec

    return None   # triggers rule-based fallback
```

The rest of the service code calls `recommender.recommend(student_data)` — that
contract does not change.

---

## Step 6 — Preserve the Rule-Based Fallback

Your system already has a rule-based fallback in `ProgramRecommendationEngine`.
Make sure your new load path **returns `None`** (not raises an exception) when
models are missing, so the existing fallback path is still reached cleanly.
Never let a missing `.pkl` file crash the enrollment flow for a real student.

---

## Step 7 — Add Any New Dependency to `requirements.txt`

Check `requirements.txt`. If your new model requires a package that is not
already listed, add it:

```
scikit-learn>=1.3.0   # already present for Ridge; RandomForest is in scikit-learn too
```

RF is part of `scikit-learn` so no extra package is needed for RF specifically.
For other algorithms, add explicitly:

| Algorithm   | Package to add          |
| ----------- | ----------------------- |
| LightGBM    | `lightgbm`              |
| CatBoost    | `catboost`              |
| Extra Trees | already in scikit-learn |
| SVM         | already in scikit-learn |
| Neural Net  | `torch` or `tensorflow` |

---

## Step 8 — Test Offline Before Wiring Into Django

Create a standalone test script (no Django needed):

```python
# quick_test_rf.py
# Run with:  python quick_test_rf.py

from TRAINING_ARC.placement_recommender_rf import RFPlacementRecommender

rec = RFPlacementRecommender()
assert rec.load_models(), "Models failed to load — check your .pkl paths!"

dummy_student = {
    'grade_math':             90,
    'grade_science':          88,
    'grade_english':          87,
    'grade_filipino':         86,
    'grade_arpan':            85,
    'grade_mapeh':            88,
    'average_grade_tle':      87,
    'grade_esp':              89,
    'grade_6_final_average':  87.75,
    'age':                    12,
    'gender':                 1,
    # ... fill in all required survey fields
}

results = rec.recommend(dummy_student, top_n=3)
for r in results:
    print(r)
```

Only proceed to Step 9 once this prints results cleanly and without errors.

---

## Step 9 — Validate Inside Django

Run `python manage.py shell` and call the service layer directly:

```python
from enrollment_app.services.recommendation_service import ProgramRecommendationEngine

# Build sample dicts matching the real structure
academic_data  = { 'grade_math': 90, 'grade_science': 88, ... }
survey_data    = { 'enjoy_science': 1, 'motivation_level': 3, ... }
student_data   = { 'lrn': 'TEST123', 'gender': 'M', 'age': 12 }

engine = ProgramRecommendationEngine('TEST123', academic_data, survey_data, student_data)
recs   = engine.generate_recommendations()
print(recs)
```

Verify:

- The result list has the same keys the templates and views already expect.
- The fallback still works if you rename/delete the model `.pkl` files temporarily.

---

## Step 10 — Environment Variable Toggle for Production

In your Railway Variables tab (or local `.env` file), set:

```
PLACEMENT_MODEL=rf
```

This lets you switch models without redeploying code — just change the variable
and restart the server (or redeploy on Railway). To revert, set it back to:

```
PLACEMENT_MODEL=hybrid
```

---

## Summary Checklist

| #   | Step                                                              | File / Location                                     |
| --- | ----------------------------------------------------------------- | --------------------------------------------------- |
| 1   | Verify feature columns match the hybrid model exactly             | `TRAINING_ARC/placement_recommender_hybrid.py`      |
| 2   | Train model and save all artifacts as `.pkl`                      | `TRAINING_ARC/models/rf/`                           |
| 3   | Create new recommender class with `load_models()` + `recommend()` | `TRAINING_ARC/placement_recommender_rf.py`          |
| 4   | Import new class safely with `try/except`                         | `enrollment_app/services/recommendation_service.py` |
| 5   | Add factory function `_get_recommender()` to pick active model    | `enrollment_app/services/recommendation_service.py` |
| 6   | Ensure rule-based fallback is still reachable                     | `enrollment_app/services/recommendation_service.py` |
| 7   | Add any new pip dependency                                        | `requirements.txt`                                  |
| 8   | Test the class standalone (no Django)                             | `quick_test_rf.py`                                  |
| 9   | Test through Django shell                                         | `python manage.py shell`                            |
| 10  | Set env variable to activate new model                            | Railway Variables / `.env`                          |

---

## Critical Rules to Remember

1. **Same feature columns** — your new model must accept the exact same input keys
   as `HybridPlacementRecommender`. If you add or rename a column, you must
   update the service layer too.

2. **Same output shape** — `recommend()` must return a list of dicts with at least
   `placement`, `probability`, and `rank`. Every template and view depends on
   these keys.

3. **Never raise in `load_models()`** — always catch exceptions and return `False`.
   A missing model file must silently fall back to rule-based logic, not crash
   an active enrollment session.

4. **Save preprocessing objects** — imputer, scaler, encoder. If they are not
   loaded from the same `.pkl` that was used during training, inference will
   silently produce incorrect predictions.

5. **Test offline first** — validate with `quick_test_rf.py` before touching the
   running Django server.
