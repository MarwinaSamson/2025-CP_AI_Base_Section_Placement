# Program Recommendation System - Backend Implementation

## Overview

Fixed and implemented the complete program recommendation backend following the detailed business rules provided. The system now properly evaluates students and recommends programs based on both academic and non-academic criteria.

## Files Modified/Created

### 1. New File: `enrollment_app/services/recommendation_service.py`

**Purpose**: Core recommendation engine that evaluates students against all program criteria

**Key Components**:

#### `ProgramRecommendationEngine` Class

- Evaluates 6 programs: STE, SPFL, SPTVE, SNED L, OHSP, REGULAR
- Implements academic rules
- Implements non-academic/survey rules
- Ranks recommendations by criteria match percentage

**Academic Rules Implemented**:

- **STE**: Average ≥ 90 AND all subjects ≥ 85 AND DOST exam passed
- **SPFL/SPTVE**: Average ≥ 90 AND all subjects ≥ 85 AND DOST exam NOT passed
- **REGULAR**: Average ≤ 89 AND DOST exam not passed
- **SNED L**: Student has disability
- **OHSP**: Student is working

**Non-Academic Rules Implemented**:

- **STE**: Interested in science, math, English + active + studious + smart
- **SPFL**: Interested in English, foreign language, arts, tourism + active + studious
- **SPTVE**: Interested in English, technology, arts, crafts + creative + studious + smart + artistic
- **SNED L**: Has disability
- **OHSP**: Working student
- **REGULAR**: Average student, not studious, not smart/active

**Ranking System**:

- Rank 1: Meets all key criteria (100%)
- Rank 2: Meets 80% of criteria
- Rank 3+: Follow accordingly
- Last: Meets least components

**Key Methods**:

- `generate_recommendations()`: Main method to generate all recommendations
- `_evaluate_academic_criteria()`: Evaluates academic rules
- `_evaluate_non_academic_criteria()`: Evaluates non-academic/survey rules
- `check_ste_qualification()`: Verifies if student is in Qualified_for_ste table
- `get_recommendation_summary()`: Returns formatted recommendations

### 2. Modified: `enrollment_app/views/studentacademic_view.py`

**Changes Made**:

#### Updated Imports

- Added `recommendation_service` for recommendation generation
- Added `Qualified_for_ste` model for STE validation
- Added `timezone` and `json` for time handling and JSON parsing

#### Enhanced `verify_grades_ajax()` Function

**Original**: Only verified grades against OCR
**New Functionality**:

- ✅ Verifies grades against OCR (preserves original functionality)
- ✅ Generates program recommendations on successful verification
- ✅ Checks STE qualification in database
- ✅ Returns formatted recommendations with ranks and criteria met
- ✅ Saves recommendations to session for later use

**Response Format**:

```json
{
  "success": true,
  "verified": true,
  "message": "Grades verified successfully! Here are your program recommendations:",
  "overall_average": 92.5,
  "dost_exam_result": "passed",
  "recommendations": [
    {
      "rank": 1,
      "program_code": "STE",
      "program_name": "Science, Technology, Engineering",
      "percentage_match": 100,
      "recommendation_level": "Strong (Meets all criteria)",
      "criteria_met": [
        "Academic Requirements",
        "Non-Academic/Survey Requirements"
      ],
      "special_checks": [
        {
          "type": "ste_qualification",
          "message": "Student found in Qualified_for_ste database",
          "action_required": false
        }
      ],
      "ste_qualified": true
    }
  ]
}
```

#### New `confirm_program_selection_ajax()` Function

**Purpose**: Handles program selection confirmation with special validation

**Features**:

- Validates academic requirements before allowing STE selection
- Checks if student exists in `Qualified_for_ste` table for STE program
- Prevents students from selecting STE if:
  - Average < 90
  - Any subject < 85
  - DOST exam not passed
  - Not in Qualified_for_ste database
- Saves confirmed selection to session
- Provides clear error messages for failed validations

**Request Format**:

```json
{
  "program_code": "STE",
  "student_lrn": "123456789012"
}
```

**Success Response**:

```json
{
  "success": true,
  "message": "STE program confirmed successfully!",
  "program_code": "STE"
}
```

**Error Response (STE Not Qualified)**:

```json
{
  "success": false,
  "error": "You are not registered in the Qualified for STE database. Please contact your school administrator or select another program.",
  "action": "contact_admin_or_select_other"
}
```

#### New `check_ste_qualification()` Helper Function

**Purpose**: Checks if a student's LRN exists in Qualified_for_ste table

**Returns**: Tuple of (is_qualified: bool, qualified_record: Qualified_for_ste or None)

### 3. Modified: `enrollment_app/services/session_manager.py`

**Changes Made**:

#### Added Session Key

- `KEY_RECOMMENDATIONS = 'enrollment_recommendations'`

#### New Methods

- `save_recommendations(request, recommendations)`: Saves recommendation results to session
- `get_recommendations(request)`: Retrieves recommendations from session
- Updated `get_all_session_data()`: Now includes recommendations in returned data

### 4. Modified: `enrollment_app/urls.py`

**Changes Made**:

#### Added New URL Pattern

- `path('confirm-program/', confirm_program_selection_ajax, name='confirm_program_ajax')`

