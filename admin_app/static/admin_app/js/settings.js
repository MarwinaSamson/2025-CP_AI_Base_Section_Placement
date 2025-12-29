// Mock data for settings
const mockData = {
    users: [
        {
            id: 1,
            firstName: 'Kakashi',
            lastName: 'Hatake',
            email: 'kakashi@znhswest.edu.ph',
            is_superuser: true,
            is_staff_expert: false,
            is_subject_teacher: true,
            is_adviser: false,
            last_login_formatted: 'Today, 9:30 AM',
            date_joined_formatted: 'Jan 15, 2024'
        },
        {
            id: 2,
            firstName: 'Marwina',
            lastName: 'Samson',
            email: 'marwina@znhswest.edu.ph',
            is_superuser: true,
            is_staff_expert: true,
            is_subject_teacher: false,
            is_adviser: false,
            last_login_formatted: 'Yesterday, 2:15 PM',
            date_joined_formatted: 'Jan 10, 2024'
        },
        {
            id: 3,
            firstName: 'Juan',
            lastName: 'Dela Cruz',
            email: 'juan@znhswest.edu.ph',
            is_superuser: false,
            is_staff_expert: true,
            is_subject_teacher: true,
            is_adviser: false,
            last_login_formatted: '2 days ago',
            date_joined_formatted: 'Feb 1, 2024'
        },
        {
            id: 4,
            firstName: 'Maria',
            lastName: 'Santos',
            email: 'maria@znhswest.edu.ph',
            is_superuser: false,
            is_staff_expert: false,
            is_subject_teacher: true,
            is_adviser: true,
            last_login_formatted: '1 week ago',
            date_joined_formatted: 'Mar 15, 2024'
        }
    ],

    logs: [
        {
            user_full_name: 'Kakashi Hatake',
            user_role: 'Admin',
            action: 'Added new user: Maria Santos',
            date_formatted: 'Today',
            time_formatted: '9:30 AM'
        },
        {
            user_full_name: 'Marwina Samson',
            user_role: 'Admin',
            action: 'Updated school settings',
            date_formatted: 'Yesterday',
            time_formatted: '2:15 PM'
        },
        {
            user_full_name: 'Juan Dela Cruz',
            user_role: 'Staff Expert',
            action: 'Uploaded announcement image',
            date_formatted: '2 days ago',
            time_formatted: '10:45 AM'
        },
        {
            user_full_name: 'Kakashi Hatake',
            user_role: 'Admin',
            action: 'Modified contact information',
            date_formatted: '3 days ago',
            time_formatted: '3:20 PM'
        }
    ],

    positions: [
        {
            id: 1,
            name: 'Teacher I',
            description: 'Entry-level teaching position',
            userCount: 15,
            dateAdded: 'Jan 15, 2024'
        },
        {
            id: 2,
            name: 'Teacher II',
            description: 'Mid-level teaching position',
            userCount: 12,
            dateAdded: 'Jan 15, 2024'
        },
        {
            id: 3,
            name: 'Teacher III',
            description: 'Senior teaching position',
            userCount: 8,
            dateAdded: 'Jan 15, 2024'
        },
        {
            id: 4,
            name: 'Master Teacher I',
            description: 'Advanced teaching position',
            userCount: 5,
            dateAdded: 'Feb 1, 2024'
        },
        {
            id: 5,
            name: 'Head Teacher I',
            description: 'Department head position',
            userCount: 3,
            dateAdded: 'Feb 15, 2024'
        }
    ],

    departments: [
        {
            id: 1,
            name: 'English Department',
            description: 'Handles English language and literature education',
            userCount: 10,
            dateAdded: 'Jan 10, 2024'
        },
        {
            id: 2,
            name: 'Science Department',
            description: 'Covers all science subjects',
            userCount: 12,
            dateAdded: 'Jan 10, 2024'
        },
        {
            id: 3,
            name: 'Mathematics Department',
            description: 'Mathematics and related subjects',
            userCount: 8,
            dateAdded: 'Jan 10, 2024'
        },
        {
            id: 4,
            name: 'Filipino Department',
            description: 'Filipino language and culture',
            userCount: 6,
            dateAdded: 'Jan 15, 2024'
        },
        {
            id: 5,
            name: 'MAPEH Department',
            description: 'Music, Arts, Physical Education, and Health',
            userCount: 7,
            dateAdded: 'Jan 20, 2024'
        }
    ]
};

