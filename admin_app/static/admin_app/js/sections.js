const API_BASE = '/admin-portal/api';

const state = {
    programs: [],
    teachers: [],
    sections: [],
    subjects: {},
    buildings: [],
    currentProgram: null,
    currentSectionForUpdate: null,
    currentSubjectProgram: null,
};

document.addEventListener('DOMContentLoaded', () => {
    initializePage();
});

async function initializePage() {
    const urlParams = new URLSearchParams(window.location.search);
    const requestedProgram = (urlParams.get('program') || '').toUpperCase();

    try {
        await bootstrapData(requestedProgram);
        setupEventListeners();
        setupLogoutModalEvents();
        showNotification('Sections loaded', 'success');
    } catch (error) {
        console.error('Initialization error:', error);
        showNotification(error.message || 'Failed to load data. Please refresh.', 'error');
    }
}

async function bootstrapData(requestedProgram) {
    const [programs, teachers, buildings] = await Promise.all([
        fetchPrograms(),
        fetchTeachers(),
        fetchBuildings()
    ]);

    if (!programs.length) {
        throw new Error('No active programs found. Please add a program first.');
    }

    state.programs = programs;
    state.teachers = teachers;
    state.buildings = buildings;
    state.currentProgram = programs.some(p => p.code === requestedProgram)
        ? requestedProgram
        : programs[0].code;

    renderProgramTabs();
    updateActiveTab(state.currentProgram);
    populateAdviserSelects();
    populateBuildingSelects();

    await Promise.all([
        loadSections(state.currentProgram),
        loadSubjectsForProgram(state.currentProgram, true)
    ]);
}

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

// ============================= API HELPERS =============================

async function apiFetch(path, options = {}) {
    const opts = { ...options };
    opts.method = opts.method || 'GET';
    opts.headers = opts.headers || {};

    if (!['GET', 'HEAD', 'OPTIONS'].includes(opts.method.toUpperCase())) {
        opts.headers['Content-Type'] = 'application/json';
        opts.headers['X-CSRFToken'] = getCSRFToken();
    }

    opts.credentials = 'same-origin';

    const response = await fetch(`${API_BASE}${path}`, opts);
    const contentType = response.headers.get('content-type') || '';
    const isJson = contentType.includes('application/json');
    const payload = isJson ? await response.json().catch(() => ({})) : {};

    if (!response.ok) {
        const message = payload.error || payload.detail || `Request failed (${response.status})`;
        throw new Error(message);
    }

    return payload;
}

function getCSRFToken() {
    const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookies = decodedCookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i];
        while (c.charAt(0) === ' ') c = c.substring(1);
        if (c.indexOf(name) === 0) return c.substring(name.length, c.length);
    }
    return '';
}

async function fetchPrograms() {
    const data = await apiFetch('/programs/');
    return data.programs || [];
}

async function fetchTeachers() {
    const data = await apiFetch('/teachers/');
    return data.teachers || [];
}

async function fetchBuildings() {
    const data = await apiFetch('/buildings/');
    return data.buildings || [];
}

async function fetchSections(programCode) {
    const data = await apiFetch(`/sections/?program=${encodeURIComponent(programCode)}`);
    return data.sections || [];
}

async function fetchSubjects(programCode) {
    const qs = programCode ? `?program=${encodeURIComponent(programCode)}` : '';
    const data = await apiFetch(`/subjects/${qs}`);
    return data.subjects || [];
}

// ============================= PROGRAM TABS =============================

function renderProgramTabs() {
    const firstTab = document.querySelector('.tab-btn');
    const container = firstTab ? firstTab.parentElement : null;
    if (!container) return;

    container.innerHTML = '';

    state.programs.forEach(program => {
        const btn = document.createElement('button');
        btn.className = 'tab-btn px-6 py-3 border-2 border-gray-200 bg-white text-gray-600 rounded-xl cursor-pointer font-semibold transition-all duration-300 hover:bg-primary hover:text-white hover:border-primary hover:shadow-lg hover:scale-105';
        btn.dataset.program = program.code;
        btn.innerHTML = `<i class="fas fa-graduation-cap mr-2"></i>${program.code}`;
        btn.addEventListener('click', () => switchProgram(program.code));
        container.appendChild(btn);
    });
}

