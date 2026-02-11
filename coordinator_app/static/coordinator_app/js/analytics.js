document.addEventListener('DOMContentLoaded', function () {
    initializeCharts();
});

function initializeCharts() {
    const data = window.chartData;
    if (!data) return;

    // GWA Distribution Chart (Bar)
    const gwaCtx = document.getElementById('gwaDistributionChart');
    if (gwaCtx) {
        new Chart(gwaCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.gwaDistribution.labels,
                datasets: [{
                    label: 'Number of Students',
                    data: data.gwaDistribution.data,
                    backgroundColor: [
                        '#6b7280',
                        '#f59e0b',
                        '#991b1b',
                        '#10b981',
                        '#3b82f6'
                    ],
                    borderWidth: 1
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
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }

    // Subject-wise Averages Chart (Bar - horizontal)
    const subjCtx = document.getElementById('subjectAveragesChart');
    if (subjCtx && data.subjectAverages) {
        new Chart(subjCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.subjectAverages.labels,
                datasets: [{
                    label: 'Average Grade',
                    data: data.subjectAverages.data,
                    backgroundColor: '#991b1b',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: false,
                        min: 70,
                        max: 100,
                    }
                }
            }
        });
    }

    // Enrollment Status Chart (Doughnut)
    const statusCtx = document.getElementById('enrollmentStatusChart');
    if (statusCtx) {
        new Chart(statusCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: data.enrollmentStatus.labels,
                datasets: [{
                    data: data.enrollmentStatus.data,
                    backgroundColor: data.enrollmentStatus.colors
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
    }

    // Section Balance Chart (Bar - showing current vs max capacity)
    const sectionCtx = document.getElementById('sectionBalanceChart');
    if (sectionCtx) {
        const sectionData = data.sectionBalance;
        const labels = sectionData.map(s => s.name);
        const current = sectionData.map(s => s.count);
        const max = sectionData.map(s => s.max);

        new Chart(sectionCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Current Students',
                        data: current,
                        backgroundColor: '#991b1b',
                    },
                    {
                        label: 'Max Capacity',
                        data: max,
                        backgroundColor: '#e5e7eb',
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
                        beginAtZero: true,
                        ticks: { stepSize: 5 }
                    }
                }
            }
        });
    }

    // Section GWA Comparison Chart (Bar)
    const sectionGwaCtx = document.getElementById('sectionGwaChart');
    if (sectionGwaCtx && data.sectionGwa) {
        const sGwa = data.sectionGwa;
        const labels = sGwa.map(s => s.name);
        const avgs = sGwa.map(s => s.avg_gwa);

        // Color the highest bar differently
        const maxAvg = Math.max(...avgs);
        const colors = avgs.map(v => v === maxAvg && v > 0 ? '#10b981' : '#991b1b');

        new Chart(sectionGwaCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Average GWA',
                    data: avgs,
                    backgroundColor: colors,
                    borderWidth: 1
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
                        beginAtZero: false,
                        min: 70,
                        max: 100,
                    }
                }
            }
        });
    }

    // Gender Distribution Chart (Doughnut)
    const genderCtx = document.getElementById('genderDistributionChart');
    if (genderCtx) {
        new Chart(genderCtx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: data.genderDistribution.labels,
                datasets: [{
                    data: data.genderDistribution.data,
                    backgroundColor: data.genderDistribution.colors
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
    }

    // Feeder Schools Chart (Horizontal Bar)
    const feederCtx = document.getElementById('feederSchoolsChart');
    if (feederCtx && data.feederSchools && data.feederSchools.labels.length > 0) {
        new Chart(feederCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.feederSchools.labels,
                datasets: [{
                    label: 'Number of Students',
                    data: data.feederSchools.data,
                    backgroundColor: '#991b1b',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
}

function printAnalytics() {
    window.print();
}