// Initialize the page
document.addEventListener('DOMContentLoaded', function () {
    // Check if user is logged in
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn && window.location.pathname !== '/index.html') {
        window.location.href = 'index.html';
        return;
    }

    // Load initial data
    loadUsersTable();
    loadHistoryTable();
    loadPositionsTable();
    loadDepartmentsTable();
    
    // Setup all event listeners and tabs
    setupEventListeners();
    setupTabs();
    setupOthersTabs();
    setupPositionEventListeners();
    setupDepartmentEventListeners();
    setupLogoutModalEvents();
});

// ============== SETUP FUNCTIONS ==============

// Setup event listeners
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

    // File upload handlers
    document.querySelectorAll('.border-dashed input[type="file"]').forEach((input) => {
        const uploadArea = input.parentElement;
        uploadArea.addEventListener('click', function () {
            input.click();
        });

        input.addEventListener('change', function (e) {
            const file = e.target.files[0];
            if (file) {
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

        // Close dropdowns when clicking elsewhere
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

// Setup tabs
function setupTabs() {
    // Main tabs
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll("section[id$='-tab']");

    tabBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            const tabName = btn.getAttribute("data-tab");

            // Remove active class from all tabs and contents
            tabBtns.forEach((b) => {
                b.classList.remove("bg-gradient-to-r", "from-primary", "to-primary-dark", "text-white");
                b.classList.add("text-gray-700", "hover:bg-gray-50");
            });

            tabContents.forEach((c) => c.classList.add("hidden"));

            // Add active class to clicked tab and corresponding content
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

            // Remove active class from all content tabs and sections
            contentTabBtns.forEach((b) => {
                b.classList.remove("bg-red-50", "text-primary", "border-red-200");
                b.classList.add("text-gray-700", "hover:bg-gray-50", "border-gray-200");
            });

            contentSections.forEach((s) => s.classList.add("hidden"));

            // Add active class to clicked tab and corresponding section
            btn.classList.remove("text-gray-700", "hover:bg-gray-50", "border-gray-200");
            btn.classList.add("bg-red-50", "text-primary", "border-red-200");
            document.getElementById(`${contentName}-content`).classList.remove("hidden");
        });
    });
}

// Setup "Others" sub-tabs
function setupOthersTabs() {
    const othersTabBtns = document.querySelectorAll('.others-tab-btn');
    const othersSections = document.querySelectorAll('[id$="-others"]');

    othersTabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const othersName = btn.getAttribute('data-others');

            // Remove active class from all tabs and sections
            othersTabBtns.forEach(b => {
                b.classList.remove('bg-red-50', 'text-primary', 'border-red-200');
                b.classList.add('text-gray-700', 'hover:bg-gray-50', 'border-gray-200');
            });

            othersSections.forEach(s => s.classList.add('hidden'));

            // Add active class to clicked tab
            btn.classList.remove('text-gray-700', 'hover:bg-gray-50', 'border-gray-200');
            btn.classList.add('bg-red-50', 'text-primary', 'border-red-200');
            document.getElementById(`${othersName}-others`).classList.remove('hidden');
        });
    });
}

// ============== USER MANAGEMENT FUNCTIONS ==============