async function switchProgram(programCode) {
    state.currentProgram = programCode;
    updateActiveTab(programCode);
    await loadSections(programCode);
    window.history.pushState({}, '', `${window.location.pathname}?program=${programCode}`);
}

function updateActiveTab(programCode) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.program === programCode) {
            btn.classList.add('active');
        }
    });
}

// ============================= SECTIONS =============================

async function loadSections(programCode) {
    const sectionsGrid = document.getElementById('sectionsGrid');
    if (sectionsGrid) sectionsGrid.innerHTML = '<div class="col-span-full text-center py-8 text-gray-500">Loading sections...</div>';

    try {
        state.sections = await fetchSections(programCode);
        renderSectionsGrid();
    } catch (error) {
        console.error('Load sections error:', error);
        showNotification(error.message || 'Failed to load sections', 'error');
        if (sectionsGrid) sectionsGrid.innerHTML = '<div class="col-span-full text-center py-8 text-red-500">Unable to load sections.</div>';
    }
}

function renderSectionsGrid() {
    const sectionsGrid = document.getElementById('sectionsGrid');
    if (!sectionsGrid) return;

    if (!state.sections.length) {
        sectionsGrid.innerHTML = `
            <div class="col-span-full text-center py-16">
                <div class="w-24 h-24 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full flex items-center justify-center mx-auto mb-6">
                    <i class="fas fa-inbox text-3xl text-gray-400"></i>
                </div>
                <h3 class="text-xl font-semibold text-gray-600 mb-2">No Sections Found</h3>
                <p class="text-gray-500 mb-4">No sections available for ${state.currentProgram} program.</p>
                <button class="gradient-bg text-white px-6 py-3 rounded-xl hover:shadow-lg transform hover:scale-105 transition-all duration-300 font-semibold" onclick="openAddSectionModal()">
                    <i class="fas fa-plus-circle mr-2"></i>Create First Section
                </button>
            </div>`;
        return;
    }

    sectionsGrid.innerHTML = state.sections.map(section => {
        const location = section.building || section.room ? `Bldg ${section.building || ''} Room ${section.room || ''}`.trim() : 'Not set';
        const students = section.current_students || 0;
        const max = section.max_students || 0;
        const percentage = max > 0 ? Math.min(100, Math.round((students / max) * 100)) : 0;
        return `
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
                                ${section.adviser_name || 'No adviser assigned'}
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
                        <span class="text-sm font-semibold text-gray-800">${location}</span>
                    </div>
                    <div class="flex items-center justify-between p-3 bg-gradient-to-r from-red-50 to-pink-50 rounded-lg border border-red-100">
                        <div class="flex items-center gap-2">
                            <i class="fas fa-users text-red-400"></i>
                            <span class="text-sm font-medium text-red-600">Students</span>
                        </div>
                        <div class="text-right">
                            <div class="text-lg font-bold text-red-600">${students}/${max}</div>
                            <div class="w-24 h-2 bg-red-200 rounded-full overflow-hidden">
                                <div class="h-full bg-red-500 rounded-full" style="width: ${percentage}%"></div>
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
        </div>`;
    }).join('');
}

function findSectionById(sectionId) {
    return state.sections.find(s => String(s.id) === String(sectionId)) || null;
}

async function handleAddSection(event) {
    event.preventDefault();

    const sectionName = document.getElementById('sectionName').value.trim();
    const adviserId = document.getElementById('adviserName').value || null;
    const buildingId = document.getElementById('buildingNumber').value;
    const roomId = document.getElementById('roomNumber').value;
    const maxStudents = Number(document.getElementById('maxStudents').value) || 40;

    if (!sectionName || !buildingId || !roomId) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    try {
        await apiFetch('/sections/add/', {
            method: 'POST',
            body: JSON.stringify({
                name: sectionName,
                adviser: adviserId,
                building: buildingId,
                room: roomId,
                max_students: maxStudents,
                program: state.currentProgram,
            })
        });
        showNotification(`Section "${sectionName}" added successfully`, 'success');
        closeAddSectionModal();
        await Promise.all([
            loadSections(state.currentProgram),
            fetchTeachers().then(teachers => {
                state.teachers = teachers;
                populateAdviserSelects();
            })
        ]);
    } catch (error) {
        console.error('Add section error:', error);
        showNotification(error.message || 'Failed to add section', 'error');
    }
}

