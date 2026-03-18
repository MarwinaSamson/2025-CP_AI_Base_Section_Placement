// Enrollment Management - Unified Dynamic Module
let studentsData = [];
let sections = [];
let currentMode = 'manual';
let isLoadingContent = false;

document.addEventListener('DOMContentLoaded', function () {
    // Initialize from backend state
    currentMode = window.AI_ENABLED ? 'ai' : 'manual';

    // Set up mode toggle
    const modeToggle = document.getElementById('modeToggle');
    if (modeToggle) {
        modeToggle.checked = window.AI_ENABLED;
        modeToggle.addEventListener('change', handleModeToggle);
    }

    // Load initial content
    loadModeContent(currentMode, false);

    // Setup grade filter
    const gradeFilter = document.getElementById('gradeFilter');
    if (gradeFilter) {
        gradeFilter.addEventListener('change', () => {
            // Reload content for new grade
            loadModeContent(currentMode, false);
        });
    }
});

async function handleModeToggle() {
    const modeToggle = document.getElementById('modeToggle');
    const enabled = modeToggle.checked;
    const newMode = enabled ? 'ai' : 'manual';

    if (isLoadingContent) return;

    try {
        // Update backend AI preference
        const success = await toggleAIMode(enabled);

        if (success) {
            // Switch to new mode
            currentMode = newMode;
            window.AI_ENABLED = enabled;

            // Load new content
            await loadModeContent(newMode, true);

            // Update description
            updateModeDescription(newMode);
        } else {
            // Revert toggle on error
            modeToggle.checked = !enabled;
            showNotification('Failed to switch mode. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Error switching mode:', error);
        modeToggle.checked = !enabled;
        showNotification('An error occurred while switching modes', 'error');
    }
}

async function toggleAIMode(enabled) {
    try {
        const response = await fetch('/coordinator/api/toggle-ai-mode/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN
            },
            body: JSON.stringify({
                ai_enabled: enabled,
                program_code: window.PROGRAM_CODE
            })
        });

        const data = await response.json();

        if (response.ok) {
            showNotification(
                `AI automation ${enabled ? 'enabled' : 'disabled'} successfully!`,
                'success'
            );
            return true;
        } else {
            showNotification(data.error || 'Failed to update AI settings', 'error');
            return false;
        }
    } catch (error) {
        console.error('Error toggling AI mode:', error);
        showNotification('An error occurred while updating AI settings', 'error');
        return false;
    }
}

async function loadModeContent(mode, showMessage = true) {
    if (isLoadingContent) return;

    isLoadingContent = true;
    const container = document.getElementById('contentContainer');

    // Add loading state
    container.classList.add('content-loading');

    try {
        // Fetch content
        const url = mode === 'ai'
            ? '/coordinator/api/enrollment/ai-content/'
            : '/coordinator/api/enrollment/manual-content/';

        console.log('DEBUG: Fetching content from:', url);

        const response = await fetch(url, {
            headers: {
                'X-CSRFToken': window.CSRF_TOKEN
            }
        });

        console.log('DEBUG: Response status:', response.status);
        console.log('DEBUG: Response ok:', response.ok);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('DEBUG: Error response:', errorText);
            throw new Error(`Failed to load content: ${response.status} - ${errorText}`);
        }

        const data = await response.json();
        console.log('DEBUG: Received JSON data');
        console.log('DEBUG: Students count in response:', data.students ? data.students.length : 0);

        // Update window.STUDENTS_DATA with fresh data from API
        if (data.students) {
            window.STUDENTS_DATA = data.students;
            console.log('DEBUG: Updated window.STUDENTS_DATA');
        }

        // Update window.SECTIONS_DATA with fresh data from API
        if (data.sections) {
            window.SECTIONS_DATA = data.sections;
            console.log('DEBUG: Updated window.SECTIONS_DATA');
        }

        // Update content
        if (data.html) {
            container.innerHTML = data.html;
            console.log('DEBUG: Container HTML updated');
        }
        
        container.classList.remove('content-loading');

        // Load data and initialize (now with fresh window data)
        if (mode === 'ai') {
            loadAIModeData();
            setupAIEventHandlers();
        } else {
            loadManualModeData();
            setupManualEventHandlers();
        }

        if (showMessage) {
            showNotification(
                `Switched to ${mode === 'ai' ? 'AI' : 'Manual'} mode`,
                'success'
            );
        }
    } catch (error) {
        console.error('Error loading content:', error);
        container.innerHTML = `
            <div class="bg-red-50 border-2 border-red-200 rounded-xl p-8 text-center">
                <i class="fas fa-exclamation-triangle text-4xl text-red-500 mb-4"></i>
                <h3 class="text-xl font-bold text-gray-800 mb-2">Failed to Load Content</h3>
                <p class="text-gray-600 mb-4">Unable to load ${mode} mode content. Please try again.</p>
                <button onclick="loadModeContent('${mode}', false)" class="px-6 py-3 bg-primary text-white rounded-lg font-semibold hover:bg-primary-dark transition-colors">
                    <i class="fas fa-sync-alt mr-2"></i>Retry
                </button>
            </div>
        `;
        container.classList.remove('content-loading');
    } finally {
        isLoadingContent = false;
    }
}

