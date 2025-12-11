// Mock data for the sections system
const mockData = {
    currentProgram: 'STE',
    currentGradeLevel: '7',
    currentSectionForUpdate: null,
    currentSubjectProgram: 'STE',
    currentEditingSubject: null,
    currentEditingProgram: null,

    advisers: [
        { id: 1, name: 'Salatan, Juliana D.', isAssigned: false },
        { id: 2, name: 'Dela Cruz, Juan P.', isAssigned: false },
        { id: 3, name: 'Santos, Maria R.', isAssigned: true },
        { id: 4, name: 'Reyes, Carlos M.', isAssigned: false },
        { id: 5, name: 'Gonzales, Ana L.', isAssigned: true }
    ],

    subjectTeachers: [
        { id: 1, name: 'Salatan, Juliana D.', department: 'Mathematics' },
        { id: 2, name: 'Dela Cruz, Juan P.', department: 'Science' },
        { id: 3, name: 'Santos, Maria R.', department: 'English' },
        { id: 4, name: 'Reyes, Carlos M.', department: 'Filipino' },
        { id: 5, name: 'Gonzales, Ana L.', department: 'Araling Panlipunan' },
        { id: 6, name: 'Torres, Pedro S.', department: 'MAPEH' },
        { id: 7, name: 'Fernandez, Lucia B.', department: 'ESP' },
        { id: 8, name: 'Martinez, Antonio R.', department: 'Research' }
    ],

    buildingsRooms: {
        '1': ['101', '102', '103', '104', '105'],
        '2': ['201', '202', '203', '204', '205'],
        '3': ['301', '302', '303', '304', '305'],
        '4': ['Lab 1', 'Lab 2', 'Lab 3', 'Lecture 1', 'Lecture 2'],
        '5': ['IT-101', 'IT-102', 'IT-201', 'IT-202', 'Server Room']
    },

    sectionsCache: {
        'STE': [
            {
                id: 1,
                name: 'Sampaguita',
                adviser: 'Salatan, Juliana D.',
                adviserId: 1,
                location: 'Bldg 1 Room 101',
                students: 38,
                maxStudents: 40,
                program: 'STE'
            },
            {
                id: 2,
                name: 'Rosal',
                adviser: 'Dela Cruz, Juan P.',
                adviserId: 2,
                location: 'Bldg 1 Room 102',
                students: 35,
                maxStudents: 40,
                program: 'STE'
            },
            {
                id: 3,
                name: 'Orchid',
                adviser: 'Santos, Maria R.',
                adviserId: 3,
                location: 'Bldg 2 Room 201',
                students: 40,
                maxStudents: 40,
                program: 'STE'
            }
        ],
        'SPFL': [
            {
                id: 4,
                name: 'Lirio',
                adviser: 'Reyes, Carlos M.',
                adviserId: 4,
                location: 'Bldg 3 Room 301',
                students: 32,
                maxStudents: 40,
                program: 'SPFL'
            }
        ],
        'SPTVE': [
            {
                id: 5,
                name: 'Tulip',
                adviser: 'Gonzales, Ana L.',
                adviserId: 5,
                location: 'Bldg 4 Lab 1',
                students: 28,
                maxStudents: 35,
                program: 'SPTVE'
            }
        ],
        'OHSP': [],
        'SNED': [],
        'TOP5': [],
        'HETERO': []
    },

    subjectsByProgram: {
        'STE': [
            { id: 1, name: 'Mathematics', code: 'MATH-101', program: 'STE' },
            { id: 2, name: 'Science', code: 'SCI-101', program: 'STE' },
            { id: 3, name: 'English', code: 'ENG-101', program: 'STE' },
            { id: 4, name: 'Filipino', code: 'FIL-101', program: 'STE' },
            { id: 5, name: 'Araling Panlipunan', code: 'AP-101', program: 'STE' },
            { id: 6, name: 'MAPEH', code: 'MAPEH-101', program: 'STE' },
            { id: 7, name: 'ESP', code: 'ESP-101', program: 'STE' },
            { id: 8, name: 'Research', code: 'RES-101', program: 'STE' }
        ],
        'SPFL': [
            { id: 9, name: 'Spanish Language', code: 'SPAN-101', program: 'SPFL' },
            { id: 10, name: 'Japanese Language', code: 'JPN-101', program: 'SPFL' }
        ],
        'SPTVE': [],
        'OHSP': [],
        'SNED': [],
        'TOP5': [],
        'HETERO': []
    },

    programsCache: [
        { id: 1, name: 'STE', description: 'Science, Technology, and Engineering', school_year: { name: '2025-2026' }, section_count: 8, is_active: true },
        { id: 2, name: 'SPFL', description: 'Special Program in Foreign Language', school_year: { name: '2025-2026' }, section_count: 4, is_active: true },
        { id: 3, name: 'SPTVE', description: 'Special Program in Technical Vocational Education', school_year: { name: '2025-2026' }, section_count: 6, is_active: true },
        { id: 4, name: 'OHSP', description: 'Open High School Program', school_year: { name: '2025-2026' }, section_count: 3, is_active: true },
        { id: 5, name: 'SNED', description: 'Special Needs Education', school_year: { name: '2025-2026' }, section_count: 2, is_active: false },
        { id: 6, name: 'TOP5', description: 'Top 5 Program', school_year: { name: '2025-2026' }, section_count: 1, is_active: true },
        { id: 7, name: 'HETERO', description: 'Heterogeneous Class', school_year: { name: '2025-2026' }, section_count: 12, is_active: true }
    ]
};

