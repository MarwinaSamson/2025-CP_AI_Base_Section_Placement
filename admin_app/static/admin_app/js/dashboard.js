// Enhanced Mock data for the dashboard with the correct programs
const mockData = {
    notifications: [
        {
            id: 1,
            icon: 'fas fa-users',
            message: '18 new HETERO applications pending review',
            programSlug: 'hetero',
            count: 18,
            priority: 'high'
        },
        {
            id: 2,
            icon: 'fas fa-trophy',
            message: '12 TOP 5 applicants need verification',
            programSlug: 'top5',
            count: 12,
            priority: 'medium'
        },
        {
            id: 3,
            icon: 'fas fa-flask',
            message: '15 STE applications awaiting approval',
            programSlug: 'ste',
            count: 15,
            priority: 'medium'
        },
        {
            id: 4,
            icon: 'fas fa-tools',
            message: '8 SPTVE applications require documents',
            programSlug: 'sptve',
            count: 8,
            priority: 'low'
        }
    ],
    programs: [
        {
            name: 'STE',
            shortName: 'STE',
            color: 'bg-purple-500',
            icon: 'fas fa-flask',
            description: 'Science, Technology, and Engineering',
            totalApplicants: 220,
            approved: 190,
            pending: 20,
            rejected: 10,
            sections: 8,
            capacity: 320,
            enrolled: 270,
            status: 'active',
            trend: 'up',
            trendValue: 8,
            acceptanceRate: '86.4%',
            fillRate: '84.4%',
            grade7: 68,
            grade8: 67,
            grade9: 68,
            grade10: 67
        },
        {
            name: 'SPFL',
            shortName: 'SPF',
            color: 'bg-indigo-500',
            icon: 'fas fa-language',
            description: 'Special Program in Foreign Language',
            totalApplicants: 150,
            approved: 130,
            pending: 15,
            rejected: 5,
            sections: 4,
            capacity: 160,
            enrolled: 135,
            status: 'active',
            trend: 'up',
            trendValue: 5,
            acceptanceRate: '86.7%',
            fillRate: '84.4%',
            grade7: 34,
            grade8: 33,
            grade9: 34,
            grade10: 34
        },
        {
            name: 'SPTVE',
            shortName: 'SPT',
            color: 'bg-orange-500',
            icon: 'fas fa-tools',
            description: 'Special Program in Technical-Vocational Education',
            totalApplicants: 180,
            approved: 160,
            pending: 15,
            rejected: 5,
            sections: 6,
            capacity: 240,
            enrolled: 200,
            status: 'active',
            trend: 'up',
            trendValue: 12,
            acceptanceRate: '88.9%',
            fillRate: '83.3%',
            grade7: 50,
            grade8: 50,
            grade9: 50,
            grade10: 50
        },
        {
            name: 'OHSP',
            shortName: 'OHS',
            color: 'bg-teal-500',
            icon: 'fas fa-laptop-house',
            description: 'Open High School Program',
            totalApplicants: 120,
            approved: 105,
            pending: 10,
            rejected: 5,
            sections: 3,
            capacity: 120,
            enrolled: 100,
            status: 'active',
            trend: 'stable',
            trendValue: 0,
            acceptanceRate: '87.5%',
            fillRate: '83.3%',
            grade7: 25,
            grade8: 25,
            grade9: 25,
            grade10: 25
        },
        {
            name: 'SNED',
            shortName: 'SNE',
            color: 'bg-pink-500',
            icon: 'fas fa-universal-access',
            description: 'Special Needs Education',
            totalApplicants: 80,
            approved: 70,
            pending: 8,
            rejected: 2,
            sections: 2,
            capacity: 80,
            enrolled: 65,
            status: 'active',
            trend: 'stable',
            trendValue: 0,
            acceptanceRate: '87.5%',
            fillRate: '81.3%',
            grade7: 16,
            grade8: 17,
            grade9: 16,
            grade10: 16
        },
        {
            name: 'TOP 5',
            shortName: 'TOP',
            color: 'bg-green-500',
            icon: 'fas fa-trophy',
            description: 'Top 5 Regular Section',
            totalApplicants: 250,
            approved: 220,
            pending: 22,
            rejected: 8,
            sections: 5,
            capacity: 200,
            enrolled: 175,
            status: 'active',
            trend: 'up',
            trendValue: 10,
            acceptanceRate: '88.0%',
            fillRate: '87.5%',
            grade7: 44,
            grade8: 44,
            grade9: 44,
            grade10: 43
        },
        {
            name: 'HETERO',
            shortName: 'HET',
            color: 'bg-blue-500',
            icon: 'fas fa-users',
            description: 'Heterogeneous Class',
            totalApplicants: 350,
            approved: 305,
            pending: 35,
            rejected: 10,
            sections: 12,
            capacity: 480,
            enrolled: 430,
            status: 'active',
            trend: 'up',
            trendValue: 15,
            acceptanceRate: '87.1%',
            fillRate: '89.6%',
            grade7: 108,
            grade8: 107,
            grade9: 108,
            grade10: 107
        }
    ],
    summary: {
        totalApplicants: 1350,
        totalApproved: 1180,
        totalPending: 125,
        totalRejected: 45,
        totalSections: 40,
        totalCapacity: 1600,
        totalEnrolled: 1375,
        overallAcceptanceRate: '87.4%',
        overallFillRate: '85.9%'
    }
};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function () {
    // Check if user is logged in
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn) {
        window.location.href = 'login.html';
        return;
    }

    // Set current date
    updateDashboardDate();

    // Setup dropdown handlers
    setupDropdownHandlers();

    // Load notifications
    loadNotifications();

    // Load program data
    loadProgramData();

    // Setup program row click handlers
    setupProgramRowHandlers();

    // Setup sidebar active state
    setupSidebar();

    // Update statistics
    updateStatistics();

    setupLogoutModalEvents();
});

