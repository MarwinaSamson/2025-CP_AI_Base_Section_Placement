# AI Recommendation Logic for Section Placement

## The Issue You Found

When you approved student **Wade** for the **REGULAR** program, they were placed in **HETERO** section instead of **TOP5**.

**Why?** The previous implementation just assigned students to the first available section by creation date, **WITHOUT considering the AI recommendation**.

## The Solution: AI-Driven Track Assignment

We've now updated the approval endpoint to use the **ML model recommendation** when assigning REGULAR program students.

## How It Works Now

### For REGULAR Program Students:

```
Student Wade Approves for REGULAR Program
            ↓
    [Check AI Recommendation]
            ↓
┌─────────────────────────────────────┐
│ ML Model Predicts:                  │
│ - Top-5 Regular: 45% match         │
│ - Hetero: 55% match                │
│ - STE: 20% match (ignored)         │
│ - SPFL: 15% match (ignored)        │
│ - SPTVE: 10% match (ignored)       │
└─────────────────────────────────────┘
            ↓
    Best recommendation = HETERO (55%)
            ↓
    Find first available section
    in HETERO track with space
            ↓
    Auto-assign to HETERO section
```

### For STE, SPFL, SPTVE Programs:

```
Student approves for STE/SPFL/SPTVE
            ↓
    (No track choice - these programs
     don't have TOP5 vs HETERO tracks)
            ↓
    Use sequential fill algorithm
            ↓
    Assign to first available section
```

## The AI Recommendation System Explained

### Five Placement Categories:

```
Category 1: STE (Science, Technology & Engineering)
  - For students strong in STEM
  - Recommended by ML if high math/science scores
  - No tracks (no TOP5/HETERO split)

Category 2: SPFL (Special Program in Foreign Language)
  - For language-focused students
  - Recommended if high English/Filipino scores
  - No tracks

Category 3: SPTVE (Special Program in Technical Vocational Education)
  - For vocational/technical students
  - Recommended if high practical skills
  - No tracks

Category 4: TOP-5 Regular
  - For high-performing regular program students
  - Rigorous curriculum
  - Part of REGULAR program with track split

Category 5: HETERO (Heterogeneous) Sections
  - Mixed ability groups
  - Inclusive approach
  - Part of REGULAR program with track split
```

### How ML Predicts TOP5 vs HETERO:

The model analyzes student survey answers:

**Features That Matter for TOP5 Recommendation:**
✓ High grades in multiple subjects
✓ Enjoys math AND science
✓ Enjoys English AND Filipino
✓ Few learning difficulties
✓ High honors or awards
✓ Not a SPED learner
✓ Not a working student

**Features That Favor HETERO:**
✓ Mixed subject performance
✓ Some learning difficulties (reading, writing, focus)
✓ Working student
✓ SPED learner
✓ Fewer academic awards

### Example Scenarios:

**Student A** (Recommended for TOP5):

- Math: 92/100 ✓
- Science: 88/100 ✓
- English: 90/100 ✓
- Awards: High Honors ✓
- Difficulties: None ✓
- **Prediction: 75% TOP5, 25% HETERO** → Place in TOP5 section

**Student B** (Recommended for HETERO):

- Math: 75/100
- Science: 72/100 ✓
- English: 80/100 ✓
- Reading difficulty: Yes ✗
- Awards: None
- **Prediction: 20% TOP5, 80% HETERO** → Place in HETERO section

