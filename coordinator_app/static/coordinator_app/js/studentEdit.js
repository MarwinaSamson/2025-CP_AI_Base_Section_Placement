// Get student ID from URL or data attribute
const getStudentId = () => {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('id') || document.querySelector('[data-student-id]')?.dataset.studentId;
};

// API base URL from Django template
const API_BASE = window.STUDENT_API_BASE || '/admin/api/student/';

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
});

// Load all student data from API
async function loadStudentData(studentId) {
    try {
        showLoading(true);
        
        const response = await fetch(`${API_BASE}${studentId}/details/`);
        
        if (!response.ok) throw new Error('Failed to load student data');
        
        const result = await response.json();
        
        if (!result.success) throw new Error(result.error || 'Unknown error');
        
        const data = result.data;
        
        // Debug: Log the received data
        console.log('Loaded student data:', data);
        console.log('Student data:', data.student_data);
        console.log('Father data:', data.father);
        console.log('Mother data:', data.mother);
        console.log('Guardian data:', data.guardian);
        console.log('Academic data:', data.academic_data);
        
        // Populate all form sections
        populateStudentBasicInfo(data);
        populateStudentData(data.student_data, data.student);  // Pass both student_data and student
        populateFamilyData(data.father, data.mother, data.guardian);
        populateSurveyData(data.survey_data);
        populateAcademicData(data.academic_data);
        populateProgramSelection(data.program_selection);
        
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
        // Update header with student name
        const headerName = document.getElementById('studentHeaderName');
        if (headerName) {
            headerName.textContent = `${studentData.last_name}, ${studentData.first_name} ${studentData.middle_name || ''}`.trim();
        }
        
        // Update LRN display
        const lrnDisplay = document.getElementById('studentHeaderLrn');
        if (lrnDisplay) {
            lrnDisplay.innerHTML = `<i class="fas fa-hashtag mr-2"></i>LRN: ${student.lrn}`;
        }
    }
    
    // Update date added
    const dateAdded = document.getElementById('studentHeaderDate');
    if (dateAdded) {
        const date = new Date(student.created_at).toLocaleDateString('en-US', { 
            year: 'numeric', month: 'short', day: 'numeric' 
        });
        dateAdded.innerHTML = `<i class="fas fa-calendar-alt mr-2"></i>Date Added: ${date}`;
    }
    
    // Update status badge
    updateStatusBadge(student.enrollment_status);
}

// Populate student information accordion
function populateStudentData(data, studentObj) {
    if (!data) return;
    
    // Helper to safely set value
    const setValue = (selector, value) => {
        const el = document.querySelector(selector);
        if (el) el.value = value || '';
    };
    
    // Set LRN input field (from student object, not student_data)
    const studentLrnField = document.getElementById('studentLrn');
    if (studentLrnField && studentObj) {
        studentLrnField.value = studentObj.lrn;
    }
    
    // Basic information using IDs
    setValue('#firstName', data.first_name);
    setValue('#middleName', data.middle_name);
    setValue('#lastName', data.last_name);
    setValue('#age', data.age);
    setValue('#dateOfBirth', data.date_of_birth);
    setValue('#placeOfBirth', data.place_of_birth);
    
    // Gender select
    setValue('#gender', data.gender);
    
    // Address textarea
    setValue('#address', data.address);
    
    // Other fields using IDs
    setValue('#religion', data.religion);
    setValue('#dialectSpoken', data.dialect_spoken);
    setValue('#ethnicTribe', data.ethnic_tribe);
    setValue('#lastSchoolAttended', data.last_school_attended);
    setValue('#previousGradeSection', data.previous_grade_section);
    setValue('#lastSchoolYear', data.last_school_year);
    
    // SPED radio buttons
    const spedRadio = data.is_sped ? 
        document.querySelector('input[name="is_sped"][value="yes"]') :
        document.querySelector('input[name="is_sped"][value="no"]');
    if (spedRadio) spedRadio.checked = true;
    
    const spedDetails = document.querySelector('textarea[placeholder="If yes, please specify"]');
    if (spedDetails) {
        spedDetails.value = data.sped_details;
        spedDetails.disabled = !data.is_sped;
    }
    
    // Working student radio buttons
    const workingRadio = data.is_working_student ?
        document.querySelector('input[name="is_working"][value="yes"]') :
        document.querySelector('input[name="is_working"][value="no"]');
    if (workingRadio) workingRadio.checked = true;
    
    const workingDetails = document.querySelectorAll('textarea[placeholder="If yes, please specify"]')[1];
    if (workingDetails) {
        workingDetails.value = data.working_details;
        workingDetails.disabled = !data.is_working_student;
    }
}

