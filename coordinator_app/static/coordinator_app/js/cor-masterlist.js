document.addEventListener('DOMContentLoaded', function () {
    initializePage();
    setupEventListeners();
    setupPagination();
});

function initializePage() {
    window.totalStudents = 47;
    window.currentPage = 1;
    window.studentsPerPage = 8;
    window.totalPages = Math.ceil(window.totalStudents / window.studentsPerPage);
}

function setupEventListeners() {
    // Search
    const searchInput = document.getElementById('studentSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function () {
            filterStudents(this.value);
        });
    }

    // Drag-and-drop on the drop zone
    const dropZone = document.getElementById('dropZoneLabel');
    if (dropZone) {
        dropZone.addEventListener('dragover', function (e) {
            e.preventDefault();
            this.classList.add('border-teal-400', 'bg-teal-50');
        });
        dropZone.addEventListener('dragleave', function () {
            this.classList.remove('border-teal-400', 'bg-teal-50');
        });
        dropZone.addEventListener('drop', function (e) {
            e.preventDefault();
            this.classList.remove('border-teal-400', 'bg-teal-50');
            const file = e.dataTransfer.files[0];
            if (file) {
                const allowed = ['.csv', '.xlsx', '.xls'];
                const ext = '.' + file.name.split('.').pop().toLowerCase();
                if (!allowed.includes(ext)) {
                    showNotification('Invalid file type. Please upload .csv, .xlsx, or .xls files only.', 'error');
                    return;
                }
                // Assign to the file input
                const dt = new DataTransfer();
                dt.items.add(file);
                document.getElementById('importFile').files = dt.files;
                // Update UI
                document.getElementById('fileNameText').textContent = file.name;
                document.getElementById('selectedFileName').classList.remove('hidden');
                document.getElementById('importSubmitBtn').disabled = false;
            }
        });
    }
}

function setupPagination() {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const currentPageSpan = document.getElementById('currentPage');
    const totalPagesSpan = document.getElementById('totalPages');
    const showingCountSpan = document.getElementById('showingCount');
    const totalCountSpan = document.getElementById('totalCount');

    if (!prevBtn || !nextBtn) return;

    totalPagesSpan.textContent = window.totalPages;
    totalCountSpan.textContent = window.totalStudents;
    updatePaginationDisplay();

    prevBtn.addEventListener('click', function () {
        if (window.currentPage > 1) {
            window.currentPage--;
            updatePaginationDisplay();
        }
    });

    nextBtn.addEventListener('click', function () {
        if (window.currentPage < window.totalPages) {
            window.currentPage++;
            updatePaginationDisplay();
        }
    });

    function updatePaginationDisplay() {
        currentPageSpan.textContent = window.currentPage;
        showingCountSpan.textContent = Math.min(
            window.studentsPerPage,
            window.totalStudents - (window.currentPage - 1) * window.studentsPerPage
        );
        prevBtn.disabled = window.currentPage === 1;
        nextBtn.disabled = window.currentPage === window.totalPages;
    }
}

function filterStudents(searchTerm) {
    const rows = document.querySelectorAll('#studentTableBody tr');
    let visibleCount = 0;
    const searchLower = searchTerm.toLowerCase();

    rows.forEach(row => {
        const rowText = row.textContent.toLowerCase();
        if (rowText.includes(searchLower)) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });

    const emptyState = document.getElementById('emptyState');
    const tableBody  = document.getElementById('studentTableBody');

    if (visibleCount === 0 && searchTerm) {
        emptyState.classList.remove('hidden');
        if (tableBody) tableBody.style.display = 'none';
    } else {
        emptyState.classList.add('hidden');
        if (tableBody) tableBody.style.display = '';
    }

    const showingCount = document.getElementById('showingCount');
    if (showingCount) showingCount.textContent = visibleCount;
}

function clearSearch() {
    const searchInput = document.getElementById('studentSearch');
    if (searchInput) {
        searchInput.value = '';
        filterStudents('');
    }
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;

    const colors = {
        success: 'border-green-500',
        error:   'border-red-500',
        warning: 'border-yellow-500',
        info:    'border-blue-500',
    };
    const icons = {
        success: 'check-circle text-green-500',
        error:   'exclamation-circle text-red-500',
        warning: 'exclamation-triangle text-yellow-500',
        info:    'info-circle text-blue-500',
    };

    const notification = document.createElement('div');
    notification.className = `bg-white border-l-4 ${colors[type] || colors.info} rounded-lg shadow-lg p-4 max-w-sm`;
    notification.innerHTML = `
        <div class="flex items-start gap-3">
            <i class="fas fa-${icons[type] || icons.info} mt-1"></i>
            <div class="flex-1">
                <p class="text-sm font-medium text-gray-800">${message}</p>
            </div>
            <button class="text-gray-400 hover:text-gray-600 transition-colors" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    container.appendChild(notification);
    setTimeout(() => { if (notification.parentElement) notification.remove(); }, 5000);
}

// Expose globals
window.clearSearch       = clearSearch;
window.showNotification  = showNotification;