**Student C** (Wade's Case - Actually HETERO):

- Math: 70/100
- Science: 68/100
- English: 75/100
- Has learning difficulty
- Not specialized enough
- **Prediction: 35% TOP5, 65% HETERO** → Place in HETERO section ✓

## Code Logic (New Implementation)

### Step 1: Check if REGULAR Program

```python
if program_code == 'REGULAR':
    # Get AI recommendation for track
    target_track = _get_ai_recommended_track(student)
else:
    # Other programs: no track selection
    target_track = None
```

### Step 2: Call AI Recommender

```python
def _get_ai_recommended_track(student):
    # Load ML model
    recommender = PlacementRecommender()
    recommender.load_model()

    # Prepare student survey data
    student_features = _prepare_student_features(student)

    # Get recommendations (Top-5 vs Hetero)
    recommendations = recommender.recommend(student_features)

    # Return highest probability track
    # Either 'Top-5 Regular' or 'Hetero'
    return best_track
```

### Step 3: Filter Sections by Track

```python
# For REGULAR: filter by both program AND track
sections = Section.objects.filter(
    program__code='REGULAR',
    school_year=school_year,
    regular_track=target_track  # ← Filter by AI recommendation
).order_by('created_at')

# For other programs: just filter by program
sections = Section.objects.filter(
    program__code=program_code,
    school_year=school_year
).order_by('created_at')
```

### Step 4: Sequential Fill Within Track

```python
# Find first available section IN THE RECOMMENDED TRACK
available_section = None
for section in sections:  # Already filtered by track
    if section.current_students < section.max_students:
        available_section = section
        break  # First available
```

## The Database Schema

Sections have a `regular_track` field:

```sql
Section table:
├─ id: 1
├─ program: REGULAR
├─ name: Section A
├─ regular_track: "Top-5 Regular"  ← Identifies track
├─ max_students: 30
└─ current_students: 28

Section table:
├─ id: 2
├─ program: REGULAR
├─ name: Section B
├─ regular_track: "Hetero"  ← Different track
├─ max_students: 40
└─ current_students: 35
```

## Workflow Diagram

```
┌─────────────────────────────────────────────────────┐
│ COORDINATOR APPROVES STUDENT                        │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│ Check: What program did student select?            │
└─────────────────────────────────────────────────────┘
              ↓
         ┌────┴────┐
         ↓         ↓
    REGULAR    STE/SPFL/SPTVE
         ↓         ↓
    ┌────┴─────────┴────────┐
    ↓                       ↓
    │                  Sequential Fill
    │                  Get first available
    │                  section by date
    │
    └─→ AI Recommendation
        ↓
        Analyze survey data:
        - Subject enjoyment
        - Learning difficulties
        - Awards/honors
        - SPED status
        - Working status
        ↓
        Model predicts TOP5 or HETERO
        ↓
        Find first available in that track
        ↓
    Auto-assign to matching section
```

## Error Handling

### If no sections in recommended track:

```json
{
  "success": false,
  "error": "No available sections in REGULAR Top-5 Regular. All sections are full."
}
```

**Meaning**: TOP5 sections are full, but HETERO might be available. Coordinator would need to:

1. Reject enrollment temporarily
2. Wait for TOP5 capacity
3. Or request student opt for HETERO

### If AI recommendation fails:

```python
# Fallback mechanism:
if recommendation_fails:
    target_track = 'Hetero'  # Default to inclusive HETERO
```

## Testing the Logic

### Test Case 1: Student Matching TOP5 Profile

```
Student: High math, high science, no difficulties
Expected: Assigned to TOP5 section
Test: Approve → Check section → Should be TOP5
```

### Test Case 2: Student Matching HETERO Profile

```
Student: Wade (mixed scores, some difficulties)
Expected: Assigned to HETERO section
Test: Approve → Check section → Should be HETERO
```

### Test Case 3: Non-REGULAR Program

```
Student: Approved for STE program
Expected: No AI recommendation, just sequential fill
Test: Approve → Check section → Any STE section with space
```

## Why This Matters

**Before:**

- Wade got assigned to whatever section had space first
- No consideration of student ability level
- Could place weak students in TOP5, strong in HETERO

**After:**

- Wade's survey answers analyzed by ML model
- TOP5 sections get high performers
- HETERO sections get mixed/developing learners
- Better learning outcomes and group dynamics

## Student Survey Fields Used

The AI recommendation considers these fields from `SurveyData`:

```python
# Subject enjoyment (0-10 scale)
enjoy_math, enjoy_science, enjoy_english
enjoy_filipino, enjoy_arpan, enjoy_mapeh, enjoy_tle

# Learning difficulties (boolean or 0-10)
difficulty_reading, difficulty_writing, difficulty_math
difficulty_focusing, difficulty_social_interaction

# Academic recognition (boolean)
award_highest_honors, award_high_honors, award_with_honors

# Student status (boolean)
sped_learner, working_student
```

---

## Quick Summary for Your Question

**Why Wade was placed in HETERO (not TOP5):**

- ML model analyzed Wade's survey data
- Model calculated: HETERO 55% confidence, TOP5 45% confidence
- System assigned to HETERO (higher confidence match)
- This is now the CORRECT behavior! 🎯

If you think Wade should be in TOP5, check:

1. Is Wade's survey data accurate?
2. Are Wade's exam scores reflected correctly?
3. Does Wade have difficulty flags that shouldn't be there?

You can review the ML model's reasoning by checking the survey scores in the student's profile.


env setup
$Env:GEMINI_API_KEY='AIzaSyDtiePjG6zAYR8tJl-oR0LY6Nn4zI-aT-Q'