function updateDashboardDate() {
    const now = new Date();
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
    };
    const formattedDate = now.toLocaleDateString('en-US', options);
    const schoolYear = '2025-2026';

    const dateElement = document.getElementById('dashboardDate');
    if (dateElement) {
        dateElement.textContent = `${formattedDate} | School Year: ${schoolYear}`;
    }
}

function setupDropdownHandlers() {
    const schoolYear = document.getElementById('schoolYearFilter');

    if (schoolYear) {
        schoolYear.addEventListener('change', function () {
            showNotification(`School year changed to ${this.value}`, 'info');
            updateDashboardDate();
            updateStatistics();
        });
    }
}

function loadNotifications() {
    const container = document.getElementById('enrollmentNotifications');
    const unreadCount = document.getElementById('unreadCount');

    if (!container) return;

    container.innerHTML = '';

    if (mockData.notifications.length === 0) {
        container.innerHTML = `
            <div class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4 flex items-center gap-4">
                <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                    <i class="fas fa-check-circle text-green-600"></i>
                </div>
                <span class="text-gray-700 font-medium">No new submissions.</span>
            </div>
        `;
        unreadCount.textContent = '0 New';
        return;
    }

    let totalUnread = 0;

    mockData.notifications.forEach(notification => {
        totalUnread += notification.count;
        const priorityColor = notification.priority === 'high' ? 'bg-red-100 border-red-200' :
            notification.priority === 'medium' ? 'bg-yellow-100 border-yellow-200' :
                'bg-blue-100 border-blue-200';

        const notificationElement = document.createElement('div');
        notificationElement.className = `bg-gradient-to-r ${priorityColor} rounded-xl p-4 flex items-center gap-4 transition-all hover:shadow-md smooth-transition cursor-pointer`;
        notificationElement.innerHTML = `
            <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                <i class="${notification.icon} text-red-600"></i>
            </div>
            <div class="flex-1">
                <span class="text-gray-700 font-medium">${notification.message}</span>
                <div class="flex items-center gap-2 mt-1">
                    <span class="text-xs px-2 py-1 rounded-full ${notification.priority === 'high' ? 'bg-red-500 text-white' :
                    notification.priority === 'medium' ? 'bg-yellow-500 text-white' :
                        'bg-blue-500 text-white'}">
                        ${notification.priority === 'high' ? 'High Priority' :
                    notification.priority === 'medium' ? 'Medium Priority' : 'Low Priority'}
                    </span>
                    <span class="text-xs text-gray-500">${notification.count} applications</span>
                </div>
            </div>
            <span class="ml-auto bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full">${notification.count}</span>
        `;

        notificationElement.addEventListener('click', function () {
            handleNotificationClick(notification);
        });

        container.appendChild(notificationElement);
    });

    unreadCount.textContent = `${totalUnread} New`;
}

