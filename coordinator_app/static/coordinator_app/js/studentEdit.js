// Get student ID from URL or data attribute
const getStudentId = () => {
    const pathMatch = window.location.pathname.match(/\/student-edit\/([^\/]+)\/?/);
    if (pathMatch && pathMatch[1]) {
        return pathMatch[1];
    }
    
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id') || document.querySelector('[data-student-id]')?.dataset.studentId;
};

// API base URL from Django template
const API_BASE = window.STUDENT_API_BASE || '/coordinator/api/student/';

// Track if any changes were made
let hasUnsavedChanges = false;

document.addEventListener('DOMContentLoaded', async function () {
    const studentId = getStudentId();
    
    if (!studentId) {
        showNotification('Student ID not found', 'error');
        return;
    }

    // Initialize
    initializeAccordions();
    setupFormInteractions();
    
    // Load student data
    await loadStudentData(studentId);
    
    // Setup form submission handlers
    setupFormSubmission(studentId);
    
    // Track changes for unsaved changes warning
    setupChangeTracking();
    
    // Warn before leaving with unsaved changes
    window.addEventListener('beforeunload', function (e) {
        if (hasUnsavedChanges) {
            e.preventDefault();
            e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
            return e.returnValue;
        }
    });
});

// Setup change tracking
function setupChangeTracking() {
    const form = document.querySelector('form');
    if (!form) return;
    
    // Track changes on all form inputs
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('change', function() {
            hasUnsavedChanges = true;
        });
    });
}

