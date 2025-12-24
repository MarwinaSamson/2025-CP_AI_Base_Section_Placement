document.addEventListener('DOMContentLoaded', function () {
        // Load reports data
        loadReportsData();

        // Initialize pagination
        updatePagination();

        // Add event listeners for filters
        document.getElementById('programFilter').addEventListener('change', filterReports);
        document.getElementById('reportTypeFilter').addEventListener('change', filterReports);
    });

    // Sample reports data
    const reportsData = [
        { id: 1, name: 'STEM Enrollment Report Q1 2024', type: 'PDF', date: 'Mar 18, 2024', size: '2.4 MB', status: 'completed' },
        { id: 2, name: 'Exam Results Analysis - March', type: 'Excel', date: 'Mar 17, 2024', size: '1.8 MB', status: 'completed' },
        { id: 3, name: 'Section Assignment Summary', type: 'Word', date: 'Mar 16, 2024', size: '1.2 MB', status: 'completed' },
        { id: 4, name: 'Student Demographics Report', type: 'PDF', date: 'Mar 15, 2024', size: '3.1 MB', status: 'completed' },
        { id: 5, name: 'AI Assignment Performance', type: 'PDF', date: 'Mar 14, 2024', size: '2.7 MB', status: 'completed' },
        { id: 6, name: 'Interview Results Summary', type: 'Excel', date: 'Mar 13, 2024', size: '1.5 MB', status: 'completed' },
        { id: 7, name: 'Monthly Enrollment Statistics', type: 'PDF', date: 'Mar 12, 2024', size: '2.9 MB', status: 'completed' },
        { id: 8, name: 'Program Comparison Report', type: 'Word', date: 'Mar 11, 2024', size: '1.9 MB', status: 'completed' },
    ];

    let currentPage = 1;
    const itemsPerPage = 8;
    let filteredReports = [...reportsData];

    function loadReportsData() {
        const tableBody = document.getElementById('reportsTable');
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const pageReports = filteredReports.slice(startIndex, endIndex);

        tableBody.innerHTML = '';

        pageReports.forEach((report, index) => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50';
            row.innerHTML = `
                <td class="px-6 py-4 font-medium text-gray-900">
                    <div class="flex items-center gap-3">
                        <i class="fas ${getFileIcon(report.type)} ${getFileColor(report.type)}"></i>
                        <span>${report.name}</span>
                    </div>
                </td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 ${getTypeBadgeColor(report.type)} rounded-full text-xs font-semibold">
                        ${report.type}
                    </span>
                </td>
                <td class="px-6 py-4 text-gray-600">${report.date}</td>
                <td class="px-6 py-4 text-gray-600">${report.size}</td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                        ${report.status}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <button onclick="viewReport(${report.id})" class="text-primary hover:text-primary-dark" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button onclick="downloadReport(${report.id})" class="text-green-600 hover:text-green-700" title="Download">
                            <i class="fas fa-download"></i>
                        </button>
                        <button onclick="shareReport(${report.id})" class="text-purple-600 hover:text-purple-700" title="Share">
                            <i class="fas fa-share-alt"></i>
                        </button>
                        <button onclick="deleteReport(${report.id})" class="text-red-600 hover:text-red-700" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tableBody.appendChild(row);
        });

        updatePagination();
    }

    function getFileIcon(type) {
        switch (type.toLowerCase()) {
            case 'pdf': return 'fa-file-pdf';
            case 'excel': return 'fa-file-excel';
            case 'word': return 'fa-file-word';
            default: return 'fa-file';
        }
    }

    function getFileColor(type) {
        switch (type.toLowerCase()) {
            case 'pdf': return 'text-red-600';
            case 'excel': return 'text-green-600';
            case 'word': return 'text-primary';
            default: return 'text-gray-600';
        }
    }

    function getTypeBadgeColor(type) {
        switch (type.toLowerCase()) {
            case 'pdf': return 'bg-red-100 text-red-800';
            case 'excel': return 'bg-green-100 text-green-800';
            case 'word': return 'bg-red-100 text-primary';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    function filterReports(filterType = 'all') {
        const program = document.getElementById('programFilter').value;
        const reportType = document.getElementById('reportTypeFilter').value;

        filteredReports = reportsData.filter(report => {
            let matches = true;

            // Filter by program (in real app, this would check report content)
            if (program !== 'STEM') {
                // Simulated filter
                matches = report.name.toLowerCase().includes(program.toLowerCase());
            }

            // Filter by report type
            if (reportType !== 'all') {
                matches = matches && report.name.toLowerCase().includes(reportType.toLowerCase());
            }

            // Additional filters
            if (filterType === 'pdf') {
                matches = matches && report.type === 'PDF';
            } else if (filterType === 'excel') {
                matches = matches && report.type === 'Excel';
            } else if (filterType === 'recent') {
                // Simulated recent filter (last 7 days)
                const reportDate = new Date(report.date);
                const weekAgo = new Date();
                weekAgo.setDate(weekAgo.getDate() - 7);
                matches = matches && reportDate >= weekAgo;
            }

            return matches;
        });

        currentPage = 1;
        loadReportsData();
    }

    function updatePagination() {
        const totalPages = Math.ceil(filteredReports.length / itemsPerPage);
        const startItem = (currentPage - 1) * itemsPerPage + 1;
        const endItem = Math.min(currentPage * itemsPerPage, filteredReports.length);

        document.getElementById('showingCount').textContent = `${startItem}-${endItem}`;
        document.getElementById('totalCount').textContent = filteredReports.length;

        document.getElementById('prevBtn').disabled = currentPage === 1;
        document.getElementById('nextBtn').disabled = currentPage === totalPages || totalPages === 0;
    }

    function previousPage() {
        if (currentPage > 1) {
            currentPage--;
            loadReportsData();
        }
    }

    function nextPage() {
        const totalPages = Math.ceil(filteredReports.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            loadReportsData();
        }
    }

    function generateReport(type) {
        const modal = document.getElementById('reportModal');
        const progressBar = document.getElementById('reportProgress');
        const reportTitle = document.getElementById('reportTitle');
        const reportMessage = document.getElementById('reportMessage');

        // Set report details based on type
        let title = '', message = '';
        switch (type) {
            case 'enrollment':
                title = 'Enrollment Report';
                message = 'Generating enrollment statistics and analysis...';
                break;
            case 'exam':
                title = 'Exam Results Report';
                message = 'Compiling exam performance data...';
                break;
            case 'sections':
                title = 'Section Assignment Report';
                message = 'Creating section assignment summary...';
                break;
            default:
                title = 'Report Generation';
                message = 'Preparing your report...';
        }

        reportTitle.textContent = title;
        reportMessage.textContent = message;

        // Reset steps
        ['reportStep1', 'reportStep2', 'reportStep3', 'reportStep4'].forEach((id, index) => {
            const element = document.getElementById(id);
            element.classList.remove('text-green-600', 'font-semibold');
            element.textContent = element.textContent.replace('✓ ', '');
            if (index === 0) element.textContent = 'Collecting data';
            if (index === 1) element.textContent = 'Formatting document';
            if (index === 2) element.textContent = 'Adding charts';
            if (index === 3) element.textContent = 'Finalizing';
        });

        modal.classList.remove('hidden');

        // Simulate report generation
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            progressBar.style.width = progress + '%';

            // Update steps
            if (progress >= 25) {
                document.getElementById('reportStep1').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep1').textContent = '✓ Collecting data';
            }
            if (progress >= 50) {
                document.getElementById('reportStep2').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep2').textContent = '✓ Formatting document';
            }
            if (progress >= 75) {
                document.getElementById('reportStep3').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep3').textContent = '✓ Adding charts';
            }
            if (progress >= 95) {
                document.getElementById('reportStep4').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep4').textContent = '✓ Finalizing';
            }

            if (progress >= 100) {
                clearInterval(interval);
                setTimeout(() => {
                    modal.classList.add('hidden');
                    showNotification(`${title} generated successfully`, 'success');
                    progressBar.style.width = '0%';

                    // Add new report to the list
                    const newReport = {
                        id: reportsData.length + 1,
                        name: `${title} - ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`,
                        type: type === 'exam' ? 'Excel' : type === 'sections' ? 'Word' : 'PDF',
                        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
                        size: `${(Math.random() * 2 + 1).toFixed(1)} MB`,
                        status: 'completed'
                    };

                    reportsData.unshift(newReport);
                    filteredReports = [...reportsData];
                    loadReportsData();
                }, 500);
            }
        }, 100);
    }

    function generateCustomReport() {
        const modal = document.getElementById('reportModal');
        const progressBar = document.getElementById('reportProgress');
        const reportTitle = document.getElementById('reportTitle');
        const reportMessage = document.getElementById('reportMessage');

        reportTitle.textContent = 'Custom Report';
        reportMessage.textContent = 'Building your custom report with selected parameters...';

        // Reset steps
        ['reportStep1', 'reportStep2', 'reportStep3', 'reportStep4'].forEach((id, index) => {
            const element = document.getElementById(id);
            element.classList.remove('text-green-600', 'font-semibold');
            element.textContent = element.textContent.replace('✓ ', '');
            if (index === 0) element.textContent = 'Collecting data';
            if (index === 1) element.textContent = 'Formatting document';
            if (index === 2) element.textContent = 'Adding charts';
            if (index === 3) element.textContent = 'Finalizing';
        });

        modal.classList.remove('hidden');

        // Simulate custom report generation
        let progress = 0;
        const interval = setInterval(() => {
            progress += 4;
            progressBar.style.width = progress + '%';

            // Update steps
            if (progress >= 20) {
                document.getElementById('reportStep1').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep1').textContent = '✓ Collecting data';
            }
            if (progress >= 45) {
                document.getElementById('reportStep2').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep2').textContent = '✓ Formatting document';
            }
            if (progress >= 70) {
                document.getElementById('reportStep3').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep3').textContent = '✓ Adding charts';
            }
            if (progress >= 90) {
                document.getElementById('reportStep4').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep4').textContent = '✓ Finalizing';
            }

            if (progress >= 100) {
                clearInterval(interval);
                setTimeout(() => {
                    modal.classList.add('hidden');
                    showNotification('Custom report generated successfully', 'success');
                    progressBar.style.width = '0%';

                    // Add new custom report to the list
                    const newReport = {
                        id: reportsData.length + 1,
                        name: `Custom Report - ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`,
                        type: 'PDF',
                        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
                        size: `${(Math.random() * 3 + 2).toFixed(1)} MB`,
                        status: 'completed'
                    };

                    reportsData.unshift(newReport);
                    filteredReports = [...reportsData];
                    loadReportsData();
                }, 500);
            }
        }, 100);
    }

    function exportAllReports() {
        showNotification('Exporting all reports to ZIP file...', 'info');
        setTimeout(() => {
            showNotification('All reports exported successfully', 'success');
        }, 1500);
    }

    function printReportList() {
        window.print();
    }

    function viewReport(id) {
        showNotification(`Opening report #${id} for viewing...`, 'info');
        // In real app, this would open the report in a viewer
    }

    function downloadReport(id) {
        const report = reportsData.find(r => r.id === id);
        showNotification(`Downloading ${report.name}...`, 'info');
        // Simulate download
        setTimeout(() => {
            showNotification(`${report.name} downloaded successfully`, 'success');
        }, 1000);
    }

    function shareReport(id) {
        const report = reportsData.find(r => r.id === id);
        showNotification(`Sharing options for ${report.name}`, 'info');
        // In real app, this would open a share dialog
    }

    function deleteReport(id) {
        if (confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
            const index = reportsData.findIndex(r => r.id === id);
            if (index !== -1) {
                reportsData.splice(index, 1);
                filteredReports = [...reportsData];
                loadReportsData();
                showNotification('Report deleted successfully', 'success');
            }
        }
    }

    function useTemplate(templateType) {
        let templateName = '';
        switch (templateType) {
            case 'board': templateName = 'School Board Report Template'; break;
            case 'statistical': templateName = 'Statistical Summary Template'; break;
            case 'parent': templateName = 'Parent Communication Template'; break;
        }

        showNotification(`${templateName} loaded. You can now customize it.`, 'info');

        // In real app, this would load the template into the custom report builder
        setTimeout(() => {
            document.getElementById('reportTitle').scrollIntoView({ behavior: 'smooth' });
        }, 100);
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