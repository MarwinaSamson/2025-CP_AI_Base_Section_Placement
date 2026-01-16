// Global state
let studentsData = [];
let sections = [];
let currentMode = 'manual'; // 'manual' or 'ai'

document.addEventListener('DOMContentLoaded', function () {
    // Get user-specific key for localStorage
    const programCode = window.PROGRAM_CODE || 'default';
    const modeKey = `processingMode_${programCode}`;
    
    // Restore mode preference (default: manual)
    const savedMode = localStorage.getItem(modeKey) || 'manual';
    currentMode = savedMode;
    // Initialize toggle UI
    const modeToggle = document.getElementById('modeToggle');
    if (modeToggle) {
        modeToggle.checked = currentMode === 'ai';
        modeToggle.addEventListener('change', () => {
            const mode = modeToggle.checked ? 'ai' : 'manual';
            switchMode(mode);
        });
    }

    switchMode(currentMode);

    // Load data
    loadData();
    
    // Setup search functionality
    setupSearchFilters();
    
    // Update last updated time
    setInterval(updateLastUpdated, 60000); // Update every minute
});

function switchMode(mode) {
    const programCode = window.PROGRAM_CODE || 'default';
    const modeKey = `processingMode_${programCode}`;
    
    currentMode = mode;
    localStorage.setItem(modeKey, mode);
    
    const manualView = document.getElementById('manualModeView');
    const aiView = document.getElementById('aiModeView');
    const modeDescription = document.getElementById('modeDescription');
    const modeToggle = document.getElementById('modeToggle');
    
    if (mode === 'manual') {
        // Update toggle state
        if (modeToggle) modeToggle.checked = false;
        
        // Update description
        modeDescription.textContent = 'Manually review and approve student enrollment requests';
        
        // Show/hide views
        manualView.classList.remove('hidden');
        aiView.classList.add('hidden');
        
        // Load manual mode data
        loadManualModeData();
    } else {
        // Update toggle state
        if (modeToggle) modeToggle.checked = true;
        
        // Update description
        modeDescription.textContent = 'Review students that were automatically processed by AI';
        
        // Show/hide views
        aiView.classList.remove('hidden');
        manualView.classList.add('hidden');
        
        // Load AI mode data
        loadAIModeData();
    }
}

function loadManualModeData() {
    // Initialize from backend-injected data
    const rawStudents = Array.isArray(window.STUDENTS_DATA) ? window.STUDENTS_DATA : [];
    const rawSections = Array.isArray(window.SECTIONS_DATA) ? window.SECTIONS_DATA : [];

    // Map to local state shape
    studentsData = rawStudents.map(s => ({
        name: s.name,
        lrn: s.lrn,
        admin_approved: !!s.admin_approved,
        finalSection: s.finalSection || null,
    }));

    sections = rawSections.map(sec => ({
        id: sec.id || sec.id,
        name: sec.name,
        current: sec.current,
        capacity: sec.capacity,
    }));

    // Update statistics
    const pending = studentsData.filter(s => !s.admin_approved).length;
    const approved = studentsData.filter(s => s.admin_approved).length;

    animateNumber('pendingCount', pending);
    animateNumber('approvedCount', approved);
    animateNumber('sectionsCount', sections.length);

    // Populate enrollment table
    populateEnrollmentTable(studentsData);
}

