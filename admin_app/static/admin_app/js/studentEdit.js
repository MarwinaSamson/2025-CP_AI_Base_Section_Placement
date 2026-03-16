// ── Helpers ──────────────────────────────────────────────
const getStudentId = () =>
    new URLSearchParams(window.location.search).get('id') ||
    document.querySelector('[data-student-id]')?.dataset.studentId;

const API_BASE    = window.STUDENT_API_BASE || '/admin-portal/api/student/';
const MOVE_API    = window.ADMIN_MOVE_API   || '/admin-portal/api/admin-move/';
const SECTIONS_API = window.SECTIONS_API   || '/admin-portal/api/sections/';

function getCsrf() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
           document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

// ── Boot ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async function () {
    const studentId = getStudentId();
    if (!studentId) { showNotification('Student ID not found', 'error'); return; }

    await loadStudentData(studentId);

    // Grade auto-average
    document.querySelectorAll('input[step="0.01"]').forEach(inp => {
        inp.addEventListener('input', recalcAverage);
    });
});

// ── Edit Mode Toggle ──────────────────────────────────────
function toggleEditMode(enabled) {
    const badge        = document.getElementById('editModeBadge');
    const notice       = document.getElementById('editModeNotice');
    const saveBtn      = document.getElementById('saveChangesBtn');
    const photoLabel   = document.getElementById('photoUploadLabel');
    const photoInput   = document.getElementById('studentPhotoInput');
    const parentLabel  = document.getElementById('parentPhotoLabel');
    const parentInput  = document.getElementById('parentPhotoInput');
    const rcInput      = document.getElementById('reportCard');
    const rcTrigger    = document.getElementById('reportCardTrigger');
    const rcbInput     = document.getElementById('reportCardBack');
    const rcbTrigger   = document.getElementById('reportCardBackTrigger');

    if (enabled) {
        // ── Switch to EDIT mode ──
        badge.className = 'edit-mode-badge editing';
        badge.innerHTML = '<i class="fas fa-pen text-xs"></i> Editing';
        notice.classList.remove('hidden');
        saveBtn.classList.remove('hidden');

        // Unlock inline move form
        const moveForm = document.getElementById('inlineMoveForm');
        if (moveForm) { moveForm.classList.remove('opacity-50', 'pointer-events-none'); }

        // Unlock field-input elements
        document.querySelectorAll('.field-input').forEach(el => {
            el.classList.remove('readonly-mode');
            el.classList.add('edit-mode');
            if (el.tagName === 'SELECT') el.disabled = false;
            else if (el.type !== 'checkbox' && el.type !== 'radio') el.readOnly = false;
        });
        document.querySelectorAll('.radio-field').forEach(el => el.disabled = false);

        // Photo upload
        if (photoLabel) { photoLabel.classList.remove('cursor-not-allowed','opacity-50'); photoLabel.classList.add('cursor-pointer','bg-primary'); }
        if (photoInput) photoInput.disabled = false;
        if (parentLabel) { parentLabel.classList.remove('cursor-not-allowed','opacity-50'); parentLabel.classList.add('cursor-pointer','bg-primary'); }
        if (parentInput) parentInput.disabled = false;

        // Report card
        if (rcInput)    rcInput.disabled    = false;
        if (rcTrigger)  { rcTrigger.classList.remove('cursor-not-allowed','opacity-70'); rcTrigger.classList.add('cursor-pointer','bg-white'); }
        if (rcbInput)   rcbInput.disabled   = false;
        if (rcbTrigger) { rcbTrigger.classList.remove('cursor-not-allowed','opacity-70'); rcbTrigger.classList.add('cursor-pointer','bg-white'); }

    } else {
        // ── Switch to READ-ONLY mode ──
        badge.className = 'edit-mode-badge readonly';
        badge.innerHTML = '<i class="fas fa-lock text-xs"></i> Read Only';
        notice.classList.add('hidden');
        saveBtn.classList.add('hidden');

        // Lock inline move form
        const moveFormOff = document.getElementById('inlineMoveForm');
        if (moveFormOff) { moveFormOff.classList.add('opacity-50', 'pointer-events-none'); }

        document.querySelectorAll('.field-input').forEach(el => {
            el.classList.remove('edit-mode');
            el.classList.add('readonly-mode');
            if (el.tagName === 'SELECT') el.disabled = true;
            else if (el.type !== 'checkbox' && el.type !== 'radio') el.readOnly = true;
        });
        document.querySelectorAll('.radio-field').forEach(el => el.disabled = true);

        if (photoLabel) { photoLabel.classList.add('cursor-not-allowed','opacity-50'); photoLabel.classList.remove('cursor-pointer','bg-primary'); }
        if (photoInput) photoInput.disabled = true;
        if (parentLabel) { parentLabel.classList.add('cursor-not-allowed','opacity-50'); parentLabel.classList.remove('cursor-pointer','bg-primary'); }
        if (parentInput) parentInput.disabled = true;

        if (rcInput)    rcInput.disabled    = true;
        if (rcTrigger)  { rcTrigger.classList.add('cursor-not-allowed','opacity-70'); rcTrigger.classList.remove('cursor-pointer','bg-white'); }
        if (rcbInput)   rcbInput.disabled   = true;
        if (rcbTrigger) { rcbTrigger.classList.add('cursor-not-allowed','opacity-70'); rcbTrigger.classList.remove('cursor-pointer','bg-white'); }
    }
}