// Load users table
function loadUsersTable() {
    const tableBody = document.getElementById('usersTableBody');
    if (!tableBody) return;

    if (mockData.users.length === 0) {
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

    tableBody.innerHTML = mockData.users.map(user => `
        <tr class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4">
                <div class="flex items-center">
                    <img src="../../assets/kakashi.jpeg" alt="User" class="w-10 h-10 rounded-full object-cover mr-3">
                    <div>
                        <div class="font-medium text-gray-900">${user.firstName} ${user.lastName}</div>
                        <div class="text-gray-500 text-sm">${user.email}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4">
                ${user.is_superuser ? '<span class="inline-block px-3 py-1 bg-red-600 text-white rounded-full text-xs font-semibold mr-1 mb-1">Admin</span>' : ''}
                ${user.is_staff_expert ? '<span class="inline-block px-3 py-1 bg-orange-600 text-white rounded-full text-xs font-semibold mr-1 mb-1">Coordinator</span>' : ''}
                ${user.is_subject_teacher ? '<span class="inline-block px-3 py-1 bg-blue-600 text-white rounded-full text-xs font-semibold mr-1 mb-1">Subject Teacher</span>' : ''}
                ${user.is_adviser ? '<span class="inline-block px-3 py-1 bg-purple-600 text-white rounded-full text-xs font-semibold mr-1 mb-1">Adviser</span>' : ''}
            </td>
            <td class="px-6 py-4 text-gray-600">${user.last_login_formatted}</td>
            <td class="px-6 py-4 text-gray-600">${user.date_joined_formatted}</td>
            <td class="px-6 py-4">
                <div class="relative">
                    <button class="px-3 py-1 border border-gray-300 rounded-lg text-gray-600 hover:bg-gray-50 transition-colors duration-300" onclick="toggleDropdown(this)">
                        <i class="fas fa-ellipsis-v"></i>
                    </button>
                    <div class="absolute right-0 mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-200 z-10 hidden animate-dropdown">
                        <a href="#" class="block px-4 py-3 text-gray-700 hover:bg-gray-50 transition-colors duration-200 rounded-t-xl" onclick="viewProfile(${user.id})">
                            <i class="fas fa-eye mr-2"></i> View Profile
                        </a>
                        <a href="#" class="block px-4 py-3 text-gray-700 hover:bg-gray-50 transition-colors duration-200" onclick="editDetails(${user.id})">
                            <i class="fas fa-edit mr-2"></i> Edit Details
                        </a>
                        <a href="#" class="block px-4 py-3 text-gray-700 hover:bg-gray-50 transition-colors duration-200" onclick="changePermission(${user.id})">
                            <i class="fas fa-user-cog mr-2"></i> Change Permission
                        </a>
                        <div class="border-t border-gray-100"></div>
                        <a href="#" class="block px-4 py-3 text-red-600 hover:bg-red-50 transition-colors duration-200 rounded-b-xl" onclick="deleteUser(${user.id})">
                            <i class="fas fa-trash mr-2"></i> Delete User
                        </a>
                    </div>
                </div>
            </td>
        </tr>
    `).join('');
}

// Filter users
function filterUsers(searchTerm) {
    const rows = document.querySelectorAll("#usersTableBody tr");
    rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm.toLowerCase()) ? "" : "none";
    });
}

