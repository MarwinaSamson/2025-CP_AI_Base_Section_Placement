# Results Upload Module - Architecture & Flow Diagrams

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          RESULTS UPLOAD SYSTEM                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        USER INTERFACE                            │  │
│  │  ┌──────────────┬──────────────┬──────────────┐                 │  │
│  │  │  Header      │  Bulk Upload │  Manual Form │                 │  │
│  │  │  - Profile   │  - Drag/Drop │  - LRN       │                 │  │
│  │  │  - Avatar    │  - Progress  │  - Scores    │                 │  │
│  │  │  - Role      │  - Template  │  - Status    │                 │  │
│  │  │  - Program   │              │              │                 │  │
│  │  └──────────────┴──────────────┴──────────────┘                 │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                           ↓ (AJAX/Forms)                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                   JavaScript Module                              │  │
│  │  • Validation                                                    │  │
│  │  • Progress Tracking                                            │  │
│  │  • Notifications                                                │  │
│  │  • Modal Management                                             │  │
│  │  • CSRF Token Handling                                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                           ↓ (HTTP Requests)                             │
├─────────────────────────────────────────────────────────────────────────┤
│                       DJANGO BACKEND LAYER                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      URL Router                                  │  │
│  │  • results_upload/        (GET)                                 │  │
│  │  • api/results/manual-entry/  (POST)                            │  │
│  │  • api/results/bulk-upload/   (POST)                            │  │
│  │  • api/results/download-template/ (GET)                         │  │
│  │  • api/results/export/    (GET)                                 │  │
│  │  • api/results/<lrn>/view/ (GET)                                │  │
│  │  • api/results/<lrn>/delete/ (DELETE)                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                           ↓                                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      View Functions                              │  │
│  │  ┌─────────────────────────────────────────────────────────┐   │  │
│  │  │ results_upload()     - Render main page with context    │   │  │
│  │  │ manual_entry()       - Validate & save single entry     │   │  │
│  │  │ bulk_upload()        - Process Excel/CSV file           │   │  │
│  │  │ download_template()  - Generate & serve template        │   │  │
│  │  │ export_results()     - Export all records to Excel       │   │  │
│  │  │ view_result()        - Fetch single record JSON          │   │  │
│  │  │ delete_result()      - Remove record                     │   │  │
│  │  └─────────────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                           ↓ (Business Logic)                            │
├─────────────────────────────────────────────────────────────────────────┤
│                         DATABASE LAYER                                  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Qualified_for_ste                UserProfile                    │  │
│  │ ┌────────────────────┐           ┌──────────────────────┐       │  │
│  │ │ • student_lrn      │           │ • user               │       │  │
│  │ │ • exam_score       │           │ • user_type          │       │  │
│  │ │ • interview_score  │           │ • program            │       │  │
│  │ │ • status           │           │ • position           │       │  │
│  │ │ • remarks          │           │ • department         │       │  │
│  │ │ • created_at       │           │ • photo              │       │  │
│  │ │ • updated_at       │           │ • employee_id        │       │  │
│  │ │ • updated_by ────────────────────────────────────┐   │       │  │
│  │ └────────────────────┘           │                 │   │       │  │
│  │         ▲                         └─────────────────┼───┘       │  │
│  │         │                                 │         │           │  │
│  │         └─────────────────────────────────┼─────────┘           │  │
│  │                    ForeignKey             │                     │  │
│  │                                        Django User              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

## Bulk Upload Data Flow

```
┌──────────────────┐
│  User Selects    │
│  Excel/CSV File  │
└────────┬─────────┘
         │
         ↓
┌──────────────────────────────────┐
│  Frontend Validation              │
│  • File type check (.xlsx/.csv)   │
│  • File size check (< 10MB)       │
└────────┬─────────────────────────┘
         │
         ↓ (Valid)
┌──────────────────────────────────┐
│  Show Processing Modal            │
│  with Progress Bar                │
└────────┬─────────────────────────┘
         │
         ↓
┌──────────────────────────────────┐
│  POST to                          │
│  /api/results/bulk-upload/        │
│  (with CSRF token)                │
└────────┬─────────────────────────┘
         │
         ↓
    BACKEND PROCESSING
    ┌─────────────────────────────┐
    │ 1. Read File (pandas)        │
    │    • Parse Excel/CSV         │
    │                              │
    │ 2. Validate Structure        │
    │    • Check required columns: │
    │      - student_lrn           │
    │      - exam_score            │
    │      - interview_score       │
    │      - status                │
    │                              │
    │ 3. Validate Each Row         │
    │    ├─ LRN (12 digits?)       │
    │    ├─ Exam (0-100?)          │
    │    ├─ Interview (0-100?)     │
    │    └─ Status (valid choice?) │
    │                              │
    │ 4. Atomic Transaction        │
    │    ├─ Create/Update records  │
    │    ├─ Set updated_by = user  │
    │    └─ All or nothing         │
    │                              │
    │ 5. Generate Summary          │
    │    • Success count           │
    │    • Failed count            │
    │    • Error list per row      │
    └────────┬────────────────────┘
             │
         ↓ (JSON Response)
    ┌──────────────────────┐
    │ {                    │
    │   success: true,     │
    │   data: {            │
    │     success: 45,     │
    │     failed: 0,       │
    │     errors: []       │
    │   }                  │
    │ }                    │
    └────────┬─────────────┘
             │
         ↓
┌──────────────────────────────────┐
│  Update Progress to 100%          │
│  Show Success Notification        │
│  (45 records imported)            │
└────────┬─────────────────────────┘
         │
         ↓ (1 second delay)
┌──────────────────────────────────┐
│  Reload Page                      │
│  • Refresh recent uploads         │
│  • Update statistics              │
│  • Clear form                     │
└──────────────────────────────────┘
```

