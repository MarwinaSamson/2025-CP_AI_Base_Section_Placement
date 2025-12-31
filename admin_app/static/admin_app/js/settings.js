// API Configuration - FIXED: Match your Django URL structure
const API_BASE = '/admin-portal/api';  // Changed to match your URL pattern

// CSRF Token helper
function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
           document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] || '';
}

// Fetch helper
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ error: `HTTP Error: ${response.status}` }));
        throw new Error(error.error || `HTTP Error: ${response.status}`);
    }

    return await response.json();
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function () {
    // Load initial data
    loadUsersTable();
    loadHistoryTable();
    loadPositionsTable();
    loadDepartmentsTable();
    loadContentSettings();
    
    // Setup all event listeners and tabs
    setupEventListeners();
    setupTabs();
    setupOthersTabs();
    setupLogoutModalEvents();
    setupContentManagementListeners();
});

// ============== SETUP FUNCTIONS ==============

function setupEventListeners() {
    // Add User button
    const addUserBtn = document.getElementById('addUserBtn');
    if (addUserBtn) {
        addUserBtn.addEventListener('click', openAddUserModal);
    }

    // Search functionality
    const userSearch = document.getElementById('userSearch');
    if (userSearch) {
        userSearch.addEventListener('input', function () {
            filterUsers(this.value);
        });
    }

    const historySearch = document.getElementById('historySearch');
    if (historySearch) {
        historySearch.addEventListener('input', function () {
            filterHistory(this.value);
        });
    }

    // Add User Form
    const addUserForm = document.getElementById('addUserForm');
    if (addUserForm) {
        addUserForm.addEventListener('submit', handleAddUserForm);
    }

    // Add Position Form
    const addPositionForm = document.getElementById('addPositionForm');
    if (addPositionForm) {
        addPositionForm.addEventListener('submit', handleAddPositionForm);
    }

    // Add Department Form
    const addDepartmentForm = document.getElementById('addDepartmentForm');
    if (addDepartmentForm) {
        addDepartmentForm.addEventListener('submit', handleAddDepartmentForm);
    }

    // Add Position Button
    const addPositionBtn = document.getElementById('addPositionBtn');
    if (addPositionBtn) {
        addPositionBtn.addEventListener('click', openAddPositionModal);
    }

    // Add Department Button
    const addDepartmentBtn = document.getElementById('addDepartmentBtn');
    if (addDepartmentBtn) {
        addDepartmentBtn.addEventListener('click', openAddDepartmentModal);
    }

    // File upload handlers
    document.querySelectorAll('.border-dashed input[type="file"]').forEach((input) => {
        const uploadArea = input.parentElement;
        uploadArea.addEventListener('click', function () {
            input.click();
        });

        input.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                uploadLogo(file, input);
                uploadArea.innerHTML = `<i class="fas fa-check-circle text-green-500 text-3xl mb-3"></i><p class="text-green-500">${file.name}</p>`;
            }
        });
    });

    // Text editor functionality
    document.querySelectorAll(".border-gray-300 button").forEach((button) => {
        button.addEventListener("click", function (e) {
            e.preventDefault();
            const command = this.querySelector("i").classList[1].split("-")[1];
            switch (command) {
                case "bold": document.execCommand("bold"); break;
                case "italic": document.execCommand("italic"); break;
                case "underline": document.execCommand("underline"); break;
                case "ul": document.execCommand("insertUnorderedList"); break;
                case "ol": document.execCommand("insertOrderedList"); break;
                case "link": {
                    const url = prompt("Enter URL:");
                    if (url) document.execCommand("createLink", false, url);
                    break;
                }
            }
        });
    });

    // Close modals when clicking outside
    document.addEventListener('click', function (event) {
        if (event.target.classList.contains('fixed')) {
            closeAllModals();
        }

        if (!event.target.closest('.relative')) {
            document.querySelectorAll('.absolute').forEach(menu => {
                menu.classList.remove('block');
            });
        }
    });

    // Close modals with Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
}

