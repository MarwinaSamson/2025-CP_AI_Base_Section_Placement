// Dashboard API Integration - All views handle backend data
document.addEventListener('DOMContentLoaded', function () {
    // Initialize dashboard with backend data
    initializeDashboard();
});

/**
 * Initialize dashboard with all necessary data from backend
 */
async function initializeDashboard() {
    try {
        // Set current date
        updateDashboardDate();

        // Load header data (user info, school year, role)
        await loadHeaderData();

        // Load statistics
        await loadStatistics();

        // Load notifications (new students grouped by program)
        await loadNotifications();

        // Load programs overview
        await loadProgramsOverview();

        // Setup event handlers
        setupEventHandlers();

        // Setup sidebar
        setupSidebar();

        // Setup logout modal
        setupLogoutModalEvents();

    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showNotification('Error loading dashboard data', 'error');
    }
}

/**
 * Update the current date display
 */
function updateDashboardDate() {
    const now = new Date();
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
    };
    const formattedDate = now.toLocaleDateString('en-US', options);
    const dateElement = document.getElementById('dashboardDate');
    
    if (dateElement) {
        dateElement.textContent = formattedDate;
    }
}

/**
 * Load header data from backend API
 */
async function loadHeaderData() {
    try {
        const response = await fetch(window.API_BASE + 'header/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update school year
        const schoolYearElement = document.getElementById('schoolYearFilter');
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
 * Load statistics from backend API
 */
async function loadStatistics() {
    try {
        const response = await fetch(window.API_BASE + 'statistics/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update total teachers
        const totalTeachersElement = document.getElementById('totalTeachers');
        if (totalTeachersElement) {
            totalTeachersElement.textContent = data.total_teachers;
        }
        
        // Update total students
        const totalStudentsElement = document.getElementById('totalStudents');
        if (totalStudentsElement) {
            totalStudentsElement.textContent = data.total_students;
        }
        
        // Update total programs
        const totalProgramsElement = document.getElementById('totalPrograms');
        if (totalProgramsElement) {
            totalProgramsElement.textContent = data.total_programs;
        }
        
        // Update total sections
        const totalSectionsElement = document.getElementById('totalSections');
        if (totalSectionsElement) {
            totalSectionsElement.textContent = data.total_sections;
        }
        
        // Update grade breakdown
        updateGradeBreakdown(data.grade_breakdown);
        
    } catch (error) {
        console.error('Error loading statistics:', error);
        showNotification('Error loading statistics', 'error');
    }
}

/**
 * Update grade level breakdown
 */
function updateGradeBreakdown(breakdown) {
    const gradeElements = {
        'grade_7': document.querySelector('[data-grade="7"]'),
        'grade_8': document.querySelector('[data-grade="8"]'),
        'grade_9': document.querySelector('[data-grade="9"]'),
        'grade_10': document.querySelector('[data-grade="10"]')
    };
    
    // For now, use the existing static HTML elements
    // You can add data attributes to the HTML and update them here
    // This is a placeholder for future enhancement
}

/**
 * Load notifications (new students) from backend API
 */
async function loadNotifications() {
    try {
        const response = await fetch(window.API_BASE + 'notifications/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const container = document.getElementById('enrollmentNotifications');
        const unreadCount = document.getElementById('unreadCount');
        
        if (!container) return;
        
        container.innerHTML = '';
        
        if (data.notifications.length === 0 || data.total_count === 0) {
            container.innerHTML = `
                <div class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4 flex items-center gap-4">
                    <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center shadow-sm">
                        <i class="fas fa-check-circle text-green-600"></i>
                    </div>
                    <span class="text-gray-700 font-medium">No new enrollments at this time.</span>
                </div>
            `;
            unreadCount.textContent = '0 New';
            return;
        }
        
        // Update unread count
        unreadCount.textContent = `${data.total_count} New`;
        
        // Create notification cards for each program with new students
        data.notifications.forEach((notification) => {
            const notificationElement = document.createElement('div');
            notificationElement.className = `bg-white rounded-xl p-4 border border-gray-200 transition-all hover:shadow-lg hover:scale-[1.02] cursor-pointer notification-card`;
            notificationElement.setAttribute('data-program', notification.program_code);
            
            // Create students list
            const studentsList = notification.students.map(student => `
                <div class="flex items-center justify-between py-2 px-3 bg-gray-50 rounded-lg text-sm">
                    <div>
                        <p class="font-medium text-gray-800">${student.name}</p>
                        <p class="text-xs text-gray-600">LRN: ${student.lrn}</p>
                    </div>
                    <span class="text-xs text-gray-500">${student.time_ago}</span>
                </div>
            `).join('');
            
            const priorityClass = notification.count > 20 ? 'bg-red-100 border-red-200' : 
                                 notification.count > 10 ? 'bg-yellow-100 border-yellow-200' : 
                                 'bg-blue-100 border-blue-200';
            
            notificationElement.innerHTML = `
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center border border-gray-200">
                            <i class="${notification.icon} text-gray-700"></i>
                        </div>
                        <div>
                            <h3 class="font-semibold text-gray-800">${notification.program_name}</h3>
                            <p class="text-xs text-gray-600">${notification.message}</p>
                        </div>
                    </div>
                    <span class="px-3 py-1 rounded-full text-white text-xs font-bold ${priorityClass === 'bg-red-100 border-red-200' ? 'bg-red-500' : priorityClass === 'bg-yellow-100 border-yellow-200' ? 'bg-yellow-500' : 'bg-blue-500'}">
                        ${notification.count}
                    </span>
                </div>
                <div class="space-y-2 max-h-48 overflow-y-auto">
                    ${studentsList}
                </div>
                <button class="w-full mt-3 bg-primary hover:bg-primary-dark text-white py-2 rounded-lg text-sm font-medium transition-all">
                    Review Enrollments
                </button>
            `;
            
            // Add click handler to review button
            const reviewBtn = notificationElement.querySelector('button');
            if (reviewBtn) {
                reviewBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    // Navigate to enrollment review for this program
                    window.location.href = `${window.ENROLLMENT_URL}?program=${notification.program_code}&review=pending`;
                });
            }
            
            container.appendChild(notificationElement);
        });
        
    } catch (error) {
        console.error('Error loading notifications:', error);
        showNotification('Error loading enrollment notifications', 'error');
    }
}

/**
 * Load programs overview from backend API
 */
async function loadProgramsOverview() {
    try {
        const response = await fetch(window.API_BASE + 'programs/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const tableBody = document.getElementById('programsTable');
        
        if (!tableBody) return;
        
        tableBody.innerHTML = '';
        
        // Color mapping for programs
        const colorMap = {
            'STE': 'bg-purple-500',
            'SPFL': 'bg-indigo-500',
            'SPTVE': 'bg-orange-500',
            'OHSP': 'bg-teal-500',
            'SNED': 'bg-pink-500',
            'TOP 5': 'bg-green-500',
            'HETERO': 'bg-blue-500'
        };
        
        const iconMap = {
            'STE': 'fas fa-flask',
            'SPFL': 'fas fa-language',
            'SPTVE': 'fas fa-tools',
            'OHSP': 'fas fa-laptop-house',
            'SNED': 'fas fa-universal-access',
            'TOP 5': 'fas fa-trophy',
            'HETERO': 'fas fa-users'
        };
        
        // Add program rows
        data.programs.forEach(program => {
            const row = document.createElement('tr');
            row.className = 'program-row hover:bg-blue-50 cursor-pointer transition-all border-b border-gray-200';
            row.setAttribute('data-program', program.code);
            
            const fillPercentage = program.capacity > 0 ? Math.round(((program.approved) / program.capacity) * 100) : 0;
            
            row.innerHTML = `
                <td class="p-4">
                    <div class="flex items-center gap-3">
                        <div class="w-3 h-3 rounded-full ${colorMap[program.code] || 'bg-gray-500'}"></div>
                        <div>
                            <span class="font-medium text-gray-800">${program.code}</span>
                            <p class="text-xs text-gray-500">${program.name}</p>
                        </div>
                    </div>
                </td>
                <td class="p-4">
                    <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">
                        ${program.status === 'active' ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="p-4">
                    <div class="font-medium text-gray-800">${program.total_applicants}</div>
                    <div class="text-xs text-gray-500">${program.acceptance_rate}% acceptance</div>
                </td>
                <td class="p-4">
                    <div class="font-medium text-green-600">${program.approved}</div>
                    <div class="text-xs text-green-600">${Math.round((program.approved / (program.total_applicants || 1)) * 100)}%</div>
                </td>
                <td class="p-4">
                    <div class="font-medium text-yellow-600">${program.pending}</div>
                    <div class="text-xs text-yellow-600">Under review</div>
                </td>
                <td class="p-4">
                    <div class="font-medium text-red-600">${program.rejected}</div>
                    <div class="text-xs text-red-600">${Math.round((program.rejected / (program.total_applicants || 1)) * 100)}%</div>
                </td>
                <td class="p-4">
                    <div class="font-medium text-gray-800">${program.approved}/${program.capacity}</div>
                    <div class="w-20 bg-gray-200 rounded-full h-2 mt-1">
                        <div class="${fillPercentage >= 85 ? 'bg-green-600' : fillPercentage >= 70 ? 'bg-yellow-600' : 'bg-red-600'} h-2 rounded-full" 
                             style="width: ${Math.min(fillPercentage, 100)}%"></div>
                    </div>
                    <div class="text-xs ${fillPercentage >= 85 ? 'text-green-600' : fillPercentage >= 70 ? 'text-yellow-600' : 'text-red-600'} mt-1">
                        ${fillPercentage}% filled
                    </div>
                </td>
                <td class="p-4 text-gray-700">${program.sections}</td>
                <td class="p-4">
                    <div class="flex items-center gap-1">
                        <i class="fas fa-${program.trend === 'up' ? 'arrow-up text-green-600' : program.trend === 'down' ? 'arrow-down text-red-600' : 'minus text-gray-500'}"></i>
                        <span class="text-sm font-medium">${program.trend_value}%</span>
                    </div>
                    <div class="text-xs text-gray-500">vs last year</div>
                </td>
            `;
            
            // Add click handler
            row.addEventListener('click', () => {
                window.location.href = `${window.ENROLLMENT_URL}?program=${program.code}`;
            });
            
            tableBody.appendChild(row);
        });
        
        // Add summary row
        const summary = data.summary;
        const summaryRow = document.createElement('tr');
        summaryRow.className = 'bg-gray-50 font-semibold';
        summaryRow.innerHTML = `
            <td class="p-4 text-gray-800">TOTAL</td>
            <td class="p-4"></td>
            <td class="p-4 text-gray-800">${data.programs.reduce((sum, p) => sum + p.total_applicants, 0)}</td>
            <td class="p-4 text-green-600">${summary.total_approved}</td>
            <td class="p-4 text-yellow-600">${summary.total_pending}</td>
            <td class="p-4 text-red-600">${summary.total_rejected}</td>
            <td class="p-4 text-gray-800">${summary.total_approved}/${data.programs.reduce((sum, p) => sum + p.capacity, 0)}</td>
            <td class="p-4 text-gray-800">${data.programs.reduce((sum, p) => sum + p.sections, 0)}</td>
            <td class="p-4 text-blue-600">${summary.overall_acceptance_rate}%</td>
        `;
        tableBody.appendChild(summaryRow);
        
        // Update summary cards
        updateSummaryCards(summary);
        
    } catch (error) {
        console.error('Error loading programs overview:', error);
        showNotification('Error loading programs overview', 'error');
    }
}

/**
 * Update summary cards with backend data
 */
function updateSummaryCards(summary) {
    // Update Total Approved card
    const approvedCard = document.querySelector('[data-card="approved"]');
    if (approvedCard) {
        approvedCard.querySelector('p:nth-of-type(2)').textContent = summary.total_approved;
    }
    
    // Update Pending Review card
    const pendingCard = document.querySelector('[data-card="pending"]');
    if (pendingCard) {
        pendingCard.querySelector('p:nth-of-type(2)').textContent = summary.total_pending;
    }
    
    // Update Acceptance Rate card
    const acceptanceCard = document.querySelector('[data-card="acceptance"]');
    if (acceptanceCard) {
        acceptanceCard.querySelector('p:nth-of-type(2)').textContent = summary.overall_acceptance_rate + '%';
    }
}

/**
 * Setup event handlers
 */
function setupEventHandlers() {
    // Add any additional event listeners here
    // For example, refresh button, filters, etc.
    
    // Refresh data button (if needed)
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            initializeDashboard();
            showNotification('Dashboard refreshed', 'success');
        });
    }
}

/**
 * Setup sidebar active state
 */
function setupSidebar() {
    // Add active state to dashboard link
    const dashboardLink = document.querySelector('a[href="{% url \'admin_app:dashboard\' %}"]');
    if (dashboardLink) {
        dashboardLink.parentElement.classList.add('active');
    }
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;

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

/**
 * Setup logout modal events
 */
function setupLogoutModalEvents() {
    const modal = document.getElementById('logoutModal');
    if (!modal) return;

    // Listen for logout links (updated to use Django URL)
    document.addEventListener('click', function(e) {
        const logoutLink = e.target.closest('a[href="{% url \'admin_app:logout\' %}"]');
        if (logoutLink) {
            e.preventDefault();
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    });

    // Close button
    const closeBtn = document.getElementById('closeLogoutModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }

    // Cancel button
    const cancelBtn = document.getElementById('cancelLogoutBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }

    // Confirm logout button
    const confirmBtn = document.getElementById('confirmLogoutBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', () => {
            // Redirect to logout URL
            window.location.href = '{% url "admin_app:logout" %}';
        });
    }

    // Close when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });

    // Close with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
}