// ── Load Data ─────────────────────────────────────────────
async function loadStudentData(studentId) {
    showLoading(true);
    try {
        const res  = await fetch(`${API_BASE}${studentId}/details/`);
        if (!res.ok) throw new Error('Failed to fetch student data');
        const result = await res.json();
        if (!result.success) throw new Error(result.error || 'Unknown error');

        const d = result.data;
        populateStudentData(d.student_data, d.student);
        populateFamilyData(d.father, d.mother, d.guardian);
        populateSurveyData(d.survey_data);
        populateAcademicData(d.academic_data);
        populatePlacement(d.program_selection);

        showNotification('Student data loaded', 'success');
    } catch (err) {
        showNotification('Error loading student: ' + err.message, 'error');
    } finally {
        showLoading(false);
    }
}

// ── Populate helpers ──────────────────────────────────────
function set(id, val) {
    const el = document.getElementById(id);
    if (el && val !== undefined && val !== null) el.value = val;
}
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val || '—';
}

function populateStudentData(sd, student) {
    if (!sd) return;
    set('studentLrn', student?.lrn);
    set('academicLrn', student?.lrn);
    set('headerLrn', student?.lrn);
    set('firstName', sd.first_name);
    set('middleName', sd.middle_name);
    set('lastName', sd.last_name);
    set('age', sd.age);
    set('dateOfBirth', sd.date_of_birth);
    set('placeOfBirth', sd.place_of_birth);
    set('gender', sd.gender);
    set('address', sd.address);
    set('religion', sd.religion);
    set('dialectSpoken', sd.dialect_spoken);
    set('ethnicTribe', sd.ethnic_tribe);
    set('lastSchoolAttended', sd.last_school_attended);
    set('previousGradeSection', sd.previous_grade_section);
    set('lastSchoolYear', sd.last_school_year);

    const enrollingAs = Array.isArray(sd.enrolling_as) ? sd.enrolling_as[0] : sd.enrolling_as;
    set('enrollingAs', enrollingAs);

    // SPED
    const spedVal = sd.is_sped ? 'yes' : 'no';
    const spedRadio = document.querySelector(`input[name="is_sped"][value="${spedVal}"]`);
    if (spedRadio) spedRadio.checked = true;
    const spedTxt = document.querySelector('textarea[name="sped_details"]');
    if (spedTxt) spedTxt.value = sd.sped_details || '';

    // Working
    const workVal = sd.is_working_student ? 'yes' : 'no';
    const workRadio = document.querySelector(`input[name="is_working"][value="${workVal}"]`);
    if (workRadio) workRadio.checked = true;
    const workTxt = document.querySelector('textarea[name="working_details"]');
    if (workTxt) workTxt.value = sd.working_details || '';

    // Photo
    if (sd.student_photo) {
        const el = document.getElementById('studentPhotoDisplay');
        if (el) el.innerHTML = `<img src="${sd.student_photo}" class="w-full h-full object-cover" />`;
    }
}