async function handleUpdateSection(event) {
    event.preventDefault();
    if (!state.currentSectionForUpdate) return;

    const sectionId = state.currentSectionForUpdate.id;
    const sectionName = document.getElementById('updateSectionName').value.trim();
    const adviserId = document.getElementById('updateAdviserName').value || null;
    const buildingId = document.getElementById('updateBuilding').value;
    const roomId = document.getElementById('updateRoom').value;
    const maxStudents = Number(document.getElementById('updateMaxStudents').value) || 40;

    if (!sectionName || !buildingId || !roomId) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    try {
        await apiFetch(`/sections/${sectionId}/update/`, {
            method: 'PUT',
            body: JSON.stringify({
                name: sectionName,
                adviser: adviserId,
                building: buildingId,
                room: roomId,
                max_students: maxStudents,
            })
        });
        showNotification(`Section "${sectionName}" updated`, 'success');
        closeUpdateSectionModal();
        await Promise.all([
            loadSections(state.currentProgram),
            fetchTeachers().then(teachers => {
                state.teachers = teachers;
                populateAdviserSelects();
            })
        ]);
    } catch (error) {
        console.error('Update section error:', error);
        showNotification(error.message || 'Failed to update section', 'error');
    }
}

function updateSection(sectionId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    toggleDropdown(sectionId);
    setTimeout(() => openUpdateSectionModal(sectionId), 120);
}

async function deleteSection(sectionId, event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    toggleDropdown(sectionId);

    setTimeout(async () => {
        if (!confirm('Delete this section?')) return;
        try {
            await apiFetch(`/sections/${sectionId}/delete/`, { method: 'DELETE' });
            showNotification('Section deleted', 'success');
            await Promise.all([
                loadSections(state.currentProgram),
                fetchTeachers().then(teachers => {
                    state.teachers = teachers;
                    populateAdviserSelects();
                })
            ]);
        } catch (error) {
            console.error('Delete section error:', error);
            showNotification(error.message || 'Failed to delete section', 'error');
        }
    }, 120);
}

function openAddSectionModal() {
    const modal = document.getElementById('addSectionModal');
    if (!modal) return;
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
    populateAdviserSelects();
    populateBuildingSelects();
}

function closeAddSectionModal() {
    const modal = document.getElementById('addSectionModal');
    if (!modal) return;
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    const form = document.getElementById('addSectionForm');
    if (form) form.reset();
}

function openUpdateSectionModal(sectionId) {
    const section = findSectionById(sectionId);
    if (!section) return;
    state.currentSectionForUpdate = section;

    populateAdviserSelects(section.adviser_id);
    populateBuildingSelects();

    document.getElementById('updateSectionName').value = section.name || '';
    document.getElementById('updateAdviserName').value = section.adviser_id || '';
    document.getElementById('updateMaxStudents').value = section.max_students || 40;

    // Find building and room IDs
    if (section.building) {
        const building = state.buildings.find(b => b.name === section.building);
        if (building) {
            document.getElementById('updateBuilding').value = building.id;
            populateRoomSelectById('updateRoom', building.id);
            setTimeout(() => {
                const room = building.rooms.find(r => r.room_number === section.room);
                if (room) {
                    document.getElementById('updateRoom').value = room.id;
                }
            }, 50);
        }
    }

    const modal = document.getElementById('updateSectionModal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.classList.add('modal-open');
    }
}

function closeUpdateSectionModal() {
    const modal = document.getElementById('updateSectionModal');
    if (!modal) return;
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    const form = document.getElementById('updateSectionForm');
    if (form) form.reset();
    state.currentSectionForUpdate = null;
}

function closeAllModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
    document.body.classList.remove('modal-open');
}

