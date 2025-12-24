
document.addEventListener('DOMContentLoaded', function () {
        // Initialize charts
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
                        fill: true
                    },
                    {
                        label: 'Approved',
                        data: [80, 180, 320, 450, 580, 700, 800, 900, 1000],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true
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
                    ]
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
    });

    function showReport(type) {
        alert(`Loading ${type} report...`);
        // In real app, this would load the specific report
    }

    function generateComprehensiveReport() {
        alert('Generating comprehensive report... This may take a moment.');
        // Simulate report generation
        setTimeout(() => {
            alert('Report generated successfully! Download will start automatically.');
            // Trigger download
            const link = document.createElement('a');
            link.href = '#';
            link.download = 'comprehensive-report.pdf';
            link.click();
        }, 2000);
    }

    function exportExcel(type) {
        alert(`Exporting ${type} data to Excel...`);
        // Trigger download
        const link = document.createElement('a');
        link.href = '#';
        link.download = `${type}-data-${new Date().toISOString().split('T')[0]}.xlsx`;
        link.click();
    }

    function exportPDF(type) {
        alert(`Generating ${type} PDF report...`);
        setTimeout(() => {
            const link = document.createElement('a');
            link.href = '#';
            link.download = `${type}-report-${new Date().toISOString().split('T')[0]}.pdf`;
            link.click();
        }, 1500);
    }

    function printReport(type) {
        window.print();
    }

    function generateReport(type) {
        alert(`Regenerating ${type} report...`);
        // In real app, this would regenerate the report
    }

    function downloadReport(type) {
        alert(`Downloading ${type} report...`);
        const link = document.createElement('a');
        link.href = '#';
        link.download = `${type}-report.pdf`;
        link.click();
    }

    function downloadChart(chartId) {
        alert(`Downloading chart as image...`);
        // In real app, this would download the chart as PNG
        const link = document.createElement('a');
        link.href = '#';
        link.download = `${chartId}-chart.png`;
        link.click();
    }