## Manual Entry Data Flow

```
┌────────────────────┐
│  User Fills Form   │
│  • LRN: 12 digits  │
│  • Exam Score      │
│  • Interview Score │
│  • Status          │
└────────┬───────────┘
         │
         ↓
┌──────────────────────────────────┐
│  HTML5 Validation                 │
│  • Required fields                │
│  • Type checking                  │
│  • Pattern matching (LRN)         │
│  • Min/Max values (scores)        │
└────────┬─────────────────────────┘
         │
         ↓ (Valid)
┌──────────────────────────────────┐
│  POST /api/results/manual-entry/  │
│  FormData + CSRF Token            │
└────────┬─────────────────────────┘
         │
         ↓
    BACKEND VALIDATION
    ┌─────────────────────────────┐
    │ 1. Extract Form Data         │
    │                              │
    │ 2. Validate Each Field       │
    │    ├─ LRN format (12 digits) │
    │    ├─ Exam score (0-100)     │
    │    └─ Interview (0-100)      │
    │                              │
    │ 3. Create/Update Record      │
    │    Qualified_for_ste(        │
    │      student_lrn=X,          │
    │      exam_score=X,           │
    │      interview_score=X,      │
    │      status=X,               │
    │      updated_by=request.user │
    │    )                         │
    │                              │
    │ 4. Calculate Metrics         │
    │    • total_score             │
    │    • average_score           │
    │                              │
    │ 5. Return JSON Response      │
    └────────┬────────────────────┘
             │
         ↓ (JSON)
    ┌──────────────────────────────┐
    │ {                            │
    │   success: true,             │
    │   message: "created...",     │
    │   data: {                    │
    │     lrn: "123456789012",     │
    │     exam_score: 85.5,        │
    │     interview_score: 90.0,   │
    │     total_score: 175.5,      │
    │     average_score: 87.75     │
    │   }                          │
    │ }                            │
    └────────┬─────────────────────┘
             │
         ↓
┌──────────────────────────────────┐
│  Show Success Notification        │
│  • "Record created successfully"  │
└────────┬─────────────────────────┘
         │
         ↓
┌──────────────────────────────────┐
│  Clear Form                       │
│  Reset all fields                 │
└────────┬─────────────────────────┘
         │
         ↓ (1.5 seconds)
┌──────────────────────────────────┐
│  Reload Page                      │
│  Display new record in table      │
└──────────────────────────────────┘
```

## View Result Modal Flow

```
┌─────────────────────┐
│  User Clicks Eye    │
│  Icon on Record     │
└────────┬────────────┘
         │
         ↓
┌──────────────────────────────────┐
│  Fetch /api/results/<lrn>/view/   │
│  (AJAX GET request)               │
└────────┬─────────────────────────┘
         │
         ↓
    BACKEND RETRIEVAL
    ┌─────────────────────────────┐
    │ 1. Get Record by LRN         │
    │                              │
    │ 2. Try to Find Student       │
    │    (optional link)           │
    │                              │
    │ 3. Format Response           │
    │    • All scores              │
    │    • Calculated metrics      │
    │    • Status display name     │
    │    • Updated info            │
    │                              │
    │ 4. Return JSON               │
    └────────┬────────────────────┘
             │
         ↓ (JSON)
    ┌────────────────────────────┐
    │ {                          │
    │   lrn: "123456789012",     │
    │   student_name: "...",     │
    │   exam_score: 85.5,        │
    │   interview_score: 90.0,   │
    │   total_score: 175.5,      │
    │   average_score: 87.75,    │
    │   status: "qualified",     │
    │   status_display: "Qual.", │
    │   remarks: "...",          │
    │   updated_by: "John",      │
    │   updated_at: "2025-01-09" │
    │ }                          │
    └────────┬───────────────────┘
             │
         ↓
┌──────────────────────────────────┐
│  Generate Modal HTML              │
│  • Score cards with colors        │
│  • Status badge                   │
│  • Metadata                       │
│  • Close button                   │
└────────┬─────────────────────────┘
         │
         ↓
┌──────────────────────────────────┐
│  Show Modal                       │
│  (animate fade-in)                │
│  Overlay background               │
└────────┬─────────────────────────┘
         │
         ↓
┌──────────────────────────────────┐
│  User Clicks Close                │
│  Modal Fades Out & Removed        │
└──────────────────────────────────┘
```