// Populate family data accordion
function populateFamilyData(father, mother, guardian) {
    // Helper to safely set value
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
    
    // Populate father's data
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
    
    // Populate mother's data
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
    
    // Populate guardian's data if exists
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
    
    // Helper to safely set value
    const setValue = (selector, value) => {
        const el = document.querySelector(selector);
        if (el && value !== undefined && value !== null) {
            // For arrays, join them with commas
            if (Array.isArray(value)) {
                el.value = value.join(', ');
            } else {
                el.value = value;
            }
        }
    };
    
    // Section B - Student Profile
    setValue('#learningStyle', data.learning_style);
    setValue('#studyHours', data.study_hours);
    setValue('#studyEnvironment', data.study_environment);
    setValue('#schoolworkSupport', data.schoolwork_support);
    
    // Section C - Interests & Motivation
    setValue('#enjoyedSubjects', data.enjoyed_subjects);
    setValue('#interestedProgram', data.interested_program);
    setValue('#programMotivation', data.program_motivation);
    setValue('#enjoyedActivities', data.enjoyed_activities);
    setValue('#enjoyedActivitiesOther', data.enjoyed_activities_other);
    
    // Section D - Behavioral & Study Habits
    setValue('#assignmentsOnTime', data.assignments_on_time);
    setValue('#handleDifficultLessons', data.handle_difficult_lessons);
    
    // Section E - Technology Access
    setValue('#deviceAvailability', data.device_availability);
    setValue('#internetAccess', data.internet_access);
    
    // Section F - Attendance & Responsibility
    setValue('#absences', data.absences);
    setValue('#absenceReason', data.absence_reason);
    setValue('#participation', data.participation);
    
    // Section G - Learning Support & Special Needs
    setValue('#difficultyAreas', data.difficulty_areas);
    setValue('#extraSupport', data.extra_support);
    
    // Section H - Environmental Factors
    setValue('#quietPlace', data.quiet_place);
    setValue('#distanceFromSchool', data.distance_from_school);
    setValue('#travelDifficulty', data.travel_difficulty);
    
    console.log('Survey data populated successfully');
}

// Populate academic data accordion
function populateAcademicData(data) {
    if (!data) return;
    
    // Helper to safely set value
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
    
    // Set LRN in academic section (should match student data LRN from the input field)
    const academicLrn = document.getElementById('academicLrn');
    if (academicLrn) {
        // Get LRN from the student data input field
        const studentLrnField = document.getElementById('studentLrn');
        if (studentLrnField) {
            academicLrn.value = studentLrnField.value;
        }
    }
    
    // Set all grades using IDs - data is academic_data object
    setValue('#gradeMathematics', data.mathematics);
    setValue('#gradeAralingPanlipunan', data.araling_panlipunan);
    setValue('#gradeEnglish', data.english);
    setValue('#gradeEdukasyonSaPagpapakatao', data.edukasyon_sa_pagpapakatao);
    setValue('#gradeScience', data.science);
    setValue('#gradeEdukasyonPangkabuhayan', data.edukasyon_pangkabuhayan);
    setValue('#gradeFilipino', data.filipino);
    setValue('#gradeMapeh', data.mapeh);
    
    // Update overall average
    const averageInput = document.getElementById('overallAverage');
    if (averageInput && data.overall_average) {
        averageInput.value = data.overall_average.toFixed(2);
    }
    
    // DOST exam result
    setValue('#dostExamResult', data.dost_exam_result);
}

// Populate program selection
async function populateProgramSelection(data) {
    if (!data) return;
    
    // Helper to safely set value
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
    
    // Set the selected program from program_selection
    const programSelect = document.getElementById('placementProgram');
    if (programSelect && data.selected_program_code) {
        programSelect.value = data.selected_program_code;
        
        // Load sections for this program
        await loadSectionsByProgram(data.selected_program_code);
        
        // Then set the assigned section if exists
        if (data.assigned_section) {
            const sectionSelect = document.getElementById('placementSection');
            if (sectionSelect) {
                sectionSelect.value = data.assigned_section;
            }
        }
    }
    
    // Set admin approval status
    const approvalSelect = document.getElementById('placementAdminApproved');
    if (approvalSelect) {
        approvalSelect.value = data.admin_approved ? 'true' : 'false';
    }
    
    // Set admin notes
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
        const response = await fetch(`/admin-portal/api/sections/?program=${programCode}`);
        
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
            // Display: Section Name - Adviser (if available) - Current/Max students
            let displayText = section.name;
            if (section.adviser_name) {
                displayText += ` - ${section.adviser_name}`;
            }
            displayText += ` (${section.current_students}/${section.max_students})`;
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
        'submitted': { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: 'fa-clock', label: 'Enrollment Pending' },
        'under_review': { bg: 'bg-blue-100', text: 'text-blue-800', icon: 'fa-eye', label: 'Under Review' },
        'approved': { bg: 'bg-green-100', text: 'text-green-800', icon: 'fa-check-circle', label: 'Approved' },
        'rejected': { bg: 'bg-red-100', text: 'text-red-800', icon: 'fa-times-circle', label: 'Rejected' },
    };
    
    const config = statusMap[status] || statusMap['draft'];
    
    statusBadge.className = `${config.bg} ${config.text} px-4 py-2 rounded-full text-sm font-semibold inline-flex items-center gap-2`;
    statusBadge.innerHTML = `<i class="fas ${config.icon}"></i> ${config.label}`;
}

// Setup form submission
function setupFormSubmission(studentId) {
    const form = document.querySelector('form');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        submitBtn.disabled = true;
        
        try {
            // Collect form data
            const formData = collectFormData();
            
            // Send updates to respective endpoints
            await updateAllSections(studentId, formData);
            
            showNotification('All changes saved successfully!', 'success');
            
            // Redirect back to enrollment page after 2 seconds
            setTimeout(() => {
                window.location.href = '/admin/enrollment/';
            }, 2000);
            
        } catch (error) {
            console.error('Error saving:', error);
            showNotification('Failed to save changes: ' + error.message, 'error');
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });
}

// Collect form data from all sections
function collectFormData() {
    // This is a simplified version - expand based on your actual form structure
    const formData = {
        student_data: {},
        family_data: {},
        survey_data: {},
        academic_data: {},
        program_selection: {}
    };
    
    // You'll need to implement detailed data collection for each section
    // based on your form structure
    
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
                body: JSON.stringify({ student_data: formData.student_data })
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
            })
        );
    }
    
    await Promise.all(updatePromises);
}

// Helper: Get CSRF token
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

// Accordion and form interaction functions (from original studentEdit.js)
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

// Make functions globally available
window.toggleAccordion = toggleAccordion;
window.showNotification = showNotification;