function populateFamilyData(father, mother, guardian) {
    if (father) {
        set('fatherFamilyName', father.family_name);
        set('fatherFirstName',  father.first_name);
        set('fatherMiddleName', father.middle_name);
        set('fatherAge',        father.age);
        set('fatherDateOfBirth',father.date_of_birth);
        set('fatherOccupation', father.occupation);
        set('fatherContactNumber', father.contact_number);
        set('fatherEmail',      father.email);
    }
    if (mother) {
        set('motherFamilyName', mother.family_name);
        set('motherFirstName',  mother.first_name);
        set('motherMiddleName', mother.middle_name);
        set('motherAge',        mother.age);
        set('motherDateOfBirth',mother.date_of_birth);
        set('motherOccupation', mother.occupation);
        set('motherContactNumber', mother.contact_number);
        set('motherEmail',      mother.email);
    }
    if (guardian) {
        if (guardian.official_guardian_type) {
            const r = document.querySelector(`input[name="guardian_type"][value="${guardian.official_guardian_type}"]`);
            if (r) r.checked = true;
        }
        if (guardian.parent_photo) {
            const el = document.getElementById('parentPhotoDisplay');
            if (el) el.innerHTML = `<img src="${guardian.parent_photo}" class="w-full h-full object-cover" />`;
        }
        if (guardian.other_guardian) {
            const g = guardian.other_guardian;
            set('guardianFamilyName', g.family_name);
            set('guardianFirstName',  g.first_name);
            set('guardianMiddleName', g.middle_name);
            set('guardianAge',        g.age);
            set('guardianDateOfBirth',g.date_of_birth);
            set('guardianAddress',    g.address);
            set('guardianRelationship', g.relationship_to_student);
            set('guardianContactNumber', g.contact_number);
            set('guardianEmail',      g.email);
        }
    }
}

function populateSurveyData(s) {
    if (!s) return;
    const fields = [
        'learningStyle','studyHours','studyEnvironment','schoolworkSupport',
        'enjoyedSubjects','interestedProgram','programMotivation',
        'enjoyedActivities','enjoyedActivitiesOther','assignmentsOnTime',
        'handleDifficultLessons','deviceAvailability','internetAccess',
        'absences','absenceReason','participation','difficultyAreas',
        'extraSupport','quietPlace','distanceFromSchool','travelDifficulty'
    ];
    const map = {
        learningStyle: s.learning_style, studyHours: s.study_hours,
        studyEnvironment: s.study_environment, schoolworkSupport: s.schoolwork_support,
        enjoyedSubjects: Array.isArray(s.enjoyed_subjects) ? s.enjoyed_subjects.join(', ') : s.enjoyed_subjects,
        interestedProgram: s.interested_program, programMotivation: s.program_motivation,
        enjoyedActivities: Array.isArray(s.enjoyed_activities) ? s.enjoyed_activities.join(', ') : s.enjoyed_activities,
        enjoyedActivitiesOther: s.enjoyed_activities_other,
        assignmentsOnTime: s.assignments_on_time, handleDifficultLessons: s.handle_difficult_lessons,
        deviceAvailability: s.device_availability, internetAccess: s.internet_access,
        absences: s.absences, absenceReason: s.absence_reason, participation: s.participation,
        difficultyAreas: Array.isArray(s.difficulty_areas) ? s.difficulty_areas.join(', ') : s.difficulty_areas,
        extraSupport: s.extra_support, quietPlace: s.quiet_place,
        distanceFromSchool: s.distance_from_school, travelDifficulty: s.travel_difficulty
    };
    fields.forEach(f => set(f, map[f]));
}

function populateAcademicData(a) {
    if (!a) return;
    set('gradeMathematics',          a.mathematics);
    set('gradeAralingPanlipunan',     a.araling_panlipunan);
    set('gradeEnglish',               a.english);
    set('gradeEdukasyonSaPagpapakatao', a.edukasyon_sa_pagpapakatao);
    set('gradeScience',               a.science);
    set('gradeEdukasyonPangkabuhayan', a.edukasyon_pangkabuhayan);
    set('gradeFilipino',              a.filipino);
    set('gradeMapeh',                 a.mapeh);
    set('dostExamResult',             a.dost_exam_result);
    if (a.overall_average) set('overallAverage', parseFloat(a.overall_average).toFixed(2));

    // Report card labels
    if (a.report_card) {
        const parts = a.report_card.split('/');
        const lbl = document.getElementById('reportCardLabel');
        if (lbl) lbl.textContent = parts[parts.length - 1];
    }
}