// Modal functions
function openAddUserModal() {
    const modal = document.getElementById('addUserModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeAddUserModal() {
    const modal = document.getElementById('addUserModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    document.getElementById('addUserForm').reset();
}

function openUserProfileModal() {
    const modal = document.getElementById('userProfileModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeUserProfileModal() {
    const modal = document.getElementById('userProfileModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
}

function closeAllModals() {
    document.querySelectorAll('.fixed').forEach(modal => {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
    });
}

// Handle add user form
function handleAddUserForm(event) {
    event.preventDefault();

    const firstName = document.getElementById('first_name').value;
    const lastName = document.getElementById('last_name').value;
    const email = document.getElementById('email').value;
    const username = document.getElementById('username').value;
    const position = document.getElementById('position').value;
    const department = document.getElementById('department').value;
    const password = document.getElementById('password').value;

    if (!firstName || !lastName || !email || !username || !position || !password) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    // Get selected permissions
    const adminAccess = document.getElementById('admin_access').checked;
    const staffExpertAccess = document.getElementById('staff_expert_access').checked;

    // Create new user
    const newUser = {
        id: Date.now(),
        firstName: firstName,
        lastName: lastName,
        email: email,
        is_superuser: adminAccess,
        is_staff_expert: staffExpertAccess,
        is_subject_teacher: false,
        is_adviser: false,
        last_login_formatted: 'Just now',
        date_joined_formatted: new Date().toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        })
    };

    // Add to mock data
    mockData.users.push(newUser);

    // Show success message
    showNotification(`User ${firstName} ${lastName} added successfully!`, 'success');

    // Reload table
    loadUsersTable();

    // Close modal
    closeAddUserModal();
}

// User management functions
function viewProfile(userId) {
    const user = mockData.users.find(u => u.id === userId);
    if (user) {
        openUserProfileModal();
    }
}

function editDetails(userId) {
    const user = mockData.users.find(u => u.id === userId);
    if (user) {
        showNotification(`Edit functionality for ${user.firstName} ${user.lastName} coming soon`, 'info');
    }
}

function changePermission(userId) {
    const user = mockData.users.find(u => u.id === userId);
    if (user) {
        showNotification(`Permission change for ${user.firstName} ${user.lastName} coming soon`, 'info');
    }
}

function deleteUser(userId) {
    const user = mockData.users.find(u => u.id === userId);
    if (user) {
        if (confirm(`Are you sure you want to delete ${user.firstName} ${user.lastName}?`)) {
            mockData.users = mockData.users.filter(u => u.id !== userId);
            loadUsersTable();
            showNotification(`User ${user.firstName} ${user.lastName} deleted successfully!`, 'success');
        }
    }
}

// Dropdown functionality
function toggleDropdown(button) {
    const dropdown = button.nextElementSibling;
    const isShowing = dropdown.classList.contains('hidden');

    // Close all other dropdowns
    document.querySelectorAll('.absolute').forEach(menu => {
        if (menu !== dropdown) {
            menu.classList.remove('block');
            menu.classList.add('hidden');
        }
    });

    // Toggle current dropdown
    if (isShowing) {
        dropdown.classList.remove('hidden');
        dropdown.classList.add('block');
    } else {
        dropdown.classList.remove('block');
        dropdown.classList.add('hidden');
    }
}

// ============== HISTORY LOG FUNCTIONS ==============

// Load history table
function loadHistoryTable() {
    const tableBody = document.getElementById('historyTableBody');
    if (!tableBody) return;

    if (mockData.logs.length === 0) {
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

    tableBody.innerHTML = mockData.logs.map(log => `
        <tr class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-gray-600">${log.action}</td>
            <td class="px-6 py-4 text-gray-600">${log.date_formatted}</td>
            <td class="px-6 py-4 text-gray-600">${log.time_formatted}</td>
        </tr>
    `).join('');
}

// Filter history
function filterHistory(searchTerm) {
    const rows = document.querySelectorAll("#historyTableBody tr");
    rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm.toLowerCase()) ? "" : "none";
    });
}

// ============== POSITION FUNCTIONS ==============

function setupPositionEventListeners() {
    // Add Position button
    const addPositionBtn = document.getElementById('addPositionBtn');
    if (addPositionBtn) {
        addPositionBtn.addEventListener('click', () => openPositionModal());
    }

    // Position search
    const positionSearch = document.getElementById('positionSearch');
    if (positionSearch) {
        positionSearch.addEventListener('input', function() {
            filterPositions(this.value);
        });
    }

    // Add Position form
    const addPositionForm = document.getElementById('addPositionForm');
    if (addPositionForm) {
        addPositionForm.addEventListener('submit', handlePositionForm);
    }
}

