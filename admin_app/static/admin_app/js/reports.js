    document.addEventListener('DOMContentLoaded', function () {
        // Load reports data
        loadReportsData();

        // Initialize pagination
        updatePagination();

        // Add event listeners for filters
        document.getElementById('schoolYearFilter').addEventListener('change', filterReports);
        document.getElementById('reportTypeFilter').addEventListener('change', filterReports);
    });

    // Sample system reports data (admin-specific)
    const reportsData = [
        { id: 1, name: 'System Audit Report - Q1 2024', type: 'Audit', generatedBy: 'System Admin', date: 'Mar 18, 2024', size: '3.2 MB', status: 'completed' },
        { id: 2, name: 'User Activity Analysis - March', type: 'Activity', generatedBy: 'Admin', date: 'Mar 17, 2024', size: '2.8 MB', status: 'completed' },
        { id: 3, name: 'Database Performance Report', type: 'System', generatedBy: 'System Admin', date: 'Mar 16, 2024', size: '4.1 MB', status: 'completed' },
        { id: 4, name: 'Security Compliance Report', type: 'Security', generatedBy: 'Admin', date: 'Mar 15, 2024', size: '3.5 MB', status: 'completed' },
        { id: 5, name: 'Monthly Executive Summary', type: 'Executive', generatedBy: 'System Admin', date: 'Mar 14, 2024', size: '2.9 MB', status: 'completed' },
        { id: 6, name: 'Backup Status Report', type: 'System', generatedBy: 'Admin', date: 'Mar 13, 2024', size: '1.8 MB', status: 'completed' },
        { id: 7, name: 'System Usage Statistics', type: 'Analytics', generatedBy: 'System Admin', date: 'Mar 12, 2024', size: '3.1 MB', status: 'completed' },
        { id: 8, name: 'Data Integrity Report', type: 'System', generatedBy: 'Admin', date: 'Mar 11, 2024', size: '2.7 MB', status: 'completed' },
        { id: 9, name: 'Quarterly Performance Review', type: 'Executive', generatedBy: 'System Admin', date: 'Mar 10, 2024', size: '5.2 MB', status: 'completed' },
        { id: 10, name: 'User Access Logs', type: 'Audit', generatedBy: 'Admin', date: 'Mar 09, 2024', size: '3.9 MB', status: 'completed' },
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
                <td class="px-6 py-4 text-gray-600">${report.generatedBy}</td>
                <td class="px-6 py-4 text-gray-600">${report.date}</td>
                <td class="px-6 py-4 text-gray-600">${report.size}</td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <button onclick="viewReport(${report.id})" class="text-blue-600 hover:text-blue-700" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button onclick="downloadReport(${report.id})" class="text-green-600 hover:text-green-700" title="Download">
                            <i class="fas fa-download"></i>
                        </button>
                        <button onclick="shareReport(${report.id})" class="text-purple-600 hover:text-purple-700" title="Share">
                            <i class="fas fa-share-alt"></i>
                        </button>
                        <button onclick="archiveReport(${report.id})" class="text-yellow-600 hover:text-yellow-700" title="Archive">
                            <i class="fas fa-archive"></i>
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
            case 'audit': return 'fa-shield-alt';
            case 'security': return 'fa-lock';
            case 'executive': return 'fa-chart-line';
            case 'activity': return 'fa-users';
            case 'system': return 'fa-server';
            case 'analytics': return 'fa-chart-bar';
            default: return 'fa-file';
        }
    }

    function getFileColor(type) {
        switch (type.toLowerCase()) {
            case 'audit': return 'text-red-600';
            case 'security': return 'text-purple-600';
            case 'executive': return 'text-blue-600';
            case 'activity': return 'text-green-600';
            case 'system': return 'text-gray-600';
            case 'analytics': return 'text-yellow-600';
            default: return 'text-gray-600';
        }
    }

    function getTypeBadgeColor(type) {
        switch (type.toLowerCase()) {
            case 'audit': return 'bg-red-100 text-red-800';
            case 'security': return 'bg-purple-100 text-purple-800';
            case 'executive': return 'bg-blue-100 text-blue-800';
            case 'activity': return 'bg-green-100 text-green-800';
            case 'system': return 'bg-gray-100 text-gray-800';
            case 'analytics': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    function filterReports(filterType = 'all') {
        const schoolYear = document.getElementById('schoolYearFilter').value;
        const reportType = document.getElementById('reportTypeFilter').value;

        filteredReports = reportsData.filter(report => {
            let matches = true;

            // Filter by school year (simulated)
            if (schoolYear !== '2025-2026') {
                // In real app, this would check report date range
                matches = report.name.toLowerCase().includes(schoolYear.slice(2, 4));
            }

            // Filter by report type
            if (reportType !== 'all') {
                matches = matches && report.type.toLowerCase().includes(reportType.toLowerCase());
            }

            // Additional filters
            if (filterType === 'audit') {
                matches = matches && report.type === 'Audit';
            } else if (filterType === 'system') {
                matches = matches && report.type === 'System';
            } else if (filterType === 'recent') {
                // Simulated recent filter (last 30 days)
                const reportDate = new Date(report.date);
                const monthAgo = new Date();
                monthAgo.setDate(monthAgo.getDate() - 30);
                matches = matches && reportDate >= monthAgo;
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
            case 'audit':
                title = 'System Audit Report';
                message = 'Generating system security and audit logs...';
                break;
            case 'user_activity':
                title = 'User Activity Report';
                message = 'Compiling user activity and access logs...';
                break;
            case 'data_management':
                title = 'Data Management Report';
                message = 'Analyzing database performance and storage...';
                break;
            default:
                title = 'System Report';
                message = 'Preparing your system report...';
        }

        reportTitle.textContent = title;
        reportMessage.textContent = message;

        // Reset steps
        ['reportStep1', 'reportStep2', 'reportStep3', 'reportStep4'].forEach((id, index) => {
            const element = document.getElementById(id);
            element.classList.remove('text-green-600', 'font-semibold');
            element.textContent = element.textContent.replace('✓ ', '');
            if (index === 0) element.textContent = 'Collecting system logs';
            if (index === 1) element.textContent = 'Analyzing user activity';
            if (index === 2) element.textContent = 'Compiling metrics';
            if (index === 3) element.textContent = 'Finalizing report';
        });

        modal.classList.remove('hidden');

        // Simulate report generation
        let progress = 0;
        const interval = setInterval(() => {
            progress += 4;
            progressBar.style.width = progress + '%';

            // Update steps
            if (progress >= 20) {
                document.getElementById('reportStep1').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep1').textContent = '✓ Collecting system logs';
            }
            if (progress >= 45) {
                document.getElementById('reportStep2').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep2').textContent = '✓ Analyzing user activity';
            }
            if (progress >= 70) {
                document.getElementById('reportStep3').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep3').textContent = '✓ Compiling metrics';
            }
            if (progress >= 90) {
                document.getElementById('reportStep4').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep4').textContent = '✓ Finalizing report';
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
                        type: type === 'audit' ? 'Audit' : type === 'user_activity' ? 'Activity' : 'System',
                        generatedBy: 'System Admin',
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

    function generateAdvancedReport() {
        const modal = document.getElementById('reportModal');
        const progressBar = document.getElementById('reportProgress');
        const reportTitle = document.getElementById('reportTitle');
        const reportMessage = document.getElementById('reportMessage');

        reportTitle.textContent = 'Advanced System Report';
        reportMessage.textContent = 'Building comprehensive system analysis with advanced metrics...';

        // Reset steps
        ['reportStep1', 'reportStep2', 'reportStep3', 'reportStep4'].forEach((id, index) => {
            const element = document.getElementById(id);
            element.classList.remove('text-green-600', 'font-semibold');
            element.textContent = element.textContent.replace('✓ ', '');
            if (index === 0) element.textContent = 'Collecting system logs';
            if (index === 1) element.textContent = 'Analyzing user activity';
            if (index === 2) element.textContent = 'Compiling metrics';
            if (index === 3) element.textContent = 'Finalizing report';
        });

        modal.classList.remove('hidden');

        // Simulate advanced report generation
        let progress = 0;
        const interval = setInterval(() => {
            progress += 3;
            progressBar.style.width = progress + '%';

            // Update steps
            if (progress >= 15) {
                document.getElementById('reportStep1').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep1').textContent = '✓ Collecting system logs';
            }
            if (progress >= 40) {
                document.getElementById('reportStep2').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep2').textContent = '✓ Analyzing user activity';
            }
            if (progress >= 65) {
                document.getElementById('reportStep3').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep3').textContent = '✓ Compiling metrics';
            }
            if (progress >= 85) {
                document.getElementById('reportStep4').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep4').textContent = '✓ Finalizing report';
            }

            if (progress >= 100) {
                clearInterval(interval);
                setTimeout(() => {
                    modal.classList.add('hidden');
                    showNotification('Advanced system report generated successfully', 'success');
                    progressBar.style.width = '0%';

                    // Add new advanced report to the list
                    const newReport = {
                        id: reportsData.length + 1,
                        name: `Advanced System Analysis - ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`,
                        type: 'Analytics',
                        generatedBy: 'System Admin',
                        date: new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
                        size: `${(Math.random() * 4 + 3).toFixed(1)} MB`,
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
        showNotification('Archiving all system reports to ZIP file...', 'info');
        setTimeout(() => {
            showNotification('All reports archived successfully', 'success');
        }, 1500);
    }

    function printReportList() {
        showNotification('Generating printable summary...', 'info');
        setTimeout(() => {
            window.print();
        }, 500);
    }

    function viewReport(id) {
        const report = reportsData.find(r => r.id === id);
        showNotification(`Opening ${report.name} in report viewer...`, 'info');
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

    function archiveReport(id) {
        const report = reportsData.find(r => r.id === id);
        if (confirm(`Archive ${report.name}? Archived reports are moved to long-term storage.`)) {
            showNotification(`${report.name} archived successfully`, 'success');
        }
    }

    function useTemplate(templateType) {
        let templateName = '';
        switch (templateType) {
            case 'executive': templateName = 'Monthly Executive Report Template'; break;
            case 'quarterly': templateName = 'Quarterly Performance Template'; break;
            case 'security': templateName = 'Security Audit Template'; break;
        }

        showNotification(`${templateName} loaded. You can now customize it.`, 'info');

        // In real app, this would load the template into the advanced report builder
        setTimeout(() => {
            document.getElementById('reportTitle').scrollIntoView({ behavior: 'smooth' });
        }, 100);
    }

    function showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');

        const bgColor = type === 'success' ? 'bg-green-500' :
            type === 'error' ? 'bg-red-500' :
                type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500';

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