document.addEventListener('DOMContentLoaded', function () {
    // Populate section filter dropdown from backend data
    populateSectionFilter();

    // Load reports data
    loadReportsData();

    // Initialize pagination
    updatePagination();

    // Add event listener for report type filter
    document.getElementById('reportTypeFilter').addEventListener('change', function () {
        filterReports('all');
    });
});

// Populate section dropdown with real sections from backend
function populateSectionFilter() {
    const sectionSelect = document.getElementById('sectionFilter');
    if (window.sectionsData && window.sectionsData.length > 0) {
        window.sectionsData.forEach(function (section) {
            const option = document.createElement('option');
            option.value = section.id;
            option.textContent = section.name;
            sectionSelect.appendChild(option);
        });
    }
}

// Sample reports data (uses dynamic program code)
const programCode = window.programCode || 'STE';
const reportsData = [
    { id: 1, name: programCode + ' Enrollment Report - Current SY', type: 'PDF', category: 'enrollment', date: 'Feb 10, 2026', size: '2.4 MB', status: 'completed' },
    { id: 2, name: programCode + ' Academic Performance Summary', type: 'Excel', category: 'academic', date: 'Feb 9, 2026', size: '1.8 MB', status: 'completed' },
    { id: 3, name: programCode + ' Section Assignment Report', type: 'Word', category: 'sections', date: 'Feb 8, 2026', size: '1.2 MB', status: 'completed' },
    { id: 4, name: programCode + ' Student Demographics Report', type: 'PDF', category: 'enrollment', date: 'Feb 7, 2026', size: '3.1 MB', status: 'completed' },
    { id: 5, name: programCode + ' AI Placement Summary', type: 'PDF', category: 'summary', date: 'Feb 6, 2026', size: '2.7 MB', status: 'completed' },
    { id: 6, name: programCode + ' GWA Distribution Analysis', type: 'Excel', category: 'academic', date: 'Feb 5, 2026', size: '1.5 MB', status: 'completed' },
    { id: 7, name: programCode + ' Monthly Enrollment Statistics', type: 'PDF', category: 'enrollment', date: 'Feb 4, 2026', size: '2.9 MB', status: 'completed' },
    { id: 8, name: programCode + ' Section Capacity Report', type: 'Word', category: 'sections', date: 'Feb 3, 2026', size: '1.9 MB', status: 'completed' },
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

    if (pageReports.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="px-6 py-8 text-center text-gray-500">No reports found</td></tr>';
        updatePagination();
        return;
    }

    pageReports.forEach(function (report) {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        row.innerHTML =
            '<td class="px-6 py-4 font-medium text-gray-900">' +
                '<div class="flex items-center gap-3">' +
                    '<i class="fas ' + getFileIcon(report.type) + ' ' + getFileColor(report.type) + '"></i>' +
                    '<span>' + report.name + '</span>' +
                '</div>' +
            '</td>' +
            '<td class="px-6 py-4">' +
                '<span class="px-3 py-1 ' + getTypeBadgeColor(report.type) + ' rounded-full text-xs font-semibold">' +
                    report.type +
                '</span>' +
            '</td>' +
            '<td class="px-6 py-4 text-gray-600">' + report.date + '</td>' +
            '<td class="px-6 py-4 text-gray-600">' + report.size + '</td>' +
            '<td class="px-6 py-4">' +
                '<span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">' +
                    report.status +
                '</span>' +
            '</td>' +
            '<td class="px-6 py-4">' +
                '<div class="flex gap-2">' +
                    '<button onclick="viewReport(' + report.id + ')" class="text-primary hover:text-primary-dark" title="View">' +
                        '<i class="fas fa-eye"></i>' +
                    '</button>' +
                    '<button onclick="downloadReport(' + report.id + ')" class="text-green-600 hover:text-green-700" title="Download">' +
                        '<i class="fas fa-download"></i>' +
                    '</button>' +
                    '<button onclick="shareReport(' + report.id + ')" class="text-purple-600 hover:text-purple-700" title="Share">' +
                        '<i class="fas fa-share-alt"></i>' +
                    '</button>' +
                    '<button onclick="deleteReport(' + report.id + ')" class="text-red-600 hover:text-red-700" title="Delete">' +
                        '<i class="fas fa-trash"></i>' +
                    '</button>' +
                '</div>' +
            '</td>';
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

function filterReports(filterType) {
    var reportType = document.getElementById('reportTypeFilter').value;

    filteredReports = reportsData.filter(function (report) {
        var matches = true;

        // Filter by report category (from header dropdown)
        if (reportType !== 'all') {
            matches = matches && report.category === reportType;
        }

        // Additional filters (from button bar)
        if (filterType === 'pdf') {
            matches = matches && report.type === 'PDF';
        } else if (filterType === 'excel') {
            matches = matches && report.type === 'Excel';
        } else if (filterType === 'recent') {
            var reportDate = new Date(report.date);
            var weekAgo = new Date();
            weekAgo.setDate(weekAgo.getDate() - 7);
            matches = matches && reportDate >= weekAgo;
        }

        return matches;
    });

    currentPage = 1;
    loadReportsData();
}

function updatePagination() {
    var totalPages = Math.ceil(filteredReports.length / itemsPerPage);
    var startItem = filteredReports.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    var endItem = Math.min(currentPage * itemsPerPage, filteredReports.length);

    document.getElementById('showingCount').textContent = startItem + '-' + endItem;
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
    var totalPages = Math.ceil(filteredReports.length / itemsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        loadReportsData();
    }
}

function generateReport(type) {
    var modal = document.getElementById('reportModal');
    var progressBar = document.getElementById('reportProgress');
    var reportTitle = document.getElementById('reportTitle');
    var reportMessage = document.getElementById('reportMessage');

    // Set report details and build download URL
    var title = '', message = '', url = '', fileType = 'PDF';
    switch (type) {
        case 'enrollment':
            title = 'Enrollment Report';
            message = 'Generating enrollment statistics and analysis...';
            var status = document.getElementById('enrollmentStatusFilter').value;
            url = '/coordinator/reports/generate/enrollment/?status=' + encodeURIComponent(status);
            fileType = 'PDF';
            break;
        case 'academic':
            title = 'Academic Performance Report';
            message = 'Compiling subject grades and GWA data...';
            var gwaFilter = document.getElementById('academicFilter').value;
            url = '/coordinator/reports/generate/academic/?gwa_filter=' + encodeURIComponent(gwaFilter);
            fileType = 'Excel';
            break;
        case 'sections':
            title = 'Section Assignment Report';
            message = 'Creating section assignment summary...';
            var sectionId = document.getElementById('sectionFilter').value;
            url = '/coordinator/reports/generate/sections/?section_id=' + encodeURIComponent(sectionId);
            fileType = 'Word';
            break;
        default:
            title = 'Report Generation';
            message = 'Preparing your report...';
            return;
    }

    reportTitle.textContent = title;
    reportMessage.textContent = message;

    // Reset steps
    ['reportStep1', 'reportStep2', 'reportStep3', 'reportStep4'].forEach(function (id, index) {
        var element = document.getElementById(id);
        element.classList.remove('text-green-600', 'font-semibold');
        if (index === 0) element.textContent = 'Collecting data';
        if (index === 1) element.textContent = 'Formatting document';
        if (index === 2) element.textContent = 'Adding charts';
        if (index === 3) element.textContent = 'Finalizing';
    });

    // Show modal with progress animation
    modal.classList.remove('hidden');

    var progress = 0;
    var downloadTriggered = false;
    var interval = setInterval(function () {
        progress += 10;
        progressBar.style.width = Math.min(progress, 90) + '%';

        if (progress >= 25) {
            document.getElementById('reportStep1').classList.add('text-green-600', 'font-semibold');
            document.getElementById('reportStep1').textContent = '\u2713 Collecting data';
        }
        if (progress >= 50) {
            document.getElementById('reportStep2').classList.add('text-green-600', 'font-semibold');
            document.getElementById('reportStep2').textContent = '\u2713 Formatting document';
        }
        if (progress >= 75) {
            document.getElementById('reportStep3').classList.add('text-green-600', 'font-semibold');
            document.getElementById('reportStep3').textContent = '\u2713 Adding charts';
        }

        // At 90%, trigger the real download
        if (progress >= 90 && !downloadTriggered) {
            downloadTriggered = true;
            clearInterval(interval);

            // Trigger file download via hidden iframe
            var iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = url;
            document.body.appendChild(iframe);

            // Clean up and finalize after a brief delay
            setTimeout(function () {
                progressBar.style.width = '100%';
                document.getElementById('reportStep4').classList.add('text-green-600', 'font-semibold');
                document.getElementById('reportStep4').textContent = '\u2713 Finalizing';

                setTimeout(function () {
                    modal.classList.add('hidden');
                    progressBar.style.width = '0%';
                    showNotification(title + ' generated and downloaded successfully', 'success');

                    // Remove iframe after download starts
                    setTimeout(function () {
                        if (iframe.parentElement) iframe.parentElement.removeChild(iframe);
                    }, 5000);

                    // Add to report history table
                    var dateStr = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                    var newReport = {
                        id: reportsData.length + 1,
                        name: programCode + ' ' + title + ' - ' + dateStr,
                        type: fileType,
                        category: type,
                        date: dateStr,
                        size: 'Downloaded',
                        status: 'completed'
                    };
                    reportsData.unshift(newReport);
                    filteredReports = reportsData.slice();
                    loadReportsData();
                }, 500);
            }, 800);
        }
    }, 150);
}

function generateCustomReport() {
    var modal = document.getElementById('reportModal');
    var progressBar = document.getElementById('reportProgress');
    var reportTitle = document.getElementById('reportTitle');
    var reportMessage = document.getElementById('reportMessage');

    reportTitle.textContent = 'Custom Report';
    reportMessage.textContent = 'Building your custom report with selected parameters...';

    // Reset steps
    ['reportStep1', 'reportStep2', 'reportStep3', 'reportStep4'].forEach(function (id, index) {
        var element = document.getElementById(id);
        element.classList.remove('text-green-600', 'font-semibold');
        if (index === 0) element.textContent = 'Collecting data';
        if (index === 1) element.textContent = 'Formatting document';
        if (index === 2) element.textContent = 'Adding charts';
        if (index === 3) element.textContent = 'Finalizing';
    });

    modal.classList.remove('hidden');

    // Simulate custom report generation
    var progress = 0;
    var interval = setInterval(function () {
        progress += 4;
        progressBar.style.width = progress + '%';

        if (progress >= 20) {
            document.getElementById('reportStep1').classList.add('text-green-600', 'font-semibold');
            document.getElementById('reportStep1').textContent = '\u2713 Collecting data';
        }
        if (progress >= 45) {
            document.getElementById('reportStep2').classList.add('text-green-600', 'font-semibold');
            document.getElementById('reportStep2').textContent = '\u2713 Formatting document';
        }
        if (progress >= 70) {
            document.getElementById('reportStep3').classList.add('text-green-600', 'font-semibold');
            document.getElementById('reportStep3').textContent = '\u2713 Adding charts';
        }
        if (progress >= 90) {
            document.getElementById('reportStep4').classList.add('text-green-600', 'font-semibold');
            document.getElementById('reportStep4').textContent = '\u2713 Finalizing';
        }

        if (progress >= 100) {
            clearInterval(interval);
            setTimeout(function () {
                modal.classList.add('hidden');
                showNotification('Custom report generated successfully', 'success');
                progressBar.style.width = '0%';

                var dateStr = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

                var newReport = {
                    id: reportsData.length + 1,
                    name: programCode + ' Custom Report - ' + dateStr,
                    type: 'PDF',
                    category: 'summary',
                    date: dateStr,
                    size: (Math.random() * 3 + 2).toFixed(1) + ' MB',
                    status: 'completed'
                };

                reportsData.unshift(newReport);
                filteredReports = reportsData.slice();
                loadReportsData();
            }, 500);
        }
    }, 100);
}

function exportAllReports() {
    showNotification('Exporting all reports to ZIP file...', 'info');
    setTimeout(function () {
        showNotification('All reports exported successfully', 'success');
    }, 1500);
}

function printReportList() {
    window.print();
}

function viewReport(id) {
    showNotification('Opening report #' + id + ' for viewing...', 'info');
}

function downloadReport(id) {
    var report = reportsData.find(function (r) { return r.id === id; });
    showNotification('Downloading ' + report.name + '...', 'info');
    setTimeout(function () {
        showNotification(report.name + ' downloaded successfully', 'success');
    }, 1000);
}

function shareReport(id) {
    var report = reportsData.find(function (r) { return r.id === id; });
    showNotification('Sharing options for ' + report.name, 'info');
}

function deleteReport(id) {
    if (confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
        var index = reportsData.findIndex(function (r) { return r.id === id; });
        if (index !== -1) {
            reportsData.splice(index, 1);
            filteredReports = reportsData.slice();
            loadReportsData();
            showNotification('Report deleted successfully', 'success');
        }
    }
}

function useTemplate(templateType) {
    var templateName = '';
    switch (templateType) {
        case 'board': templateName = 'School Board Report Template'; break;
        case 'statistical': templateName = 'Statistical Summary Template'; break;
        case 'parent': templateName = 'Parent Communication Template'; break;
    }

    showNotification(templateName + ' loaded. You can now customize it.', 'info');

    setTimeout(function () {
        document.querySelector('.bg-white.rounded-2xl.shadow-lg.p-6.border.border-gray-200.mb-8').scrollIntoView({ behavior: 'smooth' });
    }, 100);
}

function showNotification(message, type) {
    type = type || 'info';
    var container = document.getElementById('notificationContainer');
    var notification = document.createElement('div');

    var bgColor = type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' :
            type === 'warning' ? 'bg-yellow-500' : 'bg-primary';

    notification.className = bgColor + ' text-white px-4 py-3 rounded-lg shadow-lg animate-fade-in';
    notification.innerHTML =
        '<div class="flex items-center justify-between">' +
            '<span>' + message + '</span>' +
            '<button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">' +
                '<i class="fas fa-times"></i>' +
            '</button>' +
        '</div>';

    container.appendChild(notification);

    setTimeout(function () {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}