function loadPositionsTable() {
    const tableBody = document.getElementById('positionsTableBody');
    if (!tableBody) return;

    if (mockData.positions.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="px-6 py-8 text-center text-gray-500">
                    <i class="fas fa-briefcase text-4xl mb-3"></i>
                    <p>No positions found. Add your first position!</p>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = mockData.positions.map(position => `
        <tr class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-gradient-to-br from-primary to-primary-dark rounded-lg flex items-center justify-center mr-3">
                        <i class="fas fa-briefcase text-white"></i>
                    </div>
                    <div>
                        <div class="font-medium text-gray-900">${position.name}</div>
                        <div class="text-gray-500 text-sm">${position.description || 'No description'}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                    <button 
                        onclick="editPosition(${position.id})"
                        class="px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors duration-300"
                        title="Edit"
                    >
                        <i class="fas fa-edit"></i>
                    </button>
                    <button 
                        onclick="deletePosition(${position.id})"
                        class="px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors duration-300"
                        title="Delete"
                    >
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function filterPositions(searchTerm) {
    const rows = document.querySelectorAll('#positionsTableBody tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm.toLowerCase()) ? '' : 'none';
    });
}

function openPositionModal(positionId = null) {
    const modal = document.getElementById('addPositionModal');
    const form = document.getElementById('addPositionForm');
    const modalTitle = document.getElementById('positionModalTitle');
    const submitText = document.getElementById('positionSubmitText');
    
    form.reset();
    
    if (positionId) {
        const position = mockData.positions.find(p => p.id === positionId);
        if (position) {
            document.getElementById('positionId').value = position.id;
            document.getElementById('position_name').value = position.name;
            document.getElementById('position_description').value = position.description || '';
            modalTitle.textContent = 'Edit Position';
            submitText.textContent = 'Update Position';
        }
    } else {
        document.getElementById('positionId').value = '';
        modalTitle.textContent = 'Add New Position';
        submitText.textContent = 'Add Position';
    }
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closePositionModal() {
    const modal = document.getElementById('addPositionModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    document.getElementById('addPositionForm').reset();
}

function handlePositionForm(event) {
    event.preventDefault();
    
    const positionId = document.getElementById('positionId').value;
    const name = document.getElementById('position_name').value;
    const description = document.getElementById('position_description').value;
    
    if (!name) {
        showNotification('Please enter position name', 'error');
        return;
    }
    
    if (positionId) {
        // Edit existing position
        const position = mockData.positions.find(p => p.id === parseInt(positionId));
        if (position) {
            position.name = name;
            position.description = description;
            showNotification(`Position "${name}" updated successfully!`, 'success');
        }
    } else {
        // Add new position
        const newPosition = {
            id: Date.now(),
            name: name,
            description: description,
            userCount: 0,
            dateAdded: new Date().toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            })
        };
        
        mockData.positions.push(newPosition);
        showNotification(`Position "${name}" added successfully!`, 'success');
    }
    
    loadPositionsTable();
    closePositionModal();
}

function editPosition(positionId) {
    openPositionModal(positionId);
}

function deletePosition(positionId) {
    const position = mockData.positions.find(p => p.id === positionId);
    if (position) {
        if (position.userCount > 0) {
            showNotification(`Cannot delete "${position.name}" - ${position.userCount} users are assigned to this position`, 'error');
            return;
        }
        
        if (confirm(`Are you sure you want to delete "${position.name}"?`)) {
            mockData.positions = mockData.positions.filter(p => p.id !== positionId);
            loadPositionsTable();
            showNotification(`Position "${position.name}" deleted successfully!`, 'success');
        }
    }
}

// ============== DEPARTMENT FUNCTIONS ==============

function setupDepartmentEventListeners() {
    // Add Department button
    const addDepartmentBtn = document.getElementById('addDepartmentBtn');
    if (addDepartmentBtn) {
        addDepartmentBtn.addEventListener('click', () => openDepartmentModal());
    }

    // Department search
    const departmentSearch = document.getElementById('departmentSearch');
    if (departmentSearch) {
        departmentSearch.addEventListener('input', function() {
            filterDepartments(this.value);
        });
    }

    // Add Department form
    const addDepartmentForm = document.getElementById('addDepartmentForm');
    if (addDepartmentForm) {
        addDepartmentForm.addEventListener('submit', handleDepartmentForm);
    }
}

function loadDepartmentsTable() {
    const tableBody = document.getElementById('departmentsTableBody');
    if (!tableBody) return;

    if (mockData.departments.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="px-6 py-8 text-center text-gray-500">
                    <i class="fas fa-building text-4xl mb-3"></i>
                    <p>No departments found. Add your first department!</p>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = mockData.departments.map(department => `
        <tr class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4">
                <div class="flex items-center">
                    <div class="w-10 h-10 bg-gradient-to-br from-primary to-primary-dark rounded-lg flex items-center justify-center mr-3">
                        <i class="fas fa-building text-white"></i>
                    </div>
                    <div>
                        <div class="font-medium text-gray-900">${department.name}</div>
                        <div class="text-gray-500 text-sm">${department.description || 'No description'}</div>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4">
                <div class="flex items-center gap-2">
                    <button 
                        onclick="editDepartment(${department.id})"
                        class="px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors duration-300"
                        title="Edit"
                    >
                        <i class="fas fa-edit"></i>
                    </button>
                    <button 
                        onclick="deleteDepartment(${department.id})"
                        class="px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors duration-300"
                        title="Delete"
                    >
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function filterDepartments(searchTerm) {
    const rows = document.querySelectorAll('#departmentsTableBody tr');
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm.toLowerCase()) ? '' : 'none';
    });
}