function populatePlacement(p) {
    if (!p) return;

    // Summary display (plain text paragraphs)
    const prog = document.getElementById('displayProgram');
    const sec  = document.getElementById('displaySection');
    const stat = document.getElementById('displayStatus');
    if (prog) prog.textContent = p.selected_program_code || '—';
    if (sec)  sec.textContent  = p.assigned_section      || 'Not yet assigned';
    if (stat) {
        stat.textContent  = p.admin_approved ? 'Approved' : 'Pending';
        stat.className    = `text-sm font-semibold ${p.admin_approved ? 'text-green-700' : 'text-yellow-700'}`;
    }

    // Pre-select program dropdown to match current
    const programSelect = document.getElementById('moveTargetProgram');
    if (programSelect && p.selected_program_code) {
        programSelect.value = p.selected_program_code;
        // Auto-load sections for the current program
        onInlineProgramChange(p.assigned_section);
    }

    set('placementAdminNotes', p.admin_notes);
}

// ── Grade average ─────────────────────────────────────────
function recalcAverage() {
    const inputs = document.querySelectorAll('input[step="0.01"]');
    let sum = 0, count = 0;
    inputs.forEach(inp => {
        const v = parseFloat(inp.value);
        if (!isNaN(v) && inp.value !== '') { sum += v; count++; }
    });
    const avg = document.getElementById('overallAverage');
    if (avg && count > 0) avg.value = (sum / count).toFixed(2);
}