function setupTabs() {
    // Main tabs
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll("section[id$='-tab']");

    tabBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            const tabName = btn.getAttribute("data-tab");

            tabBtns.forEach((b) => {
                b.classList.remove("bg-gradient-to-r", "from-primary", "to-primary-dark", "text-white");
                b.classList.add("text-gray-700", "hover:bg-gray-50");
            });

            tabContents.forEach((c) => c.classList.add("hidden"));

            btn.classList.remove("text-gray-700", "hover:bg-gray-50");
            btn.classList.add("bg-gradient-to-r", "from-primary", "to-primary-dark", "text-white");
            document.getElementById(`${tabName}-tab`).classList.remove("hidden");
        });
    });

    // Content Management sub-tabs
    const contentTabBtns = document.querySelectorAll(".content-tab-btn");
    const contentSections = document.querySelectorAll("[id$='-content']");

    contentTabBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            const contentName = btn.getAttribute("data-content");

            contentTabBtns.forEach((b) => {
                b.classList.remove("bg-red-50", "text-primary", "border-red-200");
                b.classList.add("text-gray-700", "hover:bg-gray-50", "border-gray-200");
            });

            contentSections.forEach((s) => s.classList.add("hidden"));

            btn.classList.remove("text-gray-700", "hover:bg-gray-50", "border-gray-200");
            btn.classList.add("bg-red-50", "text-primary", "border-red-200");
            document.getElementById(`${contentName}-content`).classList.remove("hidden");
        });
    });
}

function setupOthersTabs() {
    const othersTabBtns = document.querySelectorAll('.others-tab-btn');
    const othersSections = document.querySelectorAll('[id$="-others"]');

    othersTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const othersName = btn.getAttribute('data-others');

            othersTabBtns.forEach(b => {
                b.classList.remove('bg-red-50', 'text-primary', 'border-red-200');
                b.classList.add('text-gray-700', 'hover:bg-gray-50', 'border-gray-200');
            });

            othersSections.forEach(s => s.classList.add('hidden'));

            btn.classList.remove('text-gray-700', 'hover:bg-gray-50', 'border-gray-200');
            btn.classList.add('bg-red-50', 'text-primary', 'border-red-200');
            document.getElementById(`${othersName}-others`).classList.remove('hidden');
        });
    });
}

// ============== USER MANAGEMENT FUNCTIONS ==============