function openDepartmentModal(departmentId = null) {
    const modal = document.getElementById('addDepartmentModal');
    const form = document.getElementById('addDepartmentForm');
    const modalTitle = document.getElementById('departmentModalTitle');
    const submitText = document.getElementById('departmentSubmitText');
    
    form.reset();
    
    if (departmentId) {
        const department = mockData.departments.find(d => d.id === departmentId);
        if (department) {
            document.getElementById('departmentId').value = department.id;
            document.getElementById('department_name').value = department.name;
            document.getElementById('department_description').value = department.description || '';
            modalTitle.textContent = 'Edit Department';
            submitText.textContent = 'Update Department';
        }
    } else {
        document.getElementById('departmentId').value = '';
        modalTitle.textContent = 'Add New Department';
        submitText.textContent = 'Add Department';
    }
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeDepartmentModal() {
    const modal = document.getElementById('addDepartmentModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    document.getElementById('addDepartmentForm').reset();
}

function handleDepartmentForm(event) {
    event.preventDefault();
    
    const departmentId = document.getElementById('departmentId').value;
    const name = document.getElementById('department_name').value;
    const description = document.getElementById('department_description').value;
    
    if (!name) {
        showNotification('Please enter department name', 'error');
        return;
    }
    
    if (departmentId) {
        // Edit existing department
        const department = mockData.departments.find(d => d.id === parseInt(departmentId));
        if (department) {
            department.name = name;
            department.description = description;
            showNotification(`Department "${name}" updated successfully!`, 'success');
        }
    } else {
        // Add new department
        const newDepartment = {
            id: Date.now(),
            name: name,
            description: description,
            userCount: 0,
            dateAdded: new Date().toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            })
        };
        
        mockData.departments.push(newDepartment);
        showNotification(`Department "${name}" added successfully!`, 'success');
    }
    
    loadDepartmentsTable();
    closeDepartmentModal();
}

function editDepartment(departmentId) {
    openDepartmentModal(departmentId);
}

function deleteDepartment(departmentId) {
    const department = mockData.departments.find(d => d.id === departmentId);
    if (department) {
        if (department.userCount > 0) {
            showNotification(`Cannot delete "${department.name}" - ${department.userCount} users are assigned to this department`, 'error');
            return;
        }
        
        if (confirm(`Are you sure you want to delete "${department.name}"?`)) {
            mockData.departments = mockData.departments.filter(d => d.id !== departmentId);
            loadDepartmentsTable();
            showNotification(`Department "${department.name}" deleted successfully!`, 'success');
        }
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
        if (e.target.closest('a[href="{% url \'admin_app:logout\' %}"]')) {
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
                window.location.href = '{% url "admin_app:logout" %}';
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

// ============== MAKE FUNCTIONS GLOBALLY AVAILABLE ==============

window.openAddUserModal = openAddUserModal;
window.closeAddUserModal = closeAddUserModal;
window.openUserProfileModal = openUserProfileModal;
window.closeUserProfileModal = closeUserProfileModal;
window.viewProfile = viewProfile;
window.editDetails = editDetails;
window.changePermission = changePermission;
window.deleteUser = deleteUser;
window.toggleDropdown = toggleDropdown;
window.showNotification = showNotification;
window.openPositionModal = openPositionModal;
window.closePositionModal = closePositionModal;
window.editPosition = editPosition;
window.deletePosition = deletePosition;
window.openDepartmentModal = openDepartmentModal;
window.closeDepartmentModal = closeDepartmentModal;
window.editDepartment = editDepartment;
window.deleteDepartment = deleteDepartment;