#### Updated Imports

- Added `confirm_program_selection_ajax` to imports

### 5. Modified: `enrollment_app/views/__init__.py`

**Changes Made**:

#### Updated Exports

- Added `confirm_program_selection_ajax` to imports and `__all__` list

## Business Logic Implementation Details

### Academic Evaluation Flowchart

```
IF average >= 90 AND all subjects >= 85 AND DOST passed
  ├─ ELIGIBLE FOR: STE (if in Qualified_for_ste table)

ELSE IF average >= 90 AND all subjects >= 85 AND DOST not passed
  ├─ ELIGIBLE FOR: SPFL, SPTVE

ELSE IF average <= 89
  ├─ ELIGIBLE FOR: REGULAR

IF student has disability (is_sped = True)
  └─ ELIGIBLE FOR: SNED L

IF student is working (is_working_student = True)
  └─ ELIGIBLE FOR: OHSP
```

### Non-Academic Evaluation Scoring

Each program receives a score based on criteria met:

- Score = (Criteria Met / Total Criteria) × 100
- Programs with 0% match are excluded from recommendations
- Programs with ≥50% match are included

**Example**:

- STE: Student meets 5 out of 6 criteria = 83% match = Rank 2 ("Good: Meets 80% of criteria")

### STE Special Validation

When student attempts to confirm STE program:

1. Check academic requirements (average ≥ 90, all subjects ≥ 85, DOST passed)
2. Query `Qualified_for_ste` table using student LRN
3. Verify status = 'qualified'
4. If status ≠ 'qualified' or record doesn't exist → DENY and show error

## Database Interactions

### Models Used

1. **`Qualified_for_ste`** (from coordinator_app)

   - Field: `student_lrn` (CharField, max_length=12)
   - Field: `status` (CharField, choices: pending, qualified, not_qualified, waitlisted)
   - Used for: Verifying STE program eligibility

2. **`Student`** (from enrollment_app)

   - Field: `is_sped` (BooleanField)
   - Field: `is_working_student` (BooleanField)
   - Used for: Checking disability and working status

3. **`StudentData`** (from enrollment_app)
   - Used for: Storing grades and survey responses

## Testing Recommendations

### Test Scenarios

**Scenario 1: STE Eligible Student (All Requirements Met)**

- Average: 92
- All subjects: 85+
- DOST: Passed
- In Qualified_for_ste: Yes, status='qualified'
- Expected: STE as Rank 1 recommendation

**Scenario 2: STE Academic Eligible but Not in Database**

- Average: 92
- All subjects: 85+
- DOST: Passed
- In Qualified_for_ste: No
- Expected: STE offered but confirmation fails with clear message

**Scenario 3: SPFL/SPTVE Eligible**

- Average: 91
- All subjects: 86
- DOST: Not Passed
- Expected: SPFL and SPTVE as top recommendations

**Scenario 4: Regular Program**

- Average: 85
- DOST: Not Passed
- Expected: REGULAR as primary recommendation

**Scenario 5: Disability Student**

- has disability: Yes
- Expected: SNED L as primary recommendation

**Scenario 6: Working Student**

- is_working_student: Yes
- Expected: OHSP as primary recommendation

## API Integration Points

### Frontend Integration

The HTML/JavaScript should call these endpoints:

**1. Get Recommendations**

```javascript
POST /enrollment/verify-grades/
Body: {} (uses session data)
```

**2. Confirm Program Selection**

```javascript
POST /enrollment/confirm-program/
Body: {
  "program_code": "STE",
  "student_lrn": "123456789012"
}
```

## Notes for Frontend Developer

1. When "See Recommended Program" button is clicked:

   - Call `/enrollment/verify-grades/` endpoint
   - Display recommendations with ranks
   - Show "Recommendation Level" to explain match percentage

2. When student clicks "Confirm" on a program:

   - Call `/enrollment/confirm-program/` endpoint
   - For STE, show the additional database verification message
   - Handle error responses gracefully
   - Suggest alternative programs if STE confirmation fails

3. Session Data Flow:
   - Student completes academic form → Session saved
   - Student clicks "See Recommendations" → Grades verified + Recommendations generated + Saved to session
   - Student confirms selection → Validated + Saved to session

## Error Handling

**Common Error Scenarios**:

| Error                   | HTTP Status | Message                                        | Action                     |
| ----------------------- | ----------- | ---------------------------------------------- | -------------------------- |
| No academic data        | 400         | "No academic data found"                       | Redirect to academic form  |
| No survey data          | 400         | "No survey data found"                         | Redirect to survey form    |
| OCR verification failed | 200         | Mismatches listed                              | Show correction form       |
| STE not in database     | 400         | "Not registered in Qualified for STE database" | Contact admin/select other |
| Invalid JSON            | 400         | "Invalid JSON"                                 | Retry with proper format   |

## Performance Considerations

- Recommendation generation is lightweight (O(n) where n=6 programs)
- STE database check is indexed on `student_lrn`
- All data stored in session (no DB writes during recommendation)
- Final confirmation writes only to session initially

---

**Implementation Status**: ✅ Complete and Ready for Testing
**Last Updated**: January 4, 2026