async function loadUsersTable() {
    const tableBody = document.getElementById('usersTableBody');
    if (!tableBody) return;

    try {
        tableBody.innerHTML = '<tr><td colspan="5" class="px-6 py-8 text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';
        
        const response = await apiCall('/users/');
        const users = response.users || [];

        if (users.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                        <i class="fas fa-users text-4xl mb-3"></i>
                        <p>No users found. Add your first user!</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = users.map(user => {
            const accessBadges = user.access_badges.map(badge => {
                const color = badge === 'Admin' ? 'red' : 'orange';
                return `<span class="inline-block px-3 py-1 bg-${color}-600 text-white rounded-full text-xs font-semibold mr-1 mb-1">${badge}</span>`;
            }).join('');
            
            const initials = user.first_name && user.last_name 
                ? `${user.first_name[0]}${user.last_name[0]}` 
                : user.username[0].toUpperCase();
            
            return `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4">
                    <div class="flex items-center">
                        <div class="w-10 h-10 bg-gradient-to-br from-primary to-primary-dark rounded-full flex items-center justify-center mr-3">
                            <span class="text-white font-bold text-xs">${initials}</span>
                        </div>
                        <div>
                            <div class="font-medium text-gray-900">${user.full_name}</div>
                            <div class="text-gray-500 text-sm">${user.email}</div>
                            <div class="text-gray-400 text-xs">ID: ${user.employee_id}</div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4">
                    ${accessBadges}
                </td>
                <td class="px-6 py-4 text-gray-600">${user.last_login}</td>
                <td class="px-6 py-4 text-gray-600">${user.date_joined}</td>
                <td class="px-6 py-4">
                    <div class="relative">
                        <button class="px-3 py-1 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors duration-300" onclick="toggleDropdown(this)">
                            <i class="fas fa-ellipsis-v"></i>
                        </button>
                        <div class="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-200 z-10 hidden animate-dropdown">
                            <a href="#" class="block px-4 py-3 text-gray-700 hover:bg-gray-50 transition-colors duration-200 rounded-t-xl" onclick="viewUserProfile(${user.id}); return false;">
                                <i class="fas fa-eye mr-2"></i> View Profile
                            </a>
                            <a href="#" class="block px-4 py-3 text-gray-700 hover:bg-gray-50 transition-colors duration-200" onclick="editUser(${user.id}); return false;">
                                <i class="fas fa-edit mr-2"></i> Edit Details
                            </a>
                            <div class="border-t border-gray-100"></div>
                            <a href="#" class="block px-4 py-3 text-red-600 hover:bg-red-50 transition-colors duration-200 rounded-b-xl" onclick="deleteUser(${user.id}); return false;">
                                <i class="fas fa-trash mr-2"></i> Delete User
                            </a>
                        </div>
                    </div>
                </td>
            </tr>
        `;
        }).join('');
    } catch (error) {
        console.error('Error loading users:', error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-8 text-center text-red-500">
                    <i class="fas fa-exclamation-triangle mb-2"></i><br>
                    Error loading users: ${error.message}
                </td>
            </tr>
        `;
        showNotification('Error loading users', 'error');
    }
}

function filterUsers(searchTerm) {
    const rows = document.querySelectorAll("#usersTableBody tr");
    rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm.toLowerCase()) ? "" : "none";
    });
}

async function openAddUserModal() {
    const modal = document.getElementById('addUserModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    // Load positions, departments, and programs into dropdowns
    await loadPositionsDropdown();
    await loadDepartmentsDropdown();
    await loadProgramsDropdown();
    
    // Setup event listeners for user type checkboxes
    setupUserTypeListeners();
}

function setupUserTypeListeners() {
    const adminCheckbox = document.getElementById('admin_access');
    const coordinatorCheckbox = document.getElementById('staff_expert_access');
    const programField = document.getElementById('programField');
    const programSelect = document.getElementById('program');
    
    if (!adminCheckbox || !coordinatorCheckbox) return;
    
    function updateProgramField() {
        const isCoordinator = coordinatorCheckbox.checked;
        const isAdmin = adminCheckbox.checked;
        
        if (isCoordinator && !isAdmin) {
            // Only coordinator - show program field
            programField.classList.remove('hidden');
            programSelect.required = true;
        } else {
            // Admin or both - hide program field
            programField.classList.add('hidden');
            programSelect.required = false;
            programSelect.value = '';
        }
    }
    
    adminCheckbox.removeEventListener('change', updateProgramField);
    coordinatorCheckbox.removeEventListener('change', updateProgramField);
    
    adminCheckbox.addEventListener('change', updateProgramField);
    coordinatorCheckbox.addEventListener('change', updateProgramField);
    
    // Initial check
    updateProgramField();
}

async function loadPositionsDropdown() {
    const positionSelect = document.getElementById('position');
    if (!positionSelect) return;
    
    try {
        const response = await apiCall('/positions/');
        const positions = response.positions || [];
        
        // Clear existing options except the first (placeholder)
        positionSelect.innerHTML = '<option value="">Select Position</option>';
        
        // Add positions
        positions.forEach(position => {
            const option = document.createElement('option');
            option.value = position.id;
            option.textContent = position.name;
            positionSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading positions:', error);
        showNotification('Error loading positions', 'error');
    }
}

async function loadDepartmentsDropdown() {
    const departmentSelect = document.getElementById('department');
    if (!departmentSelect) return;
    
    try {
        const response = await apiCall('/departments/');
        const departments = response.departments || [];
        
        // Clear existing options except the first (placeholder)
        departmentSelect.innerHTML = '<option value="">Select Department</option>';
        
        // Add departments
        departments.forEach(department => {
            const option = document.createElement('option');
            option.value = department.id;
            option.textContent = department.name;
            departmentSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading departments:', error);
        showNotification('Error loading departments', 'error');
    }
}

async function loadProgramsDropdown() {
    const programSelect = document.getElementById('program');
    if (!programSelect) return;
    
    try {
        const response = await apiCall('/programs/');
        const programs = response.programs || [];
        
        // Clear existing options except the first (placeholder)
        programSelect.innerHTML = '<option value="">Select Program</option>';
        
        // Add programs
        programs.forEach(program => {
            const option = document.createElement('option');
            option.value = program.id;
            option.textContent = program.name;
            programSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading programs:', error);
        showNotification('Error loading programs', 'error');
    }
}

function closeAddUserModal() {
    const modal = document.getElementById('addUserModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    document.getElementById('addUserForm').reset();
}

function closeAllModals() {
    document.querySelectorAll('.fixed').forEach(modal => {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
    });
}

async function handleAddUserForm(event) {
    event.preventDefault();

    const firstName = document.getElementById('first_name').value.trim();
    const lastName = document.getElementById('last_name').value.trim();
    const email = document.getElementById('email').value.trim();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const employeeid = document.getElementById('employeeid').value.trim();
    const position = document.getElementById('position').value;
    const department = document.getElementById('department').value;
    const program = document.getElementById('program').value;
    
    // Determine user type from checkboxes
    const adminAccess = document.getElementById('admin_access').checked;
    const coordinatorAccess = document.getElementById('staff_expert_access').checked;

    if (!firstName || !lastName || !email || !username || !password || !employeeid) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }
    
    // Validate program for coordinators
    if (coordinatorAccess && !adminAccess && !program) {
        showNotification('Program is required for coordinators', 'error');
        return;
    }

    // Show loading state
    const submitButton = event.target.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Adding User...';

    try {
        await apiCall('/users/add/', 'POST', {
            first_name: firstName,
            last_name: lastName,
            email,
            username,
            password,
            employee_id: employeeid,
            position: position || null,
            department: department || null,
            program: program || null,
            admin_access: adminAccess,
            coordinator_access: coordinatorAccess
        });

        showNotification(`User ${firstName} ${lastName} added successfully!`, 'success');
        loadUsersTable();
        closeAddUserModal();
        document.getElementById('addUserForm').reset();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    }
}

async function viewUserProfile(userId) {
    showNotification('View profile functionality coming soon', 'info');
}

async function editUser(userId) {
    showNotification('Edit functionality coming soon', 'info');
}

async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }

    try {
        await apiCall(`/users/${userId}/delete/`, 'DELETE');
        showNotification('User deleted successfully!', 'success');
        loadUsersTable();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

function toggleDropdown(button) {
    const dropdown = button.nextElementSibling;
    const isShowing = dropdown.classList.contains('hidden');

    document.querySelectorAll('.absolute').forEach(menu => {
        if (menu !== dropdown) {
            menu.classList.remove('block');
            menu.classList.add('hidden');
        }
    });

    if (isShowing) {
        dropdown.classList.remove('hidden');
        dropdown.classList.add('block');
    } else {
        dropdown.classList.remove('block');
        dropdown.classList.add('hidden');
    }
}

// ============== ACTIVITY LOG FUNCTIONS ==============

async function loadHistoryTable() {
    const tableBody = document.getElementById('historyTableBody');
    if (!tableBody) return;

    try {
        tableBody.innerHTML = '<tr><td colspan="3" class="px-6 py-8 text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';
        
        const response = await apiCall('/logs/');
        const logs = response.data;

        if (logs.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="3" class="px-6 py-8 text-center text-gray-500">
                        <i class="fas fa-history text-4xl mb-3"></i>
                        <p>No activity logs yet.</p>
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = logs.map(log => `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 text-gray-600">
                    <div class="font-medium">${log.user_full_name}</div>
                    <div class="text-sm text-gray-500">${log.action}</div>
                </td>
                <td class="px-6 py-4 text-gray-600">${log.date_formatted}</td>
                <td class="px-6 py-4 text-gray-600">${log.time_formatted}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading logs:', error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="3" class="px-6 py-8 text-center text-red-500">
                    Error loading logs: ${error.message}
                </td>
            </tr>
        `;
    }
}

function filterHistory(searchTerm) {
    const rows = document.querySelectorAll("#historyTableBody tr");
    rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm.toLowerCase()) ? "" : "none";
    });
}

// ============== LOGO MANAGEMENT ==============

async function uploadLogo(file, input) {
    const uploadArea = input.parentElement;
    const logoType = input.dataset.logoType || 'school';

    const formData = new FormData();
    formData.append('image', file);
    formData.append('logo_type', logoType);
    formData.append('alt_text', `${logoType} Logo`);

    try {
        const response = await fetch(`${API_BASE}/logos/upload/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error);
        }

        const data = await response.json();
        showNotification('Logo uploaded successfully!', 'success');
        loadLogos();
    } catch (error) {
        showNotification(`Error uploading logo: ${error.message}`, 'error');
    }
}