function populateEnrollmentTable(students) {
    const tbody = document.getElementById('enrollmentTableBody');
    tbody.innerHTML = '';
    
    if (students.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-12 text-center text-gray-500">
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
        
        const statusBadge = student.admin_approved 
            ? '<span class="px-4 py-2 text-xs font-bold rounded-full bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md"><i class="fas fa-check-circle mr-1"></i>Approved</span>'
            : '<span class="px-4 py-2 text-xs font-bold rounded-full bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-md"><i class="fas fa-clock mr-1"></i>Pending</span>';
        
        const sectionDropdown = !student.admin_approved ? `
            <select id="sectionSelect_${student.lrn}" class="px-3 py-2 border-2 border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-primary">
                <option value="">Select Section</option>
                ${sections.map(s => `<option value="${s.id}">${s.name} (${s.current}/${s.capacity})</option>`).join('')}
            </select>
        ` : (student.finalSection ? `<span class="px-3 py-1 bg-green-100 text-green-800 rounded-lg text-sm font-semibold">${getSectionNameById(student.finalSection) || 'Assigned'}</span>` : '<span class="text-gray-400 text-sm">Not Assigned</span>');
        
        const actionBtn = !student.admin_approved
            ? `<button onclick="approveStudent('${student.lrn}', document.getElementById('sectionSelect_${student.lrn}').value)" class="px-5 py-2.5 bg-gradient-to-r from-green-500 to-green-600 text-white rounded-lg hover:from-green-600 hover:to-green-700 transition-all text-sm font-bold shadow-md hover:shadow-lg transform hover:scale-105">
                <i class="fas fa-check mr-1"></i>Approve
               </button>`
            : '<span class="text-gray-400 text-sm italic">Approved</span>';
        
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
            </td>
            <td class="px-6 py-5 text-sm text-gray-700 font-mono font-semibold">${student.lrn || '---'}</td>
            <td class="px-6 py-5">${statusBadge}</td>
            <td class="px-6 py-5">
                <div class="flex items-center gap-2">
                    ${sectionDropdown}
                    ${actionBtn}
                    <button onclick="viewStudentDetails('${student.lrn}')" class="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all text-sm font-semibold shadow-sm hover:shadow-md transform hover:scale-105">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function loadAIModeData() {
    // Filter AI-processed students from backend data (those auto-approved)
    const rawStudents = Array.isArray(window.STUDENTS_DATA) ? window.STUDENTS_DATA : [];
    const rawSections = Array.isArray(window.SECTIONS_DATA) ? window.SECTIONS_DATA : [];

    // Map AI data - students with auto_approved_by_ai flag or admin_approved
    const aiProcessedStudents = rawStudents
        .filter(s => s.admin_approved && (s.auto_approved_by_ai || s.auto_assigned_by_ai))
        .map(s => ({
            name: s.name,
            lrn: s.lrn,
            finalSection: s.finalSection || null,
            admin_approved: true,
            approved_date: s.approved_date || new Date().toISOString(),
        }));

    sections = rawSections.map(sec => ({
        id: sec.id || sec.id,
        name: sec.name,
        current: sec.current,
        capacity: sec.capacity,
    }));

    // Update AI summary with animation
    animateNumber('aiProcessedCount', aiProcessedStudents.length);
    animateNumber('aiAutoApproved', aiProcessedStudents.length);
    animateNumber('aiAssigned', aiProcessedStudents.filter(s => s.finalSection).length);
    animateNumber('aiPending', rawStudents.filter(s => !s.admin_approved).length);
    
    updateLastUpdated();
    
    // Populate AI table
    populateAITable(aiProcessedStudents);
}

function populateAITable(students) {
    const tbody = document.getElementById('aiTableBody');
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
            ? new Date(student.approved_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
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
                <span class="px-4 py-2 text-xs font-bold rounded-lg bg-gradient-to-r from-green-500 to-green-600 text-white shadow-md">
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

// Helper function to get section name by ID
function getSectionNameById(sectionId) {
    const section = sections.find(s => s.id === sectionId);
    return section ? section.name : null;
}

// Approval function with backend integration
async function approveStudent(lrn, sectionId) {
    if (!lrn) {
        showNotification('Invalid student LRN', 'error');
        return;
    }
    
    if (!sectionId) {
        showNotification('Please select a section', 'error');
        return;
    }
    
    showNotification('Approving student and assigning section...', 'info');
    
    try {
        // Get CSRF token from hidden input or cookie
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                         document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
        
        const response = await fetch(`/coordinator/api/student/${lrn}/approve-and-place/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ section_id: sectionId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Student approved and assigned to section!', 'success');
            setTimeout(() => location.reload(), 1500);
        } else {
            showNotification(data.error || 'Failed to approve student', 'error');
        }
    } catch (error) {
        console.error('Error approving student:', error);
        showNotification('An error occurred while approving the student', 'error');
    }
}

function assignSection(lrn, sectionId) {
    if (!sectionId) {
        showNotification('Please select a section', 'error');
        return;
    }
    
    approveStudent(lrn, sectionId);
}

function viewStudentDetails(lrn) {
    const student = studentsData.find(s => s.lrn === lrn);
    if (student) {
        alert(`Student: ${student.name || lrn}\nLRN: ${lrn}\nStatus: ${student.admin_approved ? 'Approved' : 'Pending'}\nSection: ${student.finalSection ? getSectionNameById(student.finalSection) : 'Not Assigned'}`);
    }
}

function refreshAIData() {
    showNotification('Refreshing AI data...', 'info');
    loadAIModeData();
    
    setTimeout(() => {
        showNotification('Data refreshed successfully!', 'success');
    }, 1000);
}

function setupSearchFilters() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const aiSearchInput = document.getElementById('aiSearchInput');
    const exportBtn = document.getElementById('exportBtn');
    const printBtn = document.getElementById('printBtn');
    
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            if (currentMode === 'manual') {
                filterManualTable();
            }
        });
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', () => {
            if (currentMode === 'manual') {
                filterManualTable();
            }
        });
    }
    
    if (aiSearchInput) {
        aiSearchInput.addEventListener('input', () => {
            if (currentMode === 'ai') {
                filterAITable();
            }
        });
    }

    if (printBtn) {
        printBtn.addEventListener('click', () => window.print());
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', exportTableToCSV);
    }
}

function filterManualTable() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    
    let filtered = studentsData.filter(student => {
        const matchesSearch = student.full_name.toLowerCase().includes(searchTerm) || 
                            (student.lrn && student.lrn.includes(searchTerm));
        const matchesStatus = statusFilter === 'all' || 
                            (statusFilter === 'pending' && !student.admin_approved) ||
                            (statusFilter === 'approved' && student.admin_approved);
        return matchesSearch && matchesStatus;
    });
    
    populateEnrollmentTable(filtered);
}

function filterAITable() {
    const searchTerm = document.getElementById('aiSearchInput').value.toLowerCase();
    
    // Filter from backend data - AI-processed students
    const rawStudents = Array.isArray(window.STUDENTS_DATA) ? window.STUDENTS_DATA : [];
    const aiProcessedStudents = rawStudents
        .filter(s => s.admin_approved && (s.auto_approved_by_ai || s.auto_assigned_by_ai))
        .map(s => ({
            name: s.name,
            lrn: s.lrn,
            finalSection: s.finalSection || null,
            admin_approved: true,
            approved_date: s.approved_date || new Date().toISOString(),
        }));
    
    let filtered = aiProcessedStudents.filter(student => {
        return student.name.toLowerCase().includes(searchTerm) || 
               (student.lrn && student.lrn.includes(searchTerm));
    });
    
    populateAITable(filtered);
}

function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const startValue = parseInt(element.textContent) || 0;
    const duration = 1000; // 1 second
    const increment = (targetValue - startValue) / (duration / 16); // 60fps
    
    let currentValue = startValue;
    const timer = setInterval(() => {
        currentValue += increment;
        if ((increment > 0 && currentValue >= targetValue) || (increment < 0 && currentValue <= targetValue)) {
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
        element.textContent = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
}

function exportTableToCSV() {
    const rows = Array.from(document.querySelectorAll('#enrollmentTable tr'));
    const csv = rows.map(row => Array.from(row.querySelectorAll('th, td'))
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

function loadData() {
    if (currentMode === 'manual') {
        loadManualModeData();
    } else {
        loadAIModeData();
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
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-amber-500'
    };
    
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 ${colors[type]} text-white px-6 py-4 rounded-lg shadow-xl z-50 animate-slideInRight`;
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span class="font-semibold">${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('opacity-0', 'transition-opacity', 'duration-500');
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

function formatSectionLabel(sectionId) {
    if (!sectionId) return '';
    const match = sections.find(sec => String(sec.id) === String(sectionId));
    if (match) {
        const prefix = window.PROGRAM_CODE ? `${window.PROGRAM_CODE} - ` : '';
        return `${prefix}${match.name || match.id}`;
    }
    return sectionId;
}

function loadData() {
    studentsData = Array.isArray(window.STUDENTS_DATA) ? window.STUDENTS_DATA : [];
    sections = Array.isArray(window.SECTIONS_DATA) ? window.SECTIONS_DATA : [];
    
    // Normalize properties
    studentsData = studentsData.map(student => ({
        ...student,
        finalSection: student.finalSection ? String(student.finalSection) : null,
        aiSuggestion: student.aiSuggestion ? String(student.aiSuggestion) : null,
    }));

    sections = sections.map(section => ({
        ...section,
        id: String(section.id),
        capacity: Number(section.capacity) || 0,
        current: Number(section.current) || 0,
    }));

    // Compute AI suggestions (without assigning yet)
    setAISuggestions(false);

    updateStatistics();
    
    if (currentView === 'board') {
        renderBoardView();
    } else {
        loadStudentsData();
        initializeTableInteractions();
    }
}

function switchView(view, showMsg = true) {
    const programCode = window.PROGRAM_CODE || 'default';
    const viewKey = `viewMode_${programCode}`;
    
    currentView = view;
    localStorage.setItem(viewKey, view);
    
    const boardView = document.getElementById('boardView');
    const tableView = document.getElementById('tableView');
    const boardBtn = document.getElementById('boardViewBtn');
    const tableBtn = document.getElementById('tableViewBtn');
    const floatingActions = document.getElementById('floatingActions');
    
    if (view === 'board') {
        boardView.classList.remove('hidden');
        tableView.classList.add('hidden');
        floatingActions?.classList.remove('hidden');
        
        boardBtn.className = 'px-4 py-2 rounded-lg font-medium transition-colors bg-primary text-white';
        tableBtn.className = 'px-4 py-2 rounded-lg font-medium transition-colors bg-gray-100 text-gray-600 hover:bg-gray-200';
        
        renderBoardView();
        if (showMsg) showNotification('Switched to Board View', 'info');
    } else {
        boardView.classList.add('hidden');
        tableView.classList.remove('hidden');
        floatingActions?.classList.add('hidden');
        
        boardBtn.className = 'px-4 py-2 rounded-lg font-medium transition-colors bg-gray-100 text-gray-600 hover:bg-gray-200';
        tableBtn.className = 'px-4 py-2 rounded-lg font-medium transition-colors bg-primary text-white';
        
        loadStudentsData();
        initializeTableInteractions();
        if (showMsg) showNotification('Switched to Table View', 'info');
    }
}

function renderBoardView() {
    const programCode = window.PROGRAM_CODE || '';

    // Render unassigned students
    const unassignedContainer = document.getElementById('unassignedStudents');
    const unassignedStudents = studentsData.filter(s => !s.finalSection);
    
    document.getElementById('unassignedCount').textContent = unassignedStudents.length;
    
    if (unassignedStudents.length === 0) {
        unassignedContainer.innerHTML = `
            <div class="col-span-full text-center py-8 text-gray-400">
                <i class="fas fa-check-circle text-4xl mb-2 opacity-30"></i>
                <p class="text-sm">All students have been assigned to sections</p>
            </div>
        `;
    } else {
        unassignedContainer.innerHTML = unassignedStudents.map(student => 
            createStudentCard(student, 'unassigned')
        ).join('');
    }
    
    // Render sections
    const sectionsGrid = document.getElementById('sectionsGrid');
    sectionsGrid.innerHTML = sections.map(section => {
        const sectionId = section.id;
        const assignedStudents = studentsData.filter(s => s.finalSection === sectionId);
        const stats = calculateSectionStats(sectionId);
        const capacityPercent = section.capacity ? (stats.count / section.capacity) * 100 : 0;
        const isOverCapacity = section.capacity && stats.count >= section.capacity;
        
        return `
            <div class="bg-white rounded-2xl shadow-lg overflow-hidden transition-all section-column"
                 data-section-id="${sectionId}"
                 ondragover="handleDragOver(event)"
                 ondragleave="handleDragLeave(event)"
                 ondrop="handleDrop(event, '${sectionId}')">
                <div class="p-4 ${isOverCapacity ? 'bg-gradient-to-r from-red-500 to-red-600' : 'bg-gradient-to-r from-primary to-primary-dark'} text-white">
                    <div class="flex items-center justify-between mb-2">
                        <h3 class="font-bold text-lg">${section.name || formatSectionLabel(sectionId)}</h3>
                        <span class="text-2xl font-bold">${stats.count}/${section.capacity || '∞'}</span>
                    </div>
                    <p class="text-sm opacity-90 mb-3">${programCode || ''}</p>
                    ${section.capacity ? `
                        <div class="w-full bg-white/30 rounded-full h-2 overflow-hidden">
                            <div class="bg-white h-full transition-all duration-300" style="width: ${Math.min(capacityPercent, 100)}%"></div>
                        </div>
                    ` : ''}
                    <div class="grid grid-cols-2 gap-2 mt-3 text-xs">
                        <div class="bg-white/20 rounded-lg p-2 text-center">
                            <div class="font-bold">${stats.avgScore || '-'}</div>
                            <div class="opacity-80">Avg Score</div>
                        </div>
                        <div class="bg-white/20 rounded-lg p-2 text-center">
                            <div class="font-bold">${stats.count}</div>
                            <div class="opacity-80">Students</div>
                        </div>
                    </div>
                </div>
                <div class="p-4 space-y-2 max-h-96 overflow-y-auto">
                    ${assignedStudents.length === 0 ? `
                        <div class="text-center py-8 text-gray-400">
                            <i class="fas fa-users text-4xl mb-2 opacity-30"></i>
                            <p class="text-sm">Drop students here</p>
                        </div>
                    ` : assignedStudents.map(student => createStudentCard(student, sectionId)).join('')}
                </div>
            </div>
        `;
    }).join('');
}

function createStudentCard(student, location) {
    const examScore = Number(student.exam ?? 0);
    const interviewScore = Number(student.interview ?? 0);
    const aiSuggestion = student.aiSuggestion;
    const isInSuggestedSection = aiSuggestion && student.finalSection === aiSuggestion;
    
    return `
        <div class="bg-gray-50 p-3 rounded-lg border border-gray-200 hover:border-red-400 cursor-move transition-all hover:shadow-sm group student-card-draggable"
             draggable="true"
             data-lrn="${student.lrn}"
             ondragstart="handleDragStart(event, '${student.lrn}')"
             ondragend="handleDragEnd(event)">
            <div class="flex items-start justify-between mb-1">
                <p class="font-semibold text-sm text-gray-800 flex-1 pr-2">${student.name}</p>
                ${isInSuggestedSection ? '<i class="fas fa-robot text-green-500 flex-shrink-0" title="AI Suggested"></i>' : ''}
            </div>
            <p class="text-xs text-gray-500 mb-2 font-mono">${student.lrn}</p>
            <div class="flex items-center justify-between">
                <div class="flex gap-1">
                    <span class="px-2 py-0.5 rounded text-xs font-semibold border ${getScoreColor(examScore)}">
                        E: ${examScore}
                    </span>
                    <span class="px-2 py-0.5 rounded text-xs font-semibold border ${getScoreColor(interviewScore)}">
                        I: ${interviewScore}
                    </span>
                </div>
                ${student.admin_approved ? 
                    '<span class="px-2 py-0.5 bg-green-100 text-green-800 rounded text-xs font-semibold">✓</span>' :
                    '<span class="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-xs font-semibold">⏰</span>'
                }
            </div>
        </div>
    `;
}

function calculateSectionStats(sectionId) {
    const students = studentsData.filter(s => s.finalSection === sectionId);
    const count = students.length;
    
    if (count === 0) return { count: 0, avgScore: null };
    
    const totalScore = students.reduce((sum, s) => {
        const exam = Number(s.exam ?? 0);
        const interview = Number(s.interview ?? 0);
        return sum + ((exam + interview) / 2);
    }, 0);
    
    return { count, avgScore: Math.round(totalScore / count) };
}

function handleDragStart(event, lrn) {
    draggedStudent = studentsData.find(s => s.lrn === lrn);
    event.target.classList.add('dragging');
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', lrn);
}

function handleDragEnd(event) {
    event.target.classList.remove('dragging');
    document.querySelectorAll('.section-column').forEach(col => {
        col.classList.remove('drag-over');
    });
}

function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    const section = event.currentTarget;
    if (section.classList.contains('section-column')) {
        section.classList.add('drag-over');
    }
}

function handleDragLeave(event) {
    const section = event.currentTarget;
    if (section.classList.contains('section-column')) {
        section.classList.remove('drag-over');
    }
}

function handleDrop(event, sectionId) {
    event.preventDefault();
    const section = event.currentTarget;
    section.classList.remove('drag-over');
    
    if (!draggedStudent) return;
    
    const studentIndex = studentsData.findIndex(s => s.lrn === draggedStudent.lrn);
    if (studentIndex !== -1) {
        studentsData[studentIndex].finalSection = sectionId;
        renderBoardView();
        updateStatistics();
        showNotification(`${draggedStudent.name} assigned to ${sectionId}`, 'success');
    }
    
    draggedStudent = null;
}

function loadStudentsData() {
    const tableBody = document.getElementById('studentsTable');
    const tableHeaderAI = document.getElementById('tableHeaderAI');
    const tableHeaderDisabled = document.getElementById('tableHeaderDisabled');
    const aiToggle = document.getElementById('aiToggle');
    const isAIEnabled = aiToggle.checked;

    if (isAIEnabled) {
        tableHeaderAI.classList.remove('hidden');
        tableHeaderDisabled.classList.add('hidden');
    } else {
        tableHeaderAI.classList.add('hidden');
        tableHeaderDisabled.classList.remove('hidden');
    }

    tableBody.innerHTML = '';

    if (!studentsData.length) {
        tableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500 text-sm">No students found for your program.</td></tr>';
        return;
    }

    const selectOptions = sections
        .map(sec => `<option value="${sec.id}">${formatSectionLabel(sec.id)}</option>`)
        .join('');

    studentsData.forEach((student, index) => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50 transition-all duration-200 hover:shadow-sm border-b border-gray-100';
        const examScore = Number(student.exam ?? 0);
        const interviewScore = Number(student.interview ?? 0);
        const aiSuggestion = student.aiSuggestion;
        
        if (isAIEnabled) {
            row.innerHTML = `
                <td class="px-6 py-4">
                    <div class="font-medium text-gray-900">${student.name}</div>
                </td>
                <td class="px-6 py-4">
                    <span class="text-gray-600 font-mono text-sm">${student.lrn}</span>
                </td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center gap-1 px-3 py-1 ${getScoreColor(examScore)} rounded-full text-xs font-semibold border">
                        <i class="fas fa-graduation-cap"></i>
                        ${examScore}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center gap-1 px-3 py-1 ${getScoreColor(interviewScore)} rounded-full text-xs font-semibold border">
                        <i class="fas fa-comments"></i>
                        ${interviewScore}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold border border-green-200">
                        <i class="fas fa-robot"></i>
                        ${formatSectionLabel(aiSuggestion) || 'Not set'}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <select class="section-select w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary transition-all" data-index="${index}">
                        <option value="">Select Section</option>
                        ${selectOptions}
                    </select>
                </td>
                <td class="px-6 py-4">
                    <span class="final-section font-semibold text-gray-900" id="finalSection${index}">${student.finalSection ? formatSectionLabel(student.finalSection) : '-'}</span>
                </td>
            `;
        } else {
            row.innerHTML = `
                <td class="px-6 py-4">
                    <div class="font-medium text-gray-900">${student.name}</div>
                </td>
                <td class="px-6 py-4">
                    <span class="text-gray-600 font-mono text-sm">${student.lrn}</span>
                </td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center gap-1 px-3 py-1 ${getScoreColor(examScore)} rounded-full text-xs font-semibold border">
                        <i class="fas fa-graduation-cap"></i>
                        ${examScore}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center gap-1 px-3 py-1 ${getScoreColor(interviewScore)} rounded-full text-xs font-semibold border">
                        <i class="fas fa-comments"></i>
                        ${interviewScore}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="student-status inline-flex items-center gap-1 px-3 py-1 ${student.admin_approved ? 'bg-green-100 text-green-800 border-green-200' : 'bg-amber-100 text-amber-800 border-amber-200'} rounded-full text-xs font-semibold border" id="status${index}">
                        <i class="fas ${student.admin_approved ? 'fa-check-circle' : 'fa-clock'}"></i> 
                        ${student.admin_approved ? 'Approved' : 'Pending'}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <select class="section-select-disabled px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all" data-index="${index}">
                            <option value="">Assign Section</option>
                            ${selectOptions}
                        </select>
                        <button class="action-button px-4 py-2 bg-gradient-to-r from-primary to-primary-dark text-white rounded-lg text-sm font-medium inline-flex items-center gap-2 hover:shadow-md transition-all hover:scale-105" data-index="${index}" data-lrn="${student.lrn}" onclick="viewStudentDetails('${student.lrn}')">
                            <i class="fas fa-eye"></i> 
                            <span>View</span>
                        </button>
                    </div>
                </td>
            `;
        }
        tableBody.appendChild(row);
    });
}

function getScoreColor(score) {
    if (score >= 90) return 'bg-green-100 text-green-800';
    if (score >= 80) return 'bg-red-100 text-primary';
    if (score >= 70) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
}

function initializeTableInteractions() {
    document.addEventListener('change', function (e) {
        if (e.target.classList.contains('section-select')) {
            const index = e.target.dataset.index;
            const finalSection = document.getElementById(`finalSection${index}`);
            studentsData[index].finalSection = e.target.value || null;
            finalSection.textContent = studentsData[index].finalSection ? formatSectionLabel(studentsData[index].finalSection) : '-';

            if (!e.target.value && document.getElementById('aiToggle').checked) {
                const aiSuggestion = studentsData[index].aiSuggestion;
                if (aiSuggestion) {
                    e.target.value = aiSuggestion;
                    studentsData[index].finalSection = aiSuggestion;
                    finalSection.textContent = formatSectionLabel(aiSuggestion);
                }
            }
        }

        if (e.target.classList.contains('section-select-disabled')) {
            const index = e.target.dataset.index;
            const statusSpan = document.getElementById(`status${index}`);
            studentsData[index].finalSection = e.target.value || null;
            
            if (e.target.value) {
                statusSpan.className = 'student-status inline-flex items-center gap-1 px-3 py-1 bg-green-100 text-green-800 border-green-200 rounded-full text-xs font-semibold border';
                statusSpan.innerHTML = '<i class="fas fa-check-circle"></i> Assigned';
            } else {
                statusSpan.className = 'student-status inline-flex items-center gap-1 px-3 py-1 bg-amber-100 text-amber-800 border-amber-200 rounded-full text-xs font-semibold border';
                statusSpan.innerHTML = '<i class="fas fa-clock"></i> Pending';
            }
        }
    });
}

function viewStudentDetails(lrn) {
    if (lrn) {
        window.location.href = `/coordinator/student-edit/${lrn}/`;
    } else {
        showNotification('Unable to load student details', 'error');
    }
}

// Removed - AI Assignment runs automatically when enabled, no manual trigger needed
// runAIAssignment() function removed - assignments happen in real-time via backend signals

// Removed - these functions did nothing useful
// saveAssignments() and finalizeAssignments() removed
// clearAllAssignments() removed - data is read-only from backend

function exportAssignments() {
    showNotification('Export functionality coming soon', 'info');
}

function printAssignments() {
    window.print();
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

    const bgColor = type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' : 'bg-primary';

    const icon = type === 'success' ? 'fa-check-circle' :
        type === 'error' ? 'fa-exclamation-circle' :
            type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';

    notification.className = `${bgColor} text-white px-6 py-4 rounded-xl shadow-lg flex items-center gap-3 animate-slide-in`;
    notification.innerHTML = `
        <i class="fas ${icon} text-xl"></i>
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

// Update statistics counters
function updateStatistics() {
    // Total students
    const totalStudents = studentsData.length;
    document.getElementById('studentsCount').textContent = totalStudents;

    // Approved students
    const approvedStudents = studentsData.filter(s => s.admin_approved).length;
    document.getElementById('approvedCount').textContent = approvedStudents;

    // Pending students
    const pendingStudents = totalStudents - approvedStudents;
    document.getElementById('pendingCount').textContent = pendingStudents;

    // Sections available
    document.getElementById('sectionsCount').textContent = sections.length;

    // Update AI description
    const aiDescription = document.getElementById('aiDescription');
    if (approvedStudents > 0 && pendingStudents > 0) {
        aiDescription.textContent = `${approvedStudents} students approved and ready for assignment. ${pendingStudents} students pending admin approval.`;
    } else if (approvedStudents > 0) {
        aiDescription.textContent = `All ${approvedStudents} students have been approved and are ready for section assignment.`;
    } else {
        aiDescription.textContent = 'Use AI to automatically assign students to optimal sections based on multiple criteria';
    }
}

function setAISuggestions(assign = false) {
    if (!sections.length) return;

    const capacityMap = Object.fromEntries(sections.map(s => [s.id, s.capacity || 0]));
    const loadMap = sections.reduce((acc, s) => ({ ...acc, [s.id]: 0 }), {});

    // Current loads from existing finalSection assignments
    studentsData.forEach(s => {
        if (s.finalSection && loadMap[s.finalSection] !== undefined) {
            loadMap[s.finalSection] += 1;
        }
    });

    const findBestSection = () => {
        let best = null;
        sections.forEach(sec => {
            const current = loadMap[sec.id] || 0;
            const capacity = capacityMap[sec.id] || 0;
            const available = capacity ? capacity - current : Number.POSITIVE_INFINITY;
            if (best === null) {
                best = { id: sec.id, available, current };
                return;
            }
            const bestAvailable = best.available;
            const bestCurrent = best.current;
            if (available > bestAvailable || (available === bestAvailable && current < bestCurrent)) {
                best = { id: sec.id, available, current };
            }
        });
        return best?.id || (sections[0]?.id ?? null);
    };

    studentsData = studentsData.map(student => {
        if (!student.admin_approved) return student; // only auto-place approved
        const target = findBestSection();
        if (!target) return student;

        // Update load if we are assigning
        if (assign) {
            if (student.finalSection && loadMap[student.finalSection] !== undefined) {
                loadMap[student.finalSection] -= 1;
            }
            loadMap[target] = (loadMap[target] || 0) + 1;
            return { ...student, aiSuggestion: target, finalSection: target };
        }

        return { ...student, aiSuggestion: target };
    });
}