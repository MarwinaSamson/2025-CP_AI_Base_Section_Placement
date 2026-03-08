// API Configuration - FIXED: Match your Django URL structure
const API_BASE = '/admin-portal/api';  // Changed to match your URL pattern

// Global state variables
let allTeachers = [];

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
    loadTeachersTable();
    loadPositionsTable();
    loadDepartmentsTable();
    loadBuildingsTable();
    loadSchoolYearsTable();
    loadRequirementsSchoolYearDropdown();
    loadDocumentRequirementsTable();
    loadGradeLevelsTable();
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

    // Add Teacher Button
    const addTeacherBtn = document.getElementById('addTeacherBtn');
    if (addTeacherBtn) {
        addTeacherBtn.addEventListener('click', openAddTeacherModal);
    }

    // Add Teacher Form
    const addTeacherForm = document.getElementById('addTeacherForm');
    if (addTeacherForm) {
        addTeacherForm.addEventListener('submit', handleAddTeacherForm);
    }

    // Teacher Search
    const teacherSearch = document.getElementById('teacherSearch');
    if (teacherSearch) {
        teacherSearch.addEventListener('input', function() {
            filterTeachers(this.value);
        });
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

    // Add Grade Level Button
    const addGradeLevelBtn = document.getElementById('addGradeLevelBtn');
    if (addGradeLevelBtn) {
        addGradeLevelBtn.addEventListener('click', openAddGradeLevelModal);
    }

    // Grade Level Form
    const gradeLevelForm = document.getElementById('gradeLevelForm');
    if (gradeLevelForm) {
        gradeLevelForm.addEventListener('submit', handleGradeLevelForm);
    }

    // Grade Level Search
    const gradeLevelSearch = document.getElementById('gradeLevelSearch');
    if (gradeLevelSearch) {
        gradeLevelSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#gradeLevelsTableBody tr');
            rows.forEach(row => {
                row.style.display = row.textContent.toLowerCase().includes(searchTerm) ? '' : 'none';
            });
        });
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

    // Document Requirements: Add Button
    const addDocumentRequirementBtn = document.getElementById('addDocumentRequirementBtn');
    if (addDocumentRequirementBtn) {
        addDocumentRequirementBtn.addEventListener('click', openAddDocumentRequirementModal);
    }

    // Document Requirements: Form Submit
    const addDocumentRequirementForm = document.getElementById('addDocumentRequirementForm');
    if (addDocumentRequirementForm) {
        addDocumentRequirementForm.addEventListener('submit', handleAddDocumentRequirementForm);
    }

    // Document Requirements: Search
    const documentRequirementSearch = document.getElementById('documentRequirementSearch');
    if (documentRequirementSearch) {
        documentRequirementSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#documentRequirementsTableBody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }

    // Document Requirements: School Year filter
    const requirementsSchoolYearSelect = document.getElementById('requirementsSchoolYearSelect');
    if (requirementsSchoolYearSelect) {
        requirementsSchoolYearSelect.addEventListener('change', () => {
            loadDocumentRequirementsTable();
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

// async function viewUserProfile(userId) {
//     try {
//         const response = await apiCall(`/users/${userId}/`, 'GET');
//         const user = response.user;
//         // Show user info in a modal (replace with your modal logic)
//         let info = `User: ${user.full_name || user.username}<br>Email: ${user.email}<br>Position: ${user.position || ''}<br>Department: ${user.department || ''}<br>User Type: ${user.user_type || ''}`;
//         showNotification(info, 'info');
//         // TODO: Replace showNotification with your actual modal display logic
//     } catch (error) {
//         showNotification(`Error: ${error.message}`, 'error');
//     }
// }

async function viewUserProfile(userId) {
    try {
        // Show modal immediately with loading state
        const modal = document.getElementById('viewUserModal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');

        // Reset fields to loading placeholders
        document.getElementById('viewUserFullName').textContent = 'Loading...';
        document.getElementById('viewUserUsername').textContent = '';
        document.getElementById('viewUserInitials').textContent = '…';
        document.getElementById('viewUserEmployeeId').textContent = '—';
        document.getElementById('viewUserEmail').textContent = '—';
        document.getElementById('viewUserPosition').textContent = '—';
        document.getElementById('viewUserDepartment').textContent = '—';
        document.getElementById('viewUserDateJoined').textContent = '—';
        document.getElementById('viewUserTypeBadge').textContent = '';
        document.getElementById('viewUserStatus').textContent = '';

        const response = await apiCall(`/users/${userId}/`, 'GET');
        const user = response.user;

        // Full name & initials
        const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.username;
        const initials = (user.first_name?.[0] || '') + (user.last_name?.[0] || '') || user.username?.[0]?.toUpperCase() || 'U';

        document.getElementById('viewUserFullName').textContent = fullName;
        document.getElementById('viewUserUsername').textContent = `@${user.username}`;
        document.getElementById('viewUserInitials').textContent = initials.toUpperCase();

        // Employee ID, email, position, department
        document.getElementById('viewUserEmployeeId').textContent = user.employee_id || 'N/A';
        document.getElementById('viewUserEmail').textContent = user.email || 'N/A';
        document.getElementById('viewUserPosition').textContent = user.position || 'Not assigned';
        document.getElementById('viewUserDepartment').textContent = user.department || 'Not assigned';
        document.getElementById('viewUserDateJoined').textContent = user.date_joined || 'N/A';

        // User type badge
        const badge = document.getElementById('viewUserTypeBadge');
        const isAdmin = user.user_type === 'admin';
        badge.textContent = isAdmin ? 'Admin' : 'Coordinator';
        badge.className = `inline-block mt-1 px-3 py-0.5 text-xs font-semibold rounded-full ${
            isAdmin ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
        }`;

        // Account status
        const statusEl = document.getElementById('viewUserStatus');
        if (user.is_active) {
            statusEl.innerHTML = '<span class="inline-flex items-center gap-1.5"><i class="fas fa-circle text-green-500 text-xs"></i> Active</span>';
        } else {
            statusEl.innerHTML = '<span class="inline-flex items-center gap-1.5"><i class="fas fa-circle text-gray-400 text-xs"></i> Inactive</span>';
        }

        // Wire the "Edit User" button in the view modal
        const editBtn = document.getElementById('viewModalEditBtn');
        editBtn.onclick = () => {
            closeViewUserModal();
            editUser(userId);
        };

    } catch (error) {
        closeViewUserModal();
        showNotification(`Error loading user: ${error.message}`, 'error');
    }
}

function closeViewUserModal() {
    const modal = document.getElementById('viewUserModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
}


// async function editUser(userId) {
//     try {
//         const response = await apiCall(`/users/${userId}/`, 'GET');
//         const user = response.user;
//         // Populate your edit modal form fields with user data (replace with your modal logic)
        // Example:
        // document.getElementById('editUserName').value = user.username;
        // document.getElementById('editUserEmail').value = user.email;
        // ...
        // Show the edit modal
        // document.getElementById('editUserModal').style.display = 'block';
        showNotification('Edit modal would open here (implement modal UI)', 'info');
        // On form submit, call update API:
        // await apiCall(`/users/${userId}/update/`, 'PUT', updatedData);
        // showNotification('User updated successfully!', 'success');
        // loadUsersTable();
//     } catch (error) {
//         showNotification(`Error: ${error.message}`, 'error');
//     }
// }

async function editUser(userId) {
    try {
        // Open modal immediately with loading state
        const modal = document.getElementById('editUserModal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');

        const submitBtn = document.getElementById('editUserSubmitBtn');
        submitBtn.disabled = true;
        document.getElementById('editUserSubmitText').textContent = 'Loading...';

        // Load dropdowns in parallel with user data
        const [userResponse] = await Promise.all([
            apiCall(`/users/${userId}/`, 'GET'),
            loadEditPositionsDropdown(),
            loadEditDepartmentsDropdown(),
            loadEditProgramsDropdown(),
        ]);

        const user = userResponse.user;

        // Populate hidden ID
        document.getElementById('editUserId').value = userId;

        // Basic fields
        document.getElementById('edit_first_name').value = user.first_name || '';
        document.getElementById('edit_last_name').value = user.last_name || '';
        document.getElementById('edit_username').value = user.username || '';
        document.getElementById('edit_email').value = user.email || '';
        document.getElementById('edit_employee_id').value = user.employee_id || '';

        // Position & Department — select by ID (returned from updated backend)
        const positionSelect = document.getElementById('edit_position');
        const departmentSelect = document.getElementById('edit_department');

        if (user.position_id) {
            positionSelect.value = user.position_id;
        } else {
            positionSelect.value = '';
        }

        if (user.department_id) {
            departmentSelect.value = user.department_id;
        } else {
            departmentSelect.value = '';
        }

        // Access checkboxes
        const isAdmin = user.user_type === 'admin';
        const isCoordinator = user.user_type === 'coordinator';
        document.getElementById('edit_admin_access').checked = isAdmin;
        document.getElementById('edit_coordinator_access').checked = isCoordinator;

        // Program field visibility
        const programField = document.getElementById('editProgramField');
        const programSelect = document.getElementById('edit_program');
        if (isCoordinator && !isAdmin) {
            programField.classList.remove('hidden');
            if (user.program_id) {
                programSelect.value = user.program_id;
            }
        } else {
            programField.classList.add('hidden');
        }

        // Wire access checkbox listeners for the edit modal
        setupEditUserTypeListeners();

        submitBtn.disabled = false;
        document.getElementById('editUserSubmitText').textContent = 'Save Changes';

    } catch (error) {
        closeEditUserModal();
        showNotification(`Error loading user for edit: ${error.message}`, 'error');
    }
}

function closeEditUserModal() {
    const modal = document.getElementById('editUserModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    document.getElementById('editUserForm').reset();
    document.getElementById('editProgramField').classList.add('hidden');
}

async function submitEditUserForm() {
    const userId = document.getElementById('editUserId').value;
    if (!userId) return;

    const firstName = document.getElementById('edit_first_name').value.trim();
    const lastName = document.getElementById('edit_last_name').value.trim();
    const email = document.getElementById('edit_email').value.trim();
    const employeeId = document.getElementById('edit_employee_id').value.trim();
    const positionId = document.getElementById('edit_position').value || null;
    const departmentId = document.getElementById('edit_department').value || null;
    const isAdmin = document.getElementById('edit_admin_access').checked;
    const isCoordinator = document.getElementById('edit_coordinator_access').checked;
    const programId = document.getElementById('edit_program').value || null;

    // Validation
    if (!firstName || !lastName || !email || !employeeId) {
        showNotification('First name, last name, email, and employee ID are required.', 'error');
        return;
    }
    if (!isAdmin && !isCoordinator) {
        showNotification('Please select at least one access level.', 'error');
        return;
    }
    if (isCoordinator && !isAdmin && !programId) {
        showNotification('Program is required for coordinators.', 'error');
        return;
    }

    const userType = isAdmin ? 'admin' : 'coordinator';

    // Loading state
    const submitBtn = document.getElementById('editUserSubmitBtn');
    const submitText = document.getElementById('editUserSubmitText');
    const originalText = submitText.textContent;
    submitBtn.disabled = true;
    submitText.textContent = 'Saving...';
    submitBtn.querySelector('i').className = 'fas fa-spinner fa-spin';

    try {
        await apiCall(`/users/${userId}/update/`, 'PUT', {
            first_name: firstName,
            last_name: lastName,
            email: email,
            employee_id: employeeId,
            position_id: positionId ? parseInt(positionId) : null,
            department_id: departmentId ? parseInt(departmentId) : null,
            user_type: userType,
            program_id: programId ? parseInt(programId) : null,
        });

        showNotification(`${firstName} ${lastName}'s details updated successfully!`, 'success');
        closeEditUserModal();
        loadUsersTable(); // Refresh the table
        loadHistoryTable();
    } catch (error) {
        showNotification(`Error updating user: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitText.textContent = originalText;
        submitBtn.querySelector('i').className = 'fas fa-save';
    }
}

// ---- DROPDOWN LOADERS FOR EDIT MODAL ----

async function loadEditPositionsDropdown() {
    const select = document.getElementById('edit_position');
    if (!select) return;
    try {
        const response = await apiCall('/positions/');
        const positions = response.positions || [];
        select.innerHTML = '<option value="">Select Position</option>' +
            positions.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    } catch (e) {
        console.error('Error loading positions for edit modal:', e);
    }
}

async function loadEditDepartmentsDropdown() {
    const select = document.getElementById('edit_department');
    if (!select) return;
    try {
        const response = await apiCall('/departments/');
        const departments = response.departments || [];
        select.innerHTML = '<option value="">Select Department</option>' +
            departments.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
    } catch (e) {
        console.error('Error loading departments for edit modal:', e);
    }
}

async function loadEditProgramsDropdown() {
    const select = document.getElementById('edit_program');
    if (!select) return;
    try {
        const response = await apiCall('/programs/');
        const programs = response.programs || [];
        select.innerHTML = '<option value="">Select Program</option>' +
            programs.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    } catch (e) {
        console.error('Error loading programs for edit modal:', e);
    }
}

// ---- ACCESS LEVEL TOGGLE FOR EDIT MODAL ----

function setupEditUserTypeListeners() {
    const adminCb = document.getElementById('edit_admin_access');
    const coordinatorCb = document.getElementById('edit_coordinator_access');
    const programField = document.getElementById('editProgramField');
    const programSelect = document.getElementById('edit_program');

    const updateEditProgramField = () => {
        const isCoordOnly = coordinatorCb.checked && !adminCb.checked;
        if (isCoordOnly) {
            programField.classList.remove('hidden');
            programSelect.required = true;
        } else {
            programField.classList.add('hidden');
            programSelect.required = false;
            programSelect.value = '';
        }
    };

    // Remove old listeners (clone trick)
    const newAdmin = adminCb.cloneNode(true);
    const newCoord = coordinatorCb.cloneNode(true);
    adminCb.parentNode.replaceChild(newAdmin, adminCb);
    coordinatorCb.parentNode.replaceChild(newCoord, coordinatorCb);

    newAdmin.addEventListener('change', updateEditProgramField);
    newCoord.addEventListener('change', updateEditProgramField);
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


// ============== TEACHER MANAGEMENT FUNCTIONS ==============

async function loadTeachersTable() {
    try {
        const response = await apiCall('/settings/teachers/');
        const teachers = response.data || [];
        allTeachers = teachers;
        
        const tbody = document.getElementById('teachersTableBody');
        if (!tbody) return;
        
        renderTeachersTable(teachers);
    } catch (error) {
        console.error('Error loading teachers:', error);
        const tbody = document.getElementById('teachersTableBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-red-500 py-4">Error loading teachers: ${error.message}</td></tr>`;
        }
    }
}

function renderTeachersTable(teachers) {
    const tbody = document.getElementById('teachersTableBody');
    if (!tbody) return;
    
    if (teachers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-4">No teachers found</td></tr>';
        return;
    }
    
    tbody.innerHTML = teachers.map(teacher => `
        <tr class="border-b border-gray-200 hover:bg-gray-50">
            <td class="px-6 py-4 text-gray-900 font-medium">${teacher.full_name}</td>
            <td class="px-6 py-4 text-gray-600">${teacher.email}</td>
            <td class="px-6 py-4 text-gray-600">${teacher.position_name || '-'}</td>
            <td class="px-6 py-4 text-gray-600">${teacher.department_name || '-'}</td>
            <td class="px-6 py-4">
                ${teacher.is_adviser 
                    ? '<span class="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">Adviser</span>' 
                    : '<span class="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs font-medium">Available</span>'}
            </td>
            <td class="px-6 py-4">
                <div class="flex gap-2">
                    <button onclick="editTeacher(${teacher.id})" 
                            class="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm">
                        <i class="fas fa-edit mr-1"></i>Edit
                    </button>
                    <button onclick="deleteTeacher(${teacher.id})" 
                            class="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-sm"
                            ${teacher.is_adviser ? 'disabled title="Cannot delete adviser"' : ''}>
                        <i class="fas fa-trash mr-1"></i>Delete
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function filterTeachers(searchTerm) {
    const filtered = allTeachers.filter(teacher => {
        const term = searchTerm.toLowerCase();
        return teacher.full_name.toLowerCase().includes(term) ||
               teacher.email.toLowerCase().includes(term) ||
               (teacher.position_name || '').toLowerCase().includes(term) ||
               (teacher.department_name || '').toLowerCase().includes(term);
    });
    renderTeachersTable(filtered);
}

async function loadTeacherDropdowns() {
    try {
        // Load positions
        const positionsResponse = await apiCall('/positions/');
        const positions = positionsResponse.positions || positionsResponse.data || [];
        const positionSelect = document.getElementById('teacher_position');
        if (positionSelect) {
            positionSelect.innerHTML = '<option value="">Select Position</option>' +
                positions.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
        }
        
        // Load departments
        const departmentsResponse = await apiCall('/departments/');
        const departments = departmentsResponse.departments || departmentsResponse.data || [];
        const departmentSelect = document.getElementById('teacher_department');
        if (departmentSelect) {
            departmentSelect.innerHTML = '<option value="">Select Department</option>' +
                departments.map(d => `<option value="${d.id}">${d.name}</option>`).join('');
        }
    } catch (error) {
        console.error('Error loading dropdowns:', error);
    }
}

async function openAddTeacherModal() {
    await loadTeacherDropdowns();
    
    const modal = document.getElementById('addTeacherModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.getElementById('addTeacherForm').reset();
    document.getElementById('teacherId').value = '';
    document.getElementById('teacherModalTitle').textContent = 'Add New Teacher';
    document.getElementById('teacherSubmitText').textContent = 'Add Teacher';
}

function closeTeacherModal() {
    const modal = document.getElementById('addTeacherModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
}

async function handleAddTeacherForm(event) {
    event.preventDefault();
    
    const teacherId = document.getElementById('teacherId').value;
    const data = {
        first_name: document.getElementById('teacher_first_name').value,
        middle_name: document.getElementById('teacher_middle_name').value,
        last_name: document.getElementById('teacher_last_name').value,
        email: document.getElementById('teacher_email').value,
        position_id: document.getElementById('teacher_position').value || null,
        department_id: document.getElementById('teacher_department').value || null,
        address: document.getElementById('teacher_address').value
    };
    
    try {
        if (teacherId) {
            // Update existing teacher
            await apiCall(`/settings/teachers/${teacherId}/update/`, 'PUT', data);
            showNotification('Teacher updated successfully!', 'success');
        } else {
            // Add new teacher
            await apiCall('/settings/teachers/add/', 'POST', data);
            showNotification('Teacher added successfully!', 'success');
        }
        
        loadTeachersTable();
        closeTeacherModal();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

async function editTeacher(id) {
    const teacher = allTeachers.find(t => t.id === id);
    if (!teacher) {
        showNotification('Teacher not found', 'error');
        return;
    }
    
    await loadTeacherDropdowns();
    
    document.getElementById('teacherId').value = teacher.id;
    document.getElementById('teacher_first_name').value = teacher.first_name;
    document.getElementById('teacher_middle_name').value = teacher.middle_name || '';
    document.getElementById('teacher_last_name').value = teacher.last_name;
    document.getElementById('teacher_email').value = teacher.email;
    document.getElementById('teacher_position').value = teacher.position_id || '';
    document.getElementById('teacher_department').value = teacher.department_id || '';
    document.getElementById('teacher_address').value = teacher.address || '';
    
    document.getElementById('teacherModalTitle').textContent = 'Edit Teacher';
    document.getElementById('teacherSubmitText').textContent = 'Update Teacher';
    
    const modal = document.getElementById('addTeacherModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

async function deleteTeacher(id) {
    const teacher = allTeachers.find(t => t.id === id);
    if (!teacher) return;
    
    if (teacher.is_adviser) {
        showNotification('Cannot delete a teacher who is assigned as a section adviser', 'error');
        return;
    }
    
    if (!confirm(`Are you sure you want to delete ${teacher.full_name}?`)) {
        return;
    }
    
    try {
        await apiCall(`/settings/teachers/${id}/delete/`, 'DELETE');
        showNotification('Teacher deleted successfully!', 'success');
        loadTeachersTable();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// Expose teacher functions globally
window.loadTeachersTable = loadTeachersTable;
window.openAddTeacherModal = openAddTeacherModal;
window.closeTeacherModal = closeTeacherModal;
window.editTeacher = editTeacher;
window.deleteTeacher = deleteTeacher;


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

// ============== DOCUMENT REQUIREMENTS FUNCTIONS ==============

async function loadRequirementsSchoolYearDropdown() {
    const select = document.getElementById('requirementsSchoolYearSelect');
    if (!select) return;
    try {
        const res = await apiCall('/school-years/');
        const years = res.school_years || [];
        const active = res.active_year || null;
        select.innerHTML = '<option value="">All School Years</option>' + years.map(y => `<option value="${y.id}" ${active && active.id === y.id ? 'selected' : ''}>${y.year_label}</option>`).join('');
    } catch (err) {
        console.error('Error loading school years for requirements:', err);
    }
}

async function loadDocumentRequirementsTable() {
    const tbody = document.getElementById('documentRequirementsTableBody');
    if (!tbody) return;
    try {
        tbody.innerHTML = '<tr><td colspan="7" class="px-6 py-8 text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';
        const select = document.getElementById('requirementsSchoolYearSelect');
        const schoolYearId = select && select.value ? select.value : '';
        const query = schoolYearId ? `?school_year_id=${encodeURIComponent(schoolYearId)}` : '';
        const res = await apiCall(`/document-requirements/${query}`);
        const requirements = res.requirements || [];

        if (requirements.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-6 py-8 text-center text-gray-500">
                        <i class="fas fa-file-alt text-4xl mb-3"></i>
                        <p>No requirements found. Add your first requirement!</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = requirements.map(r => `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 text-gray-800 font-medium">${r.name}</td>
                <td class="px-6 py-4"><span class="inline-block bg-primary/10 text-primary px-3 py-1 rounded-full text-xs font-semibold">${r.requirement_type}</span></td>
                <td class="px-6 py-4 text-gray-600 text-sm">${r.allowed_extensions.join(', ')}</td>
                <td class="px-6 py-4 text-gray-600 text-sm">${r.max_file_size_mb.toFixed ? r.max_file_size_mb.toFixed(2) : r.max_file_size_mb}</td>
                <td class="px-6 py-4">${r.is_active ? '<span class="inline-block px-3 py-1 bg-green-600 text-white rounded-full text-xs font-semibold">Active</span>' : '<span class="inline-block px-3 py-1 bg-gray-400 text-white rounded-full text-xs font-semibold">Inactive</span>'}</td>
                <td class="px-6 py-4 text-gray-600 text-sm">${r.order}</td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <button class="px-3 py-1 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50" onclick="openEditDocumentRequirement(${r.id}); return false;"><i class="fas fa-edit"></i></button>
                        <button class="px-3 py-1 border border-gray-300 rounded-lg text-red-600 hover:bg-red-50" onclick="deleteDocumentRequirement(${r.id}); return false;"><i class="fas fa-trash"></i></button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error loading document requirements:', err);
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-8 text-center text-red-500">
                    <i class="fas fa-exclamation-triangle mb-2"></i><br>
                    Error loading requirements: ${err.message}
                </td>
            </tr>
        `;
        showNotification('Error loading requirements', 'error');
    }
}

function openAddDocumentRequirementModal() {
    const modal = document.getElementById('addDocumentRequirementModal');
    if (!modal) return;
    document.getElementById('documentRequirementModalTitle').textContent = 'Add Document Requirement';
    document.getElementById('documentRequirementSubmitText').textContent = 'Add Requirement';
    document.getElementById('documentRequirementId').value = '';
    // Reset form
    const form = document.getElementById('addDocumentRequirementForm');
    if (form) form.reset();
    // Populate school years
    populateRequirementSchoolYearsInModal();
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeDocumentRequirementModal() {
    const modal = document.getElementById('addDocumentRequirementModal');
    if (!modal) return;
    modal.classList.remove('flex');
    modal.classList.add('hidden');
}

async function populateRequirementSchoolYearsInModal() {
    const select = document.getElementById('document_school_year');
    if (!select) return;
    try {
        const res = await apiCall('/school-years/');
        const years = res.school_years || [];
        const active = res.active_year || null;
        select.innerHTML = years.map(y => `<option value="${y.id}" ${active && active.id === y.id ? 'selected' : ''}>${y.year_label}</option>`).join('');
    } catch (err) {
        console.error('Error loading school years:', err);
    }
}

async function handleAddDocumentRequirementForm(event) {
    event.preventDefault();
    const form = event.target;
    const id = document.getElementById('documentRequirementId').value;
    const payload = {
        school_year_id: document.getElementById('document_school_year').value,
        name: document.getElementById('document_name').value.trim(),
        requirement_type: document.getElementById('document_type').value,
        order: parseInt(document.getElementById('document_order').value || '0', 10),
        file_format: document.getElementById('document_formats').value.trim() || 'pdf,jpg,jpeg,png',
        max_file_size_mb: parseFloat(document.getElementById('document_max_size').value || '5'),
        is_active: document.getElementById('document_is_active').checked,
        description: document.getElementById('document_description').value || '',
    };

    if (!payload.school_year_id || !payload.name) {
        showNotification('School year and requirement name are required', 'error');
        return;
    }

    // Show loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Saving...';

    try {
        if (id) {
            await apiCall(`/document-requirements/${id}/update/`, 'PUT', payload);
            showNotification('Requirement updated successfully', 'success');
        } else {
            await apiCall('/document-requirements/add/', 'POST', payload);
            showNotification('Requirement added successfully', 'success');
        }
        await loadDocumentRequirementsTable();
        closeDocumentRequirementModal();
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    }
}

async function openEditDocumentRequirement(requirementId) {
    try {
        // Fetch single requirement by listing and finding (no single endpoint)
        const res = await apiCall('/document-requirements/');
        const req = (res.requirements || []).find(r => r.id === requirementId);
        if (!req) {
            showNotification('Requirement not found', 'error');
            return;
        }
        const modal = document.getElementById('addDocumentRequirementModal');
        document.getElementById('documentRequirementModalTitle').textContent = 'Edit Document Requirement';
        document.getElementById('documentRequirementSubmitText').textContent = 'Save Changes';
        document.getElementById('documentRequirementId').value = req.id;

        await populateRequirementSchoolYearsInModal();
        document.getElementById('document_school_year').value = req.school_year_id;
        document.getElementById('document_name').value = req.name;
        document.getElementById('document_type').value = req.requirement_type;
        document.getElementById('document_order').value = req.order;
        document.getElementById('document_formats').value = req.file_format;
        document.getElementById('document_max_size').value = req.max_file_size_mb;
        document.getElementById('document_is_active').checked = !!req.is_active;
        document.getElementById('document_description').value = req.description || '';

        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } catch (err) {
        showNotification(`Error: ${err.message}`, 'error');
    }
}

async function deleteDocumentRequirement(requirementId) {
    if (!confirm('Delete this requirement?')) return;
    try {
        await apiCall(`/document-requirements/${requirementId}/delete/`, 'DELETE');
        showNotification('Requirement deleted successfully', 'success');
        await loadDocumentRequirementsTable();
    } catch (err) {
        showNotification(`Error: ${err.message}`, 'error');
    }
}

// Expose functions for inline handlers
window.openAddDocumentRequirementModal = openAddDocumentRequirementModal;
window.openEditDocumentRequirement = openEditDocumentRequirement;
window.deleteDocumentRequirement = deleteDocumentRequirement;
window.loadDocumentRequirementsTable = loadDocumentRequirementsTable;
window.viewUserProfile = viewUserProfile;
window.closeViewUserModal = closeViewUserModal;
window.editUser = editUser;
window.closeEditUserModal = closeEditUserModal;
window.submitEditUserForm = submitEditUserForm;

// ============== GRADE LEVEL MANAGEMENT ==============

async function loadGradeLevelsTable() {
    const tbody = document.getElementById('gradeLevelsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-8 text-center"><i class="fas fa-spinner fa-spin"></i> Loading...</td></tr>';
    try {
        const res = await apiCall('/grade-levels/');
        const levels = res.grade_levels || [];
        if (!levels.length) {
            tbody.innerHTML = '<tr><td colspan="5" class="px-6 py-8 text-center text-gray-500"><i class="fas fa-layer-group text-4xl mb-3"></i><p>No grade levels found.</p></td></tr>';
            return;
        }
        tbody.innerHTML = levels.map(gl => `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 font-mono font-semibold text-primary">${gl.code}</td>
                <td class="px-6 py-4 font-semibold text-gray-800">${gl.name}</td>
                <td class="px-6 py-4 text-sm text-gray-600">${gl.description || '<span class="text-gray-400 italic">—</span>'}</td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 rounded-full text-xs font-semibold ${gl.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}">
                        ${gl.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td class="px-6 py-4">
                    <div class="flex gap-2">
                        <button onclick="openEditGradeLevel(${gl.id}, '${escapeHtml(gl.code)}', '${escapeHtml(gl.name)}', '${escapeHtml(gl.description || '')}', ${gl.is_active})"
                            class="px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg text-xs font-semibold hover:bg-blue-100 transition-colors">
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button onclick="deleteGradeLevel(${gl.id}, '${escapeHtml(gl.name)}')"
                            class="px-3 py-1.5 bg-red-50 text-red-700 rounded-lg text-xs font-semibold hover:bg-red-100 transition-colors">
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" class="px-6 py-8 text-center text-red-500">Error: ${err.message}</td></tr>`;
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function openAddGradeLevelModal() {
    document.getElementById('gradeLevelModalTitle').innerHTML = '<i class="fas fa-layer-group mr-2"></i>Add Grade Level';
    document.getElementById('gradeLevelSubmitText').textContent = 'Add Grade Level';
    document.getElementById('gradeLevelId').value = '';
    document.getElementById('gradeLevel_code').value = '';
    document.getElementById('gradeLevel_name').value = '';
    document.getElementById('gradeLevel_description').value = '';
    document.getElementById('gradeLevel_is_active').checked = true;
    const modal = document.getElementById('gradeLevelModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function openEditGradeLevel(id, code, name, description, isActive) {
    document.getElementById('gradeLevelModalTitle').innerHTML = '<i class="fas fa-edit mr-2"></i>Edit Grade Level';
    document.getElementById('gradeLevelSubmitText').textContent = 'Save Changes';
    document.getElementById('gradeLevelId').value = id;
    document.getElementById('gradeLevel_code').value = code;
    document.getElementById('gradeLevel_name').value = name;
    document.getElementById('gradeLevel_description').value = description;
    document.getElementById('gradeLevel_is_active').checked = isActive;
    const modal = document.getElementById('gradeLevelModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeGradeLevelModal() {
    const modal = document.getElementById('gradeLevelModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

async function handleGradeLevelForm(e) {
    e.preventDefault();
    const id = document.getElementById('gradeLevelId').value;
    const payload = {
        code: document.getElementById('gradeLevel_code').value.trim(),
        name: document.getElementById('gradeLevel_name').value.trim(),
        description: document.getElementById('gradeLevel_description').value.trim(),
        is_active: document.getElementById('gradeLevel_is_active').checked,
    };
    try {
        if (id) {
            await apiCall(`/grade-levels/${id}/update/`, 'PUT', payload);
            showNotification('Grade level updated successfully', 'success');
        } else {
            await apiCall('/grade-levels/add/', 'POST', payload);
            showNotification('Grade level added successfully', 'success');
        }
        closeGradeLevelModal();
        await loadGradeLevelsTable();
    } catch (err) {
        showNotification(`Error: ${err.message}`, 'error');
    }
}

async function deleteGradeLevel(id, name) {
    if (!confirm(`Delete grade level "${name}"? This cannot be undone.`)) return;
    try {
        await apiCall(`/grade-levels/${id}/delete/`, 'DELETE');
        showNotification('Grade level deleted successfully', 'success');
        await loadGradeLevelsTable();
    } catch (err) {
        showNotification(`Error: ${err.message}`, 'error');
    }
}

window.loadGradeLevelsTable = loadGradeLevelsTable;
window.openEditGradeLevel = openEditGradeLevel;
window.deleteGradeLevel = deleteGradeLevel;
window.closeGradeLevelModal = closeGradeLevelModal;