async function loadLogos() {
    try {
        const response = await apiCall('/logos/');
        const logos = response.data;

        logos.forEach(logo => {
            const input = document.querySelector(`input[data-logo-type="${logo.logo_type}"]`);
            if (input) {
                const uploadArea = input.parentElement;
                uploadArea.innerHTML = `<i class="fas fa-check-circle text-green-500 text-3xl mb-3"></i><p class="text-green-500">Uploaded: ${logo.formatted_date}</p>`;
            }
        });
    } catch (error) {
        console.error('Error loading logos:', error);
    }
}

// ============== CONTENT SETTINGS ==============

async function saveContentSettings(settingType, key, value) {
    try {
        const response = await apiCall('/settings/save/', 'POST', {
            setting_type: settingType,
            key,
            value
        });

        showNotification('Settings saved successfully!', 'success');
        return response;
    } catch (error) {
        showNotification(`Error saving settings: ${error.message}`, 'error');
        throw error;
    }
}

// ============== NOTIFICATION FUNCTION ==============

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
            <button class="text-gray-400 hover:text-gray-600 transition-colors duration-300" onclick="this.parentElement.parentElement.remove()">
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
    const modal = document.getElementById('logoutModal');
    if (!modal) return;

    document.addEventListener('click', function(e) {
        if (e.target.closest('a[href*="logout"]')) {
            e.preventDefault();
            e.stopPropagation();
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    });

    const closeBtn = document.getElementById('closeLogoutModal');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }

    const cancelBtn = document.getElementById('cancelLogoutBtn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }

    const logoutBtn = document.getElementById('confirmLogoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            window.location.href = logoutBtn.dataset.logoutUrl || '/admin/logout/';
        });
    }

    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
}