function populateAdviserSelects(currentAdviserId = null) {
    const selects = [document.getElementById('adviserName'), document.getElementById('updateAdviserName')];
    selects.forEach(select => {
        if (!select) return;
        select.innerHTML = '<option value="">Select Adviser</option>';
        state.teachers.forEach(teacher => {
            const isCurrent = currentAdviserId && String(teacher.id) === String(currentAdviserId);
            const isAvailable = !teacher.is_adviser || isCurrent;
            if (!isAvailable) return; // Only list teachers not yet advisers (unless editing current adviser)

            const option = document.createElement('option');
            option.value = teacher.id;
            option.textContent = teacher.name;

            if (isCurrent) {
                option.selected = true;
            }

            select.appendChild(option);
        });
    });
}

function populateBuildingSelects() {
    const selects = [document.getElementById('buildingNumber'), document.getElementById('updateBuilding')];
    selects.forEach(select => {
        if (!select) return;
        select.innerHTML = '<option value="">Select Building</option>';
        state.buildings.forEach(building => {
            const option = document.createElement('option');
            option.value = building.id;
            option.textContent = building.name;
            select.appendChild(option);
        });
    });
}

function populateRoomSelectById(roomSelectId, buildingId) {
    const roomSelect = document.getElementById(roomSelectId);
    if (!roomSelect) return;
    roomSelect.innerHTML = '<option value="">Select Room</option>';
    
    const building = state.buildings.find(b => String(b.id) === String(buildingId));
    if (!building) return;
    
    building.rooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room.id;
        option.textContent = room.room_number;
        roomSelect.appendChild(option);
    });
}

// ============================= SUBJECTS =============================

async function loadSubjectsForProgram(programCode, force = false) {
    state.currentSubjectProgram = programCode;
    if (force || !state.subjects[programCode]) {
        try {
            state.subjects[programCode] = await fetchSubjects(programCode);
        } catch (error) {
            console.error('Load subjects error:', error);
            showNotification(error.message || 'Failed to load subjects', 'error');
            state.subjects[programCode] = [];
        }
    }
    renderSubjectsTable(state.subjects[programCode]);
}