// Load all student data from API
async function loadStudentData(studentId) {
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE}${studentId}/details/`);
        
        if (!response.ok) throw new Error('Failed to load student data');
        
        const result = await response.json();
        
        if (!result.success) throw new Error(result.error || 'Unknown error');
        
        const data = result.data;
        
        console.log('Loaded student data:', data);
        
        // Populate all form sections
        populateStudentBasicInfo(data);
        populateStudentData(data.student_data, data.student);
        populateFamilyData(data.father, data.mother, data.guardian);
        populateSurveyData(data.survey_data);
        populateAcademicData(data.academic_data);
        populateProgramSelection(data.program_selection);
        
        // Mark as no unsaved changes after initial load
        hasUnsavedChanges = false;
        
        showLoading(false);
        showNotification('Student data loaded successfully', 'success');
        
    } catch (error) {
        console.error('Error loading student data:', error);
        showLoading(false);
        showNotification('Failed to load student data: ' + error.message, 'error');
    }
}

// Populate basic student info in header
function populateStudentBasicInfo(data) {
    const student = data.student;
    const studentData = data.student_data;
    
    if (studentData) {
        const headerName = document.getElementById('studentHeaderName');
        if (headerName) {
            headerName.textContent = `${studentData.last_name}, ${studentData.first_name} ${studentData.middle_name || ''}`.trim();
        }
        
        const lrnDisplay = document.getElementById('studentHeaderLrn');
        if (lrnDisplay) {
            lrnDisplay.innerHTML = `<i class="fas fa-hashtag mr-2"></i>LRN: ${student.lrn}`;
        }
    }
    
    const dateAdded = document.getElementById('studentHeaderDate');
    if (dateAdded) {
        const date = new Date(student.created_at).toLocaleDateString('en-US', { 
            year: 'numeric', month: 'short', day: 'numeric' 
        });
        dateAdded.innerHTML = `<i class="fas fa-calendar-alt mr-2"></i>Date Added: ${date}`;
    }
    
    updateStatusBadge(student.enrollment_status);
}

// Populate student information accordion
function populateStudentData(data, studentObj) {
    if (!data) return;
    
    const setValue = (selector, value) => {
        const el = document.querySelector(selector);
        if (el) el.value = value || '';
    };
    
    const studentLrnField = document.getElementById('studentLrn');
    if (studentLrnField && studentObj) {
        studentLrnField.value = studentObj.lrn;
    }
    
    setValue('#firstName', data.first_name);
    setValue('#middleName', data.middle_name);
    setValue('#lastName', data.last_name);
    setValue('#age', data.age);
    setValue('#dateOfBirth', data.date_of_birth);
    setValue('#placeOfBirth', data.place_of_birth);
    setValue('#gender', data.gender);
    setValue('#address', data.address);
    setValue('#religion', data.religion);
    setValue('#dialectSpoken', data.dialect_spoken);
    setValue('#ethnicTribe', data.ethnic_tribe);
    setValue('#lastSchoolAttended', data.last_school_attended);
    setValue('#previousGradeSection', data.previous_grade_section);
    setValue('#lastSchoolYear', data.last_school_year);
    
    const spedRadio = data.is_sped ? 
        document.querySelector('input[name="is_sped"][value="yes"]') :
        document.querySelector('input[name="is_sped"][value="no"]');
    if (spedRadio) spedRadio.checked = true;
    
    const spedDetails = document.querySelector('textarea[placeholder="If yes, please specify"]');
    if (spedDetails) {
        spedDetails.value = data.sped_details || '';
        spedDetails.disabled = !data.is_sped;
    }
    
    const workingRadio = data.is_working_student ?
        document.querySelector('input[name="is_working"][value="yes"]') :
        document.querySelector('input[name="is_working"][value="no"]');
    if (workingRadio) workingRadio.checked = true;
    
    const workingDetails = document.querySelectorAll('textarea[placeholder="If yes, please specify"]')[1];
    if (workingDetails) {
        workingDetails.value = data.working_details || '';
        workingDetails.disabled = !data.is_working_student;
    }
}

// Populate family data accordion
function populateFamilyData(father, mother, guardian) {
    const setValue = (selector, value) => {
        const el = document.querySelector(selector);
        if (el && value !== undefined && value !== null) {
            if (el.tagName === 'SELECT') {
                el.value = value;
            } else if (el.type === 'checkbox' || el.type === 'radio') {
                el.checked = value;
            } else {
                el.value = value;
            }
        }
    };
    
    if (father) {
        setValue('#fatherFamilyName', father.family_name);
        setValue('#fatherFirstName', father.first_name);
        setValue('#fatherMiddleName', father.middle_name);
        setValue('#fatherAge', father.age);
        setValue('#fatherOccupation', father.occupation);
        setValue('#fatherDateOfBirth', father.date_of_birth);
        setValue('#fatherContactNumber', father.contact_number);
        setValue('#fatherEmail', father.email);
    }
    
    if (mother) {
        setValue('#motherFamilyName', mother.family_name);
        setValue('#motherFirstName', mother.first_name);
        setValue('#motherMiddleName', mother.middle_name);
        setValue('#motherAge', mother.age);
        setValue('#motherOccupation', mother.occupation);
        setValue('#motherDateOfBirth', mother.date_of_birth);
        setValue('#motherContactNumber', mother.contact_number);
        setValue('#motherEmail', mother.email);
    }
    
    if (guardian && guardian.other_guardian) {
        const g = guardian.other_guardian;
        setValue('#guardianFamilyName', g.family_name);
        setValue('#guardianFirstName', g.first_name);
        setValue('#guardianMiddleName', g.middle_name);
        setValue('#guardianAge', g.age);
        setValue('#guardianOccupation', g.occupation);
        setValue('#guardianDateOfBirth', g.date_of_birth);
        setValue('#guardianAddress', g.address);
        setValue('#guardianRelationship', g.relationship_to_student);
        setValue('#guardianContactNumber', g.contact_number);
        setValue('#guardianEmail', g.email);
    }
}

// Populate survey/non-academic data
function populateSurveyData(data) {
    if (!data) return;
    
    const setValue = (selector, value) => {
        const el = document.querySelector(selector);
        if (el && value !== undefined && value !== null) {
            if (Array.isArray(value)) {
                el.value = value.join(', ');
            } else {
                el.value = value;
            }
        }
    };
    
    setValue('#learningStyle', data.learning_style);
    setValue('#studyHours', data.study_hours);
    setValue('#studyEnvironment', data.study_environment);
    setValue('#schoolworkSupport', data.schoolwork_support);
    setValue('#enjoyedSubjects', data.enjoyed_subjects);
    setValue('#interestedProgram', data.interested_program);
    setValue('#programMotivation', data.program_motivation);
    setValue('#enjoyedActivities', data.enjoyed_activities);
    setValue('#enjoyedActivitiesOther', data.enjoyed_activities_other);
    setValue('#assignmentsOnTime', data.assignments_on_time);
    setValue('#handleDifficultLessons', data.handle_difficult_lessons);
    setValue('#deviceAvailability', data.device_availability);
    setValue('#internetAccess', data.internet_access);
    setValue('#absences', data.absences);
    setValue('#absenceReason', data.absence_reason);
    setValue('#participation', data.participation);
    setValue('#difficultyAreas', data.difficulty_areas);
    setValue('#extraSupport', data.extra_support);
    setValue('#quietPlace', data.quiet_place);
    setValue('#distanceFromSchool', data.distance_from_school);
    setValue('#travelDifficulty', data.travel_difficulty);
}

// Populate academic data accordion
function populateAcademicData(data) {
    if (!data) return;
    
    const setValue = (selector, value) => {
        const el = document.querySelector(selector);
        if (el && value !== undefined && value !== null) {
            if (el.tagName === 'SELECT') {
                el.value = value;
            } else if (el.type === 'checkbox' || el.type === 'radio') {
                el.checked = value;
            } else {
                el.value = value;
            }
        }
    };
    
    const academicLrn = document.getElementById('academicLrn');
    if (academicLrn) {
        const studentLrnField = document.getElementById('studentLrn');
        if (studentLrnField) {
            academicLrn.value = studentLrnField.value;
        }
    }
    
    setValue('#gradeMathematics', data.mathematics);
    setValue('#gradeAralingPanlipunan', data.araling_panlipunan);
    setValue('#gradeEnglish', data.english);
    setValue('#gradeEdukasyonSaPagpapakatao', data.edukasyon_sa_pagpapakatao);
    setValue('#gradeScience', data.science);
    setValue('#gradeEdukasyonPangkabuhayan', data.edukasyon_pangkabuhayan);
    setValue('#gradeFilipino', data.filipino);
    setValue('#gradeMapeh', data.mapeh);
    
    const averageInput = document.getElementById('overallAverage');
    if (averageInput && data.overall_average) {
        averageInput.value = data.overall_average.toFixed(2);
    }
    
    setValue('#dostExamResult', data.dost_exam_result);
}

// Populate program selection
async function populateProgramSelection(data) {
    if (!data) return;
    
    const setValue = (selector, value) => {
        const el = document.querySelector(selector);
        if (el && value !== undefined && value !== null) {
            if (el.tagName === 'SELECT') {
                el.value = value;
            } else if (el.type === 'checkbox' || el.type === 'radio') {
                el.checked = value;
            } else {
                el.value = value;
            }
        }
    };
    
    const programSelect = document.getElementById('placementProgram');
    if (programSelect && data.selected_program_code) {
        programSelect.value = data.selected_program_code;
        
        await loadSectionsByProgram(data.selected_program_code);
        
        if (data.assigned_section) {
            const sectionSelect = document.getElementById('placementSection');
            if (sectionSelect) {
                sectionSelect.value = data.assigned_section;
            }
        }
    }
    
    const approvalSelect = document.getElementById('placementAdminApproved');
    if (approvalSelect) {
        approvalSelect.value = data.admin_approved ? 'true' : 'false';
    }
    
    setValue('#placementAdminNotes', data.admin_notes);
    
    console.log('Program selection populated:', data);
}

// Load sections by program
async function loadSectionsByProgram(programCode) {
    if (!programCode) {
        const sectionSelect = document.getElementById('placementSection');
        if (sectionSelect) {
            sectionSelect.innerHTML = '<option value="">Select program first</option>';
            sectionSelect.disabled = true;
        }
        return;
    }
    
    try {
        const response = await fetch(`/coordinator/api/sections/?program=${programCode}`);
        
        if (!response.ok) {
            throw new Error('Failed to load sections');
        }
        
        const result = await response.json();
        updateSectionDropdown(result.sections);
        
    } catch (error) {
        console.error('Error loading sections:', error);
        const sectionSelect = document.getElementById('placementSection');
        if (sectionSelect) {
            sectionSelect.innerHTML = '<option value="">Error loading sections</option>';
            sectionSelect.disabled = true;
        }
    }
}

// Update section dropdown with sections data
function updateSectionDropdown(sections) {
    const sectionSelect = document.getElementById('placementSection');
    if (!sectionSelect) return;
    
    sectionSelect.innerHTML = '<option value="">Select Section</option>';
    
    if (sections && sections.length > 0) {
        sections.forEach(section => {
            const option = document.createElement('option');
            option.value = section.id;
            let displayText = section.name;
            if (section.adviser_name) {
                displayText += ` - ${section.adviser_name}`;
            }
            displayText += ` (${section.current_students}/${section.max_students})`;
            
            // Disable if section is full
            if (section.current_students >= section.max_students) {
                option.disabled = true;
                displayText += ' - FULL';
            }
            
            option.textContent = displayText;
            sectionSelect.appendChild(option);
        });
        sectionSelect.disabled = false;
    } else {
        sectionSelect.innerHTML = '<option value="">No sections available for this program</option>';
        sectionSelect.disabled = false;
    }
}

// Update status badge
function updateStatusBadge(status) {
    const statusBadge = document.getElementById('studentHeaderStatus');
    if (!statusBadge) return;
    
    const statusMap = {
        'draft': { bg: 'bg-gray-100', text: 'text-gray-800', icon: 'fa-file', label: 'Draft' },
        'submitted': { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: 'fa-clock', label: 'Pending Review' },
        'under_review': { bg: 'bg-blue-100', text: 'text-blue-800', icon: 'fa-eye', label: 'Under Review' },
        'approved': { bg: 'bg-green-100', text: 'text-green-800', icon: 'fa-check-circle', label: 'Approved' },
        'rejected': { bg: 'bg-red-100', text: 'text-red-800', icon: 'fa-times-circle', label: 'Rejected' },
    };
    
    const config = statusMap[status] || statusMap['draft'];
    
    statusBadge.className = `${config.bg} ${config.text} px-4 py-2 rounded-full text-sm font-semibold inline-flex items-center gap-2`;
    statusBadge.innerHTML = `<i class="fas ${config.icon}"></i> ${config.label}`;
}

// Setup form submission - THE KEY FUNCTION
function setupFormSubmission(studentId) {
    const form = document.querySelector('form');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get approval status
        const approvalSelect = document.getElementById('placementAdminApproved');
        const isApproved = approvalSelect && approvalSelect.value === 'true';
        const sectionSelect = document.getElementById('placementSection');
        const selectedSection = sectionSelect ? sectionSelect.value : '';
        
        // Validation: If approving, section must be selected
        if (isApproved && !selectedSection) {
            showNotification('Please select a section before approving the enrollment', 'error');
            return;
        }
        
        // Check for missing requirements if approving
        if (isApproved) {
            const studentName = document.getElementById('studentHeaderName')?.textContent || 'Unknown';
            const missingRequirements = checkMissingRequirements(studentName);
            
            if (missingRequirements.length > 0) {
                // Show modal with missing requirements
                showMissingRequirementsModal(missingRequirements, studentName);
                
                // Store approval data for "Approve Anyway" button
                const sectionName = sectionSelect.options[sectionSelect.selectedIndex].text;
                const adminNotes = document.getElementById('placementAdminNotes')?.value || '';
                
                pendingApprovalData = {
                    studentId: studentId,
                    sectionId: selectedSection,
                    sectionName: sectionName,
                    adminNotes: adminNotes
                };
                
                return; // Stop here - user must click "Approve Anyway" to continue
            }
        }
        
        // Confirm approval action (if all requirements met)
        if (isApproved) {
            const sectionName = sectionSelect.options[sectionSelect.selectedIndex].text;
            const confirmApprove = confirm(
                `You are about to APPROVE this enrollment and place the student in:\n\n${sectionName}\n\nThis will:\n- Update enrollment status to "Approved"\n- Assign student to selected section\n- Update section capacity\n\nDo you want to proceed?`
            );
            
            if (!confirmApprove) {
                return;
            }
        }
        
        // Show loading
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
        submitBtn.disabled = true;
        
        try {
            // Collect form data
            const formData = collectFormData();
            
            // Send updates to respective endpoints
            await updateAllSections(studentId, formData);
            
            // If approved, trigger section placement
            if (isApproved && selectedSection) {
                await approveAndPlaceStudent(studentId, selectedSection, formData.program_selection.admin_notes || '');
            }
            
            hasUnsavedChanges = false;
            showNotification('All changes saved successfully!', 'success');
            
            // Redirect based on action
            setTimeout(() => {
                if (isApproved) {
                    // Redirect to section management to confirm placement
                    window.location.href = '/coordinator/section-management/';
                } else {
                    // Stay on page or go back to section assignment
                    window.location.href = '/coordinator/section-assignment/';
                }
            }, 1500);
            
        } catch (error) {
            console.error('Error saving:', error);
            showNotification('Failed to save changes: ' + error.message, 'error');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });
}

// Approve enrollment and place student in section
async function approveAndPlaceStudent(studentId, sectionId, adminNotes) {
    try {
        const response = await fetch(`${API_BASE}${studentId}/approve-and-place/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                section_id: sectionId,
                admin_notes: adminNotes
            })
        });
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to approve and place student');
        }
        
        console.log('Student approved and placed successfully:', result);
        return result;
        
    } catch (error) {
        console.error('Error approving and placing student:', error);
        throw error;
    }
}

