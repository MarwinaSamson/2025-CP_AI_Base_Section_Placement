# FIELD LOCATION VERIFICATION

## 1. TRANSFEREE GRADE LEVEL

Location: Personal Info → Other Details
HTML ID: `transfereeGradeLevelContainer` (should be visible when "Enrolling As" = "Transferee")
Expected: Dropdown with Grade 7, 8, 9, 10

Status: ✓ PRESENT in template (lines 813-828)

---

## 2. PROGRAM FIELD

Location: Enrollment Placement section
HTML ID: `displayProgram`
Expected: Read-only text field showing program code (e.g., "REGULAR")

Status: ✓ PRESENT in template (lines 2218-2226)
JavaScript loads it: Line 2569 `programInput.value = progSel.selected_program_code;`

---

## 3. TRACK CATEGORY SELECTOR

Location: Enrollment Placement section  
HTML ID: `trackSelectorContainer` (hidden by default)
Shows when:

- Student is TRANSFEREE
- Program is REGULAR
- Transferee Grade Level is set

Status: ✓ PRESENT in template (lines 2253-2273)
JavaScript controls visibility: Line 2600 checks conditions

---

## JAVASCRIPT FLOW

1. Page loads → DOMContentLoaded fires (line 2538)
2. `loadProgramName()` called (line 2635)
   - Fetches `/coordinator/api/student/{id}/details/`
   - Sets: `programInput.value = progSel.selected_program_code`
   - Loads: `studentData = response.data.student_data` (global)
   - Shows/hides track selector based on conditions
3. Transferee section loads (line 2649)
   - Fetches `/coordinator/api/student/{id}/details/`
   - Sets: `transfereeGradeLevelSelect.value = studentData.transferee_grade_level`
   - Sets: `enrollingAsSelect.value = studentData.enrolling_as`
   - Shows/hides grade level container
4. Listeners attached:
   - `enrollingAsSelect` change: shows/hides grade field, auto-saves, reloads program
   - `transfereeGradeLevelSelect` change: auto-saves, reloads program (to update track visibility)

---

## DEBUGGING STEPS

1. Open Browser Console (F12)
2. Load student edit page
3. Look for these messages:

   ```
   ✓ DEBUG: Element Check
   📥 StudentData loaded globally: {full_name: "...", enrolling_as: "transferee", ...}
   ✓ Loaded transferee_grade_level: 8
   ✓ Enrolling as updated to: transferee
   ```

4. Check if Program field has value:
   - Console: `document.getElementById("displayProgram").value`
5. Check if Grade field visible:
   - Console: `document.getElementById("transfereeGradeLevelContainer").classList`
6. Check if Track selector visible:
   - Console: `document.getElementById("trackSelectorContainer").classList`

---

## COMMON ISSUES

❌ Program field still empty?
→ API might not be returning `selected_program_code`
→ Check: `/coordinator/api/student/{id}/details/` endpoint

❌ Grade field not visible?
→ `enrolling_as` not being set to "transferee"
→ Check: `studentData.enrolling_as` value

❌ Track selector not showing?
→ Grade level not set, OR
→ Program not REGULAR, OR
→ Condition `isTransferee && isRegular && transfereeGradeLevel` fails
→ Check console logs for which condition failed