function loadProgramData() {
    const tableBody = document.getElementById('programsTable');

    if (!tableBody) return;

    tableBody.innerHTML = '';

    mockData.programs.forEach(program => {
        const fillPercentage = Math.round((program.enrolled / program.capacity) * 100);
        const row = document.createElement('tr');
        row.className = 'program-row hover:bg-blue-50 cursor-pointer transition-all border-b border-gray-200 smooth-transition';
        row.setAttribute('data-program', program.shortName);
        row.innerHTML = `
            <td class="p-4">
                <div class="flex items-center gap-3">
                    <span class="program-indicator ${program.color}"></span>
                    <div>
                        <span class="font-medium text-gray-800">${program.name}</span>
                        <p class="text-xs text-gray-500">${program.description}</p>
                    </div>
                </div>
            </td>
            <td class="p-4">
                <span class="status-badge ${program.status === 'active' ? 'status-active' : 'status-inactive'}">
                    ${program.status === 'active' ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td class="p-4">
                <div class="font-medium text-gray-800">${program.totalApplicants}</div>
                <div class="text-xs text-gray-500">${program.acceptanceRate} acceptance</div>
            </td>
            <td class="p-4">
                <div class="font-medium text-gray-800">${program.approved}</div>
                <div class="text-xs text-green-600">${Math.round((program.approved / program.totalApplicants) * 100)}%</div>
            </td>
            <td class="p-4">
                <div class="font-medium text-gray-800">${program.pending}</div>
                <div class="text-xs text-yellow-600">Needs review</div>
            </td>
            <td class="p-4">
                <div class="font-medium text-gray-800">${program.rejected}</div>
                <div class="text-xs text-red-600">${Math.round((program.rejected / program.totalApplicants) * 100)}%</div>
            </td>
            <td class="p-4">
                <div class="font-medium text-gray-800">${program.enrolled}/${program.capacity}</div>
                <div class="w-20 bg-gray-200 rounded-full h-2 mt-1">
                    <div class="${program.fillRate >= 85 ? 'bg-green-600' : program.fillRate >= 70 ? 'bg-yellow-600' : 'bg-red-600'} h-2 rounded-full" 
                          style="width: ${fillPercentage}%"></div>
                </div>
                <div class="text-xs ${program.fillRate >= 85 ? 'text-green-600' : program.fillRate >= 70 ? 'text-yellow-600' : 'text-red-600'} mt-1">
                    ${program.fillRate} filled
                </div>
            </td>
            <td class="p-4 text-gray-700">${program.sections}</td>
            <td class="p-4">
                <div class="flex items-center gap-1 ${program.trend === 'up' ? 'trend-up' : program.trend === 'down' ? 'trend-down' : 'trend-stable'}">
                    <i class="fas fa-${program.trend === 'up' ? 'arrow-up' : program.trend === 'down' ? 'arrow-down' : 'minus'}"></i>
                    <span class="text-sm font-medium">${program.trendValue}%</span>
                </div>
                <div class="text-xs text-gray-500 mt-1">vs last year</div>
            </td>
        `;

        tableBody.appendChild(row);
    });

    // Add summary row
    const summaryRow = document.createElement('tr');
    summaryRow.className = 'bg-gray-50 font-semibold';
    summaryRow.innerHTML = `
        <td class="p-4 text-gray-700">TOTAL</td>
        <td class="p-4"></td>
        <td class="p-4 text-gray-700">${mockData.summary.totalApplicants}</td>
        <td class="p-4 text-green-600">${mockData.summary.totalApproved}</td>
        <td class="p-4 text-yellow-600">${mockData.summary.totalPending}</td>
        <td class="p-4 text-red-600">${mockData.summary.totalRejected}</td>
        <td class="p-4 text-gray-700">${mockData.summary.totalEnrolled}/${mockData.summary.totalCapacity}</td>
        <td class="p-4 text-gray-700">${mockData.summary.totalSections}</td>
        <td class="p-4 text-blue-600">${mockData.summary.overallAcceptanceRate}</td>
    `;
    tableBody.appendChild(summaryRow);
}

function setupProgramRowHandlers() {
    // Delegate event handling to table body
    const tableBody = document.getElementById('programsTable');
    if (tableBody) {
        tableBody.addEventListener('click', function (e) {
            const row = e.target.closest('.program-row');
            if (row) {
                const program = row.getAttribute('data-program');
                showNotification(`Navigating to ${program} sections...`, 'info');

                // Simulate navigation
                setTimeout(() => {
                    window.location.href = `sections.html?program=${encodeURIComponent(program)}`;
                }, 500);
            }
        });
    }
}

