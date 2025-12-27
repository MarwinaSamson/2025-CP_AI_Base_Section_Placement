document.addEventListener('DOMContentLoaded', function () {
    const loginForm = document.getElementById('loginForm');
    const adminRoleBtn = document.getElementById('adminRoleBtn');
    const coordinatorRoleBtn = document.getElementById('coordinatorRoleBtn');
    const coordinatorProgramField = document.getElementById('coordinatorProgramField');
    const loginTitle = document.getElementById('loginTitle');
    const loginButton = document.getElementById('loginButton');
    
    let selectedRole = 'admin';

    // Role selection
    adminRoleBtn.addEventListener('click', function () {
        selectedRole = 'admin';
        adminRoleBtn.classList.add('bg-white', 'text-primary', 'shadow-sm');
        adminRoleBtn.classList.remove('text-gray-600');
        coordinatorRoleBtn.classList.remove('bg-white', 'text-primary', 'shadow-sm');
        coordinatorRoleBtn.classList.add('text-gray-600');
        coordinatorProgramField.classList.add('hidden');
        loginTitle.textContent = 'Admin Login';
        loginButton.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg> Login as Admin';
    });

    coordinatorRoleBtn.addEventListener('click', function () {
        selectedRole = 'coordinator';
        coordinatorRoleBtn.classList.add('bg-white', 'text-primary', 'shadow-sm');
        coordinatorRoleBtn.classList.remove('text-gray-600');
        adminRoleBtn.classList.remove('bg-white', 'text-primary', 'shadow-sm');
        adminRoleBtn.classList.add('text-gray-600');
        coordinatorProgramField.classList.remove('hidden');
        loginTitle.textContent = 'Coordinator Login';
        loginButton.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"></path></svg> Login as Coordinator';
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

    // Form submission - CRITICAL: Prevent default form submission
    loginForm.addEventListener('submit', function (e) {
        e.preventDefault(); // PREVENT DEFAULT FORM SUBMISSION
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const program = document.getElementById('programSelect').value;

        // Validation
        if (!username || !password) {
            showModal('Error', 'Please enter both username and password.');
            return;
        }

        if (selectedRole === 'coordinator' && !program) {
            showModal('Error', 'Please select a program.');
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
                'X-Requested-With': 'XMLHttpRequest' // Helps Django identify AJAX requests
            },
            body: formData,
            credentials: 'same-origin' // Include cookies
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || 'Login failed');
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showModal('Success', data.message, true);
                
                // Redirect after short delay
                setTimeout(() => {
                    console.log('Redirecting to:', data.redirect_url); // Debug log
                    window.location.href = data.redirect_url;
                }, 1000);
            } else {
                showModal('Error', data.message);
                loginButton.disabled = false;
                loginButton.innerHTML = originalButtonContent;
            }
        })
        .catch(error => {
            console.error('Login error:', error); // Debug log
            showModal('Error', error.message || 'An error occurred. Please try again.');
            loginButton.disabled = false;
            loginButton.innerHTML = originalButtonContent;
        });
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
        }, 1500);
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