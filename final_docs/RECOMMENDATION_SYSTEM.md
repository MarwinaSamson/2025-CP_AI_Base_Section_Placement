# Program Recommendation System Documentation

## Overview

The Program Recommendation System is an AI-powered engine that suggests appropriate academic programs to incoming Grade 7 students based on their academic performance, survey responses, and special conditions. The system uses a **hybrid approach**: ML-based recommendations when available, with automatic fallback to rule-based logic.

**File Location:** `enrollment_app/services/recommendation_service.py`

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Available Programs](#available-programs)
3. [Recommendation Flow](#recommendation-flow)
4. [ML-Based Recommendations](#ml-based-recommendations)
5. [Rule-Based Fallback](#rule-based-fallback)
6. [Filtering Rules](#filtering-rules)
7. [Special Program Inclusion](#special-program-inclusion)
8. [Data Requirements](#data-requirements)
9. [Configuration](#configuration)
10. [Pros and Cons](#pros-and-cons)
11. [Examples](#examples)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Student Enrollment Data                       │
│  (Academic Data, Survey Data, Student Data)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                generate_academic_recommendations()               │
│                     Main Entry Point                             │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────┐         ┌──────────────────────┐
│   ML Recommender     │         │   Rule-Based Engine  │
│   (Primary)          │         │   (Fallback)         │
│                      │         │                      │
│ PlacementRecommender │         │ ProgramRecommendation│
│ from TRAINING_ARC    │         │ Engine               │
└──────────────────────┘         └──────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              _filter_by_highest_program_rule()                   │
│                  Program Visibility Filtering                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              _apply_special_program_inclusion()                  │
│              (OHSP for Working Students, SNED L for PWD)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Final Recommendations                         │
│                    (Displayed to Student)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Available Programs

| Program Code | Full Name | Target Students |
|--------------|-----------|-----------------|
| **STE** | Science, Technology, Engineering | High achievers (avg ≥90, DOST passed) |
| **SPFL** | Special Program in Foreign Language | High achievers interested in languages |
| **SPTVE** | Special Program in Technical Vocational Education | High achievers interested in technology/vocational |
| **REGULAR - TOP5** | Regular Program (Top 5 Section) | Above-average students within regular program |
| **REGULAR - HETERO** | Regular Program (Heterogeneous) | Average students, default track |
| **OHSP** | Open High School Program | Working students |
| **SNED L** | Special Needs Education Program | Students with disabilities (PWD/SPED) |

---

## Recommendation Flow

### Step 1: Data Collection
```
Input Sources:
├── academic_data    → Grades, overall average, DOST exam result
├── survey_data      → Interests, learning style, enjoyed subjects
└── student_data     → LRN, is_sped, is_working_student, gender, age
```

### Step 2: ML or Rule-Based Processing
```python
# Priority: ML first, Rule-based as fallback
if ML_AVAILABLE and model.load_model():
    recommendations = ML_Recommender.recommend(features)
else:
    recommendations = RuleBasedEngine.generate()
```

### Step 3: Filtering
```
Apply filters in order:
1. _filter_by_highest_program_rule()  → Hide programs based on probability
2. _apply_special_program_inclusion() → Add OHSP/SNED L if applicable
```

### Step 4: Output
```
Return sorted list of recommendations with:
- program_code
- program_name
- percentage_match (probability × 100)
- recommendation_level
- rank
```

---

## ML-Based Recommendations

### Model Details
- **Location:** `TRAINING_ARC/models/`
- **Class:** `PlacementRecommender`
- **Output:** Probability distribution across 5 placements

### ML Placements Mapping
| ML Output | System Code | Regular Track |
|-----------|-------------|---------------|
| STE | STE | - |
| SPFL | SPFL | - |
| SPTVE | SPTVE | - |
| Top-5 Regular | REGULAR | TOP5 |
| Hetero | REGULAR | HETERO |

### Feature Mapping
The system maps student data to 50+ ML features including:

**Academic Features:**
- `grade_math`, `grade_science`, `grade_english`, `grade_filipino`
- `grade_arpan`, `grade_mapeh`, `average_grade_tle`, `grade_esp`
- `grade_6_final_average`

**Survey Features:**
- `enjoy_math`, `enjoy_science`, `enjoy_english` (binary)
- `learning_style` (1-5 categorical)
- `study_hours_daily` (1-4 categorical)
- `preferred_program` (1-5 categorical)

**Behavioral Features:**
- `assignment_completion`, `handle_difficulty`
- `difficulty_reading`, `difficulty_math`, `difficulty_focusing`
- `school_participation`, `received_awards`

### Probability to Recommendation Level
| Probability | Level |
|-------------|-------|
| ≥ 90% | Strong (High ML match) |
| ≥ 70% | Good (ML match) |
| ≥ 50% | Fair (ML match) |
| < 50% | Weak (ML match) |

---

## Rule-Based Fallback

Used when ML model is unavailable or fails to load.

### Academic Rules

| Program | Academic Criteria |
|---------|-------------------|
| **STE** | Average ≥ 90 AND all subjects ≥ 85 AND DOST = "passed" |
| **SPFL** | Average ≥ 90 AND all subjects ≥ 85 AND DOST ≠ "passed" |
| **SPTVE** | Average ≥ 90 AND all subjects ≥ 85 AND DOST ≠ "passed" |
| **REGULAR** | Average ≤ 89 |
| **SNED L** | is_sped = True |
| **OHSP** | is_working_student = True |

### Non-Academic Rules (Survey-Based)

| Program | Survey Criteria |
|---------|-----------------|
| **STE** | Interested in: science, math, English + Active + Studious + Smart |
| **SPFL** | Interested in: English, foreign language, arts, tourism + Active + Studious |
| **SPTVE** | Interested in: English, technology, arts, crafts + Creative + Studious + Smart + Artistic |
| **REGULAR** | Not studious + Not smart + Not active (2 of 3) |

### Score Calculation
```
overall_score = (academic_score + non_academic_score) / 2
percentage_match = round(overall_score)
```

---

## Filtering Rules

### Rule 1: Highest Program Filter

**Purpose:** Prevent students from choosing programs they're not qualified for.

**Logic:**
```
IF highest_probability_program ∈ {Top-5 Regular, Hetero}:
    HIDE all specialized programs (STE, SPFL, SPTVE)

IF highest_probability_program ∈ {STE, SPFL, SPTVE}:
    SHOW all programs
```

**Examples:**

| Highest Program | Visible Programs |
|-----------------|------------------|
| Hetero (45%) | REGULAR only |
| Top-5 Regular (40%) | REGULAR only |
| SPFL (35%) | ALL programs |
| STE (50%) | ALL programs |

### Rule 2: Top-5 Threshold Filter

**Purpose:** Hide Top-5 Regular option for students who clearly don't qualify.

**Logic:**
```
IF Top-5 Regular probability < 15%:
    HIDE Top-5 Regular

Hetero is ALWAYS shown (never hidden)
```

**Threshold:** `TOP5_MIN_THRESHOLD = 0.15` (15%)

**Examples:**

| Top-5 Prob | Hetero Prob | Top-5 Visible? |
|------------|-------------|----------------|
| 1% | 99% | NO (hidden) |
| 14% | 70% | NO (hidden) |
| 15% | 60% | YES |
| 40% | 35% | YES |

### Rule 3: Exempt Programs

**OHSP and SNED L are NEVER filtered out by probability rules.**

These programs follow their own inclusion rules based on student status, not ML probability.

---

## Special Program Inclusion

### OHSP (Working Students)

**Trigger:** `student_data['is_working_student'] = True`

**Behavior:**
- Automatically added to recommendations if not already present
- Rank: Inserted at position 1 (top)
- Percentage match: 100%
- Level: "Strong (Working Student - Auto-included)"

### SNED L (PWD/SPED Students)

**Trigger:** `student_data['is_sped'] = True`

**Behavior:**
- Automatically added to recommendations if not already present
- Rank: Inserted at position 1 (top)
- Percentage match: 100%
- Level: "Strong (PWD/SPED - Auto-included)"

### Combined Scenario
If student is BOTH working AND PWD:
- Both OHSP and SNED L are auto-included
- Both appear at top of recommendations

---

## Data Requirements

### Minimum Required Data

| Data Source | Required Fields |
|-------------|-----------------|
| **student_data** | `lrn`, `is_sped`, `is_working_student` |
| **academic_data** | `overall_average`, at least 4 subject grades |
| **survey_data** | `enjoyed_subjects`, `learning_style` |

### Optional but Recommended

| Data Source | Optional Fields |
|-------------|-----------------|
| **academic_data** | `dost_exam_result`, all 8 subject grades |
| **survey_data** | `study_hours`, `schoolwork_support`, `difficulty_areas` |
| **student_data** | `gender`, `date_of_birth` |

### Data Validation
- Missing grades default to `None` (skipped in calculations)
- Missing survey fields default to `0` or empty list
- Missing boolean flags default to `False`

---

## Configuration

### Thresholds (Configurable)

| Constant | Value | Location | Description |
|----------|-------|----------|-------------|
| `TOP5_MIN_THRESHOLD` | 0.15 | `_filter_by_highest_program_rule()` | Minimum probability to show Top-5 |

### Program Categories (Constants)

```python
REGULAR_TRACKS = {'Top-5 Regular', 'Hetero'}
SPECIALIZED_PROGRAMS = {'STE', 'SPFL', 'SPTVE'}
EXEMPT_PROGRAMS = {'OHSP', 'SNED L'}
```

### ML Model Path

```python
model_path = settings.BASE_DIR / 'TRAINING_ARC' / 'models'
```

---

## Pros and Cons

### ML-Based Approach

| Pros | Cons |
|------|------|
| Data-driven predictions | Requires trained model |
| Considers complex patterns | Black-box (less interpretable) |
| Adapts to new data patterns | May need retraining periodically |
| Probability-based ranking | Dependent on training data quality |

### Rule-Based Approach

| Pros | Cons |
|------|------|
| Transparent and explainable | Rigid, doesn't adapt |
| Easy to modify rules | May miss complex patterns |
| No model dependency | Binary decisions (qualify/don't) |
| Predictable behavior | Requires manual rule updates |

### Filtering Rules

| Pros | Cons |
|------|------|
| Prevents unqualified selections | May limit student choice |
| Cleaner UI (fewer options) | Students don't see all options |
| Guides students appropriately | Threshold tuning needed |
| Reduces enrollment errors | Could be perceived as restrictive |

### Special Inclusion Rules

| Pros | Cons |
|------|------|
| Ensures PWD/working students see relevant programs | Always at top may seem pushy |
| Automatic, no manual intervention | Students may ignore other options |
| 100% match clearly indicates relevance | Could overshadow better fits |

---

## Examples

### Example 1: High Achiever (STE Candidate)

**Input:**
```python
academic_data = {
    'overall_average': 95,
    'mathematics': 96,
    'science': 94,
    'english': 93,
    'dost_exam_result': 'passed'
}
student_data = {'is_sped': False, 'is_working_student': False}
```

**ML Output:**
```
STE: 65%
SPFL: 20%
SPTVE: 10%
Top-5 Regular: 4%
Hetero: 1%
```

**After Filtering:** ALL programs shown (STE is highest)

**Final Recommendations:**
1. STE (65% - Strong)
2. SPFL (20% - Weak)
3. SPTVE (10% - Weak)
4. Regular - Top 5 (4% - Weak)
5. Regular - Hetero (1% - Weak)

---

### Example 2: Average Student

**Input:**
```python
academic_data = {
    'overall_average': 82,
    'mathematics': 80,
    'science': 78,
    'english': 85
}
student_data = {'is_sped': False, 'is_working_student': False}
```

**ML Output:**
```
Hetero: 75%
Top-5 Regular: 12%
SPFL: 8%
STE: 3%
SPTVE: 2%
```

**After Filtering:**
- Hetero is highest (REGULAR) → Hide STE, SPFL, SPTVE
- Top-5 = 12% < 15% threshold → Hide Top-5

**Final Recommendations:**
1. Regular - Hetero (75% - Good)

---

### Example 3: Working Student

**Input:**
```python
academic_data = {'overall_average': 85}
student_data = {'is_sped': False, 'is_working_student': True}
```

**ML Output:**
```
Hetero: 60%
Top-5 Regular: 25%
SPFL: 10%
STE: 3%
SPTVE: 2%
```

**After Filtering:**
- Hetero is highest → Hide STE, SPFL, SPTVE
- Top-5 = 25% ≥ 15% → Show Top-5

**After Special Inclusion:**
- OHSP auto-included (working student)

**Final Recommendations:**
1. OHSP (100% - Strong, Auto-included)
2. Regular - Hetero (60% - Fair)
3. Regular - Top 5 (25% - Weak)

---

### Example 4: PWD Student with High Grades

**Input:**
```python
academic_data = {
    'overall_average': 92,
    'dost_exam_result': 'passed'
}
student_data = {'is_sped': True, 'is_working_student': False}
```

**ML Output:**
```
STE: 55%
SPFL: 25%
Top-5 Regular: 15%
Hetero: 4%
SPTVE: 1%
```

**After Filtering:** ALL programs shown (STE is highest)

**After Special Inclusion:**
- SNED L auto-included (PWD)

**Final Recommendations:**
1. SNED L (100% - Strong, Auto-included)
2. STE (55% - Fair)
3. SPFL (25% - Weak)
4. Regular - Top 5 (15% - Weak)
5. Regular - Hetero (4% - Weak)
6. SPTVE (1% - Weak)

---

## Maintenance Notes

### Adding New Programs
1. Add to `PROGRAMS` dict in `ProgramRecommendationEngine`
2. Add mapping in `code_map` in `_format_ml_recommendations()`
3. Update filtering rules if needed
4. Retrain ML model with new label

### Adjusting Thresholds
1. Modify `TOP5_MIN_THRESHOLD` in `_filter_by_highest_program_rule()`
2. Test with sample data to verify behavior
3. Consider user feedback for fine-tuning

### Debugging
- Enable prints in `generate_academic_recommendations()` for ML failures
- Check `_ML_AVAILABLE` flag for model loading status
- Verify feature mapping in `_map_session_to_ml_features()`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Initial | Rule-based recommendations |
| 2.0 | - | Added ML-based recommendations |
| 2.1 | - | Added program visibility filtering |
| 2.2 | - | Added Top-5 threshold filtering (15%) |
| 2.3 | - | Added special program auto-inclusion |

---

## Related Files

- `TRAINING_ARC/placement_recommender.py` - ML model class
- `TRAINING_ARC/models/` - Trained model files
- `enrollment_app/signals.py` - Uses recommendations for auto-assignment
- `enrollment_app/views/studentacademic_view.py` - Displays recommendations to students
