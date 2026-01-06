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

async function loadHeaderData() {
    try {
        const response = await fetch('/admin-portal/api/settings/header/');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update school year (if you add it to the template)
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
        
    } catch (error) {
        console.error('Error loading header data:', error);
        showNotification('Error loading user information', 'error');
    }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function () {

     loadHeaderData();
    // Load initial data
    loadUsersTable();
    loadHistoryTable();
    loadPositionsTable();
    loadDepartmentsTable();
    loadBuildingsTable();
    loadSchoolYearsTable();
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

    // Add Building Button
    const addBuildingBtn = document.getElementById('addBuildingBtn');
    if (addBuildingBtn) {
        addBuildingBtn.addEventListener('click', openAddBuildingModal);
    }

    // Add School Year Button
    const addSchoolYearBtn = document.getElementById('addSchoolYearBtn');
    if (addSchoolYearBtn) {
        addSchoolYearBtn.addEventListener('click', openAddSchoolYearModal);
    }

    // Add School Year Form
    const addSchoolYearForm = document.getElementById('addSchoolYearForm');
    if (addSchoolYearForm) {
        addSchoolYearForm.addEventListener('submit', handleAddSchoolYearForm);
    }

    // School Year Search
    const schoolYearSearch = document.getElementById('schoolYearSearch');
    if (schoolYearSearch) {
        schoolYearSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#schoolYearsTableBody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Add Building Form
    const addBuildingForm = document.getElementById('addBuildingForm');
    if (addBuildingForm) {
        addBuildingForm.addEventListener('submit', handleAddBuildingForm);
    }

    // Add Room Form
    const addRoomForm = document.getElementById('addRoomForm');
    if (addRoomForm) {
        addRoomForm.addEventListener('submit', handleAddRoomForm);
    }

    // Building Search
    const buildingSearch = document.getElementById('buildingSearch');
    if (buildingSearch) {
        buildingSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#buildingsTableBody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
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
    const emptyState = document.getElementById('emptyState');
    if (!tableBody) return;

    try {
        tableBody.innerHTML = '<tr><td colspan="6" class="px-6 py-8 text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';
        if (emptyState) emptyState.classList.add('hidden');
        
        const response = await apiCall('/activity-logs/');
        const logs = response.logs || [];

        if (logs.length === 0) {
            tableBody.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');

        tableBody.innerHTML = logs.map(log => `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 text-gray-700 font-medium text-sm">
                    ${log.user}
                </td>
                <td class="px-6 py-4 text-gray-700 font-medium text-sm">
                    <span class="inline-block bg-primary/10 text-primary px-3 py-1 rounded-full text-xs font-semibold">
                        ${log.action}
                    </span>
                </td>
                <td class="px-6 py-4 text-gray-600 text-sm">
                    ${log.description}
                </td>
                <td class="px-6 py-4 text-gray-600 text-sm">
                    ${log.date}
                </td>
                <td class="px-6 py-4 text-gray-600 text-sm">
                    ${log.time}
                </td>
                <td class="px-6 py-4 text-gray-600 text-sm font-mono text-xs">
                    ${log.ip_address}
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading logs:', error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="px-6 py-8 text-center text-red-500">
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
            // Get the logout URL from the sidebar link
            const logoutLink = document.querySelector('a[href*="logout"]');
            if (logoutLink) {
                window.location.href = logoutLink.href;
            } else {
                // Fallback to default logout URL
                window.location.href = '/admin-portal/logout/';
            }
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
    
    // Save Announcement Caption
    const saveAnnouncementCaptionBtn = document.getElementById('saveAnnouncementCaptionBtn');
    if (saveAnnouncementCaptionBtn) {
        saveAnnouncementCaptionBtn.addEventListener('click', saveAnnouncementCaption);
    }
    
    // Save Contact Info
    const saveContactBtn = document.getElementById('saveContactBtn');
    if (saveContactBtn) {
        saveContactBtn.addEventListener('click', saveContactInfo);
    }
    
    // Save Footer Info
    const saveFooterBtn = document.getElementById('saveFooterBtn');
    if (saveFooterBtn) {
        saveFooterBtn.addEventListener('click', saveFooterInfo);
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
        
        // Load Announcement Caption
        if (settings.announcement_caption) {
            const announcementCaption = document.getElementById('announcementCaption');
            if (announcementCaption) {
                announcementCaption.innerHTML = settings.announcement_caption.value || '';
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
        
        // Load Footer Info
        if (settings.footer_copyright) {
            const footerCopyright = document.getElementById('footerCopyright');
            if (footerCopyright) footerCopyright.value = settings.footer_copyright.value || '';
        }
        
        // Load Footer Links (stored as JSON)
        if (settings.footer_links) {
            try {
                const footerLinks = JSON.parse(settings.footer_links.value || '{}');
                if (footerLinks.link1_text) {
                    const link1Text = document.getElementById('footerLink1Text');
                    if (link1Text) link1Text.value = footerLinks.link1_text;
                }
                if (footerLinks.link1_url) {
                    const link1Url = document.getElementById('footerLink1Url');
                    if (link1Url) link1Url.value = footerLinks.link1_url;
                }
                if (footerLinks.link2_text) {
                    const link2Text = document.getElementById('footerLink2Text');
                    if (link2Text) link2Text.value = footerLinks.link2_text;
                }
                if (footerLinks.link2_url) {
                    const link2Url = document.getElementById('footerLink2Url');
                    if (link2Url) link2Url.value = footerLinks.link2_url;
                }
            } catch (e) {
                console.error('Error parsing footer links:', e);
            }
        }
        
        // Load Footer Social Media (stored as JSON)
        if (settings.footer_social) {
            try {
                const footerSocial = JSON.parse(settings.footer_social.value || '{}');
                if (footerSocial.facebook) {
                    const facebookUrl = document.getElementById('footerFacebook');
                    if (facebookUrl) facebookUrl.value = footerSocial.facebook;
                }
                if (footerSocial.twitter) {
                    const twitterUrl = document.getElementById('footerTwitter');
                    if (twitterUrl) twitterUrl.value = footerSocial.twitter;
                }
                if (footerSocial.instagram) {
                    const instagramUrl = document.getElementById('footerInstagram');
                    if (instagramUrl) instagramUrl.value = footerSocial.instagram;
                }
            } catch (e) {
                console.error('Error parsing footer social:', e);
            }
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

async function saveAnnouncementCaption() {
    const announcementCaption = document.getElementById('announcementCaption');
    if (!announcementCaption) return;
    
    const captionHTML = announcementCaption.innerHTML;
    
    try {
        await apiCall('/content/save/', 'POST', {
            setting_type: 'announcement_caption',
            setting_value: captionHTML
        });
        
        showNotification('Announcement caption saved successfully!', 'success');
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

async function saveFooterInfo() {
    const footerCopyright = document.getElementById('footerCopyright')?.value || '';
    const footerLink1Text = document.getElementById('footerLink1Text')?.value || '';
    const footerLink1Url = document.getElementById('footerLink1Url')?.value || '';
    const footerLink2Text = document.getElementById('footerLink2Text')?.value || '';
    const footerLink2Url = document.getElementById('footerLink2Url')?.value || '';
    const footerFacebook = document.getElementById('footerFacebook')?.value || '';
    const footerTwitter = document.getElementById('footerTwitter')?.value || '';
    const footerInstagram = document.getElementById('footerInstagram')?.value || '';
    
    try {
        // Save footer links as JSON
        const footerLinks = {
            link1: { text: footerLink1Text, url: footerLink1Url },
            link2: { text: footerLink2Text, url: footerLink2Url }
        };
        
        const footerSocial = {
            facebook: footerFacebook,
            twitter: footerTwitter,
            instagram: footerInstagram
        };
        
        // Save all footer fields
        await Promise.all([
            apiCall('/content/save/', 'POST', {
                setting_type: 'footer_copyright',
                setting_value: footerCopyright
            }),
            apiCall('/content/save/', 'POST', {
                setting_type: 'footer_links',
                setting_value: JSON.stringify(footerLinks)
            }),
            apiCall('/content/save/', 'POST', {
                setting_type: 'footer_social',
                setting_value: JSON.stringify(footerSocial)
            })
        ]);
        
        showNotification('Footer information saved successfully!', 'success');
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// ============== BUILDINGS & ROOMS MANAGEMENT ==============

async function loadBuildingsTable() {
    try {
        const response = await apiCall('/buildings/');
        const buildings = response.buildings || [];
        
        const tbody = document.getElementById('buildingsTableBody');
        if (!tbody) return;
        
        if (buildings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center text-gray-500 py-8">No buildings found. Add your first building!</td></tr>';
            return;
        }
        
        tbody.innerHTML = buildings.map((building, index) => `
            <tr class="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 font-semibold text-gray-600">${index + 1}</td>
                <td class="px-6 py-4 text-gray-900 font-medium">${building.name}</td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
                        <i class="fas fa-door-open mr-1"></i>
                        ${building.room_count} ${building.room_count === 1 ? 'room' : 'rooms'}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <button 
                            onclick="manageRooms(${building.id}, '${building.name.replace(/'/g, "\\'")}', event)" 
                            class="px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 text-sm font-medium transition-all duration-200 flex items-center gap-1"
                            title="Manage Rooms"
                        >
                            <i class="fas fa-door-open"></i>
                            <span>Rooms</span>
                        </button>
                        <button 
                            onclick="editBuilding(${building.id}, '${building.name.replace(/'/g, "\\'")}', event)" 
                            class="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm font-medium transition-all duration-200"
                            title="Edit Building"
                        >
                            <i class="fas fa-edit"></i>
                        </button>
                        <button 
                            onclick="deleteBuilding(${building.id}, event)" 
                            class="px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 text-sm font-medium transition-all duration-200"
                            title="Delete Building"
                        >
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading buildings:', error);
        const tbody = document.getElementById('buildingsTableBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-red-500 py-4">Error loading buildings: ${error.message}</td></tr>`;
        }
    }
}

function openAddBuildingModal() {
    const modal = document.getElementById('addBuildingModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.getElementById('addBuildingForm').reset();
    document.getElementById('buildingId').value = '';
    document.getElementById('buildingModalTitle').innerHTML = '<i class="fas fa-building"></i> Add New Building';
    document.getElementById('buildingSubmitText').textContent = 'Add Building';
}

function closeBuildingModal() {
    const modal = document.getElementById('addBuildingModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    document.getElementById('addBuildingForm').reset();
}

async function handleAddBuildingForm(event) {
    event.preventDefault();
    
    const buildingId = document.getElementById('buildingId').value;
    const name = document.getElementById('building_name').value.trim();
    
    if (!name) {
        showNotification('Building name is required', 'error');
        return;
    }
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
    
    try {
        if (buildingId) {
            // Update existing building
            await apiCall(`/buildings/${buildingId}/update/`, 'PUT', { name });
            showNotification('Building updated successfully!', 'success');
        } else {
            // Add new building
            await apiCall('/buildings/add/', 'POST', { name });
            showNotification('Building added successfully!', 'success');
        }
        
        loadBuildingsTable();
        closeBuildingModal();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

function editBuilding(id, name, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    document.getElementById('buildingId').value = id;
    document.getElementById('building_name').value = name;
    document.getElementById('buildingModalTitle').innerHTML = '<i class="fas fa-edit"></i> Edit Building';
    document.getElementById('buildingSubmitText').textContent = 'Update Building';
    
    const modal = document.getElementById('addBuildingModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

async function deleteBuilding(id, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (!confirm('Are you sure you want to delete this building? All rooms in this building will also be deleted.')) {
        return;
    }
    
    try {
        await apiCall(`/buildings/${id}/delete/`, 'DELETE');
        showNotification('Building deleted successfully!', 'success');
        loadBuildingsTable();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// ============== ROOMS MANAGEMENT ==============

async function manageRooms(buildingId, buildingName, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    console.log('manageRooms called with:', { buildingId, buildingName });
    
    document.getElementById('currentBuildingId').value = buildingId;
    document.getElementById('currentBuildingName').textContent = buildingName;
    
    const modal = document.getElementById('manageRoomsModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    await loadRoomsTable(buildingId);
}

function closeManageRoomsModal() {
    const modal = document.getElementById('manageRoomsModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    document.getElementById('addRoomForm').reset();
    
    // Refresh buildings table to update room counts
    loadBuildingsTable();
}

async function loadRoomsTable(buildingId) {
    try {
        if (!buildingId) {
            throw new Error('Building ID is required');
        }
        
        const response = await apiCall(`/rooms/?building=${buildingId}`);
        const rooms = response.rooms || [];
        
        const tbody = document.getElementById('roomsTableBody');
        if (!tbody) return;
        
        if (rooms.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-gray-500 py-8">No rooms in this building. Add your first room above!</td></tr>';
            return;
        }
        
        tbody.innerHTML = rooms.map((room, index) => `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-3 font-semibold text-gray-600">${index + 1}</td>
                <td class="px-6 py-3 text-gray-900 font-medium">${room.room_number}</td>
                <td class="px-6 py-3">
                    <div class="flex gap-2">
                        <button 
                            onclick="editRoom(${room.id}, '${room.room_number.replace(/'/g, "\\'")}', event)" 
                            class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm transition-all duration-200"
                        >
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button 
                            onclick="deleteRoom(${room.id}, event)" 
                            class="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm transition-all duration-200"
                        >
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading rooms:', error);
        const tbody = document.getElementById('roomsTableBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="3" class="text-center text-red-500 py-4">Error loading rooms: ${error.message}</td></tr>`;
        }
    }
}

async function handleAddRoomForm(event) {
    event.preventDefault();
    
    const buildingId = document.getElementById('currentBuildingId').value;
    const roomNumber = document.getElementById('room_number').value.trim();
    
    if (!roomNumber) {
        showNotification('Room number is required', 'error');
        return;
    }
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Adding...';
    
    try {
        await apiCall('/rooms/add/', 'POST', {
            building_id: buildingId,
            room_number: roomNumber
        });
        
        showNotification('Room added successfully!', 'success');
        document.getElementById('addRoomForm').reset();
        await loadRoomsTable(buildingId);
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

async function editRoom(roomId, roomNumber, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    const newRoomNumber = prompt('Enter new room number:', roomNumber);
    if (!newRoomNumber || newRoomNumber === roomNumber) {
        return;
    }
    
    try {
        await apiCall(`/rooms/${roomId}/update/`, 'PUT', {
            room_number: newRoomNumber.trim()
        });
        
        showNotification('Room updated successfully!', 'success');
        const buildingId = document.getElementById('currentBuildingId').value;
        await loadRoomsTable(buildingId);
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

async function deleteRoom(roomId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    
    if (!confirm('Are you sure you want to delete this room?')) {
        return;
    }
    
    try {
        await apiCall(`/rooms/${roomId}/delete/`, 'DELETE');
        showNotification('Room deleted successfully!', 'success');
        const buildingId = document.getElementById('currentBuildingId').value;
        await loadRoomsTable(buildingId);
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// ============== SCHOOL YEAR MANAGEMENT ==============

async function loadSchoolYearsTable() {
    try {
        const response = await apiCall('/school-years/', 'GET');
        const schoolYears = response.school_years || [];
        
        const tbody = document.getElementById('schoolYearsTableBody');
        if (!tbody) return;
        
        // Update active school year display
        const activeYear = response.active_year || schoolYears.find(sy => sy.is_active);
        const activeYearDisplay = document.getElementById('activeSchoolYearDisplay');
        const activeYearDates = document.getElementById('activeSchoolYearDates');
        const enrollmentStatus = document.getElementById('enrollmentStatusDisplay');

        if (activeYear && activeYearDisplay && activeYearDates && enrollmentStatus) {
            activeYearDisplay.textContent = activeYear.year_label;
            activeYearDates.textContent = `${formatDate(activeYear.start_date)} - ${formatDate(activeYear.end_date)}`;
            enrollmentStatus.innerHTML = activeYear.enrollment_open 
                ? '<i class="fas fa-door-open mr-1"></i>Enrollment Open' 
                : '<i class="fas fa-door-closed mr-1"></i>Enrollment Closed';
        } else if (activeYearDisplay && activeYearDates && enrollmentStatus) {
            activeYearDisplay.textContent = 'No active school year';
            activeYearDates.textContent = '';
            enrollmentStatus.textContent = 'Enrollment status unavailable';
        }
        
        if (schoolYears.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-8">No school years found. Add your first school year!</td></tr>';
            return;
        }
        
        tbody.innerHTML = schoolYears.map(sy => `
            <tr class="border-b border-gray-200 hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4">
                    <div class="font-bold text-gray-900 text-lg">${sy.year_label}</div>
                    <div class="text-xs text-gray-500">Created: ${formatDate(sy.created_at)}</div>
                </td>
                <td class="px-6 py-4 text-gray-600">${formatDate(sy.start_date)}</td>
                <td class="px-6 py-4 text-gray-600">${formatDate(sy.end_date)}</td>
                <td class="px-6 py-4">
                    ${sy.is_active 
                        ? '<span class="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold"><i class="fas fa-check-circle mr-1"></i>Active</span>'
                        : '<span class="inline-flex items-center px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm font-semibold"><i class="fas fa-circle mr-1"></i>Inactive</span>'
                    }
                </td>
                <td class="px-6 py-4">
                    ${sy.enrollment_open 
                        ? '<span class="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold"><i class="fas fa-door-open mr-1"></i>Open</span>'
                        : '<span class="inline-flex items-center px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm font-semibold"><i class="fas fa-door-closed mr-1"></i>Closed</span>'
                    }
                </td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <button 
                            onclick="editSchoolYear(${sy.id}, '${sy.year_label}', '${sy.start_date}', '${sy.end_date}', ${sy.is_active}, ${sy.enrollment_open})" 
                            class="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-sm font-medium transition-all duration-200"
                            title="Edit School Year"
                        >
                            <i class="fas fa-edit"></i>
                        </button>
                        ${!sy.is_active ? `
                        <button 
                            onclick="deleteSchoolYear(${sy.id})" 
                            class="px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 text-sm font-medium transition-all duration-200"
                            title="Delete School Year"
                        >
                            <i class="fas fa-trash"></i>
                        </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error loading school years:', error);
        const tbody = document.getElementById('schoolYearsTableBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-red-500 py-4">Error loading school years: ${error.message}</td></tr>`;
        }
    }
}

function openAddSchoolYearModal() {
    const modal = document.getElementById('addSchoolYearModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.getElementById('addSchoolYearForm').reset();
    document.getElementById('schoolYearId').value = '';
    document.getElementById('schoolYearModalTitle').innerHTML = '<i class="fas fa-calendar-alt"></i> Add New School Year';
    document.getElementById('schoolYearSubmitText').textContent = 'Add School Year';
}

function closeSchoolYearModal() {
    const modal = document.getElementById('addSchoolYearModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    document.getElementById('addSchoolYearForm').reset();
}

async function handleAddSchoolYearForm(event) {
    event.preventDefault();
    
    const schoolYearId = document.getElementById('schoolYearId').value;
    const yearLabel = document.getElementById('school_year_label').value.trim();
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    const isActive = document.getElementById('is_active').checked;
    const enrollmentOpen = document.getElementById('enrollment_open').checked;
    
    // Validation
    if (!yearLabel || !startDate || !endDate) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }
    
    if (new Date(startDate) >= new Date(endDate)) {
        showNotification('End date must be after start date', 'error');
        return;
    }
    
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
    
    try {
        const data = {
            year_label: yearLabel,
            start_date: startDate,
            end_date: endDate,
            is_active: isActive,
            enrollment_open: enrollmentOpen
        };

        const endpoint = schoolYearId ? `/school-years/${schoolYearId}/update/` : '/school-years/add/';
        const method = schoolYearId ? 'PUT' : 'POST';
        const response = await apiCall(endpoint, method, data);

        showNotification(response.message || 'School year saved successfully!', 'success');
        await loadSchoolYearsTable();
        closeSchoolYearModal();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

function editSchoolYear(id, yearLabel, startDate, endDate, isActive, enrollmentOpen) {
    document.getElementById('schoolYearId').value = id;
    document.getElementById('school_year_label').value = yearLabel;
    document.getElementById('start_date').value = startDate;
    document.getElementById('end_date').value = endDate;
    document.getElementById('is_active').checked = isActive;
    document.getElementById('enrollment_open').checked = enrollmentOpen;
    document.getElementById('schoolYearModalTitle').innerHTML = '<i class="fas fa-edit"></i> Edit School Year';
    document.getElementById('schoolYearSubmitText').textContent = 'Update School Year';
    
    const modal = document.getElementById('addSchoolYearModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

async function deleteSchoolYear(id) {
    if (!confirm('Are you sure you want to delete this school year? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await apiCall(`/school-years/${id}/delete/`, 'DELETE');
        showNotification(response.message || 'School year deleted successfully!', 'success');
        await loadSchoolYearsTable();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}



// ============== MAKE FUNCTIONS GLOBALLY AVAILABLE ==============

window.loadBuildingsTable = loadBuildingsTable;
window.openAddBuildingModal = openAddBuildingModal;
window.closeBuildingModal = closeBuildingModal;
window.editBuilding = editBuilding;
window.deleteBuilding = deleteBuilding;
window.manageRooms = manageRooms;
window.closeManageRoomsModal = closeManageRoomsModal;
window.editRoom = editRoom;
window.deleteRoom = deleteRoom;
window.loadSchoolYearsTable = loadSchoolYearsTable;
window.openAddSchoolYearModal = openAddSchoolYearModal;
window.closeSchoolYearModal = closeSchoolYearModal;
window.editSchoolYear = editSchoolYear;
window.deleteSchoolYear = deleteSchoolYear;
