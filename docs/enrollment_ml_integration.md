# Enrollment Flow with ML Recommendations

## Overview

- This document describes how enrollment captures data, verifies grades/name, and generates program recommendations using the ML model in TRAINING_ARC.
- Runtime flow combines backend verification plus ML inference and displays ranked programs in the UI, with a fallback to the legacy rule engine if ML is unavailable.

## Data Collection Steps

1. Student Data / LRN verification: persisted in session under `enrollment_student_data` and `enrollment_lrn_verified`.
2. Family Data: stored in `enrollment_family_data`.
3. Survey Data: stored in `enrollment_survey_data` (interests, activities, tech access, etc.).
4. Academic Data: entered/ocr-validated in `academic_data`, including grades, DOST result, OCR outputs, and report-card files.

## OCR and Name Verification

- Triggered when posting the academic form (`/academic/`).
- Uses [enrollment_app/services/ocr_service.py](../enrollment_app/services/ocr_service.py) and Google Gemini OCR.
- Blocks recommendation if:
  - Name verification missing/failed.
  - OCR verification missing/failed.
  - Grade mismatches detected.
- Known issue: Gemini `429 RESOURCE_EXHAUSTED` returns “OCR Error: Gemini OCR Error: 429…”. Retrying later is required; add exponential backoff or local OCR fallback if desired.

## Recommendation Generation (Backend)

- Endpoint: `verify_grades_ajax` in [enrollment_app/views/studentacademic_view.py](../enrollment_app/views/studentacademic_view.py).
- Primary path (ML): `generate_academic_recommendations` in [enrollment_app/services/recommendation_service.py](../enrollment_app/services/recommendation_service.py)
  - Loads model artifacts from `TRAINING_ARC/models` (placement_recommendation_model.pkl, imputer.pkl, feature_names.pkl).
  - Maps session data to model features via `_map_session_to_ml_features`.
  - Produces ranked placements: STE, SPFL, SPTVE, REGULAR (with tracks TOP5/HETERO).
  - Formats to frontend-friendly payload with `program_code`, `regular_track`, `percentage_match`, `recommendation_level`.
- Fallback path (rule-based): same function calls `ProgramRecommendationEngine` when ML load/inference fails.
- STE special check: `Qualified_for_ste` guard still applied in the view when displaying/confirming selections.

## Frontend Rendering

- File: [enrollment_app/static/enrollment_app/js/sectionPlacement.js](../enrollment_app/static/enrollment_app/js/sectionPlacement.js)
- Flow after successful verification:
  - `renderProgramRecommendations(data)` now prefers server `data.recommendations` (ML/rule) to build cards.
  - REGULAR variants keep `regular_track` (TOP5/HETERO) for display and submission.
  - If server data is absent, client-side rule fallback runs.
- Confirm Selection:
  - Posts to `/confirm-program/` with `program_code` and optional `regular_track` (TOP5/HETERO preserved).

## Key Session Keys

- `enrollment_student_data`, `enrollment_family_data`, `enrollment_survey_data`, `academic_data` (includes OCR results), `enrollment_recommendations` (server payload), `program_selection` (after confirm).

## Runtime Dependencies

- Python libs: pandas, numpy, scikit-learn, joblib (runtime inference). imblearn/xgboost only needed for retraining.
- Model artifacts: `TRAINING_ARC/models/*`.
- OCR: Google Gemini OCR credentials and quota.

## Try It / Test Quickly

```powershell
# Run server
python manage.py runserver

# Sanity-check model load (from repo root)
python - << 'PY'
from TRAINING_ARC.placement_recommender import PlacementRecommender
from pathlib import Path
r = PlacementRecommender(model_path=str(Path('TRAINING_ARC')/'models'))
print('Loaded:', r.load_model())
PY
```

## Troubleshooting

- OCR 429 RESOURCE_EXHAUSTED: quota/rate limit; retry later or switch to alternative OCR provider; add backoff in OCR service if needed.
- No recommendations shown: ensure academic form POST succeeded and `verify_grades_ajax` returned `success: true`; check browser console for fetch errors.
- REGULAR track missing: confirm server payload includes `regular_track`; frontend now honors it when rendering and confirming.
- ML fallback triggered: message becomes “Program recommendations generated successfully.” instead of “ML-based…”. Check model files and Python deps.
