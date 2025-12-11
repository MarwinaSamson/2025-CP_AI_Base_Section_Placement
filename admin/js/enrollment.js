// Filter functionality
        document.addEventListener('DOMContentLoaded', function () {
            // Check if user is logged in
            const isLoggedIn = localStorage.getItem('isLoggedIn');
            if (!isLoggedIn && window.location.pathname !== '/index.html') {
                window.location.href = 'index.html';
                return;
            }

            // Set current date in school year filter if needed
            const currentYear = new Date().getFullYear();
            const nextYear = currentYear + 1;
            const currentSchoolYear = `${currentYear}-${nextYear}`;

            // Update school year filter if option exists
            const schoolYearSelect = document.getElementById('schoolYearFilter');
            if (schoolYearSelect) {
                const currentOption = Array.from(schoolYearSelect.options).find(option =>
                    option.value === currentSchoolYear
                );
                if (!currentOption) {
                    // Add current school year if not exists
                    const option = document.createElement('option');
                    option.value = currentSchoolYear;
                    option.textContent = currentSchoolYear;
                    schoolYearSelect.insertBefore(option, schoolYearSelect.firstChild);
                }
                schoolYearSelect.value = currentSchoolYear;
            }

            // Add filter event listeners
            const programFilter = document.getElementById('programFilter');
            const statusFilter = document.getElementById('statusFilter');

            if (programFilter) {
                programFilter.addEventListener('change', function () {
                    filterTable();
                });
            }

            if (statusFilter) {
                statusFilter.addEventListener('change', function () {
                    filterTable();
                });
            }

            // Initialize table filtering
            filterTable();

            setupLogoutModalEvents();
        });

        function filterTable() {
            const programFilter = document.getElementById('programFilter');
            const statusFilter = document.getElementById('statusFilter');

            const selectedProgram = programFilter ? programFilter.value : 'all';
            const selectedStatus = statusFilter ? statusFilter.value : 'all';

            const rows = document.querySelectorAll('tbody tr');
            let visibleCount = 0;

            rows.forEach(row => {
                const programCell = row.querySelector('td:nth-child(4)');
                const statusCell = row.querySelector('td:nth-child(7) span');

                if (!programCell || !statusCell) return;

                const rowProgram = programCell.textContent.trim().toLowerCase();
                const rowStatus = statusCell.textContent.trim().toLowerCase();

                const programMatch = selectedProgram === 'all' ||
                    (selectedProgram === 'ste' && rowProgram === 'ste') ||
                    (selectedProgram === 'spfl' && rowProgram === 'spfl') ||
                    (selectedProgram === 'stem' && rowProgram === 'stem') ||
                    (selectedProgram === 'abm' && rowProgram === 'abm') ||
                    (selectedProgram === 'top5' && rowProgram.includes('top')) ||
                    (selectedProgram === 'hetero' && rowProgram === 'hetero') ||
                    (selectedProgram === 'ohsp' && rowProgram === 'ohsp');

                const statusMatch = selectedStatus === 'all' ||
                    (selectedStatus === 'pending' && rowStatus.includes('pending')) ||
                    (selectedStatus === 'approved' && rowStatus.includes('approved')) ||
                    (selectedStatus === 'rejected' && rowStatus.includes('rejected'));

                if (programMatch && statusMatch) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // Update stats based on visible rows
            updateVisibleStats(visibleCount);
        }

        function updateVisibleStats(visibleCount) {
            // This is a simplified version - in a real app, you'd calculate based on filtered data
            console.log(`Currently showing ${visibleCount} requests`);
        }

        function refreshData() {
            // Show loading state
            const refreshBtn = document.querySelector('button[onclick="refreshData()"]');
            const originalHTML = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            refreshBtn.disabled = true;

            // Simulate API call
            setTimeout(() => {
                // Reset button
                refreshBtn.innerHTML = originalHTML;
                refreshBtn.disabled = false;

                // Show notification
                showNotification('Data refreshed successfully!', 'success');

                // Re-filter table
                filterTable();
            }, 1000);
        }

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

        // Handle enrollment details navigation
        function viewEnrollmentDetails(studentId) {
            // Store the student ID in localStorage to retrieve in enrollmentDetails.html
            localStorage.setItem('currentEnrollmentId', studentId);
            window.location.href = `enrollmentDetails.html?id=${studentId}`;
        }// Filter functionality
        document.addEventListener('DOMContentLoaded', function () {
            // Check if user is logged in
            const isLoggedIn = localStorage.getItem('isLoggedIn');
            if (!isLoggedIn && window.location.pathname !== '/index.html') {
                window.location.href = 'index.html';
                return;
            }

            // Set current date in school year filter if needed
            const currentYear = new Date().getFullYear();
            const nextYear = currentYear + 1;
            const currentSchoolYear = `${currentYear}-${nextYear}`;

            // Update school year filter if option exists
            const schoolYearSelect = document.getElementById('schoolYearFilter');
            if (schoolYearSelect) {
                const currentOption = Array.from(schoolYearSelect.options).find(option =>
                    option.value === currentSchoolYear
                );
                if (!currentOption) {
                    // Add current school year if not exists
                    const option = document.createElement('option');
                    option.value = currentSchoolYear;
                    option.textContent = currentSchoolYear;
                    schoolYearSelect.insertBefore(option, schoolYearSelect.firstChild);
                }
                schoolYearSelect.value = currentSchoolYear;
            }

            // Add filter event listeners
            const programFilter = document.getElementById('programFilter');
            const statusFilter = document.getElementById('statusFilter');

            if (programFilter) {
                programFilter.addEventListener('change', function () {
                    filterTable();
                });
            }

            if (statusFilter) {
                statusFilter.addEventListener('change', function () {
                    filterTable();
                });
            }

            // Initialize table filtering
            filterTable();
        });

        function filterTable() {
            const programFilter = document.getElementById('programFilter');
            const statusFilter = document.getElementById('statusFilter');

            const selectedProgram = programFilter ? programFilter.value : 'all';
            const selectedStatus = statusFilter ? statusFilter.value : 'all';

            const rows = document.querySelectorAll('tbody tr');
            let visibleCount = 0;

            rows.forEach(row => {
                const programCell = row.querySelector('td:nth-child(4)');
                const statusCell = row.querySelector('td:nth-child(7) span');

                if (!programCell || !statusCell) return;

                const rowProgram = programCell.textContent.trim().toLowerCase();
                const rowStatus = statusCell.textContent.trim().toLowerCase();

                const programMatch = selectedProgram === 'all' ||
                    (selectedProgram === 'ste' && rowProgram === 'ste') ||
                    (selectedProgram === 'spfl' && rowProgram === 'spfl') ||
                    (selectedProgram === 'stem' && rowProgram === 'stem') ||
                    (selectedProgram === 'abm' && rowProgram === 'abm') ||
                    (selectedProgram === 'top5' && rowProgram.includes('top')) ||
                    (selectedProgram === 'hetero' && rowProgram === 'hetero') ||
                    (selectedProgram === 'ohsp' && rowProgram === 'ohsp');

                const statusMatch = selectedStatus === 'all' ||
                    (selectedStatus === 'pending' && rowStatus.includes('pending')) ||
                    (selectedStatus === 'approved' && rowStatus.includes('approved')) ||
                    (selectedStatus === 'rejected' && rowStatus.includes('rejected'));

                if (programMatch && statusMatch) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // Update stats based on visible rows
            updateVisibleStats(visibleCount);
        }

        function updateVisibleStats(visibleCount) {
            // This is a simplified version - in a real app, you'd calculate based on filtered data
            console.log(`Currently showing ${visibleCount} requests`);
        }

        function refreshData() {
            // Show loading state
            const refreshBtn = document.querySelector('button[onclick="refreshData()"]');
            const originalHTML = refreshBtn.innerHTML;
            refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
            refreshBtn.disabled = true;

            // Simulate API call
            setTimeout(() => {
                // Reset button
                refreshBtn.innerHTML = originalHTML;
                refreshBtn.disabled = false;

                // Show notification
                showNotification('Data refreshed successfully!', 'success');

                // Re-filter table
                filterTable();
            }, 1000);
        }

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

        // Handle enrollment details navigation
        function viewEnrollmentDetails(studentId) {
            // Store the student ID in localStorage to retrieve in enrollmentDetails.html
            localStorage.setItem('currentEnrollmentId', studentId);
            window.location.href = `enrollmentDetails.html?id=${studentId}`;
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