// Collect form data from all sections
function collectFormData() {
    const formData = {
        student_data: {},
        family_data: {},
        survey_data: {},
        academic_data: {},
        program_selection: {}
    };
    
    // Helper to collect field values
    const collectFields = (selector) => {
        const data = {};
        const inputs = document.querySelectorAll(selector);
        inputs.forEach(input => {
            if (input.name && input.value !== '') {
                // Handle checkboxes and radios
                if (input.type === 'checkbox' || input.type === 'radio') {
                    if (input.checked) {
                        data[input.name] = input.value;
                    }
                } else {
                    data[input.name] = input.value;
                }
            }
        });
        return data;
    };
    
    // Collect from each accordion section
    // Since we don't have data-section attributes in HTML, collect by form structure
    
    // Student Data fields
    const studentFields = [
        'first_name', 'middle_name', 'last_name', 'age', 'date_of_birth',
        'place_of_birth', 'gender', 'address', 'religion', 'dialect_spoken',
        'ethnic_tribe', 'last_school_attended', 'previous_grade_section',
        'last_school_year', 'is_sped', 'sped_details', 'is_working', 'working_details'
    ];
    
    studentFields.forEach(field => {
        const input = document.querySelector(`[name="${field}"]`);
        if (input && input.value) {
            formData.student_data[field] = input.value;
        }
    });
    
    // Family Data fields
    const familyFields = [
        'father_family_name', 'father_first_name', 'father_middle_name', 'father_age',
        'father_occupation', 'father_date_of_birth', 'father_contact_number', 'father_email',
        'mother_family_name', 'mother_first_name', 'mother_middle_name', 'mother_age',
        'mother_occupation', 'mother_date_of_birth', 'mother_contact_number', 'mother_email',
        'guardian_family_name', 'guardian_first_name', 'guardian_middle_name', 'guardian_age',
        'guardian_occupation', 'guardian_date_of_birth', 'guardian_address',
        'guardian_relationship', 'guardian_contact_number', 'guardian_email'
    ];
    
    familyFields.forEach(field => {
        const input = document.querySelector(`[name="${field}"]`);
        if (input && input.value) {
            formData.family_data[field] = input.value;
        }
    });
    
    // Academic Data fields
    const academicFields = [
        'dost_exam_result', 'grade_mathematics', 'grade_araling_panlipunan',
        'grade_english', 'grade_edukasyon_sa_pagpapakatao', 'grade_science',
        'grade_edukasyon_pangkabuhayan', 'grade_filipino', 'grade_mapeh'
    ];
    
    academicFields.forEach(field => {
        const input = document.querySelector(`[name="${field}"]`);
        if (input && input.value) {
            formData.academic_data[field] = input.value;
        }
    });
    
    // Program Selection fields
    const programSelect = document.getElementById('placementProgram');
    const sectionSelect = document.getElementById('placementSection');
    const approvalSelect = document.getElementById('placementAdminApproved');
    const notesField = document.getElementById('placementAdminNotes');
    
    if (programSelect && programSelect.value) {
        formData.program_selection.selected_program_code = programSelect.value;
    }
    if (sectionSelect && sectionSelect.value) {
        formData.program_selection.assigned_section = sectionSelect.value;
    }
    if (approvalSelect) {
        formData.program_selection.admin_approved = approvalSelect.value === 'true';
    }
    if (notesField) {
        formData.program_selection.admin_notes = notesField.value;
    }
    
    return formData;
}