function renderSubjectsTable(subjects) {
    const tableBody = document.getElementById('subjectsTableBody');
    if (!tableBody) return;

    if (!subjects || !subjects.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center py-8">
                    <div class="flex flex-col items-center gap-3">
                        <i class="fas fa-inbox text-4xl text-gray-300"></i>
                        <p class="text-gray-500 font-medium">No subjects found for ${state.currentSubjectProgram}</p>
                        <button class="gradient-bg text-white px-4 py-2 rounded-lg text-sm" onclick="openAddSubjectForm()">
                            <i class="fas fa-plus mr-2"></i>Add First Subject
                        </button>
                    </div>
                </td>
            </tr>`;
        return;
    }

    tableBody.innerHTML = subjects.map((subject, index) => `
        <tr>
            <td class="text-center font-semibold text-gray-600">${index + 1}</td>
            <td class="subject-name">${subject.name}</td>
            <td class="font-medium text-gray-600">${subject.code}</td>
            <td>
                <div class="flex gap-2 justify-center">
                    <button class="px-3 py-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-all duration-200 flex items-center gap-2" onclick="editSubject(${subject.id})" title="Edit Subject">
                        <i class="fas fa-edit"></i>
                        <span class="text-sm font-medium">Edit</span>
                    </button>
                    <button class="px-3 py-2 bg-red-100 text-red-600 rounded-lg hover:bg-red-200 transition-all duration-200 flex items-center gap-2" onclick="deleteSubject(${subject.id})" title="Delete Subject">
                        <i class="fas fa-trash"></i>
                        <span class="text-sm font-medium">Delete</span>
                    </button>
                </div>
            </td>
        </tr>`).join('');
}

function switchSubjectProgram(program) {
    loadSubjectsForProgram(program, true);
    updateSubjectProgramTabs(program);
    cancelSubjectForm();
}

function updateSubjectProgramTabs(program) {
    document.querySelectorAll('.subject-tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.subjectProgram === program) btn.classList.add('active');
    });
}

function openManageSubjectsModal() {
    const modal = document.getElementById('manageSubjectsModal');
    if (!modal) return;
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
    const programToLoad = state.currentProgram || (state.programs[0] && state.programs[0].code);
    if (programToLoad) {
        updateSubjectProgramTabs(programToLoad);
        loadSubjectsForProgram(programToLoad, true);
    }
    cancelSubjectForm();
}

function closeManageSubjectsModal() {
    const modal = document.getElementById('manageSubjectsModal');
    if (!modal) return;
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    cancelSubjectForm();
}

function openAddSubjectForm() {
    const formContainer = document.getElementById('subjectFormContainer');
    const form = document.getElementById('subjectForm');
    if (!formContainer || !form) return;
    formContainer.style.display = 'block';
    document.getElementById('subjectFormTitle').textContent = 'Add New Subject';
    form.reset();
    document.getElementById('subjectId').value = '';
    document.getElementById('subjectProgramInput').value = state.currentSubjectProgram;
}

function editSubject(subjectId) {
    const subjects = state.subjects[state.currentSubjectProgram] || [];
    const subject = subjects.find(s => String(s.id) === String(subjectId));
    if (!subject) {
        showNotification('Subject not found', 'error');
        return;
    }

    const formContainer = document.getElementById('subjectFormContainer');
    const form = document.getElementById('subjectForm');
    if (!formContainer || !form) return;

    formContainer.style.display = 'block';
    document.getElementById('subjectFormTitle').textContent = 'Edit Subject';
    document.getElementById('subjectId').value = subject.id;
    document.getElementById('subjectProgramInput').value = subject.program_code;
    document.getElementById('subjectName').value = subject.name;
    document.getElementById('subjectCode').value = subject.code;
}

async function deleteSubject(subjectId) {
    if (!confirm('Delete this subject?')) return;
    try {
        await apiFetch(`/subjects/${subjectId}/delete/`, { method: 'DELETE' });
        showNotification('Subject deleted', 'success');
        await loadSubjectsForProgram(state.currentSubjectProgram, true);
    } catch (error) {
        console.error('Delete subject error:', error);
        showNotification(error.message || 'Failed to delete subject', 'error');
    }
}

function cancelSubjectForm() {
    const formContainer = document.getElementById('subjectFormContainer');
    const form = document.getElementById('subjectForm');
    if (formContainer) formContainer.style.display = 'none';
    if (form) form.reset();
}

async function handleSubjectFormSubmit(event) {
    event.preventDefault();
    const subjectName = document.getElementById('subjectName').value.trim();
    const subjectCode = document.getElementById('subjectCode').value.trim().toUpperCase();
    const subjectId = document.getElementById('subjectId').value;
    const programCode = document.getElementById('subjectProgramInput').value || state.currentSubjectProgram;

    if (!subjectName || !subjectCode) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }

    const payload = { name: subjectName, code: subjectCode, program: programCode };
    try {
        if (subjectId) {
            await apiFetch(`/subjects/${subjectId}/update/`, { method: 'PUT', body: JSON.stringify(payload) });
            showNotification('Subject updated', 'success');
        } else {
            await apiFetch('/subjects/add/', { method: 'POST', body: JSON.stringify(payload) });
            showNotification('Subject added', 'success');
        }
        await loadSubjectsForProgram(programCode, true);
        cancelSubjectForm();
    } catch (error) {
        console.error('Subject save error:', error);
        showNotification(error.message || 'Failed to save subject', 'error');
    }
}

// ============================= PROGRAMS (READ-ONLY) =============================

function loadAllPrograms() {
    renderProgramsTable(state.programs);
}

function renderProgramsTable(programs) {
    const tableBody = document.getElementById('programsTableBody');
    if (!tableBody) return;

    if (!programs.length) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center py-8">
                    <div class="flex flex-col items-center gap-3">
                        <i class="fas fa-inbox text-4xl text-gray-300"></i>
                        <p class="text-gray-500 font-medium">No programs found</p>
                    </div>
                </td>
            </tr>`;
        return;
    }

    tableBody.innerHTML = programs.map((program, index) => `
        <tr>
            <td class="text-center font-semibold text-gray-600">${index + 1}</td>
            <td class="subject-name">${program.code}</td>
            <td class="text-gray-600 text-sm">${program.description || '<em class="text-gray-400">No description</em>'}</td>
            <td class="font-medium text-gray-700">${program.name || program.code}</td>
            <td class="text-center">—</td>
            <td class="text-center">
                <span class="px-3 py-1 ${true ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'} rounded-full text-xs font-semibold">Active</span>
            </td>
            <td class="text-center text-xs text-gray-400">Managed in backend</td>
        </tr>`).join('');
}