// Initialize the page
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM Content Loaded - Sections Page');
    
    // Check if user is logged in
    const isLoggedIn = localStorage.getItem('isLoggedIn');
    if (!isLoggedIn) {
        window.location.href = 'login.html';
        return;
    }

    console.log('User is logged in');
    
    // Set active program from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const programParam = urlParams.get('program');
    if (programParam) {
        mockData.currentProgram = programParam.toUpperCase();
        console.log('Program from URL:', mockData.currentProgram);
    }

    // Log initial state
    console.log('Initial program:', mockData.currentProgram);
    console.log('Sections cache:', mockData.sectionsCache);

    // Load initial data
    loadSections(mockData.currentProgram);
    
    // Update active tab visually
    updateActiveTab(mockData.currentProgram);
    
    setupEventListeners();
    populateAdviserSelects();
    populateBuildingSelects();
    populateSubjectTeacherSelects();

    console.log('Page initialization complete');

    setupLogoutModalEvents();
});

// Event Listeners Setup
function setupEventListeners() {
    // Program tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchProgram(btn.dataset.program));
    });

    // Form submissions
    const addSectionForm = document.getElementById('addSectionForm');
    if (addSectionForm) {
        addSectionForm.addEventListener('submit', handleAddSection);
    }

    const updateSectionForm = document.getElementById('updateSectionForm');
    if (updateSectionForm) {
        updateSectionForm.addEventListener('submit', handleUpdateSection);
    }

    const subjectForm = document.getElementById('subjectForm');
    if (subjectForm) {
        subjectForm.addEventListener('submit', handleSubjectFormSubmit);
    }

    const programForm = document.getElementById('programForm');
    if (programForm) {
        programForm.addEventListener('submit', handleProgramFormSubmit);
    }

    // Building change listeners
    const addBuildingSelect = document.getElementById('buildingNumber');
    if (addBuildingSelect) {
        addBuildingSelect.addEventListener('change', function () {
            populateRoomSelectById('roomNumber', this.value);
        });
    }

    const updateBuildingSelect = document.getElementById('updateBuilding');
    if (updateBuildingSelect) {
        updateBuildingSelect.addEventListener('change', function () {
            populateRoomSelectById('updateRoom', this.value);
        });
    }

    // Close modals when clicking outside
    document.addEventListener('click', function (event) {
        if (event.target.classList.contains('modal')) {
            closeAllModals();
        }

        // Close dropdowns when clicking elsewhere
        if (!event.target.closest('.relative')) {
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.classList.add('hidden');
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

// Load Sections
function loadSections(program) {
    console.log(`Loading sections for program: ${program}`);
    const sections = mockData.sectionsCache[program] || [];
    const sectionsGrid = document.getElementById('sectionsGrid');

    if (!sectionsGrid) {
        console.error('Sections grid element not found!');
        return;
    }

    console.log(`Found ${sections.length} sections for ${program}`);

    // Remove loading indicator
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }

    if (sections.length === 0) {
        sectionsGrid.innerHTML = `
            <div class="col-span-full text-center py-16">
                <div class="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                    <i class="fas fa-inbox text-3xl text-gray-400"></i>
                </div>
                <h3 class="text-xl font-semibold text-gray-600 mb-2">No Sections Found</h3>
                <p class="text-gray-500 mb-4">No sections available for ${program} program.</p>
                <button class="gradient-bg text-white px-6 py-3 rounded-xl hover:shadow-lg transform hover:scale-105 transition-all duration-300 font-semibold" onclick="openAddSectionModal()">
                    <i class="fas fa-plus-circle mr-2"></i>Create First Section
                </button>
            </div>
        `;
        return;
    }

    sectionsGrid.innerHTML = sections.map(section => `
        <div class="bg-gradient-to-br from-white to-gray-50 rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div class="p-6">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center gap-4">
                        <div class="w-14 h-14 bg-gradient-to-br from-primary to-primary-dark rounded-xl flex items-center justify-center shadow-lg">
                            <i class="fas fa-users text-white text-lg"></i>
                        </div>
                        <div class="flex-1">
                            <h3 class="text-xl font-bold text-gray-800">${section.name}</h3>
                            <p class="text-sm text-gray-600 flex items-center gap-1 mt-1">
                                <i class="fas fa-user-graduate text-primary"></i>
                                ${section.adviser}
                            </p>
                        </div>
                    </div>
                    <div class="relative">
                        <button class="menu-btn w-10 h-10 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-all duration-300" onclick="event.stopPropagation(); toggleDropdown(${section.id})">
                            <i class="fas fa-ellipsis-v text-lg"></i>
                       </button>
                        <div class="dropdown-menu hidden" id="dropdown-${section.id}">
                            <button class="dropdown-item w-full text-left px-4 py-3 hover:bg-green-50 transition-all duration-200 flex items-center gap-3 group" onclick="updateSection(${section.id}, event)">
                                <div class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center group-hover:bg-green-200 transition-colors">
                                    <i class="fas fa-edit text-green-600 text-sm"></i>
                                </div>
                                <div>
                                    <div class="font-semibold text-gray-700">Update</div>
                                    <div class="text-xs text-gray-500">Edit section details</div>
                                </div>
                            </button>
                            <div class="border-t border-gray-100 my-1"></div>
                            <button class="dropdown-item w-full text-left px-4 py-3 hover:bg-red-50 transition-all duration-200 flex items-center gap-3 group text-red-600" onclick="deleteSection(${section.id}, event)">
                                <div class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center group-hover:bg-red-200 transition-colors">
                                    <i class="fas fa-trash text-red-600 text-sm"></i>
                                </div>
                                <div>
                                    <div class="font-semibold">Delete</div>
                                    <div class="text-xs text-red-500">Remove this section</div>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="space-y-3">
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-map-marker-alt text-gray-400"></i>
                            <span class="text-sm font-medium text-gray-600">Location</span>
                        </div>
                        <span class="text-sm font-semibold text-gray-800">${section.location}</span>
                    </div>
                    
                    <div class="flex items-center justify-between p-3 bg-gradient-to-r from-red-50 to-pink-50 rounded-lg border border-red-100">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-users text-red-400"></i>
                            <span class="text-sm font-medium text-red-600">Students</span>
                        </div>
                        <div class="text-right">
                            <div class="text-lg font-bold text-red-600">${section.students}/${section.maxStudents}</div>
                            <div class="w-24 h-2 bg-red-200 rounded-full overflow-hidden">
                                <div class="h-full bg-red-500 rounded-full" style="width: ${(section.students / section.maxStudents) * 100}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="bg-gray-50 px-6 py-3 border-t border-gray-200">
                <button class="w-full text-center text-sm font-semibold text-gray-600 hover:text-primary transition-colors duration-300 flex items-center justify-center gap-2" onclick="openSectionMasterlist(${section.id})">
                    <i class="fas fa-list-alt"></i>
                    View Masterlist
                </button>
            </div>
        </div>
    `).join('');
}

// Tab switching
function switchProgram(program) {
    console.log(`Switching program to: ${program}`);
    updateActiveTab(program);
    mockData.currentProgram = program;
    loadSections(program);

    // Update URL without reloading page
    const newUrl = new URL(window.location);
    newUrl.searchParams.set("program", program);
    window.history.pushState({}, "", newUrl);
}

function updateActiveTab(program) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    const targetTab = document.querySelector(`[data-program="${program}"]`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
}

// Populate Selects
function populateAdviserSelects(currentAdviserId = null) {
    const adviserSelects = [
        document.getElementById('adviserName'),
        document.getElementById('updateAdviserName')
    ];

    adviserSelects.forEach(select => {
        if (select) {
            select.innerHTML = '<option value="">Select Adviser</option>';
            mockData.advisers.forEach(adviser => {
                const option = document.createElement('option');
                option.value = adviser.id;
                option.textContent = adviser.name;
                if (adviser.isAssigned && adviser.id != currentAdviserId) {
                    option.disabled = true;
                    option.textContent += ' (Unavailable)';
                }
                select.appendChild(option);
            });
        }
    });
}

function populateSubjectTeacherSelects() {
    const teacherSelects = document.querySelectorAll('select[data-subject-id]');
    teacherSelects.forEach(select => {
        select.innerHTML = '<option value="">Select Teacher</option>';
        mockData.subjectTeachers.forEach(teacher => {
            const option = document.createElement('option');
            option.value = teacher.id;
            option.textContent = `${teacher.name}${teacher.department ? ' - ' + teacher.department : ''}`;
            select.appendChild(option);
        });
    });
}

function populateBuildingSelects() {
    const buildingSelects = [
        document.getElementById('buildingNumber'),
        document.getElementById('updateBuilding')
    ];

    buildingSelects.forEach(select => {
        if (select) {
            select.innerHTML = '<option value="">Select Building</option>';
            for (const building in mockData.buildingsRooms) {
                const option = document.createElement('option');
                option.value = building;
                option.textContent = building.replace('building', 'Building ');
                select.appendChild(option);
            }
        }
    });
}

function populateRoomSelectById(roomSelectId, buildingValue) {
    const roomSelect = document.getElementById(roomSelectId);
    if (roomSelect) {
        roomSelect.innerHTML = '<option value="">Select Room</option>';
        if (mockData.buildingsRooms[buildingValue]) {
            mockData.buildingsRooms[buildingValue].forEach(room => {
                const option = document.createElement('option');
                option.value = room;
                option.textContent = room;
                roomSelect.appendChild(option);
            });
        }
    }
}

// Modal Functions
function openAddSectionModal() {
    try {
        const modal = document.getElementById('addSectionModal');
        if (!modal) {
            console.error('Add section modal not found!');
            showNotification('Modal not found. Please refresh the page.', 'error');
            return;
        }
        modal.style.display = 'flex';
        document.body.classList.add('modal-open');
        populateAdviserSelects();
        populateBuildingSelects();
        console.log('Add section modal opened');
    } catch (error) {
        console.error('Error opening add section modal:', error);
        showNotification('Error opening modal. Please check console.', 'error');
    }
}

function closeAddSectionModal() {
    const modal = document.getElementById('addSectionModal');
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    document.getElementById('addSectionForm').reset();
}

function openUpdateSectionModal(sectionId) {
    const section = findSectionById(sectionId);
    if (!section) return;

    mockData.currentSectionForUpdate = section;

    // Populate selects first
    populateAdviserSelects(section.adviserId);
    populateBuildingSelects();

    // Fill form fields
    document.getElementById('updateSectionName').value = section.name;
    document.getElementById('updateAdviserName').value = section.adviserId || '';
    document.getElementById('updateMaxStudents').value = section.maxStudents;

    // Parse and set building + room
    const locationMatch = section.location.match(/Bldg (\d+) Room (.+)/);
    if (locationMatch) {
        const building = locationMatch[1];
        const room = locationMatch[2];
        document.getElementById('updateBuilding').value = building;
        populateRoomSelectById('updateRoom', building);
        setTimeout(() => {
            const roomSelect = document.getElementById('updateRoom');
            if (roomSelect) {
                roomSelect.value = room;
            }
        }, 50);
    }

    // Open modal
    const modal = document.getElementById('updateSectionModal');
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
}

function closeUpdateSectionModal() {
    const modal = document.getElementById('updateSectionModal');
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    document.getElementById('updateSectionForm').reset();
    mockData.currentSectionForUpdate = null;
}

function openManageSubjectsModal() {
    try {
        const modal = document.getElementById('manageSubjectsModal');
        if (!modal) {
            console.error('Manage subjects modal not found!');
            showNotification('Modal not found. Please refresh the page.', 'error');
            return;
        }
        modal.style.display = 'flex';
        document.body.classList.add('modal-open');

        // Set first tab as active
        mockData.currentSubjectProgram = 'STE';
        updateSubjectProgramTabs('STE');
        loadSubjectsForProgram('STE');
        cancelSubjectForm();
        console.log('Manage subjects modal opened');
    } catch (error) {
        console.error('Error opening manage subjects modal:', error);
        showNotification('Error opening modal. Please check console.', 'error');
    }
}

function closeManageSubjectsModal() {
    const modal = document.getElementById('manageSubjectsModal');
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    cancelSubjectForm();
}

function openManageProgramsModal() {
    try {
        const modal = document.getElementById('manageProgramsModal');
        if (!modal) {
            console.error('Manage programs modal not found!');
            showNotification('Modal not found. Please refresh the page.', 'error');
            return;
        }
        modal.style.display = 'flex';
        document.body.classList.add('modal-open');

        loadAllPrograms();
        cancelProgramForm();
        console.log('Manage programs modal opened');
    } catch (error) {
        console.error('Error opening manage programs modal:', error);
        showNotification('Error opening modal. Please check console.', 'error');
    }
}

function closeManageProgramsModal() {
    const modal = document.getElementById('manageProgramsModal');
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    cancelProgramForm();
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
    document.body.classList.remove('modal-open');
}

// Section Operations
function findSectionById(sectionId) {
    const sections = mockData.sectionsCache[mockData.currentProgram] || [];
    return sections.find(section => section.id == sectionId) || null;
}

function handleAddSection(event) {
    event.preventDefault();

    const sectionName = document.getElementById('sectionName').value;
    const adviserId = document.getElementById('adviserName').value;
    const building = document.getElementById('buildingNumber').value;
    const room = document.getElementById('roomNumber').value;
    const maxStudents = document.getElementById('maxStudents').value;

    if (!sectionName || !adviserId || !building || !room) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    // Find adviser name
    const adviser = mockData.advisers.find(a => a.id == adviserId);

    // Create new section
    const newSection = {
        id: Date.now(), // Simple ID generation
        name: sectionName,
        adviser: adviser ? adviser.name : 'Unknown',
        adviserId: adviserId,
        location: `Bldg ${building} Room ${room}`,
        students: 0,
        maxStudents: maxStudents,
        program: mockData.currentProgram
    };

    // Add to cache
    if (!mockData.sectionsCache[mockData.currentProgram]) {
        mockData.sectionsCache[mockData.currentProgram] = [];
    }
    mockData.sectionsCache[mockData.currentProgram].push(newSection);

    showNotification(`Section "${sectionName}" added successfully!`, 'success');
    loadSections(mockData.currentProgram);
    closeAddSectionModal();
}

function handleUpdateSection(event) {
    event.preventDefault();
    if (!mockData.currentSectionForUpdate) return;

    const sectionName = document.getElementById('updateSectionName').value;
    const adviserId = document.getElementById('updateAdviserName').value;
    const building = document.getElementById('updateBuilding').value;
    const room = document.getElementById('updateRoom').value;
    const maxStudents = document.getElementById('updateMaxStudents').value;

    // Find adviser name
    const adviser = mockData.advisers.find(a => a.id == adviserId);

    // Update section in cache
    const sections = mockData.sectionsCache[mockData.currentProgram] || [];
    const sectionIndex = sections.findIndex(s => s.id == mockData.currentSectionForUpdate.id);

    if (sectionIndex !== -1) {
        sections[sectionIndex].name = sectionName;
        sections[sectionIndex].adviser = adviser ? adviser.name : 'Unknown';
        sections[sectionIndex].adviserId = adviserId;
        sections[sectionIndex].location = `Bldg ${building} Room ${room}`;
        sections[sectionIndex].maxStudents = maxStudents;
    }

    showNotification(`Section "${sectionName}" updated successfully!`, 'success');
    loadSections(mockData.currentProgram);
    closeUpdateSectionModal();
}

function updateSection(sectionId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    toggleDropdown(sectionId);
    setTimeout(() => {
        openUpdateSectionModal(sectionId);
    }, 150);
}

function deleteSection(sectionId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    toggleDropdown(sectionId);

    setTimeout(() => {
        if (confirm("Are you sure you want to delete this section? This action cannot be undone.")) {
            const sections = mockData.sectionsCache[mockData.currentProgram] || [];
            const sectionIndex = sections.findIndex(s => s.id == sectionId);

            if (sectionIndex !== -1) {
                const sectionName = sections[sectionIndex].name;
                sections.splice(sectionIndex, 1);
                showNotification(`Section "${sectionName}" deleted successfully!`, 'success');
                loadSections(mockData.currentProgram);
            }
        }
    }, 150);
}

// Manage Subjects Functions
function switchSubjectProgram(program) {
    mockData.currentSubjectProgram = program;
    updateSubjectProgramTabs(program);
    loadSubjectsForProgram(program);
    cancelSubjectForm();
}

function updateSubjectProgramTabs(program) {
    document.querySelectorAll('.subject-tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const targetTab = document.querySelector(`.subject-tab-btn[data-subject-program="${program}"]`);
    if (targetTab) {
        targetTab.classList.add('active');
    }
}

function loadSubjectsForProgram(program) {
    const subjects = mockData.subjectsByProgram[program] || [];
    renderSubjectsTable(subjects);
}

function renderSubjectsTable(subjects) {
    const tableBody = document.getElementById('subjectsTableBody');

    if (subjects.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-8">
                    <div class="flex flex-col items-center gap-3">
                        <i class="fas fa-inbox text-4xl text-gray-300"></i>
                        <p class="text-gray-500 font-medium">No subjects found for ${mockData.currentSubjectProgram}</p>
                        <button class="gradient-bg text-white px-4 py-2 rounded-lg text-sm" onclick="openAddSubjectForm()">
                            <i class="fas fa-plus mr-2"></i>Add First Subject
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = subjects.map((subject, index) => `
        <tr>
            <td class="text-center font-semibold text-gray-600">${index + 1}</td>
            <td class="subject-name">${subject.name}</td>
            <td class="font-medium text-gray-600">${subject.code}</td>
            <td>
                <div class="flex gap-2 justify-center">
                    <button 
                        class="px-3 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-all duration-200 flex items-center gap-2"
                        onclick="editSubject(${subject.id})"
                        title="Edit Subject">
                        <i class="fas fa-edit"></i>
                        <span class="text-sm font-medium">Edit</span>
                    </button>
                    <button 
                        class="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-all duration-200 flex items-center gap-2"
                        onclick="deleteSubject(${subject.id})"
                        title="Delete Subject">
                        <i class="fas fa-trash"></i>
                        <span class="text-sm font-medium">Delete</span>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function openAddSubjectForm() {
    document.getElementById('subjectFormContainer').style.display = 'block';
    document.getElementById('subjectFormTitle').textContent = 'Add New Subject';
    document.getElementById('subjectForm').reset();
    document.getElementById('subjectId').value = '';
    document.getElementById('subjectProgramInput').value = mockData.currentSubjectProgram;
    mockData.currentEditingSubject = null;
}

function editSubject(subjectId) {
    let subject = null;
    for (const program in mockData.subjectsByProgram) {
        subject = mockData.subjectsByProgram[program].find(s => s.id === subjectId);
        if (subject) break;
    }

    if (!subject) {
        showNotification('Subject not found!', 'error');
        return;
    }

    mockData.currentEditingSubject = subject;

    document.getElementById('subjectFormContainer').style.display = 'block';
    document.getElementById('subjectFormTitle').textContent = 'Edit Subject';
    document.getElementById('subjectId').value = subject.id;
    document.getElementById('subjectProgramInput').value = subject.program;
    document.getElementById('subjectName').value = subject.name;
    document.getElementById('subjectCode').value = subject.code;
}

function deleteSubject(subjectId) {
    if (!confirm('Are you sure you want to delete this subject? This action cannot be undone.')) {
        return;
    }

    // Find and remove subject
    for (const program in mockData.subjectsByProgram) {
        const subjectIndex = mockData.subjectsByProgram[program].findIndex(s => s.id === subjectId);
        if (subjectIndex !== -1) {
            const subjectName = mockData.subjectsByProgram[program][subjectIndex].name;
            mockData.subjectsByProgram[program].splice(subjectIndex, 1);
            showNotification(`Subject "${subjectName}" deleted successfully!`, 'success');
            loadSubjectsForProgram(mockData.currentSubjectProgram);
            return;
        }
    }

    showNotification('Subject not found!', 'error');
}

function cancelSubjectForm() {
    document.getElementById('subjectFormContainer').style.display = 'none';
    document.getElementById('subjectForm').reset();
    mockData.currentEditingSubject = null;
}

function handleSubjectFormSubmit(event) {
    event.preventDefault();

    const subjectName = document.getElementById('subjectName').value;
    const subjectCode = document.getElementById('subjectCode').value;
    const subjectId = document.getElementById('subjectId').value;
    const isUpdate = !!subjectId;

    if (!subjectName || !subjectCode) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    if (isUpdate) {
        // Update existing subject
        let subjectFound = false;
        for (const program in mockData.subjectsByProgram) {
            const subjectIndex = mockData.subjectsByProgram[program].findIndex(s => s.id == subjectId);
            if (subjectIndex !== -1) {
                mockData.subjectsByProgram[program][subjectIndex].name = subjectName;
                mockData.subjectsByProgram[program][subjectIndex].code = subjectCode;
                subjectFound = true;
                break;
            }
        }

        if (subjectFound) {
            showNotification(`Subject "${subjectName}" updated successfully!`, 'success');
        }
    } else {
        // Add new subject
        if (!mockData.subjectsByProgram[mockData.currentSubjectProgram]) {
            mockData.subjectsByProgram[mockData.currentSubjectProgram] = [];
        }

        const newSubject = {
            id: Date.now(),
            name: subjectName,
            code: subjectCode,
            program: mockData.currentSubjectProgram
        };

        mockData.subjectsByProgram[mockData.currentSubjectProgram].push(newSubject);
        showNotification(`Subject "${subjectName}" added successfully!`, 'success');
    }

    loadSubjectsForProgram(mockData.currentSubjectProgram);
    cancelSubjectForm();
}

// Manage Programs Functions
function loadAllPrograms() {
    renderProgramsTable(mockData.programsCache);
}

function renderProgramsTable(programs) {
    const tableBody = document.getElementById('programsTableBody');

    if (programs.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-8">
                    <div class="flex flex-col items-center gap-3">
                        <i class="fas fa-inbox text-4xl text-gray-300"></i>
                        <p class="text-gray-500 font-medium">No programs found</p>
                        <button class="gradient-bg text-white px-4 py-2 rounded-lg text-sm" onclick="openAddProgramForm()">
                            <i class="fas fa-plus mr-2"></i>Add First Program
                        </button>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = programs.map((program, index) => `
        <tr>
            <td class="text-center font-semibold text-gray-600">${index + 1}</td>
            <td class="subject-name">${program.name}</td>
            <td class="text-gray-600 text-sm">${program.description || '<em class="text-gray-400">No description</em>'}</td>
            <td class="font-medium text-gray-700">${program.school_year.name}</td>
            <td class="text-center">
                <span class="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
                    ${program.section_count}
                </span>
            </td>
            <td class="text-center">
                ${program.is_active
                ? '<span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">Active</span>'
                : '<span class="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-semibold">Inactive</span>'
                }
            </td>
            <td>
                <div class="flex gap-2 justify-center">
                    <button 
                        class="px-3 py-2 ${program.is_active ? 'bg-yellow-100 text-yellow-600 hover:bg-yellow-200' : 'bg-green-100 text-green-600 hover:bg-green-200'} rounded-lg transition-all duration-200 flex items-center gap-2"
                        onclick="toggleProgramStatus(${program.id})"
                        title="${program.is_active ? 'Deactivate' : 'Activate'} Program">
                        <i class="fas fa-${program.is_active ? 'ban' : 'check-circle'}"></i>
                    </button>
                    <button 
                        class="px-3 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-all duration-200 flex items-center gap-2"
                        onclick="editProgram(${program.id})"
                        title="Edit Program">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button 
                        class="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-all duration-200 flex items-center gap-2"
                        onclick="deleteProgram(${program.id})"
                        title="Delete Program">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function openAddProgramForm() {
    document.getElementById('programFormContainer').style.display = 'block';
    document.getElementById('programFormTitle').textContent = 'Add New Program';
    document.getElementById('programForm').reset();
    document.getElementById('programId').value = '';
    document.getElementById('programIsActive').checked = true;
    mockData.currentEditingProgram = null;
}

function editProgram(programId) {
    const program = mockData.programsCache.find(p => p.id === programId);

    if (!program) {
        showNotification('Program not found!', 'error');
        return;
    }

    mockData.currentEditingProgram = program;

    document.getElementById('programFormContainer').style.display = 'block';
    document.getElementById('programFormTitle').textContent = 'Edit Program';
    document.getElementById('programId').value = program.id;
    document.getElementById('programName').value = program.name;
    document.getElementById('programDescription').value = program.description || '';
    document.getElementById('programIsActive').checked = program.is_active;

    setTimeout(() => {
        const yearSelect = document.getElementById('programSchoolYear');
        if (yearSelect) {
            yearSelect.value = program.school_year.name;
        }
    }, 100);
}

function deleteProgram(programId) {
    const program = mockData.programsCache.find(p => p.id === programId);

    if (!program) {
        showNotification('Program not found!', 'error');
        return;
    }

    if (!confirm(`Are you sure you want to delete the program "${program.name}"? This action cannot be undone.`)) {
        return;
    }

    const programIndex = mockData.programsCache.findIndex(p => p.id === programId);
    if (programIndex !== -1) {
        const programName = mockData.programsCache[programIndex].name;
        mockData.programsCache.splice(programIndex, 1);
        showNotification(`Program "${programName}" deleted successfully!`, 'success');
        loadAllPrograms();
    }
}

function toggleProgramStatus(programId) {
    const program = mockData.programsCache.find(p => p.id === programId);

    if (!program) {
        showNotification('Program not found!', 'error');
        return;
    }

    const action = program.is_active ? 'deactivate' : 'activate';
    const confirmMsg = program.is_active
        ? `Deactivating "${program.name}" will hide it from the system. Continue?`
        : `Activate program "${program.name}"?`;

    if (!confirm(confirmMsg)) {
        return;
    }

    program.is_active = !program.is_active;
    const status = program.is_active ? 'activated' : 'deactivated';
    showNotification(`Program "${program.name}" ${status} successfully!`, 'success');
    loadAllPrograms();
}

function cancelProgramForm() {
    document.getElementById('programFormContainer').style.display = 'none';
    document.getElementById('programForm').reset();
    mockData.currentEditingProgram = null;
}

function handleProgramFormSubmit(event) {
    event.preventDefault();

    const programName = document.getElementById('programName').value;
    const programDescription = document.getElementById('programDescription').value;
    const programSchoolYear = document.getElementById('programSchoolYear').value;
    const programIsActive = document.getElementById('programIsActive').checked;
    const programId = document.getElementById('programId').value;
    const isUpdate = !!programId;

    if (!programName || !programSchoolYear) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    if (isUpdate) {
        // Update existing program
        const programIndex = mockData.programsCache.findIndex(p => p.id == programId);
        if (programIndex !== -1) {
            mockData.programsCache[programIndex].name = programName.toUpperCase();
            mockData.programsCache[programIndex].description = programDescription;
            mockData.programsCache[programIndex].is_active = programIsActive;
            showNotification(`Program "${programName}" updated successfully!`, 'success');
        }
    } else {
        // Add new program
        const newProgram = {
            id: Date.now(),
            name: programName.toUpperCase(),
            description: programDescription,
            school_year: { name: programSchoolYear },
            section_count: 0,
            is_active: programIsActive
        };

        mockData.programsCache.push(newProgram);
        showNotification(`Program "${programName}" added successfully!`, 'success');
    }

    loadAllPrograms();
    cancelProgramForm();
}

// Utility Functions
function toggleDropdown(sectionId) {
    // Close all other dropdowns first
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        if (menu.id !== `dropdown-${sectionId}`) {
            menu.classList.add('hidden');
        }
    });

    // Toggle current dropdown
    const dropdown = document.getElementById(`dropdown-${sectionId}`);
    if (dropdown) {
        dropdown.classList.toggle('hidden');
        if (!dropdown.classList.contains('hidden')) {
            dropdown.classList.add('animate-dropdown');
        }
    }
}

function openSectionMasterlist(sectionId) {
    showNotification(`Opening masterlist for section ${sectionId}...`, 'info');
    window.location.href = "masterlist.html";
}

function showNotification(message, type = 'info') {
    const container = document.getElementById('notificationContainer');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `bg-white border-l-4 ${type === 'success' ? 'border-green-500' : type === 'error' ? 'border-red-500' : 'border-blue-500'} rounded-lg shadow-lg p-4 max-w-sm`;
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

// Make functions globally available
window.openAddSectionModal = openAddSectionModal;
window.openManageProgramsModal = openManageProgramsModal;
window.openManageSubjectsModal = openManageSubjectsModal;
window.closeAddSectionModal = closeAddSectionModal;
window.closeManageProgramsModal = closeManageProgramsModal;
window.closeManageSubjectsModal = closeManageSubjectsModal;
window.switchSubjectProgram = switchSubjectProgram;
window.openAddSubjectForm = openAddSubjectForm;
window.updateSection = updateSection;
window.deleteSection = deleteSection;
window.openSectionMasterlist = openSectionMasterlist;
window.editSubject = editSubject;
window.deleteSubject = deleteSubject;
window.cancelSubjectForm = cancelSubjectForm;
window.openAddProgramForm = openAddProgramForm;
window.editProgram = editProgram;
window.deleteProgram = deleteProgram;
window.toggleProgramStatus = toggleProgramStatus;
window.cancelProgramForm = cancelProgramForm;
window.toggleDropdown = toggleDropdown;

