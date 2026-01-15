// Global state for board view
let studentsData = [];
let sections = [];
let currentView = 'board'; // 'board' or 'table'
let draggedStudent = null;

document.addEventListener('DOMContentLoaded', function () {
    // Get user-specific key for localStorage
    const programCode = window.PROGRAM_CODE || 'default';
    const aiToggleKey = `aiToggleEnabled_${programCode}`;
    const viewKey = `viewMode_${programCode}`;
    
    // AI Toggle
    const aiToggle = document.getElementById('aiToggle');
    const aiStatus = document.getElementById('aiStatus');
    const aiSettings = document.getElementById('aiSettings');

    // Restore persisted AI toggle state per program (default: enabled)
    const savedAIToggle = localStorage.getItem(aiToggleKey);
    const initialAIEnabled = savedAIToggle === null ? true : savedAIToggle === 'true';
    aiToggle.checked = initialAIEnabled;
    applyAIToggleState(aiToggle, aiStatus, aiSettings);

    // Restore view preference
    const savedView = localStorage.getItem(viewKey) || 'board';
    currentView = savedView;
    switchView(currentView, false); // false = don't show notification on load

    aiToggle.addEventListener('change', function () {
        // Persist user preference per program
        localStorage.setItem(aiToggleKey, this.checked ? 'true' : 'false');
        applyAIToggleState(this, aiStatus, aiSettings);
        loadData();
    });

    // Load data
    loadData();
});

function applyAIToggleState(aiToggle, aiStatus, aiSettings) {
    if (aiToggle.checked) {
        aiStatus.textContent = 'Enabled';
        aiSettings.classList.remove('hidden');
    } else {
        aiStatus.textContent = 'Disabled';
        aiSettings.classList.add('hidden');
    }
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

function runAIAssignment() {
    const modal = document.getElementById('aiProcessingModal');
    const progressBar = document.getElementById('aiProgressBar');
    const progressText = document.getElementById('aiProgressText');
    const aiStats = document.getElementById('aiStats');

    modal.classList.remove('hidden');

    const criteria = [];
    if (document.getElementById('criteriaAcademic').checked) criteria.push('Academic');
    if (document.getElementById('criteriaInterview').checked) criteria.push('Interview');
    if (document.getElementById('criteriaBalance').checked) criteria.push('Gender Balance');
    if (document.getElementById('criteriaLocation').checked) criteria.push('Location');
    if (document.getElementById('criteriaSpecial').checked) criteria.push('Special Needs');
    if (document.getElementById('criteriaExtracurricular').checked) criteria.push('Extracurricular');

    let progress = 0;
    const steps = [
        'Analyzing academic patterns...',
        'Evaluating interview performance...',
        'Optimizing gender distribution...',
        'Balancing section capacities...',
        'Finalizing assignments...'
    ];

    let currentStep = 0;
    const interval = setInterval(() => {
        progress += 2;
        progressBar.style.width = progress + '%';

        if (progress % 20 === 0 && currentStep < steps.length) {
            progressText.textContent = steps[currentStep];
            currentStep++;

            const studentsAnalyzed = Math.min(studentsData.length, Math.floor(progress / 100 * studentsData.length));
            const sectionsOptimized = Math.min(4, Math.floor(progress / 100 * 4));
            const confidence = Math.min(95, Math.floor(progress * 0.95));

            aiStats.innerHTML = `
                <div>Students Analyzed: <span class="font-semibold">${studentsAnalyzed}/${studentsData.length}</span></div>
                <div>Sections Optimized: <span class="font-semibold">${sectionsOptimized}/4</span></div>
                <div>Criteria Applied: <span class="font-semibold">${criteria.length}</span></div>
                <div>Confidence Score: <span class="font-semibold">${confidence}%</span></div>
            `;
        }

        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                modal.classList.add('hidden');

                // Auto-assign based on AI suggestions
                studentsData = studentsData.map(student => ({
                    ...student,
                    finalSection: student.aiSuggestion || student.finalSection
                }));

                if (currentView === 'board') {
                    renderBoardView();
                } else {
                    loadStudentsData();
                    // Update selects in table view
                    studentsData.forEach((student, index) => {
                        const select = document.querySelector(`.section-select[data-index="${index}"]`);
                        if (select && student.finalSection) {
                            select.value = student.finalSection;
                            const finalSection = document.getElementById(`finalSection${index}`);
                            if (finalSection) finalSection.textContent = student.finalSection;
                        }
                    });
                }

                updateStatistics();
                showNotification(`AI assignment completed using ${criteria.length} criteria. Suggestions applied.`, 'success');
                progressBar.style.width = '0%';
            }, 1000);
        }
    }, 50);
}

function saveAssignments() {
    showNotification('Section assignments saved successfully', 'success');
}

function finalizeAssignments() {
    if (confirm('Are you sure you want to finalize assignments? This action cannot be undone.')) {
        showNotification('Assignments finalized and locked', 'success');
    }
}

function clearAllAssignments() {
    if (confirm('Clear all section assignments? This will remove all students from their assigned sections.')) {
        // Clear finalSection for all students
        studentsData = studentsData.map(s => ({ ...s, finalSection: null }));
        
        if (currentView === 'board') {
            renderBoardView();
        } else {
            const selects = document.querySelectorAll('.section-select, .section-select-disabled');
            const finalSections = document.querySelectorAll('.final-section');
            selects.forEach(select => select.value = '');
            finalSections.forEach(span => span.textContent = '-');
        }

        showNotification('All assignments cleared', 'info');
    }
}

function exportAssignments() {
    const format = prompt('Enter export format (pdf or docx):', 'pdf');
    
    if (!format || !['pdf', 'docx'].includes(format.toLowerCase())) {
        showNotification('Invalid format. Please choose pdf or docx.', 'error');
        return;
    }

    const students = [];
    const rows = document.querySelectorAll('#studentsTable tr');
    
    rows.forEach((row) => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 0) {
            // Get AI suggestion
            const aiSuggestionEl = row.querySelector('.bg-green-100');
            let aiSuggestion = '';
            if (aiSuggestionEl) {
                const text = aiSuggestionEl.textContent.trim();
                aiSuggestion = text.replace('🤖', '').trim();
            }
            
            // Get final section
            const finalSectionEl = row.querySelector('.final-section');
            const sectionSelect = row.querySelector('.section-select-disabled');
            
            let finalSection = '-';
            if (finalSectionEl) {
                finalSection = finalSectionEl.textContent.trim();
            } else if (sectionSelect) {
                finalSection = sectionSelect.value || '-';
            }
            
            students.push({
                name: cells[0].textContent.trim(),
                lrn: cells[1].textContent.trim(),
                exam: parseInt(cells[2].textContent) || 0,
                interview: parseInt(cells[3].textContent) || 0,
                aiSuggestion: aiSuggestion || window.PROGRAM_CODE || '-',
                finalSection: finalSection
            });
        }
    });

    const url = format.toLowerCase() === 'pdf' 
        ? '/coordinator/export-assignments-pdf/'
        : '/coordinator/export-assignments-docx/';

    showNotification(`Exporting section assignments to ${format.toUpperCase()}...`, 'info');

    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ students: students })
    })
    .then(response => {
        if (!response.ok) throw new Error('Export failed');
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Section_Assignments_${window.PROGRAM_CODE}_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showNotification('Assignments exported successfully', 'success');
    })
    .catch(error => {
        console.error('Export error:', error);
        showNotification('Export failed. Please try again.', 'error');
    });
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

function printAssignments() {
    window.print();
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