document.addEventListener('DOMContentLoaded', function () {
        // Initialize charts
        initializeCharts();

        // Add event listeners for filters
        document.getElementById('programFilter').addEventListener('change', updateAnalytics);
        document.getElementById('timeFilter').addEventListener('change', updateAnalytics);
    });

    function initializeCharts() {
        // Score Distribution Chart
        const scoreCtx = document.getElementById('scoreDistributionChart').getContext('2d');
        new Chart(scoreCtx, {
            type: 'bar',
            data: {
                labels: ['90-100', '80-89', '70-79', '60-69', 'Below 60'],
                datasets: [{
                    label: 'Number of Students',
                    data: [45, 68, 52, 38, 45],
                    backgroundColor: [
                        '#10b981',
                        '#991b1b',  // Changed from blue to primary red
                        '#f59e0b',
                        '#ef4444',
                        '#6b7280'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                }
            }
        });

        // Qualification Trends Chart
        const trendCtx = document.getElementById('qualificationTrendChart').getContext('2d');
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [
                    {
                        label: 'Qualified',
                        data: [65, 75, 80, 85, 82, 88],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Total Applicants',
                        data: [120, 135, 145, 150, 155, 160],
                        borderColor: '#991b1b',  // Changed from blue to primary red
                        backgroundColor: 'rgba(153, 27, 27, 0.1)',
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
                }
            }
        });

        // Section Balance Chart
        const balanceCtx = document.getElementById('sectionBalanceChart').getContext('2d');
        new Chart(balanceCtx, {
            type: 'doughnut',
            data: {
                labels: ['STEM-1', 'STEM-2', 'STEM-3', 'STEM-4'],
                datasets: [{
                    data: [30, 29, 31, 30],
                    backgroundColor: [
                        '#991b1b',  // Changed from blue to primary red
                        '#10b981',
                        '#f59e0b',
                        '#8b5cf6'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });

        // AI Performance Chart
        const aiCtx = document.getElementById('aiPerformanceChart').getContext('2d');
        new Chart(aiCtx, {
            type: 'radar',
            data: {
                labels: ['Accuracy', 'Speed', 'Fairness', 'Consistency', 'Balance'],
                datasets: [{
                    label: 'AI Performance',
                    data: [85, 90, 82, 88, 86],
                    backgroundColor: 'rgba(153, 27, 27, 0.2)',  // Changed from blue to primary red
                    borderColor: '#991b1b',
                    pointBackgroundColor: '#991b1b',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#991b1b'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                }
            }
        });
    }

    function updateAnalytics() {
        const program = document.getElementById('programFilter').value;
        const period = document.getElementById('timeFilter').value;

        // In a real app, this would fetch new data from the server
        console.log(`Updating analytics for ${program} - ${period}`);
        showNotification(`Analytics updated for ${program} program`, 'info');
    }

    function exportAnalytics() {
        showNotification('Exporting analytics data to Excel...', 'info');
        setTimeout(() => {
            showNotification('Analytics data exported successfully', 'success');
        }, 1500);
    }

    function printAnalytics() {
        window.print();
    }

    function generateReport() {
        showNotification('Generating PDF report...', 'info');
        setTimeout(() => {
            showNotification('PDF report generated successfully', 'success');
            // In a real app, this would trigger a download
            const link = document.createElement('a');
            link.href = '#';
            link.download = 'analytics-report.pdf';
            link.click();
        }, 2000);
    }

    function refreshSectionBalance() {
        showNotification('Refreshing section balance data...', 'info');
        // In a real app, this would reload the chart data
    }

    function showNotification(message, type = 'info') {
        // Simple notification implementation
        alert(`${type.toUpperCase()}: ${message}`);
    }