// ============== POSITIONS TABLE ==============
async function loadPositionsTable() {
    try {
        const response = await apiCall('/positions/');
        const positions = response.data || [];
        
        const tbody = document.getElementById('positionsTableBody');
        if (!tbody) return;
        
        if (positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="2" class="text-center text-gray-500 py-4">No positions found</td></tr>';
            return;
        }
        
        tbody.innerHTML = positions.map(position => `
            <tr class="border-b border-gray-200 hover:bg-gray-50">
                <td class="px-6 py-4 text-gray-900">${position.name}</td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <button onclick="editPosition(${position.id}, '${position.name}', '${position.description || ''}')" 
                                class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button onclick="deletePosition(${position.id})" 
                                class="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm">
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading positions:', error);
        const tbody = document.getElementById('positionsTableBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="2" class="text-center text-red-500 py-4">Error loading positions: ${error.message}</td></tr>`;
        }
    }
}

function openAddPositionModal() {
    const modal = document.getElementById('addPositionModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.getElementById('addPositionForm').reset();
    document.getElementById('positionId').value = '';
    document.getElementById('positionModalTitle').textContent = 'Add New Position';
    document.getElementById('positionSubmitText').textContent = 'Add Position';
}

function closePositionModal() {
    const modal = document.getElementById('addPositionModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
}

async function handleAddPositionForm(event) {
    event.preventDefault();
    
    const positionId = document.getElementById('positionId').value;
    const name = document.getElementById('position_name').value;
    const description = document.getElementById('position_description').value;
    
    try {
        if (positionId) {
            // Update existing position
            await apiCall(`/positions/${positionId}/update/`, 'PUT', { name, description });
            showNotification('Position updated successfully!', 'success');
        } else {
            // Add new position
            await apiCall('/positions/add/', 'POST', { name, description });
            showNotification('Position added successfully!', 'success');
        }
        
        loadPositionsTable();
        closePositionModal();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

function editPosition(id, name, description) {
    document.getElementById('positionId').value = id;
    document.getElementById('position_name').value = name;
    document.getElementById('position_description').value = description || '';
    document.getElementById('positionModalTitle').textContent = 'Edit Position';
    document.getElementById('positionSubmitText').textContent = 'Update Position';
    
    const modal = document.getElementById('addPositionModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

async function deletePosition(id) {
    if (!confirm('Are you sure you want to delete this position?')) {
        return;
    }
    
    try {
        await apiCall(`/positions/${id}/delete/`, 'DELETE');
        showNotification('Position deleted successfully!', 'success');
        loadPositionsTable();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// ============== DEPARTMENTS TABLE ==============
async function loadDepartmentsTable() {
    try {
        const response = await apiCall('/departments/');
        const departments = response.data || [];
        
        const tbody = document.getElementById('departmentsTableBody');
        if (!tbody) return;
        
        if (departments.length === 0) {
            tbody.innerHTML = '<tr><td colspan="2" class="text-center text-gray-500 py-4">No departments found</td></tr>';
            return;
        }
        
        tbody.innerHTML = departments.map(department => `
            <tr class="border-b border-gray-200 hover:bg-gray-50">
                <td class="px-6 py-4 text-gray-900">${department.name}</td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <button onclick="editDepartment(${department.id}, '${department.name}', '${department.description || ''}')" 
                                class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button onclick="deleteDepartment(${department.id})" 
                                class="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm">
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading departments:', error);
        const tbody = document.getElementById('departmentsTableBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="2" class="text-center text-red-500 py-4">Error loading departments: ${error.message}</td></tr>`;
        }
    }
}

function openAddDepartmentModal() {
    const modal = document.getElementById('addDepartmentModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.getElementById('addDepartmentForm').reset();
    document.getElementById('departmentId').value = '';
    document.getElementById('departmentModalTitle').textContent = 'Add New Department';
    document.getElementById('departmentSubmitText').textContent = 'Add Department';
}

function closeDepartmentModal() {
    const modal = document.getElementById('addDepartmentModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
}

async function handleAddDepartmentForm(event) {
    event.preventDefault();
    
    const departmentId = document.getElementById('departmentId').value;
    const name = document.getElementById('department_name').value;
    const description = document.getElementById('department_description').value;
    
    try {
        if (departmentId) {
            // Update existing department
            await apiCall(`/departments/${departmentId}/update/`, 'PUT', { name, description });
            showNotification('Department updated successfully!', 'success');
        } else {
            // Add new department
            await apiCall('/departments/add/', 'POST', { name, description });
            showNotification('Department added successfully!', 'success');
        }
        
        loadDepartmentsTable();
        closeDepartmentModal();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

function editDepartment(id, name, description) {
    document.getElementById('departmentId').value = id;
    document.getElementById('department_name').value = name;
    document.getElementById('department_description').value = description || '';
    document.getElementById('departmentModalTitle').textContent = 'Edit Department';
    document.getElementById('departmentSubmitText').textContent = 'Update Department';
    
    const modal = document.getElementById('addDepartmentModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

async function deleteDepartment(id) {
    if (!confirm('Are you sure you want to delete this department?')) {
        return;
    }
    
    try {
        await apiCall(`/departments/${id}/delete/`, 'DELETE');
        showNotification('Department deleted successfully!', 'success');
        loadDepartmentsTable();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// ============== MAKE FUNCTIONS GLOBALLY AVAILABLE ==============

window.openAddUserModal = openAddUserModal;
window.closeAddUserModal = closeAddUserModal;
window.editDetails = editDetails;
window.changePermission = changePermission;
window.deleteUser = deleteUser;
window.toggleDropdown = toggleDropdown;
window.showNotification = showNotification;
window.saveContentSettings = saveContentSettings;
window.loadLogos = loadLogos;
window.loadPositionsTable = loadPositionsTable;
window.loadDepartmentsTable = loadDepartmentsTable;
window.openAddPositionModal = openAddPositionModal;
window.closePositionModal = closePositionModal;
window.editPosition = editPosition;
window.deletePosition = deletePosition;
window.openAddDepartmentModal = openAddDepartmentModal;
window.closeDepartmentModal = closeDepartmentModal;
window.editDepartment = editDepartment;
window.deleteDepartment = deleteDepartment;


// ============== CONTENT MANAGEMENT FUNCTIONS ==============

function setupContentManagementListeners() {
    // Save Header Caption
    const saveHeaderCaptionBtn = document.getElementById('saveHeaderCaptionBtn');
    if (saveHeaderCaptionBtn) {
        saveHeaderCaptionBtn.addEventListener('click', saveHeaderCaption);
    }
    
    // Save Contact Info
    const saveContactBtn = document.getElementById('saveContactBtn');
    if (saveContactBtn) {
        saveContactBtn.addEventListener('click', saveContactInfo);
    }
}

async function loadContentSettings() {
    try {
        const response = await apiCall('/content/settings/');
        const settings = response.settings || {};
        
        // Load Header Caption
        if (settings.header_caption) {
            const headerCaption = document.getElementById('headerCaption');
            if (headerCaption) {
                headerCaption.innerHTML = settings.header_caption.value || '';
            }
        }
        
        // Load Contact Info
        if (settings.contact_address) {
            const contactAddress = document.getElementById('contactAddress');
            if (contactAddress) contactAddress.value = settings.contact_address.value || '';
        }
        if (settings.contact_phone) {
            const contactPhone = document.getElementById('contactPhone');
            if (contactPhone) contactPhone.value = settings.contact_phone.value || '';
        }
        if (settings.contact_email) {
            const contactEmail = document.getElementById('contactEmail');
            if (contactEmail) contactEmail.value = settings.contact_email.value || '';
        }
        if (settings.contact_facebook) {
            const contactFacebook = document.getElementById('contactFacebook');
            if (contactFacebook) contactFacebook.value = settings.contact_facebook.value || '';
        }
        if (settings.contact_hours) {
            const contactHours = document.getElementById('contactHours');
            if (contactHours) contactHours.value = settings.contact_hours.value || '';
        }
        
    } catch (error) {
        console.error('Error loading content settings:', error);
    }
}

async function saveHeaderCaption() {
    const headerCaption = document.getElementById('headerCaption');
    if (!headerCaption) return;
    
    const captionHTML = headerCaption.innerHTML;
    
    try {
        await apiCall('/content/save/', 'POST', {
            setting_type: 'header_caption',
            setting_value: captionHTML
        });
        
        showNotification('Header caption saved successfully!', 'success');
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

async function saveContactInfo() {
    const contactAddress = document.getElementById('contactAddress')?.value || '';
    const contactPhone = document.getElementById('contactPhone')?.value || '';
    const contactEmail = document.getElementById('contactEmail')?.value || '';
    const contactFacebook = document.getElementById('contactFacebook')?.value || '';
    const contactHours = document.getElementById('contactHours')?.value || '';
    
    try {
        // Save all contact fields
        await Promise.all([
            apiCall('/content/save/', 'POST', {
                setting_type: 'contact_address',
                setting_value: contactAddress
            }),
            apiCall('/content/save/', 'POST', {
                setting_type: 'contact_phone',
                setting_value: contactPhone
            }),
            apiCall('/content/save/', 'POST', {
                setting_type: 'contact_email',
                setting_value: contactEmail
            }),
            apiCall('/content/save/', 'POST', {
                setting_type: 'contact_facebook',
                setting_value: contactFacebook
            }),
            apiCall('/content/save/', 'POST', {
                setting_type: 'contact_hours',
                setting_value: contactHours
            })
        ]);
        
        showNotification('Contact information saved successfully!', 'success');
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

async function uploadContentImage(file, settingType, displayElement) {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('setting_type', settingType);
    
    try {
        const response = await fetch(`${API_BASE}/content/upload-image/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error);
        }
        
        const data = await response.json();
        showNotification('Image uploaded successfully!', 'success');
        
        // Update display element with success state
        if (displayElement) {
            displayElement.innerHTML = `<i class="fas fa-check-circle text-green-500 text-3xl mb-3"></i><p class="text-green-500">Uploaded Successfully</p>`;
        }
        
        return data;
    } catch (error) {
        showNotification(`Error uploading image: ${error.message}`, 'error');
        throw error;
    }
}