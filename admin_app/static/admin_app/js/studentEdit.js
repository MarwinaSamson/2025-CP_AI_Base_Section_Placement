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
    
    // Load student data
    await loadStudentData(studentId);
    
    // MAKE ALL FIELDS READ-ONLY after loading data
    makeAllFieldsReadonly();
    
    // Note: Form submission is now disabled since everything is read-only
});

function makeAllFieldsReadonly() {
    const form = document.querySelector('form');
    if (!form) return;

    // Get all input, textarea, and select elements
    const allInputs = form.querySelectorAll('input:not([type="hidden"]), textarea, select');
    
    allInputs.forEach(element => {
        // Skip hidden inputs
        if (element.type === 'hidden') return;
        
        // For text inputs, textareas, and date inputs - make readonly
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            element.readOnly = true;
            element.classList.add('bg-gray-50', 'cursor-not-allowed');
            
            // Also disable file inputs
            if (element.type === 'file') {
                element.disabled = true;
            }
            
            // Disable checkboxes and radio buttons
            if (element.type === 'checkbox' || element.type === 'radio') {
                element.disabled = true;
                element.classList.add('cursor-not-allowed');
            }
        }
        
        // For select elements - disable them
        if (element.tagName === 'SELECT') {
            element.disabled = true;
            element.classList.add('bg-gray-50', 'cursor-not-allowed');
        }
    });
    
    // Disable all buttons except "Back to Enrollment"
    const allButtons = form.querySelectorAll('button');
    allButtons.forEach(button => {
        // Don't disable accordion toggle buttons
        if (button.classList.contains('accordion-header') || button.onclick?.toString().includes('toggleAccordion')) {
            return;
        }
        
        // Disable submit and other action buttons
        if (button.type === 'submit' || button.classList.contains('action-button')) {
            button.disabled = true;
            button.classList.add('opacity-50', 'cursor-not-allowed');
        }
    });
    
    // Hide the "Save All Changes" button and show read-only message
    const actionButtonsSection = document.querySelector('.bg-white.rounded-2xl.shadow-lg.p-6.border.border-gray-200:last-of-type');
    if (actionButtonsSection) {
        actionButtonsSection.innerHTML = `
            <div class="text-center">
                <div class="inline-block px-6 py-4 bg-blue-50 border-2 border-blue-200 rounded-xl">
                    <i class="fas fa-lock text-blue-600 mr-2 text-xl"></i>
                    <span class="text-blue-700 font-semibold text-lg">Read-Only View</span>
                    <p class="text-blue-600 text-sm mt-2">All student information is displayed in read-only mode. No changes can be made from this view.</p>
                </div>
                <div class="mt-4">
                    <a href="{% url 'admin_app:enrollment' %}" class="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-primary to-primary-dark text-white rounded-xl font-semibold hover:shadow-lg hover:scale-105 transition-all duration-300">
                        <i class="fas fa-arrow-left"></i>
                        Back to Enrollment
                    </a>
                </div>
            </div>
        `;
    }
    
    console.log('All fields set to read-only mode');
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
        
        // Debug: Log the received data
        console.log('Loaded student data:', data);
        
        // Populate all form sections
        populateStudentBasicInfo(data);
        populateStudentData(data.student_data, data.student);
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
    }
    
    const workingRadio = data.is_working_student ?
        document.querySelector('input[name="is_working"][value="yes"]') :
        document.querySelector('input[name="is_working"][value="no"]');
    if (workingRadio) workingRadio.checked = true;
    
    const workingDetails = document.querySelectorAll('textarea[placeholder="If yes, please specify"]')[1];
    if (workingDetails) {
        workingDetails.value = data.working_details || '';
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
    }
    
    const approvalSelect = document.getElementById('placementAdminApproved');
    if (approvalSelect) {
        approvalSelect.value = data.admin_approved ? 'true' : 'false';
    }
    
    setValue('#placementAdminNotes', data.admin_notes);
    
    // Set section if available
    const sectionSelect = document.getElementById('placementSection');
    if (sectionSelect && data.assigned_section) {
        // Create an option with the assigned section value
        const option = document.createElement('option');
        option.value = data.assigned_section;
        option.textContent = data.assigned_section;
        option.selected = true;
        sectionSelect.appendChild(option);
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

// Accordion functions
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