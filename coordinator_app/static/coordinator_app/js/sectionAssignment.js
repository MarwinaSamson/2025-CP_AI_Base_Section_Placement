document.addEventListener('DOMContentLoaded', function () {
        // AI Toggle
        const aiToggle = document.getElementById('aiToggle');
        const aiStatus = document.getElementById('aiStatus');
        const aiSettings = document.getElementById('aiSettings');

        aiToggle.addEventListener('change', function () {
            if (this.checked) {
                aiStatus.textContent = 'Enabled';
                aiSettings.classList.remove('hidden');
                showNotification('AI Assistant enabled', 'success');
            } else {
                aiStatus.textContent = 'Disabled';
                aiSettings.classList.add('hidden');
                showNotification('AI Assistant disabled', 'warning');
            }
        });

        // Load sample data
        loadStudentsData();

        // Initialize tooltips and interactions
        initializeTableInteractions();
    });

    function loadStudentsData() {
        const tableBody = document.getElementById('studentsTable');
        const sampleData = [
            { name: 'Santos, Maria R.', lrn: '234567890123', exam: 92, interview: 88, aiSuggestion: 'STEM-1' },
            { name: 'Gonzales, Pedro M.', lrn: '345678901234', exam: 85, interview: 82, aiSuggestion: 'STEM-2' },
            { name: 'Fernandez, Ana L.', lrn: '456789012345', exam: 95, interview: 90, aiSuggestion: 'STEM-1' },
            { name: 'Martinez, Carlos J.', lrn: '567890123456', exam: 78, interview: 85, aiSuggestion: 'STEM-3' },
            { name: 'Torres, Sofia R.', lrn: '678901234567', exam: 88, interview: 92, aiSuggestion: 'STEM-2' },
            { name: 'Reyes, Miguel A.', lrn: '789012345678', exam: 91, interview: 87, aiSuggestion: 'STEM-1' },
            { name: 'Cruz, Isabella M.', lrn: '890123456789', exam: 82, interview: 79, aiSuggestion: 'STEM-4' },
            { name: 'Aquino, Luis D.', lrn: '901234567890', exam: 96, interview: 94, aiSuggestion: 'STEM-1' }
        ];

        tableBody.innerHTML = '';

        sampleData.forEach((student, index) => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50';
            row.innerHTML = `
                <td class="px-6 py-4 font-medium text-gray-900">${student.name}</td>
                <td class="px-6 py-4 text-gray-600">${student.lrn}</td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 ${getScoreColor(student.exam)} rounded-full text-xs font-semibold">
                        ${student.exam}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 ${getScoreColor(student.interview)} rounded-full text-xs font-semibold">
                        ${student.interview}%
                    </span>
                </td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                        <i class="fas fa-robot mr-1"></i>${student.aiSuggestion}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <select class="section-select w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary" data-index="${index}">
                        <option value="">Select Section</option>
                        <option value="STEM-1">STEM-1 (Sampaguita)</option>
                        <option value="STEM-2">STEM-2 (Rosal)</option>
                        <option value="STEM-3">STEM-3 (Orchid)</option>
                        <option value="STEM-4">STEM-4 (Daisy)</option>
                    </select>
                </td>
                <td class="px-6 py-4">
                    <span class="final-section font-medium text-gray-900" id="finalSection${index}">-</span>
                </td>
            `;
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
        // When section is selected, update final section
        document.addEventListener('change', function (e) {
            if (e.target.classList.contains('section-select')) {
                const index = e.target.dataset.index;
                const finalSection = document.getElementById(`finalSection${index}`);
                finalSection.textContent = e.target.value || '-';

                // If AI is enabled and no manual selection, suggest AI recommendation
                if (!e.target.value && document.getElementById('aiToggle').checked) {
                    const aiSuggestion = e.target.closest('tr').querySelector('.bg-green-100').textContent.split(' ')[1];
                    e.target.value = aiSuggestion;
                    finalSection.textContent = aiSuggestion;
                }
            }
        });
    }

    function runAIAssignment() {
        const modal = document.getElementById('aiProcessingModal');
        const progressBar = document.getElementById('aiProgressBar');
        const progressText = document.getElementById('aiProgressText');
        const aiStats = document.getElementById('aiStats');

        modal.classList.remove('hidden');

        // Get selected criteria
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

            // Update progress text every 20%
            if (progress % 20 === 0 && currentStep < steps.length) {
                progressText.textContent = steps[currentStep];
                currentStep++;

                // Update stats
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

                    // Apply AI suggestions to table
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
        showNotification('Exporting section assignments to Excel...', 'info');
        setTimeout(() => {
            showNotification('Assignments exported successfully', 'success');
        }, 1500);
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