## Delete Record Flow

```
┌──────────────────┐
│  User Clicks     │
│  Delete Icon     │
└────────┬─────────┘
         │
         ↓
┌──────────────────────────────────┐
│  Show Confirmation Dialog         │
│  "Delete this record?"            │
│  [Cancel] [Confirm]               │
└────────┬─────────────────────────┘
         │
    ┌────┴─────┐
    │           │
    ↓ (Cancel)  ↓ (Confirm)
  [ABORT]      ┌─────────────────────────────┐
               │ DELETE /api/results/<lrn>/  │
               │ (with CSRF token)           │
               └────────┬────────────────────┘
                        │
                        ↓
                   BACKEND DELETE
                   ┌──────────────┐
                   │ Find record  │
                   │ Delete it    │
                   │ Return JSON  │
                   └────────┬─────┘
                            │
                        ↓ (Success)
                   ┌─────────────────┐
                   │ {               │
                   │   success: true │
                   │ }               │
                   └────────┬────────┘
                            │
                        ↓
                   ┌──────────────────┐
                   │ Show Success     │
                   │ Notification     │
                   └────────┬─────────┘
                            │
                        ↓ (1 second)
                   ┌──────────────────┐
                   │ Reload Page      │
                   │ Record Removed   │
                   └──────────────────┘
```

## Header Display with User Profile

```
┌─────────────────────────────────────────────────────────────┐
│                        PAGE HEADER                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Left Side                                                   │
│  ┌──────────────────────────┐                               │
│  │ Title: Upload Results    │                               │
│  │ Subtitle: Manage qual... │                               │
│  └──────────────────────────┘                               │
│                                                              │
│                             Right Side (User Profile)        │
│                             ┌──────────────────────────────┐ │
│                             │ Name: Marwina, John          │ │
│                             │ ┌─────────────────────────┐  │ │
│                             │ │ Admin │ STE             │  │ │
│                             │ └─────────────────────────┘  │ │
│                             │                              │ │
│                             │  ┌──────────────────┐        │ │
│                             │  │                  │        │ │
│                             │  │  ┌────────────┐  │        │ │
│                             │  │  │ PHOTO or   │  │        │ │
│                             │  │  │ INITIALS   │  │        │ │
│                             │  │  │  (MJ)      │  │        │ │
│                             │  │  └────────────┘  │        │ │
│                             │  │                  │        │ │
│                             │  └──────────────────┘        │ │
│                             │                              │ │
│                             └──────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Avatar Rendering Logic:
┌──────────────────┐
│  Check if user   │
│  has profile     │
└────────┬─────────┘
         │
    ┌────┴───────────┐
    │                │
    ↓ (Yes, has)     ↓ (No, empty)
┌─────────────────┐  Get initials
│ Check if photo  │  (First + Last)
└────────┬────────┘  │
    │                ↓
├───┴───────┐     Display
│           │     Initials
↓ (Has)     ↓ (No) Badge
│           │      (MJ)
Display    Display  in
Photo      Initials Gradient
URL        Badge    (Red)
```

## Error Handling Flow

```
┌──────────────────────────┐
│  Invalid Input / Error   │
└────────┬─────────────────┘
         │
    ┌────┴───────────────┐
    │                    │
Frontend Error       Backend Error
    │                    │
    ↓                    ↓
HTML5 Validation    Validation Logic
shows message       returns JSON
                    {
Cannot submit         success: false,
                      message: "Error details"
                    }
    │                    │
    ↓                    ↓
User sees          JavaScript catches
inline errors      and shows
                   notification
    │
    └─────────────────┬─────────────────────┐
                      │                     │
                      ↓                     ↓
            LRN Format Error          Score Range Error
            "Must be 12 digits"       "Must be 0-100"
                      │                     │
                      └────────┬────────────┘
                               │
                        User corrects
                        and resubmits
```

---

These diagrams show:

1. **Overall Architecture** - How components interact
2. **Bulk Upload** - File processing pipeline
3. **Manual Entry** - Form submission flow
4. **View Result** - Modal display sequence
5. **Delete Record** - Confirmation and removal
6. **Header Display** - User profile rendering with avatar logic
7. **Error Handling** - Validation and error feedback

Each flow diagram shows the complete journey from user action to final result.
