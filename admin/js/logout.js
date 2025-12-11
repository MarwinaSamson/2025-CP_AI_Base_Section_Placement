// DOM Elements
        const logoutBtn = document.getElementById('logoutBtn');
        const logoutModal = document.getElementById('logoutModal');
        const closeModalBtn = document.getElementById('closeModal');
        const cancelLogoutBtn = document.getElementById('cancelLogout');
        const confirmLogoutBtn = document.getElementById('confirmLogout');
        const modalUserName = document.getElementById('modalUserName');
        const modalSessionTime = document.getElementById('modalSessionTime');
        const currentUser = document.getElementById('currentUser');

        // Check if user is logged in
        const username = localStorage.getItem('username') || 'Demo Administrator';
        currentUser.textContent = username;
        modalUserName.textContent = username;

        // Set session start time (for demo purposes)
        const sessionStart = new Date();
        const formattedTime = sessionStart.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
        modalSessionTime.textContent = `${formattedTime} today`;

        // Show modal function
        function showLogoutModal() {
            logoutModal.classList.remove('hidden');
            logoutModal.classList.add('block');
            document.body.style.overflow = 'hidden'; // Prevent scrolling
        }

        // Hide modal function
        function hideLogoutModal() {
            logoutModal.classList.remove('block');
            logoutModal.classList.add('hidden');
            document.body.style.overflow = 'auto'; // Re-enable scrolling
        }

        // Logout function
        function performLogout() {
            // Clear user data from localStorage
            localStorage.removeItem('isLoggedIn');
            localStorage.removeItem('username');
            localStorage.removeItem('loginTime');

            console.log("User logged out - session cleared");

            // Redirect to logout success page
            window.location.href = 'logout-success.html'; // Create this page
            // Or redirect to login page directly:
            // window.location.href = 'login.html';
        }

        // Event Listeners
        logoutBtn.addEventListener('click', showLogoutModal);
        closeModalBtn.addEventListener('click', hideLogoutModal);
        cancelLogoutBtn.addEventListener('click', hideLogoutModal);

        confirmLogoutBtn.addEventListener('click', () => {
            // Optional: Add loading state
            confirmLogoutBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging out...';
            confirmLogoutBtn.disabled = true;

            // Perform logout after a short delay for UX
            setTimeout(() => {
                performLogout();
            }, 500);
        });

        // Close modal when clicking outside
        logoutModal.addEventListener('click', (e) => {
            if (e.target === logoutModal) {
                hideLogoutModal();
            }
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !logoutModal.classList.contains('hidden')) {
                hideLogoutModal();
            }
        });

        // Store login time for session tracking
        if (!localStorage.getItem('loginTime')) {
            localStorage.setItem('loginTime', new Date().toISOString());
        }