function setupSidebar() {
    // Add active state to current page
    const currentPage = window.location.pathname.split('/').pop();
    const navItems = document.querySelectorAll('nav a');

    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href === currentPage || (href === 'dashboard.html' && currentPage === '')) {
            item.classList.add('bg-red-700', 'scale-105', 'shadow-lg');
            item.classList.remove('hover:bg-red-700/80');
        }
    });
}

function handleNotificationClick(notification) {
    showNotification(`Opening ${notification.programSlug.toUpperCase()} enrollment review...`, 'info');

    // Mark as read (simulated)
    const index = mockData.notifications.findIndex(n => n.id === notification.id);
    if (index > -1) {
        mockData.notifications.splice(index, 1);
        loadNotifications();
    }

    // Navigate to enrollment page
    setTimeout(() => {
        window.location.href = `enrollment.html?program=${notification.programSlug}&review=true`;
    }, 800);
}

function updateStatistics() {
    // Update statistics based on school year
    const schoolYear = document.getElementById('schoolYearFilter').value;
    const isCurrentYear = schoolYear === '2025-2026';

    const stats = {
        '2025-2026': {
            teachers: 52,
            students: 1450,
            programs: 7,
            sections: 42
        },
        '2024-2025': {
            teachers: 48,
            students: 1365,
            programs: 7,
            sections: 36
        }
    };

    const data = stats[schoolYear] || stats['2025-2026'];

    document.getElementById('totalTeachers').textContent = data.teachers;
    document.getElementById('totalStudents').textContent = data.students;
    document.getElementById('totalPrograms').textContent = data.programs;
    document.getElementById('totalSections').textContent = data.sections;
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `notification bg-white border-l-4 ${type === 'success' ? 'border-green-500' : type === 'error' ? 'border-red-500' : 'border-blue-500'} rounded-lg shadow-lg p-4 max-w-sm`;
    notification.innerHTML = `
        <div class="flex items-start gap-3">
            <i class="fas fa-${type === 'success' ? 'check-circle text-green-500' : type === 'error' ? 'exclamation-circle text-red-500' : 'info-circle text-blue-500'} mt-1"></i>
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

// ============== LOGOUT MODAL FUNCTIONS ==============

function setupLogoutModalEvents() {
    console.log('Setting up logout modal events...');
    
    // Get the modal that's already in the HTML
    const modal = document.getElementById('logoutModal');
    if (!modal) {
        console.error('Logout modal not found in HTML!');
        return;
    }

    // Open modal when clicking logout link
    document.addEventListener('click', function(e) {
        if (e.target.closest('a[href="logout.html"]')) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Logout link clicked');
            
            // Update user info in modal
            const currentUser = localStorage.getItem('username') || 'Administrator';
            const loginTime = localStorage.getItem('loginTime');
            
            const modalUserElement = document.getElementById('modalCurrentUser');
            const modalSessionElement = document.getElementById('modalSessionTime');
            
            if (modalUserElement) {
                modalUserElement.textContent = currentUser;
            }
            
            if (modalSessionElement && loginTime) {
                const sessionDate = new Date(loginTime);
                const formattedTime = sessionDate.toLocaleTimeString('en-US', { 
                    hour: '2-digit', 
                    minute: '2-digit',
                    hour12: true 
                });
                modalSessionElement.textContent = formattedTime;
            } else if (modalSessionElement) {
                modalSessionElement.textContent = 'Just now';
            }
            
            // Show modal
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    });

    // Close modal with X button (FIXED ID - it's closeLogoutModal in your HTML)
    const closeBtn = document.getElementById('closeLogoutModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }

    // Cancel button (FIXED ID - it's cancelLogoutBtn in your HTML)
    const cancelBtn = document.getElementById('cancelLogoutBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }

    // Logout button (FIXED ID - it's confirmLogoutBtn in your HTML)
    const logoutBtn = document.getElementById('confirmLogoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            const originalText = logoutBtn.innerHTML;
            
            // Show loading
            logoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging out...';
            logoutBtn.disabled = true;
            
            showNotification('Logging out...', 'info');
            
            // Clear storage
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('username');
            localStorage.removeItem('loginTime');
            
            // Hide modal and redirect
            setTimeout(() => {
                modal.classList.add('hidden');
                document.body.style.overflow = 'auto';
                logoutBtn.innerHTML = originalText;
                logoutBtn.disabled = false;
                window.location.href = 'logout.html';
            }, 1000);
        });
    }
    
    // Close modal when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
    
    // Close with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (!modal.classList.contains('hidden')) {
                modal.classList.add('hidden');
                document.body.style.overflow = 'auto';
            }
        }
    });
}