function openManageProgramsModal() {
    const modal = document.getElementById('manageProgramsModal');
    if (!modal) return;
    modal.style.display = 'flex';
    document.body.classList.add('modal-open');
    loadAllPrograms();
    cancelProgramForm();
}

function closeManageProgramsModal() {
    const modal = document.getElementById('manageProgramsModal');
    if (!modal) return;
    modal.style.display = 'none';
    document.body.classList.remove('modal-open');
    cancelProgramForm();
}

function openAddProgramForm() {
    showNotification('Program management is handled in the backend.', 'info');
}

function editProgram() {
    showNotification('Program management is handled in the backend.', 'info');
}

function deleteProgram() {
    showNotification('Program management is handled in the backend.', 'info');
}

function toggleProgramStatus() {
    showNotification('Program management is handled in the backend.', 'info');
}

function cancelProgramForm() {
    const formContainer = document.getElementById('programFormContainer');
    const form = document.getElementById('programForm');
    if (formContainer) formContainer.style.display = 'none';
    if (form) form.reset();
}

function handleProgramFormSubmit(event) {
    event.preventDefault();
    showNotification('Program management is handled in the backend.', 'info');
}

// ============================= UTILITIES =============================

function toggleDropdown(sectionId) {
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        if (menu.id !== `dropdown-${sectionId}`) menu.classList.add('hidden');
    });
    const dropdown = document.getElementById(`dropdown-${sectionId}`);
    if (dropdown) dropdown.classList.toggle('hidden');
}

function openSectionMasterlist(sectionId) {
    window.location.href = `/admin-portal/masterlist/${sectionId}/`;
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
        </div>`;

    container.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}

// ============================= LOGOUT MODAL =============================

function setupLogoutModalEvents() {
    const modal = document.getElementById('logoutModal');
    if (!modal) return;

    document.addEventListener('click', function (e) {
        if (e.target.closest('a[href="logout.html"]')) {
            e.preventDefault();
            e.stopPropagation();
            const currentUser = localStorage.getItem('username') || 'Administrator';
            const loginTime = localStorage.getItem('loginTime');
            const modalUserElement = document.getElementById('modalCurrentUser');
            const modalSessionElement = document.getElementById('modalSessionTime');
            if (modalUserElement) modalUserElement.textContent = currentUser;
            if (modalSessionElement && loginTime) {
                const sessionDate = new Date(loginTime);
                modalSessionElement.textContent = sessionDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
            } else if (modalSessionElement) {
                modalSessionElement.textContent = 'Just now';
            }
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    });

    const closeBtn = document.getElementById('closeLogoutModal');
    if (closeBtn) closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    });

    const cancelBtn = document.getElementById('cancelLogoutBtn');
    if (cancelBtn) cancelBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
        document.body.style.overflow = 'auto';
    });

    const logoutBtn = document.getElementById('confirmLogoutBtn');
    if (logoutBtn) logoutBtn.addEventListener('click', () => {
        const originalText = logoutBtn.innerHTML;
        logoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging out...';
        logoutBtn.disabled = true;
        showNotification('Logging out...', 'info');
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('username');
        localStorage.removeItem('loginTime');
        setTimeout(() => {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
            logoutBtn.innerHTML = originalText;
            logoutBtn.disabled = false;
            window.location.href = '/admin-portal/logout/';
        }, 1000);
    });

    modal.addEventListener('click', function (e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
}

// ============================= EXPORTS =============================

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