// ── Save All Changes ──────────────────────────────────────
async function saveAllChanges() {
    const studentId = getStudentId();
    const btn = document.getElementById('saveChangesBtn');
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';

    try {
        // Collect student data
        const sd = {
            first_name: document.getElementById('firstName')?.value,
            last_name:  document.getElementById('lastName')?.value,
            middle_name: document.getElementById('middleName')?.value,
            age:        document.getElementById('age')?.value,
            date_of_birth: document.getElementById('dateOfBirth')?.value,
            place_of_birth: document.getElementById('placeOfBirth')?.value,
            gender:     document.getElementById('gender')?.value,
            address:    document.getElementById('address')?.value,
            religion:   document.getElementById('religion')?.value,
            dialect_spoken: document.getElementById('dialectSpoken')?.value,
            ethnic_tribe: document.getElementById('ethnicTribe')?.value,
            last_school_attended: document.getElementById('lastSchoolAttended')?.value,
            previous_grade_section: document.getElementById('previousGradeSection')?.value,
            last_school_year: document.getElementById('lastSchoolYear')?.value,
            enrolling_as: document.getElementById('enrollingAs')?.value,
            is_sped: document.querySelector('input[name="is_sped"]:checked')?.value === 'yes',
            is_working_student: document.querySelector('input[name="is_working"]:checked')?.value === 'yes',
        };

        // Academic
        const ad = {
            dost_exam_result: document.getElementById('dostExamResult')?.value,
            mathematics: document.getElementById('gradeMathematics')?.value,
            araling_panlipunan: document.getElementById('gradeAralingPanlipunan')?.value,
            english: document.getElementById('gradeEnglish')?.value,
            edukasyon_sa_pagpapakatao: document.getElementById('gradeEdukasyonSaPagpapakatao')?.value,
            science: document.getElementById('gradeScience')?.value,
            edukasyon_pangkabuhayan: document.getElementById('gradeEdukasyonPangkabuhayan')?.value,
            filipino: document.getElementById('gradeFilipino')?.value,
            mapeh: document.getElementById('gradeMapeh')?.value,
        };

        // Admin notes
        const notes = document.getElementById('placementAdminNotes')?.value || '';

        await Promise.all([
            fetch(`${API_BASE}${studentId}/update/student-data/`, {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                body: JSON.stringify(sd)
            }),
            fetch(`${API_BASE}${studentId}/update/academic-data/`, {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                body: JSON.stringify(ad)
            }),
            fetch(`${API_BASE}${studentId}/update/program-selection/`, {
                method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
                body: JSON.stringify({ admin_notes: notes })
            }),
        ]);

        showNotification('All changes saved successfully!', 'success');

        // Turn off edit mode after save
        document.getElementById('editToggle').checked = false;
        toggleEditMode(false);

    } catch (err) {
        showNotification('Save failed: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
    }
}

// ── Admin Move Modal ──────────────────────────────────────
function openAdminMoveModal() {
    const studentId = getStudentId();
    const modal = document.getElementById('adminMoveModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    // Populate current placement
    document.getElementById('moveCurrentProgram').textContent =
        document.getElementById('displayProgram')?.value || '—';
    document.getElementById('moveCurrentSection').textContent =
        document.getElementById('displaySection')?.value || '—';
    document.getElementById('moveModalStudentName').textContent =
        `LRN: ${studentId}`;

    // Reset
    document.getElementById('moveTargetProgram').value = '';
    document.getElementById('moveTargetSection').innerHTML = '<option value="">Select program first</option>';
    document.getElementById('moveTargetSection').disabled = true;
    document.getElementById('moveReason').value = '';
    document.getElementById('sectionLoadMsg').textContent = '';
}

function closeAdminMoveModal() {
    const modal = document.getElementById('adminMoveModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
}

async function onInlineProgramChange(preselectSectionName) {
    const programCode   = document.getElementById('moveTargetProgram').value;
    const sectionSelect = document.getElementById('moveTargetSection');
    const msg           = document.getElementById('inlineSectionMsg');

    if (!programCode) {
        sectionSelect.innerHTML = '<option value="">Select program first</option>';
        sectionSelect.disabled  = true;
        if (msg) msg.textContent = '';
        return;
    }

    sectionSelect.disabled  = true;
    sectionSelect.innerHTML = '<option value="">Loading sections...</option>';
    if (msg) msg.textContent = 'Fetching available sections...';

    try {
        const res     = await fetch(`${SECTIONS_API}?program=${encodeURIComponent(programCode)}`);
        const data    = await res.json();
        const sections = data.sections || [];

        if (sections.length === 0) {
            sectionSelect.innerHTML = '<option value="">No sections available</option>';
            if (msg) msg.textContent = 'No sections found for this program.';
            return;
        }

        sectionSelect.innerHTML = '<option value="">-- Select Section --</option>' +
            sections.map(s => {
                const full  = s.current_students >= s.max_students;
                const label = `${s.name} — ${s.adviser_name || 'No adviser'} (${s.current_students}/${s.max_students})${full ? ' — FULL' : ''}`;
                return `<option value="${s.id}" ${full ? 'disabled' : ''}>${label}</option>`;
            }).join('');

        sectionSelect.disabled = false;
        if (msg) msg.textContent = `${sections.length} section(s) available.`;

        // Pre-select if a section name was passed (e.g. current assignment)
        if (preselectSectionName) {
            Array.from(sectionSelect.options).forEach(opt => {
                if (opt.text.startsWith(preselectSectionName)) {
                    sectionSelect.value = opt.value;
                }
            });
        }
    } catch (err) {
        sectionSelect.innerHTML = '<option value="">Error loading sections</option>';
        if (msg) msg.textContent = 'Failed to load sections.';
    }
}

async function confirmInlineMove() {
    const studentId   = getStudentId();
    const programCode = document.getElementById('moveTargetProgram').value;
    const sectionId   = document.getElementById('moveTargetSection').value;
    const reason      = document.getElementById('placementAdminNotes')?.value?.trim();

    if (!programCode) { showNotification('Please select a program', 'error'); return; }
    if (!sectionId)   { showNotification('Please select a section',  'error'); return; }
    if (!reason)      { showNotification('Please enter a reason / notes', 'error'); return; }

    const btn  = document.getElementById('confirmInlineMoveBtn');
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Moving...';

    try {
        const res = await fetch(MOVE_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
            body: JSON.stringify({
                student_lrn:     studentId,
                to_program_code: programCode,
                to_section_id:   parseInt(sectionId),
                reason
            })
        });

        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Move failed');

        // Update summary display
        const prog = document.getElementById('displayProgram');
        const sec  = document.getElementById('displaySection');
        const stat = document.getElementById('displayStatus');
        if (prog) prog.textContent = data.program_name;
        if (sec)  sec.textContent  = data.section_name;
        if (stat) { stat.textContent = 'Approved'; stat.className = 'text-sm font-semibold text-green-700'; }

        showNotification(`Student moved to ${data.program_name} — ${data.section_name}`, 'success');

    } catch (err) {
        showNotification('Error: ' + err.message, 'error');
    } finally {
        btn.disabled  = false;
        btn.innerHTML = orig;
    }
}

async function onMoveProgramChange() {
    const programCode = document.getElementById('moveTargetProgram').value;
    const sectionSelect = document.getElementById('moveTargetSection');
    const msg = document.getElementById('sectionLoadMsg');

    if (!programCode) {
        sectionSelect.innerHTML = '<option value="">Select program first</option>';
        sectionSelect.disabled = true;
        msg.textContent = '';
        return;
    }

    sectionSelect.disabled = true;
    sectionSelect.innerHTML = '<option value="">Loading sections...</option>';
    msg.textContent = 'Fetching available sections...';

    try {
        const res = await fetch(`${SECTIONS_API}?program=${encodeURIComponent(programCode)}`);
        const data = await res.json();
        const sections = data.sections || [];

        if (sections.length === 0) {
            sectionSelect.innerHTML = '<option value="">No sections available</option>';
            msg.textContent = 'No sections found for this program.';
            return;
        }

        sectionSelect.innerHTML = '<option value="">-- Select Section --</option>' +
            sections.map(s => {
                const full = s.current_students >= s.max_students;
                return `<option value="${s.id}" ${full ? 'disabled' : ''}>
                    ${s.name} — ${s.adviser_name || 'No adviser'} (${s.current_students}/${s.max_students})${full ? ' FULL' : ''}
                </option>`;
            }).join('');

        sectionSelect.disabled = false;
        msg.textContent = `${sections.length} section(s) available.`;
    } catch (err) {
        sectionSelect.innerHTML = '<option value="">Error loading sections</option>';
        msg.textContent = 'Failed to load sections.';
    }
}

async function confirmAdminMove() {
    const studentId = getStudentId();
    const programCode = document.getElementById('moveTargetProgram').value;
    const sectionId   = document.getElementById('moveTargetSection').value;
    const reason      = document.getElementById('moveReason').value.trim();

    if (!programCode) { showNotification('Please select a target program', 'error'); return; }
    if (!sectionId)   { showNotification('Please select a target section',  'error'); return; }
    if (!reason)      { showNotification('Please enter a reason for this move', 'error'); return; }

    const btn = document.getElementById('confirmMoveBtn');
    const orig = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Moving...';

    try {
        const res = await fetch(MOVE_API, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
            body: JSON.stringify({
                student_lrn: studentId,
                to_program_code: programCode,
                to_section_id: parseInt(sectionId),
                reason
            })
        });

        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Move failed');

        showNotification(`Student successfully moved to ${data.program_name} — ${data.section_name}`, 'success');
        closeAdminMoveModal();

        // Refresh placement display
        set('displayProgram', data.program_name);
        set('displaySection', data.section_name);
        set('displayStatus',  'Approved');

    } catch (err) {
        showNotification('Error: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
    }
}

// ── Utilities ─────────────────────────────────────────────
function showLoading(show) {
    let el = document.getElementById('loadingOverlay');
    if (show && !el) {
        el = document.createElement('div');
        el.id = 'loadingOverlay';
        el.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        el.innerHTML = `<div class="bg-white rounded-2xl p-8 shadow-2xl text-center">
            <i class="fas fa-spinner fa-spin text-4xl text-red-600 mb-4 block"></i>
            <p class="text-gray-700 font-semibold">Loading student data...</p>
        </div>`;
        document.body.appendChild(el);
    } else if (!show && el) {
        el.remove();
    }
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;
    const colors = { success:'border-green-500', error:'border-red-500', warning:'border-yellow-500', info:'border-blue-500' };
    const icons  = { success:'fa-check-circle text-green-500', error:'fa-exclamation-circle text-red-500', warning:'fa-exclamation-triangle text-yellow-500', info:'fa-info-circle text-blue-500' };
    const n = document.createElement('div');
    n.className = `bg-white border-l-4 ${colors[type]} rounded-lg shadow-lg p-4 max-w-sm notif-slide`;
    n.innerHTML = `<div class="flex items-start gap-3">
        <i class="fas ${icons[type]} mt-1 flex-shrink-0"></i>
        <div class="flex-1"><p class="text-sm font-medium text-gray-800">${message}</p></div>
        <button onclick="this.parentElement.parentElement.remove()" class="text-gray-400 hover:text-gray-600"><i class="fas fa-times"></i></button>
    </div>`;
    container.appendChild(n);
    setTimeout(() => { if (n.parentElement) n.remove(); }, 5000);
}

// Expose to HTML inline handlers
window.toggleEditMode     = toggleEditMode;
window.saveAllChanges     = saveAllChanges;
window.onInlineProgramChange = onInlineProgramChange;
window.confirmInlineMove     = confirmInlineMove;
// Keep old modal functions in case modal HTML is still present
window.openAdminMoveModal    = openAdminMoveModal;
window.closeAdminMoveModal   = closeAdminMoveModal;
window.onMoveProgramChange   = onMoveProgramChange;
window.confirmAdminMove      = confirmAdminMove;
window.showNotification    = showNotification;