function updateModeDescription(mode) {
    const modeDescription = document.getElementById('modeDescription');
    if (modeDescription) {
        if (mode === 'ai') {
            modeDescription.textContent = 'Review students that were automatically processed by AI';
        } else {
            modeDescription.textContent = 'Manually review and approve student enrollment requests';
        }
    }
}

// ===================
// Manual Mode Functions
// ===================
function loadManualModeData() {
    const rawStudents = Array.isArray(window.STUDENTS_DATA) ? window.STUDENTS_DATA : [];
    const rawSections = Array.isArray(window.SECTIONS_DATA) ? window.SECTIONS_DATA : [];

    studentsData = rawStudents.map(s => ({
        name: s.name,
        lrn: s.lrn,
        admin_approved: !!s.admin_approved,
        finalSection: s.finalSection || null,
    }));

    sections = rawSections.map(sec => ({
        id: sec.id,
        name: sec.name,
        current: sec.current,
        capacity: sec.capacity,
    }));

    const pending = studentsData.filter(s => !s.admin_approved).length;
    const approved = studentsData.filter(s => s.admin_approved).length;

    animateNumber('pendingCount', pending);
    animateNumber('approvedCount', approved);
    animateNumber('sectionsCount', sections.length);

    populateEnrollmentTable(studentsData);
}

function populateEnrollmentTable(students) {
    const tbody = document.getElementById('enrollmentTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-6 py-12 text-center text-gray-500">
                    <i class="fas fa-inbox text-6xl mb-4 text-gray-300"></i>
                    <p class="font-bold text-lg">No enrollment requests found</p>
                    <p class="text-sm mt-2">New applications will appear here</p>
                </td>
            </tr>
        `;
        return;
    }

    students.forEach((student, index) => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50 transition-all duration-200 animate-fadeIn';
        row.style.animationDelay = `${index * 50}ms`;

        let statusBadge;
        if (student.admin_approved) {
            statusBadge = '<span class="px-4 py-2 text-xs font-bold rounded-full bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md"><i class="fas fa-check-circle mr-1"></i>Approved</span>';
        } else if (student.enrollment_status === 'under_review') {
            statusBadge = '<span class="px-4 py-2 text-xs font-bold rounded-full bg-red-500 text-white shadow-md"><i class="fas fa-user-clock mr-1"></i>Under Review</span>';
        } else {
            statusBadge = '<span class="px-4 py-2 text-xs font-bold rounded-full bg-yellow-500 text-white shadow-md"><i class="fas fa-clock mr-1"></i>Pending</span>';
        }

        // Build flag indicator
        let flagHtml = '';
        if (student.flag_message) {
            flagHtml = `<div class="mt-2 p-2 bg-yellow-50 border-l-4 border-yellow-400 text-xs text-yellow-800 rounded">
                <i class="fas fa-exclamation-triangle mr-1"></i>${student.flag_message}
            </div>`;
        }

        row.innerHTML = `
            <td class="px-6 py-5">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-gradient-to-br from-primary to-primary-dark rounded-lg flex items-center justify-center text-white font-bold shadow-md">
                        ${student.name ? student.name.charAt(0) : '?'}
                    </div>
                    <div>
                        <div class="font-bold text-gray-800">${student.name || student.lrn}</div>
                        <div class="text-xs text-gray-500 mt-0.5">${window.PROGRAM_CODE || ''}</div>
                    </div>
                </div>
                ${flagHtml}
            </td>
            <td class="px-6 py-5 text-sm text-gray-700 font-mono font-semibold">${student.lrn || '---'}</td>
            <td class="px-6 py-5">${statusBadge}</td>
            <td class="px-6 py-5">
                <button onclick="viewStudentDetails('${student.lrn}')" class="px-5 py-2.5 bg-gradient-to-r from-primary to-primary-dark text-white rounded-lg hover:from-primary-dark hover:to-primary transition-all text-sm font-bold shadow-md hover:shadow-lg transform hover:scale-105">
                    <i class="fas fa-eye mr-2"></i>View Details
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function setupManualEventHandlers() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const exportBtn = document.getElementById('exportBtn');
    const printBtn = document.getElementById('printBtn');

    if (searchInput) {
        searchInput.addEventListener('input', filterManualTable);
    }

    if (statusFilter) {
        statusFilter.addEventListener('change', filterManualTable);
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', exportTableToCSV);
    }

    if (printBtn) {
        printBtn.addEventListener('click', () => window.print());
    }
}

function filterManualTable() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');

    if (!searchInput || !statusFilter) return;

    const searchTerm = searchInput.value.toLowerCase();
    const status = statusFilter.value;

    let filtered = studentsData.filter(student => {
        const matchesSearch = (student.name && student.name.toLowerCase().includes(searchTerm)) ||
                            (student.lrn && student.lrn.toLowerCase().includes(searchTerm));
        const matchesStatus = status === 'all' ||
                            (status === 'pending' && !student.admin_approved && student.enrollment_status !== 'under_review') ||
                            (status === 'under_review' && student.enrollment_status === 'under_review') ||
                            (status === 'approved' && student.admin_approved);
        return matchesSearch && matchesStatus;
    });

    populateEnrollmentTable(filtered);
}