// Update all sections via API
async function updateAllSections(studentId, formData) {
    const updatePromises = [];
    
    // Update student data
    if (Object.keys(formData.student_data).length > 0) {
        updatePromises.push(
            fetch(`${API_BASE}${studentId}/update/student-data/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(formData.student_data)
            }).then(response => {
                if (!response.ok) throw new Error(`Student data update failed: ${response.status}`);
                return response.json();
            })
        );
    }
    
    // Update family data
    if (Object.keys(formData.family_data).length > 0) {
        updatePromises.push(
            fetch(`${API_BASE}${studentId}/update/family-data/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(formData.family_data)
            }).then(response => {
                if (!response.ok) throw new Error(`Family data update failed: ${response.status}`);
                return response.json();
            })
        );
    }
    
    // Update academic data
    if (Object.keys(formData.academic_data).length > 0) {
        updatePromises.push(
            fetch(`${API_BASE}${studentId}/update/academic-data/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(formData.academic_data)
            }).then(response => {
                if (!response.ok) throw new Error(`Academic data update failed: ${response.status}`);
                return response.json();
            })
        );
    }
    
    // Update program selection (without triggering placement)
    if (Object.keys(formData.program_selection).length > 0) {
        updatePromises.push(
            fetch(`${API_BASE}${studentId}/update/program-selection/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(formData.program_selection)
            }).then(response => {
                if (!response.ok) throw new Error(`Program selection update failed: ${response.status}`);
                return response.json();
            })
        );
    }
    
    if (updatePromises.length === 0) {
        console.log('No changes to save');
        return;
    }
    
    const results = await Promise.all(updatePromises);
    
    for (const result of results) {
        if (!result.success) {
            throw new Error(result.error || 'Unknown error occurred during update');
        }
    }
}

