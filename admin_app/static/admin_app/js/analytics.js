document.addEventListener('DOMContentLoaded', function () {
    // Load header data first
    loadHeaderData();
    
    // Initialize charts
    initializeCharts();
});

/**
 * Load header data from backend API
 */
async function loadHeaderData() {
    try {
        const response = await fetch('/admin-portal/api/analytics/header/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update school year
        const schoolYearElement = document.getElementById('schoolYearDisplay');
        if (schoolYearElement) {
            schoolYearElement.textContent = data.school_year;
        }
        
        // Update user name
        const userFullNameElement = document.getElementById('userFullName');
        if (userFullNameElement) {
            userFullNameElement.textContent = data.full_name;
        }
        
        // Update user role
        const userRoleElement = document.getElementById('userRole');
        if (userRoleElement) {
            userRoleElement.textContent = data.role;
        }
        
        // Update user initials
        const userInitialsElement = document.getElementById('userInitials');
        if (userInitialsElement) {
            userInitialsElement.textContent = data.initials;
        }
        
        // If photo URL is available, update the container
        const userPhotoContainer = document.getElementById('userPhotoContainer');
        if (userPhotoContainer && data.photo_url) {
            userPhotoContainer.innerHTML = `<img src="${data.photo_url}" alt="User" class="w-full h-full object-cover">`;
        }
        
    } catch (error) {
        console.error('Error loading header data:', error);
        showNotification('Error loading user information', 'error');
    }
}

/**
 * Initialize all charts
 */
function initializeCharts() {
    // Enrollment Trends Chart
    const enrollmentCtx = document.getElementById('enrollmentChart').getContext('2d');
    new Chart(enrollmentCtx, {
        type: 'line',
        data: {
            labels: ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
            datasets: [
                {
                    label: 'Applications',
                    data: [120, 250, 400, 550, 700, 850, 950, 1100, 1250],
                    borderColor: '#991b1b',
                    backgroundColor: 'rgba(153, 27, 27, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Approved',
                    data: [80, 180, 320, 450, 580, 700, 800, 900, 1000],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Program Popularity Chart
    const programCtx = document.getElementById('programChart').getContext('2d');
    new Chart(programCtx, {
        type: 'bar',
        data: {
            labels: ['HETERO', 'TOP 5', 'STE', 'SPTVE', 'SPFL', 'OHSP', 'SNED'],
            datasets: [{
                label: 'Number of Students',
                data: [350, 250, 220, 180, 150, 100, 80],
                backgroundColor: [
                    '#991b1b',
                    '#10b981',
                    '#3b82f6',
                    '#f59e0b',
                    '#8b5cf6',
                    '#ef4444',
                    '#6b7280'
                ],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
    // Create notification container if it doesn't exist
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'fixed top-5 right-5 z-50 flex flex-col gap-2';
        document.body.appendChild(container);
    }

    const notification = document.createElement('div');
    notification.className = `notification-slide bg-white border-l-4 ${
        type === 'success' ? 'border-green-500' : 
        type === 'error' ? 'border-red-500' : 
        'border-blue-500'
    } rounded-lg shadow-lg p-4 max-w-sm`;
    
    notification.innerHTML = `
        <div class="flex items-start gap-3">
            <i class="fas fa-${
                type === 'success' ? 'check-circle text-green-500' : 
                type === 'error' ? 'exclamation-circle text-red-500' : 
                'info-circle text-blue-500'
            } mt-1"></i>
            <div class="flex-1">
                <p class="text-sm font-medium text-gray-800">${message}</p>
            </div>
            <button class="text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    container.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Report Functions
function showReport(type) {
    showNotification(`Loading ${type} report...`, 'info');
    // In real app, this would load the specific report
}

function generateComprehensiveReport() {
    showNotification('Generating comprehensive report... This may take a moment.', 'info');
    // Simulate report generation
    setTimeout(() => {
        showNotification('Report generated successfully! Download will start automatically.', 'success');
        // Trigger download
        const link = document.createElement('a');
        link.href = '#';
        link.download = 'comprehensive-report.pdf';
        link.click();
    }, 2000);
}

function exportExcel(type) {
    showNotification(`Exporting ${type} data to Excel...`, 'info');
    // Trigger download
    const link = document.createElement('a');
    link.href = '#';
    link.download = `${type}-data-${new Date().toISOString().split('T')[0]}.xlsx`;
    link.click();
}

function exportPDF(type) {
    showNotification(`Generating ${type} PDF report...`, 'info');
    setTimeout(() => {
        const link = document.createElement('a');
        link.href = '#';
        link.download = `${type}-report-${new Date().toISOString().split('T')[0]}.pdf`;
        link.click();
        showNotification('PDF report downloaded successfully!', 'success');
    }, 1500);
}

function printReport(type) {
    window.print();
}

function generateReport(type) {
    showNotification(`Regenerating ${type} report...`, 'info');
    // In real app, this would regenerate the report
    setTimeout(() => {
        showNotification(`${type} report regenerated successfully!`, 'success');
    }, 1500);
}

function downloadReport(type) {
    showNotification(`Downloading ${type} report...`, 'info');
    const link = document.createElement('a');
    link.href = '#';
    link.download = `${type}-report.pdf`;
    link.click();
}

function downloadChart(chartId) {
    showNotification('Downloading chart as image...', 'info');
    // In real app, this would download the chart as PNG
    const link = document.createElement('a');
    link.href = '#';
    link.download = `${chartId}-chart.png`;
    link.click();
}

// Add CSS for notification animation
const style = document.createElement('style');
style.textContent = `
    .notification-slide {
        animation: slideInRight 0.3s ease;
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);