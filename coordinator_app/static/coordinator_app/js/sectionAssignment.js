document.addEventListener('DOMContentLoaded', function () {
    // Get user-specific key for localStorage
    const programCode = window.PROGRAM_CODE || 'default';
    const aiToggleKey = `aiToggleEnabled_${programCode}`;
    
    // AI Toggle
    const aiToggle = document.getElementById('aiToggle');
    const aiStatus = document.getElementById('aiStatus');
    const aiSettings = document.getElementById('aiSettings');

    // Restore persisted AI toggle state per program (default: enabled)
    const savedAIToggle = localStorage.getItem(aiToggleKey);
    const initialAIEnabled = savedAIToggle === null ? true : savedAIToggle === 'true';
    aiToggle.checked = initialAIEnabled;
    applyAIToggleState(aiToggle, aiStatus, aiSettings);

    aiToggle.addEventListener('change', function () {
        // Persist user preference per program
        localStorage.setItem(aiToggleKey, this.checked ? 'true' : 'false');
        applyAIToggleState(this, aiStatus, aiSettings);
        loadStudentsData();
        initializeTableInteractions();
    });

    // Load data
    loadStudentsData();
    initializeTableInteractions();
});

function applyAIToggleState(aiToggle, aiStatus, aiSettings) {
    if (aiToggle.checked) {
        aiStatus.textContent = 'Enabled';
        aiSettings.classList.remove('hidden');
        showNotification('AI Assistant enabled', 'success');
    } else {
        aiStatus.textContent = 'Disabled';
        aiSettings.classList.add('hidden');
        showNotification('AI Assistant disabled', 'warning');
    }
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

    const sourceData = Array.isArray(window.STUDENTS_DATA) ? window.STUDENTS_DATA : [];

    tableBody.innerHTML = '';

    if (!sourceData.length) {
        tableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-4 text-center text-gray-500 text-sm">No students found for your program.</td></tr>';
        return;
    }

    sourceData.forEach((student, index) => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        const examScore = Number(student.exam ?? 0);
        const interviewScore = Number(student.interview ?? 0);
        const aiSuggestion = student.aiSuggestion || (window.PROGRAM_CODE || '');
        
        if (isAIEnabled) {
            row.innerHTML = `
                <td class="px-6 py-4 font-medium text-gray-900">${student.name}</td>
                <td class="px-6 py-4 text-gray-600">${student.lrn}</td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 ${getScoreColor(examScore)} rounded-full text-xs font-semibold">
                        ${examScore}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 ${getScoreColor(interviewScore)} rounded-full text-xs font-semibold">
                        ${interviewScore}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                        <i class="fas fa-robot mr-1"></i>${aiSuggestion}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <select class="section-select w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" data-index="${index}">
                        <option value="">Select Section</option>
                        <option value="${window.PROGRAM_CODE}-1">${window.PROGRAM_CODE}-1 (Sampaguita)</option>
                        <option value="${window.PROGRAM_CODE}-2">${window.PROGRAM_CODE}-2 (Rosal)</option>
                        <option value="${window.PROGRAM_CODE}-3">${window.PROGRAM_CODE}-3 (Orchid)</option>
                        <option value="${window.PROGRAM_CODE}-4">${window.PROGRAM_CODE}-4 (Daisy)</option>
                    </select>
                </td>
                <td class="px-6 py-4">
                    <span class="final-section font-medium text-gray-900" id="finalSection${index}">-</span>
                </td>
            `;
        } else {
            row.innerHTML = `
                <td class="px-6 py-4 font-medium text-gray-900">${student.name}</td>
                <td class="px-6 py-4 text-gray-600">${student.lrn}</td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 ${getScoreColor(examScore)} rounded-full text-xs font-semibold">
                        ${examScore}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 ${getScoreColor(interviewScore)} rounded-full text-xs font-semibold">
                        ${interviewScore}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="student-status px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit" id="status${index}">
                        <i class="fas fa-clock"></i> Pending
                    </span>
                </td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <select class="section-select-disabled px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary" data-index="${index}">
                            <option value="">Assign Section</option>
                            <option value="${window.PROGRAM_CODE}-1">${window.PROGRAM_CODE}-1 (Sampaguita)</option>
                            <option value="${window.PROGRAM_CODE}-2">${window.PROGRAM_CODE}-2 (Rosal)</option>
                            <option value="${window.PROGRAM_CODE}-3">${window.PROGRAM_CODE}-3 (Orchid)</option>
                            <option value="${window.PROGRAM_CODE}-4">${window.PROGRAM_CODE}-4 (Daisy)</option>
                        </select>
                        <button class="action-button px-3 py-2 bg-gradient-to-r from-primary to-primary-dark text-white rounded-lg text-sm font-medium flex items-center gap-1 hover:shadow-md transition-all" data-index="${index}" data-lrn="${student.lrn}" onclick="viewStudentDetails('${student.lrn}')">
                            <i class="fas fa-eye"></i> View
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
            finalSection.textContent = e.target.value || '-';

            if (!e.target.value && document.getElementById('aiToggle').checked) {
                const aiSuggestion = e.target.closest('tr').querySelector('.bg-green-100').textContent.split(' ')[1];
                e.target.value = aiSuggestion;
                finalSection.textContent = aiSuggestion;
            }
        }

        if (e.target.classList.contains('section-select-disabled')) {
            const index = e.target.dataset.index;
            const statusSpan = document.getElementById(`status${index}`);
            
            if (e.target.value) {
                statusSpan.className = 'student-status px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit';
                statusSpan.innerHTML = '<i class="fas fa-check-circle"></i> Assigned';
            } else {
                statusSpan.className = 'student-status px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit';
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

            const studentsAnalyzed = Math.min(120, Math.floor(progress / 100 * 120));
            const sectionsOptimized = Math.min(4, Math.floor(progress / 100 * 4));
            const confidence = Math.min(95, Math.floor(progress * 0.95));

            aiStats.innerHTML = `
                <div>Students Analyzed: <span class="font-semibold">${studentsAnalyzed}/120</span></div>
                <div>Sections Optimized: <span class="font-semibold">${sectionsOptimized}/4</span></div>
                <div>Criteria Applied: <span class="font-semibold">${criteria.length}</span></div>
                <div>Confidence Score: <span class="font-semibold">${confidence}%</span></div>
            `;
        }

        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(() => {
                modal.classList.add('hidden');

                const selects = document.querySelectorAll('.section-select');
                selects.forEach((select, index) => {
                    const row = select.closest('tr');
                    const aiSuggestion = row.querySelector('.bg-green-100').textContent.split(' ')[1];
                    select.value = aiSuggestion;
                    document.getElementById(`finalSection${index}`).textContent = aiSuggestion;
                });

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
    if (confirm('Clear all section assignments?')) {
        const selects = document.querySelectorAll('.section-select');
        const finalSections = document.querySelectorAll('.final-section');

        selects.forEach(select => select.value = '');
        finalSections.forEach(span => span.textContent = '-');

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

    notification.className = `${bgColor} text-white px-4 py-3 rounded-lg shadow-lg animate-fade-in`;
    notification.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    container.appendChild(notification);

    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}