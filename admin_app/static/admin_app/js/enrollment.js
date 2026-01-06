document.addEventListener('DOMContentLoaded', () => {
    // Initialize enrollment page
    initializeEnrollment();
    
    // Setup filters
    const programFilter = document.getElementById('programFilter');
    const statusFilter = document.getElementById('statusFilter');
    const schoolYearFilter = document.getElementById('schoolYearFilter');

    [programFilter, statusFilter].forEach((el) => {
        if (el) {
            el.addEventListener('change', loadAllData);
        }
    });

    const refreshBtn = document.querySelector('button[onclick="refreshData()"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadAllData);
    }

    // Setup logout modal
    setupLogoutModalEvents();
});

/**
 * Initialize enrollment page with all data
 */
async function initializeEnrollment() {
    try {
        // Load header data
        await loadHeaderData();
        
        // Load enrollment data
        await loadAllData();
    } catch (error) {
        console.error('Error initializing enrollment page:', error);
        showNotification('Error loading page data', 'error');
    }
}

/**
 * Load header data from backend API
 */
async function loadHeaderData() {
    try {
        const response = await fetch(window.ENROLLMENT_API_BASE + 'header/');
        
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
        
        // Update modal user info
        const modalCurrentUser = document.getElementById('modalCurrentUser');
        if (modalCurrentUser) {
            modalCurrentUser.textContent = data.full_name;
        }
        
    } catch (error) {
        console.error('Error loading header data:', error);
        showNotification('Error loading user information', 'error');
    }
}

function getFilters() {
    const program = document.getElementById('programFilter')?.value || 'all';
    const status = document.getElementById('statusFilter')?.value || 'all';
    // School year is now just for display, not filtering
    return { program, status };
}

async function loadAllData() {
    setRefreshLoading(true);
    await Promise.all([loadSummary(), loadRequests()]);
    setRefreshLoading(false);
}

async function loadSummary() {
    try {
        const params = new URLSearchParams(getFilters());
        const response = await fetch(`${window.ENROLLMENT_API_BASE}summary/?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to load summary');
        const data = await response.json();

        document.getElementById('totalRequestsCount').textContent = data.total_requests ?? 0;
        document.getElementById('approvedCount').textContent = data.approved ?? 0;
        document.getElementById('pendingCount').textContent = data.pending ?? 0;
        document.getElementById('rejectedCount').textContent = data.rejected ?? 0;
    } catch (err) {
        console.error(err);
        showNotification('Unable to load summary data', 'error');
    }
}

async function loadRequests() {
    const tbody = document.getElementById('requestsTbody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 text-center text-gray-500 text-sm">Loading...</td></tr>';

    try {
        const params = new URLSearchParams(getFilters());
        const response = await fetch(`${window.ENROLLMENT_API_BASE}requests/?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to load requests');
        const { results } = await response.json();

        if (!results || results.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 text-center text-gray-500 text-sm">No enrollment requests found.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        results.forEach((item, index) => {
            const row = document.createElement('tr');
            row.className = 'hover:bg-gray-50 transition-colors';
            row.innerHTML = `
                <td class="px-6 py-4 text-sm text-gray-500">${index + 1}</td>
                <td class="px-6 py-4 text-sm font-medium text-gray-900">${item.lrn}</td>
                <td class="px-6 py-4 text-sm text-gray-900">${item.student_name}</td>
                <td class="px-6 py-4 text-sm font-medium text-gray-900">${item.program}</td>
                <td class="px-6 py-4 text-sm text-gray-900">${item.grade}</td>
                <td class="px-6 py-4 text-sm text-gray-500">${item.submitted_at}</td>
                <td class="px-6 py-4">${statusBadge(item.status)}</td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <a href="${item.detail_url}" class="px-3 py-1 bg-gradient-to-r from-primary to-primary-dark text-white rounded-lg text-sm font-medium flex items-center gap-1 hover:shadow-md transition-all">
                            <i class="fas fa-eye"></i> View
                        </a>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (err) {
        console.error(err);
        tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 text-center text-red-500 text-sm">Failed to load enrollment requests.</td></tr>';
        showNotification('Unable to load enrollment requests', 'error');
    }
}

function statusBadge(status) {
    const normalized = (status || '').toLowerCase();
    if (['submitted', 'under_review', 'pending'].includes(normalized)) {
        return '<span class="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit"><i class="fas fa-clock"></i> Pending</span>';
    }
    if (normalized === 'approved') {
        return '<span class="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit"><i class="fas fa-check-circle"></i> Approved</span>';
    }
    if (normalized === 'rejected') {
        return '<span class="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit"><i class="fas fa-times-circle"></i> Rejected</span>';
    }
    return `<span class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-semibold flex items-center gap-1 w-fit">${status || 'N/A'}</span>`;
}

function setRefreshLoading(isLoading) {
    const refreshBtn = document.querySelector('button[onclick="refreshData()"]');
    if (!refreshBtn) return;
    if (isLoading) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
    } else {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
    }
}

function refreshData() {
    loadAllData();
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `bg-white border-l-4 ${type === 'success' ? 'border-green-500' : type === 'error' ? 'border-red-500' : 'border-blue-500'} rounded-lg shadow-lg p-4 max-w-sm animate-slide-in-right`;
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

    // Listen for logout links
    document.addEventListener('click', function(e) {
        const logoutLink = e.target.closest('a[href*="logout"]');
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
            // Get the logout URL from the sidebar link
            const logoutLink = document.querySelector('a[href*="logout"]');
            if (logoutLink) {
                window.location.href = logoutLink.href;
            }
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