// Show/hide loading overlay
function showLoading(show) {
    let overlay = document.getElementById('loadingOverlay');
    
    if (show && !overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        overlay.innerHTML = `
            <div class="bg-white rounded-2xl p-8 shadow-2xl">
                <i class="fas fa-spinner fa-spin text-4xl text-primary mb-4"></i>
                <p class="text-gray-700 font-semibold">Loading student data...</p>
            </div>
        `;
        document.body.appendChild(overlay);
    } else if (!show && overlay) {
        overlay.remove();
    }
}

// Accordion and form interaction functions
function initializeAccordions() {
    const firstAccordion = document.querySelector('.accordion-content');
    if (firstAccordion) {
        firstAccordion.classList.add('expanded');
        const firstChevron = document.querySelector('.accordion-header i.fa-chevron-down');
        if (firstChevron) firstChevron.classList.add('rotate-180');
    }
}

function toggleAccordion(button) {
    const content = button.nextElementSibling;
    const chevron = button.querySelector('i.fa-chevron-down');
    
    content.classList.toggle('expanded');
    chevron.classList.toggle('rotate-180');
    
    if (content.classList.contains('expanded')) {
        setTimeout(() => {
            button.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }, 100);
    }
}

function setupFormInteractions() {
    // SPED toggle
    const spedRadios = document.querySelectorAll('input[name="is_sped"]');
    const spedDetails = document.querySelector('textarea[placeholder="If yes, please specify"]');
    
    spedRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (spedDetails) {
                spedDetails.disabled = this.value === 'no';
                if (this.value === 'no') spedDetails.value = '';
            }
        });
    });
    
    // Working student toggle
    const workingRadios = document.querySelectorAll('input[name="is_working"]');
    const workingDetails = document.querySelectorAll('textarea[placeholder="If yes, please specify"]')[1];
    
    workingRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            if (workingDetails) {
                workingDetails.disabled = this.value === 'no';
                if (this.value === 'no') workingDetails.value = '';
            }
        });
    });
    
    // Calculate overall average
    const gradeInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    const averageInput = document.getElementById('overallAverage');
    
    gradeInputs.forEach(input => {
        input.addEventListener('input', () => {
            let sum = 0, count = 0;
            gradeInputs.forEach(inp => {
                const val = parseFloat(inp.value);
                if (!isNaN(val) && inp.value !== '') {
                    sum += val;
                    count++;
                }
            });
            if (count > 0 && averageInput) {
                averageInput.value = (sum / count).toFixed(2);
            }
        });
    });
    
    // Program change event - load sections dynamically
    const programSelect = document.getElementById('placementProgram');
    if (programSelect) {
        programSelect.addEventListener('change', async function() {
            const programCode = this.value;
            await loadSectionsByProgram(programCode);
        });
    }
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;
    
    const notification = document.createElement('div');
    const colors = {
        success: 'border-green-500',
        error: 'border-red-500',
        warning: 'border-yellow-500',
        info: 'border-blue-500'
    };
    const icons = {
        success: 'fa-check-circle text-green-500',
        error: 'fa-exclamation-circle text-red-500',
        warning: 'fa-exclamation-triangle text-yellow-500',
        info: 'fa-info-circle text-blue-500'
    };
    
    notification.className = `bg-white border-l-4 ${colors[type]} rounded-lg shadow-lg p-4 max-w-md animate-slide-in-right`;
    notification.innerHTML = `
        <div class="flex items-start gap-3">
            <i class="fas ${icons[type]} mt-1"></i>
            <div class="flex-1">
                <p class="text-sm font-medium text-gray-800">${message}</p>
            </div>
            <button class="text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentElement) notification.remove();
    }, 5000);
}

// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Check for missing mandatory document requirements
function checkMissingRequirements(studentName) {
    const missingRequirements = [];
    
    // Get all requirement checkboxes
    const requirementCheckboxes = document.querySelectorAll('.requirement-checkbox');
    
    requirementCheckboxes.forEach(checkbox => {
        const requirementId = checkbox.dataset.requirementId;
        const label = document.querySelector(`label[for="req_${requirementId}"]`);
        
        if (label) {
            const requirementName = label.textContent.trim().replace(/\s*\*\s*$/, '').replace(/\s*\(Optional\)\s*$/, '');
            
            // Check if it's mandatory (has asterisk or is not optional)
            const isMandatory = !label.textContent.includes('(Optional)');
            
            // Check if it's not checked/approved
            const isApproved = checkbox.checked && checkbox.disabled;
            
            if (isMandatory && !isApproved) {
                missingRequirements.push(requirementName);
            }
        }
    });
    
    return missingRequirements;
}

// Display missing requirements modal
function showMissingRequirementsModal(missingRequirements, studentName) {
    const modal = document.getElementById('missingRequirementsModal');
    const studentNameDisplay = document.getElementById('studentNameDisplay');
    const missingList = document.getElementById('missingRequirementsList');
    
    if (!modal || !studentNameDisplay || !missingList) {
        console.error('Missing requirements modal elements not found');
        return;
    }
    
    // Set student name
    studentNameDisplay.textContent = `Student: ${studentName}`;
    
    // Clear and populate missing requirements list
    missingList.innerHTML = '';
    missingRequirements.forEach(requirement => {
        const item = document.createElement('div');
        item.className = 'flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg';
        item.innerHTML = `
            <i class="fas fa-times-circle text-red-500 mt-1 flex-shrink-0"></i>
            <span class="text-gray-700">${requirement}</span>
        `;
        missingList.appendChild(item);
    });
    
    // Show modal
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

// Close missing requirements modal
function closeMissingRequirementsModal() {
    const modal = document.getElementById('missingRequirementsModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

// Store state for approve anyway button
let pendingApprovalData = null;

// Approve anyway - proceed with approval despite missing requirements
async function approveAnywayConfirm() {
    closeMissingRequirementsModal();
    
    if (pendingApprovalData) {
        try {
            await proceedWithApproval(pendingApprovalData);
        } catch (error) {
            console.error('Error during approval:', error);
            showNotification('Failed to approve enrollment: ' + error.message, 'error');
        }
    }
}

// Proceed with the actual approval
async function proceedWithApproval(approvalData) {
    const { studentId, sectionId, sectionName, adminNotes } = approvalData;
    const submitBtn = document.querySelector('form button[type="submit"]');
    
    if (submitBtn) {
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
        submitBtn.disabled = true;
    }
    
    try {
        // Call approval API
        const response = await fetch(`${API_BASE}${studentId}/approve-and-place/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                section_id: sectionId,
                admin_notes: adminNotes
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Approval failed');
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Approval failed');
        }
        
        hasUnsavedChanges = false;
        showNotification('Student approved and placed in ' + sectionName, 'success');
        
        // Redirect to section management
        setTimeout(() => {
            window.location.href = '/coordinator/section-management/';
        }, 1500);
        
    } catch (error) {
        console.error('Error approving student:', error);
        showNotification('Failed to approve student: ' + error.message, 'error');
        
        if (submitBtn) {
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-check-circle mr-2"></i>Save Changes';
            submitBtn.disabled = false;
        }
    }
}

// Make functions globally available
window.toggleAccordion = toggleAccordion;
window.showNotification = showNotification;
window.closeMissingRequirementsModal = closeMissingRequirementsModal;
window.approveAnywayConfirm = approveAnywayConfirm;