        document.addEventListener('DOMContentLoaded', function () {
            // Initialize
            initializeAccordions();
            setupFormInteractions();
            setupAdminFeatures();

            // Check if user is logged in
            const isLoggedIn = localStorage.getItem('isLoggedIn');
            if (!isLoggedIn && window.location.pathname !== '/index.html') {
                window.location.href = 'index.html';
                return;
            }

            // Hide form errors initially (since we're showing mock errors)
            document.getElementById('formErrors').style.display = 'none';

            // Setup school year filter
            const currentYear = new Date().getFullYear();
            const nextYear = currentYear + 1;
            const currentSchoolYear = `${currentYear}-${nextYear}`;
            const schoolYearSelect = document.getElementById('schoolYearFilter');
            if (schoolYearSelect) {
                const currentOption = Array.from(schoolYearSelect.options).find(option =>
                    option.value === currentSchoolYear
                );
                if (!currentOption) {
                    const option = document.createElement('option');
                    option.value = currentSchoolYear;
                    option.textContent = currentSchoolYear;
                    schoolYearSelect.insertBefore(option, schoolYearSelect.firstChild);
                }
                schoolYearSelect.value = currentSchoolYear;
            }
        });

        // Accordion functionality
        function initializeAccordions() {
            // Open first accordion by default
            const firstAccordion = document.querySelector('.accordion-content');
            if (firstAccordion) {
                firstAccordion.classList.add('expanded');
                const firstChevron = document.querySelector('.accordion-header i.fa-chevron-down');
                if (firstChevron) {
                    firstChevron.classList.add('rotate-180');
                }
            }
        }

        function toggleAccordion(button) {
            const content = button.nextElementSibling;
            const chevron = button.querySelector('i.fa-chevron-down');

            content.classList.toggle('expanded');
            chevron.classList.toggle('rotate-180');

            // Smooth scroll to accordion if opening
            if (content.classList.contains('expanded')) {
                setTimeout(() => {
                    button.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 100);
            }
        }

        // Form interactions
        function setupFormInteractions() {
            // SPED toggle
            const spedRadios = document.querySelectorAll('input[name="is_sped"]');
            const spedDetails = document.querySelector('textarea[name="sped_details"]');

            spedRadios.forEach(radio => {
                radio.addEventListener('change', function () {
                    spedDetails.disabled = this.value === 'no';
                    if (this.value === 'no') {
                        spedDetails.value = '';
                    }
                });
            });

            // Working student toggle
            const workingRadios = document.querySelectorAll('input[name="is_working"]');
            const workingDetails = document.querySelector('textarea[name="working_details"]');

            workingRadios.forEach(radio => {
                radio.addEventListener('change', function () {
                    workingDetails.disabled = this.value === 'no';
                    if (this.value === 'no') {
                        workingDetails.value = '';
                    }
                });
            });

            // Calculate overall average
            const gradeInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
            const averageInput = document.querySelector('input[value="88.13"]');

            gradeInputs.forEach(input => {
                input.addEventListener('input', calculateAverage);
            });

            function calculateAverage() {
                let sum = 0;
                let count = 0;

                gradeInputs.forEach(input => {
                    const value = parseFloat(input.value);
                    if (!isNaN(value) && input.value !== '') {
                        sum += value;
                        count++;
                    }
                });

                if (count > 0) {
                    const average = sum / count;
                    averageInput.value = average.toFixed(2);
                }
            }

            // Requirements checklist
            const requirementCheckboxes = document.querySelectorAll('.accordion-content input[type="checkbox"]');
            requirementCheckboxes.forEach(checkbox => {
                checkbox.addEventListener('change', updateRequirementsStatus);
            });

            function updateRequirementsStatus() {
                const total = requirementCheckboxes.length;
                const checked = Array.from(requirementCheckboxes).filter(cb => cb.checked).length;

                // In a real app, you might update a status indicator here
                console.log(`${checked}/${total} requirements completed`);
            }
        }

        // Admin features
        function setupAdminFeatures() {
            // Simulate admin privileges (you can set this based on actual user role)
            const isAdmin = true; // Change this based on actual authentication

            const lrnField = document.getElementById('lrnField');
            if (lrnField) {
                lrnField.readOnly = !isAdmin;
                lrnField.style.backgroundColor = isAdmin ? 'white' : '#f9fafb';
            }

            // Admin-only fields styling
            const adminOnlyFields = document.querySelectorAll('.admin-only-badge').forEach(badge => {
                const section = badge.closest('.accordion-header');
                if (section && !isAdmin) {
                    section.style.opacity = '0.5';
                    section.style.cursor = 'not-allowed';
                    section.disabled = true;

                    // Disable all inputs in admin-only section for non-admins
                    const content = section.nextElementSibling;
                    if (content) {
                        const inputs = content.querySelectorAll('input, select, textarea');
                        inputs.forEach(input => {
                            input.disabled = !isAdmin;
                            input.style.backgroundColor = '#f9fafb';
                        });
                    }
                }
            });
        }

        // Form submission
        document.querySelector('form').addEventListener('submit', function (e) {
            e.preventDefault();

            // Check for incomplete requirements
            const requirementCheckboxes = document.querySelectorAll('.accordion-content input[type="checkbox"]');
            const missingRequirements = Array.from(requirementCheckboxes)
                .filter(cb => !cb.checked)
                .map(cb => cb.nextElementSibling.textContent.trim());

            if (missingRequirements.length > 0) {
                const studentName = "Juan Dela Cruz";
                const message = `Are you sure to approve ${studentName} even if requirements are incomplete?\n\nMissing:\n${missingRequirements.map(req => ` • ${req}`).join('\n')}`;

                if (confirm(message)) {
                    document.getElementById('confirm_approve_incomplete').value = '1';
                    submitForm();
                } else {
                    // Scroll to requirements section
                    const requirementsSection = document.querySelector('[class*="clipboard-check"]').closest('.bg-white');
                    if (requirementsSection) {
                        requirementsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            } else {
                submitForm();
            }
        });

        function submitForm() {
            // Show loading state
            const submitBtn = document.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
            submitBtn.disabled = true;

            // Simulate API call
            setTimeout(() => {
                // Show success notification
                showNotification('Student information updated successfully!', 'success');

                // Reset button
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;

                // Redirect back to enrollment after 2 seconds
                setTimeout(() => {
                    window.location.href = 'enrollment.html';
                }, 2000);
            }, 1500);
        }

        // Notification system
        function showNotification(message, type = 'info') {
            const container = document.getElementById('notificationContainer');
            if (!container) return;

            const notification = document.createElement('div');
            notification.className = `bg-white border-l-4 rounded-lg shadow p-4 max-w-md animation: slideInRight 0.3s ease-out border-${type === 'success' ? 'green-500' : type === 'error' ? 'red-500' : type === 'warning' ? 'yellow-500' : 'blue-500'}`;
            notification.innerHTML = `
                <div class="flex items-start gap-3">
                    <i class="fas fa-${type === 'success' ? 'check-circle text-green-500' : type === 'error' ? 'exclamation-circle text-red-500' : type === 'warning' ? 'exclamation-triangle text-yellow-500' : 'info-circle text-blue-500'} mt-1"></i>
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

        // Make functions globally available
        window.toggleAccordion = toggleAccordion;
        window.showNotification = showNotification;