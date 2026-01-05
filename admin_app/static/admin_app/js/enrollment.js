document.addEventListener('DOMContentLoaded', () => {
    const programFilter = document.getElementById('programFilter');
    const statusFilter = document.getElementById('statusFilter');
    const schoolYearFilter = document.getElementById('schoolYearFilter');

    [programFilter, statusFilter, schoolYearFilter].forEach((el) => {
        if (el) {
            el.addEventListener('change', loadAllData);
        }
    });

    const refreshBtn = document.querySelector('button[onclick="refreshData()"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', loadAllData);
    }

    loadAllData();
});

function getFilters() {
    const program = document.getElementById('programFilter')?.value || 'all';
    const status = document.getElementById('statusFilter')?.value || 'all';
    const school_year = document.getElementById('schoolYearFilter')?.value || '';
    return { program, status, school_year };
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

            // Close modal with X button
            const closeBtn = document.getElementById('closeLogoutModal');
            if (closeBtn) {
                closeBtn.addEventListener('click', function() {
                    modal.classList.add('hidden');
                    document.body.style.overflow = 'auto';
                });
            }

            // Cancel button
            const cancelBtn = document.getElementById('cancelLogoutBtn');
            if (cancelBtn) {
                cancelBtn.addEventListener('click', function() {
                    modal.classList.add('hidden');
                    document.body.style.overflow = 'auto';
                });
            }

            // Logout button
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