document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    const adminRoleBtn = document.getElementById('adminRoleBtn');
    const coordinatorRoleBtn = document.getElementById('coordinatorRoleBtn');
    const coordinatorProgramField = document.getElementById('coordinatorProgramField');
    const programSelect = document.getElementById('programSelect');
    const loginTitle = document.getElementById('loginTitle');
    const loginButton = document.getElementById('loginButton');
    
    let selectedRole = 'admin';

    // Role selection - Admin
    adminRoleBtn.addEventListener('click', function () {
        selectedRole = 'admin';
        adminRoleBtn.classList.add('bg-white', 'text-primary', 'shadow-sm');
        adminRoleBtn.classList.remove('text-gray-600');
        coordinatorRoleBtn.classList.remove('bg-white', 'text-primary', 'shadow-sm');
        coordinatorRoleBtn.classList.add('text-gray-600');
        coordinatorProgramField.classList.add('hidden');
        
        // Clear program selection
        programSelect.value = '';
        programSelect.removeAttribute('required');
        
        loginTitle.textContent = 'Admin Login';
        loginButton.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg> Login as Admin';
        loginButton.classList.remove('from-coordinator', 'to-coordinator-dark');
        loginButton.classList.add('from-primary', 'to-primary-dark');
    });

    // Role selection - Coordinator
    coordinatorRoleBtn.addEventListener('click', function () {
        selectedRole = 'coordinator';
        coordinatorRoleBtn.classList.add('bg-white', 'text-coordinator', 'shadow-sm');
        coordinatorRoleBtn.classList.remove('text-gray-600');
        adminRoleBtn.classList.remove('bg-white', 'text-primary', 'shadow-sm');
        adminRoleBtn.classList.add('text-gray-600');
        coordinatorProgramField.classList.remove('hidden');
        
        // Make program required
        programSelect.setAttribute('required', 'required');
        
        loginTitle.textContent = 'Coordinator Login';
        loginButton.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg> Login as Coordinator';
        loginButton.classList.remove('from-primary', 'to-primary-dark');
        loginButton.classList.add('from-coordinator', 'to-coordinator-dark');
    });

    // Password toggle
    const togglePassword = document.getElementById('togglePassword');
    const passwordInput = document.getElementById('password');
    
    if (togglePassword) {
        togglePassword.addEventListener('click', function () {
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
        });
    }

    // Form submission
    loginForm.addEventListener('submit', function (e) {
        e.preventDefault(); // Prevent default form submission
        
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const program = programSelect.value.trim();

        console.log('Login attempt:', {
            username: username,
            role: selectedRole,
            program: program || 'N/A'
        });

        // Validation
        if (!username || !password) {
            showModal('Validation Error', 'Please enter both username and password.');
            return;
        }

        if (selectedRole === 'coordinator' && !program) {
            showModal('Validation Error', 'Please select a program to continue.');
            // Highlight the program field
            programSelect.classList.add('border-red-500');
            setTimeout(() => {
                programSelect.classList.remove('border-red-500');
            }, 3000);
            return;
        }

        // Show loading state
        loginButton.disabled = true;
        const originalButtonContent = loginButton.innerHTML;
        loginButton.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Logging in...';

        // Prepare form data
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        formData.append('user_type', selectedRole);
        if (selectedRole === 'coordinator') {
            formData.append('program', program);
        }

        // Get CSRF token
        const csrftoken = getCookie('csrftoken');

        // Send AJAX request
        fetch(window.location.href, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Login failed');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Login response:', data);
            if (data.success) {
                showModal('Success', data.message, true);
                
                // Redirect after short delay
                setTimeout(() => {
                    console.log('Redirecting to:', data.redirect_url);
                    window.location.href = data.redirect_url;
                }, 1500);
            } else {
                showModal('Login Failed', data.message);
                loginButton.disabled = false;
                loginButton.innerHTML = originalButtonContent;
            }
        })
        .catch(error => {
            console.error('Login error:', error);
            showModal('Error', error.message || 'An error occurred. Please try again.');
            loginButton.disabled = false;
            loginButton.innerHTML = originalButtonContent;
        });
    });

    // Add visual feedback to program select
    programSelect.addEventListener('change', function() {
        if (this.value) {
            this.classList.remove('border-red-500');
            this.classList.add('border-green-500');
            setTimeout(() => {
                this.classList.remove('border-green-500');
            }, 1000);
        }
    });
});

function showModal(title, message, isSuccess = false) {
    const modal = document.getElementById('loginModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalMessage = document.getElementById('modalMessage');
    
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    modal.classList.remove('hidden');
    
    // Auto-close success modals
    if (isSuccess) {
        setTimeout(() => {
            closeModal();
        }, 2000);
    }
}

function closeModal() {
    const modal = document.getElementById('loginModal');
    modal.classList.add('hidden');
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}