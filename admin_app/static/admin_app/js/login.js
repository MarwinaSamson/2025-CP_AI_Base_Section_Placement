document.addEventListener('DOMContentLoaded', function () {
            const adminRoleBtn = document.getElementById('adminRoleBtn');
            const coordinatorRoleBtn = document.getElementById('coordinatorRoleBtn');
            const programField = document.getElementById('coordinatorProgramField');
            const loginTitle = document.getElementById('loginTitle');
            const loginSubtitle = document.getElementById('loginSubtitle');
            const loginButton = document.getElementById('loginButton');
            const loginForm = document.getElementById('loginForm');
            const programSelect = document.getElementById('programSelect');

            // Role selection
            coordinatorRoleBtn.addEventListener('click', function () {
                coordinatorRoleBtn.classList.add('bg-white', 'text-coordinator', 'shadow-sm');
                coordinatorRoleBtn.classList.remove('text-gray-600');
                adminRoleBtn.classList.remove('bg-white', 'text-primary', 'shadow-sm');
                adminRoleBtn.classList.add('text-gray-600');

                programField.classList.remove('hidden');
                loginTitle.textContent = 'Coordinator Login';
                loginSubtitle.textContent = 'Please select your program and enter credentials';
                loginButton.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1">
                        </path>
                    </svg>
                    Login as Coordinator
                `;
                loginButton.classList.remove('from-primary', 'to-primary-dark', 'hover:from-primary-dark', 'hover:to-primary');
                loginButton.classList.add('from-coordinator', 'to-coordinator-dark', 'hover:from-coordinator-dark', 'hover:to-coordinator');
            });

            adminRoleBtn.addEventListener('click', function () {
                adminRoleBtn.classList.add('bg-white', 'text-primary', 'shadow-sm');
                adminRoleBtn.classList.remove('text-gray-600');
                coordinatorRoleBtn.classList.remove('bg-white', 'text-coordinator', 'shadow-sm');
                coordinatorRoleBtn.classList.add('text-gray-600');

                programField.classList.add('hidden');
                loginTitle.textContent = 'Admin Login';
                loginSubtitle.textContent = 'Please enter your credentials to continue';
                loginButton.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1">
                        </path>
                    </svg>
                    Login as Admin
                `;
                loginButton.classList.remove('from-coordinator', 'to-coordinator-dark', 'hover:from-coordinator-dark', 'hover:to-coordinator');
                loginButton.classList.add('from-primary', 'to-primary-dark', 'hover:from-primary-dark', 'hover:to-primary');
            });

            // Login form submission
            loginForm.addEventListener('submit', function (e) {
                e.preventDefault();

                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                const role = adminRoleBtn.classList.contains('bg-white') ? 'admin' : 'coordinator';
                const program = role === 'coordinator' ? programSelect.value : null;

                if (role === 'coordinator' && !program) {
                    showModal('Error', 'Please select a program for coordinator login.');
                    return;
                }

                // Simulate login (in real app, this would be an API call)
                if (username && password) {
                    // Save login state so dashboard.js accepts it
                    localStorage.setItem('isLoggedIn', 'true');
                    localStorage.setItem('username', username);        // Used in logout modal
                    localStorage.setItem('loginTime', new Date().toISOString()); // For session time


                    let redirectPath;
                    if (role === 'admin') {
                        redirectPath = 'dashboard.html';
                    } else {
                        redirectPath = '../../coordinator/templates/dashboard.html';  // coordinator path
                    }

                    window.location.href = redirectPath;
                } else {
                    showModal('Error', 'Please enter both username and password.');
                }
            });

            // Password visibility toggle
            document.getElementById('togglePassword').addEventListener('click', function () {
                const passwordInput = document.getElementById('password');
                const eyeIcon = document.getElementById('eyeIcon');

                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L6.59 6.59m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"></path>`;
                } else {
                    passwordInput.type = 'password';
                    eyeIcon.innerHTML = `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>`;
                }
            });

            function showModal(title, message) {
                document.getElementById('modalTitle').textContent = title;
                document.getElementById('modalMessage').textContent = message;
                document.getElementById('loginModal').classList.remove('hidden');
            }

            window.closeModal = function () {
                document.getElementById('loginModal').classList.add('hidden');
            };
        });