// ===================
// AI Mode Functions
// ===================
function loadAIModeData() {
    const rawStudents = Array.isArray(window.STUDENTS_DATA) ? window.STUDENTS_DATA : [];
    const rawSections = Array.isArray(window.SECTIONS_DATA) ? window.SECTIONS_DATA : [];

    const aiProcessedStudents = rawStudents
        .filter(s => s.admin_approved && s.approved_by &&
                    (s.approved_by.includes('AI') || s.approved_by.includes('Assistant')))
        .map(s => ({
            name: s.name,
            lrn: s.lrn,
            finalSection: s.finalSection || null,
            admin_approved: true,
            approved_date: s.approved_at || new Date().toISOString(),
        }));

    sections = rawSections.map(sec => ({
        id: sec.id,
        name: sec.name,
        current: sec.current,
        capacity: sec.capacity,
    }));

    animateNumber('aiProcessedCount', aiProcessedStudents.length);
    animateNumber('aiAutoApproved', aiProcessedStudents.length);
    animateNumber('aiAssigned', aiProcessedStudents.filter(s => s.finalSection).length);
    animateNumber('aiPending', rawStudents.filter(s => s.enrollment_status === 'under_review').length);

    updateLastUpdated();
    populateAITable(aiProcessedStudents);
}

function populateAITable(students) {
    const tbody = document.getElementById('aiTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-12 text-center text-gray-500">
                    <i class="fas fa-robot text-6xl mb-4 text-gray-300"></i>
                    <p class="font-bold text-lg">No AI-processed students yet</p>
                    <p class="text-sm mt-2 text-gray-400">Students will appear here when AI processes them automatically</p>
                </td>
            </tr>
        `;
        return;
    }

    students.forEach((student, index) => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-green-50 transition-all duration-200 animate-fadeIn';
        row.style.animationDelay = `${index * 50}ms`;

        const processedDate = student.approved_date
            ? new Date(student.approved_date).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
              })
            : '---';

        const sectionName = student.finalSection ? getSectionNameById(student.finalSection) : 'Pending Assignment';

        row.innerHTML = `
            <td class="px-6 py-5">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-gradient-to-br from-ai-primary to-ai-dark rounded-lg flex items-center justify-center text-white font-bold shadow-md">
                        ${student.name ? student.name.charAt(0) : '?'}
                    </div>
                    <div>
                        <div class="font-bold text-gray-800">${student.name || student.lrn}</div>
                        <div class="text-xs text-gray-500 mt-0.5 flex items-center gap-1">
                            <i class="fas fa-robot text-ai-primary text-xs"></i>
                            ${window.PROGRAM_CODE || ''}
                        </div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-5 text-sm text-gray-700 font-mono font-semibold">${student.lrn || '---'}</td>
            <td class="px-6 py-5">
                <span class="px-4 py-2 text-xs font-bold rounded-lg bg-gradient-to-r from-green-100 to-green-200 text-green-800 border border-green-300 shadow-sm">
                    <i class="fas fa-check-circle mr-1"></i>${sectionName}
                </span>
            </td>
            <td class="px-6 py-5 text-sm text-gray-600">
                <div class="flex items-center gap-2">
                    <i class="fas fa-calendar-check text-ai-primary"></i>
                    ${processedDate}
                </div>
            </td>
            <td class="px-6 py-5">
                <span class="px-4 py-2 text-xs font-bold rounded-lg bg-green-600 text-white shadow-md">
                    <i class="fas fa-check-double mr-1"></i>Completed
                </span>
            </td>
            <td class="px-6 py-5">
                <button onclick="viewStudentDetails('${student.lrn}')" class="px-5 py-2.5 bg-gradient-to-r from-ai-primary to-ai-dark text-white rounded-lg hover:from-green-600 hover:to-green-700 transition-all text-sm font-bold shadow-md hover:shadow-lg transform hover:scale-105">
                    <i class="fas fa-eye mr-1"></i>View Details
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function setupAIEventHandlers() {
    const aiSearchInput = document.getElementById('aiSearchInput');

    if (aiSearchInput) {
        aiSearchInput.addEventListener('input', filterAITable);
    }
}

function filterAITable() {
    const aiSearchInput = document.getElementById('aiSearchInput');
    if (!aiSearchInput) return;

    const searchTerm = aiSearchInput.value.toLowerCase();

    const rawStudents = Array.isArray(window.STUDENTS_DATA) ? window.STUDENTS_DATA : [];
    const aiProcessedStudents = rawStudents
        .filter(s => s.admin_approved && s.approved_by &&
                    (s.approved_by.includes('AI') || s.approved_by.includes('Assistant')))
        .map(s => ({
            name: s.name,
            lrn: s.lrn,
            finalSection: s.finalSection || null,
            admin_approved: true,
            approved_date: s.approved_at || new Date().toISOString(),
        }));

    let filtered = aiProcessedStudents.filter(student => {
        return (student.name && student.name.toLowerCase().includes(searchTerm)) ||
               (student.lrn && student.lrn.includes(searchTerm));
    });

    populateAITable(filtered);
}

function refreshAIData() {
    showNotification('Refreshing AI data...', 'info');

    // Reload page data (in a real app, you'd fetch fresh data from server)
    setTimeout(() => {
        loadAIModeData();
        showNotification('Data refreshed successfully!', 'success');
    }, 1000);
}

// ===================
// Utility Functions
// ===================
function getSectionNameById(sectionId) {
    const section = sections.find(s => String(s.id) === String(sectionId));
    return section ? section.name : sectionId;
}

function viewStudentDetails(lrn) {
    if (lrn) {
        window.location.href = `/coordinator/student-edit/${lrn}/`;
    }
}

function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const startValue = parseInt(element.textContent) || 0;
    const duration = 1000;
    const increment = (targetValue - startValue) / (duration / 16);

    let currentValue = startValue;
    const timer = setInterval(() => {
        currentValue += increment;
        if ((increment > 0 && currentValue >= targetValue) ||
            (increment < 0 && currentValue <= targetValue)) {
            element.textContent = targetValue;
            clearInterval(timer);
        } else {
            element.textContent = Math.round(currentValue);
        }
    }, 16);
}

function updateLastUpdated() {
    const element = document.getElementById('lastUpdated');
    if (element) {
        const now = new Date();
        element.textContent = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

function exportTableToCSV() {
    const table = document.getElementById('enrollmentTable');
    if (!table) return;

    const rows = Array.from(table.querySelectorAll('tr'));
    const csv = rows.map(row =>
        Array.from(row.querySelectorAll('th, td'))
            .map(cell => '"' + (cell.innerText || '').replace(/"/g, '""') + '"')
            .join(',')
    ).join('\n');

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'enrollment_requests.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function toggleHelpModal() {
    const helpModal = document.getElementById('helpModal');
    if (helpModal) {
        helpModal.classList.toggle('hidden');
    }
}

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

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    const notification = document.createElement('div');

    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-amber-500'
    };

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle',
        warning: 'fa-exclamation-triangle'
    };

    notification.className = `${colors[type]} text-white px-6 py-4 rounded-xl shadow-lg flex items-center gap-3 animate-slide-in`;
    notification.innerHTML = `
        <i class="fas ${icons[type]} text-xl"></i>
        <span class="flex-1">${message}</span>
        <button onclick="this.parentElement.remove()" class="text-white hover:text-gray-200 transition-colors">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(notification);

    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100px)';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}
