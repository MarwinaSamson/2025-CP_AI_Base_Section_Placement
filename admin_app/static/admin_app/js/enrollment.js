document.addEventListener('DOMContentLoaded', () => {
    initializeEnrollment();

    const programFilter     = document.getElementById('programFilter');
    const statusFilter      = document.getElementById('statusFilter');
    const gradeLevelFilter  = document.getElementById('gradeLevelFilter'); // NEW

    [programFilter, statusFilter, gradeLevelFilter].forEach(el => {
        if (el) el.addEventListener('change', loadAllData);
    });

    const refreshBtn = document.querySelector('button[onclick="refreshData()"]');
    if (refreshBtn) refreshBtn.addEventListener('click', loadAllData);

    setupLogoutModalEvents();
});

async function initializeEnrollment() {
    try {
        await loadHeaderData();
        await loadAllData();
    } catch (error) {
        console.error('Error initializing enrollment page:', error);
        showNotification('Error loading page data', 'error');
    }
}

async function loadHeaderData() {
    try {
        const response = await fetch(window.ENROLLMENT_API_BASE + 'header/');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();

        const schoolYearEl = document.getElementById('schoolYearDisplay');
        if (schoolYearEl) schoolYearEl.textContent = data.school_year;

        const userFullNameEl = document.getElementById('userFullName');
        if (userFullNameEl) userFullNameEl.textContent = data.full_name;

        const userRoleEl = document.getElementById('userRole');
        if (userRoleEl) userRoleEl.textContent = data.role;

        const userInitialsEl = document.getElementById('userInitials');
        if (userInitialsEl) userInitialsEl.textContent = data.initials;

        const userPhotoContainer = document.getElementById('userPhotoContainer');
        if (userPhotoContainer && data.photo_url) {
            userPhotoContainer.innerHTML = `<img src="${data.photo_url}" alt="User" class="w-full h-full object-cover">`;
        }

        const modalCurrentUser = document.getElementById('modalCurrentUser');
        if (modalCurrentUser) modalCurrentUser.textContent = data.full_name;

    } catch (error) {
        console.error('Error loading header data:', error);
        showNotification('Error loading user information', 'error');
    }
}

// ── Returns all active filters including the new grade level ──
function getFilters() {
    return {
        program:    document.getElementById('programFilter')?.value    || 'all',
        status:     document.getElementById('statusFilter')?.value     || 'all',
        grade:      document.getElementById('gradeLevelFilter')?.value || 'all',  // NEW
    };
}

async function loadAllData() {
    setRefreshLoading(true);
    await Promise.all([loadSummary(), loadRequests()]);
    setRefreshLoading(false);
}

// ── Fetches per-grade counts and populates the 4 grade cards ──
async function loadSummary() {
    try {
        const params = new URLSearchParams(getFilters());
        const response = await fetch(`${window.ENROLLMENT_API_BASE}summary/?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to load summary');
        const data = await response.json();

        // data.grades is an array:
        // [{ code:'G7', total:10, pending:6, approved:3 }, ...]
        const gradeMap = {};
        (data.grades || []).forEach(g => { gradeMap[g.code] = g; });

        ['G7','G8','G9','G10'].forEach(code => {
            const g = gradeMap[code] || { total: 0, pending: 0, approved: 0 };
            const key = code.toLowerCase();
            const totalEl    = document.getElementById(`${key}-total`);
            const pendingEl  = document.getElementById(`${key}-pending`);
            const approvedEl = document.getElementById(`${key}-approved`);
            if (totalEl)    totalEl.textContent    = g.total;
            if (pendingEl)  pendingEl.textContent  = g.pending;
            if (approvedEl) approvedEl.textContent = g.approved;
        });

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
                </td>`;
            tbody.appendChild(row);
        });

    } catch (err) {
        console.error(err);
        tbody.innerHTML = '<tr><td colspan="8" class="px-6 py-4 text-center text-red-500 text-sm">Failed to load enrollment requests.</td></tr>';
        showNotification('Unable to load enrollment requests', 'error');
    }
}

function statusBadge(status) {
    const s = (status || '').toLowerCase();
    if (['submitted','under_review','pending'].includes(s))
        return '<span class="px-3 py-1 bg-amber-100 text-amber-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit"><i class="fas fa-clock"></i> Pending</span>';
    if (s === 'approved')
        return '<span class="px-3 py-1 bg-emerald-100 text-emerald-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit"><i class="fas fa-check-circle"></i> Approved</span>';
    if (s === 'rejected')
        return '<span class="px-3 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold flex items-center gap-1 w-fit"><i class="fas fa-times-circle"></i> Rejected</span>';
    return `<span class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-semibold flex items-center gap-1 w-fit">${status || 'N/A'}</span>`;
}

function setRefreshLoading(isLoading) {
    const btn = document.querySelector('button[onclick="refreshData()"]');
    if (!btn) return;
    btn.disabled = isLoading;
    btn.innerHTML = isLoading
        ? '<i class="fas fa-spinner fa-spin"></i> Refreshing...'
        : '<i class="fas fa-sync-alt"></i> Refresh';
}

function refreshData() { loadAllData(); }

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;
    const n = document.createElement('div');
    n.className = `bg-white border-l-4 ${type === 'success' ? 'border-green-500' : type === 'error' ? 'border-red-500' : 'border-blue-500'} rounded-lg shadow-lg p-4 max-w-sm`;
    n.innerHTML = `
        <div class="flex items-start gap-3">
            <i class="fas fa-${type === 'success' ? 'check-circle text-green-500' : type === 'error' ? 'exclamation-circle text-red-500' : 'info-circle text-blue-500'} mt-1"></i>
            <div class="flex-1"><p class="text-sm font-medium text-gray-800">${message}</p></div>
            <button class="text-gray-400 hover:text-gray-600" onclick="this.parentElement.parentElement.remove()"><i class="fas fa-times"></i></button>
        </div>`;
    container.appendChild(n);
    setTimeout(() => { if (n.parentElement) n.remove(); }, 5000);
}

function setupLogoutModalEvents() {
    const modal = document.getElementById('logoutModal');
    if (!modal) return;
    document.addEventListener('click', e => {
        const logoutLink = e.target.closest('a[href*="logout"]');
        if (logoutLink) { e.preventDefault(); modal.classList.remove('hidden'); document.body.style.overflow = 'hidden'; }
    });
    document.getElementById('closeLogoutModal')?.addEventListener('click', () => { modal.classList.add('hidden'); document.body.style.overflow = 'auto'; });
    document.getElementById('cancelLogoutBtn')?.addEventListener('click', () => { modal.classList.add('hidden'); document.body.style.overflow = 'auto'; });
    document.getElementById('confirmLogoutBtn')?.addEventListener('click', () => {
        const logoutLink = document.querySelector('a[href*="logout"]');
        if (logoutLink) window.location.href = logoutLink.href;
    });
    modal.addEventListener('click', e => { if (e.target === modal) { modal.classList.add('hidden'); document.body.style.overflow = 'auto'; } });
    document.addEventListener('keydown', e => { if (e.key === 'Escape' && !modal.classList.contains('hidden')) { modal.classList.add('hidden'); document.body.style.overflow = 'auto'; } });
}