document.addEventListener('DOMContentLoaded', function () {
            // Initialize
            initializePage();
            setupEventListeners();
            setupPagination();

            // Check if user is logged in
            const isLoggedIn = localStorage.getItem('isLoggedIn');
            if (!isLoggedIn && window.location.pathname !== '/index.html') {
                window.location.href = 'index.html';
                return;
            }
        });

        function initializePage() {
            // Mock data for demonstration
            window.studentData = [
                {
                    id: 1,
                    lrn: '123456789012',
                    name: 'Dela Cruz, Juan Santos',
                    type: 'New Student',
                    gender: 'male',
                    age: 14,
                    average: 94.25,
                    status: 'enrolled',
                    photo: '../../assets/student1.jpg'
                },
                {
                    id: 2,
                    lrn: '234567890123',
                    name: 'Santos, Maria Reyes',
                    type: 'Transferee',
                    gender: 'female',
                    age: 13,
                    average: 88.75,
                    status: 'enrolled',
                    photo: '../../assets/student2.jpg'
                },
                {
                    id: 3,
                    lrn: '345678901234',
                    name: 'Gonzales, Pedro Martinez',
                    type: 'Returnee',
                    gender: 'male',
                    age: 15,
                    average: 82.50,
                    status: 'enrolled',
                    photo: '../../assets/student3.jpg'
                },
                {
                    id: 4,
                    lrn: '456789012345',
                    name: 'Fernandez, Ana Lopez',
                    type: 'New Student',
                    gender: 'female',
                    age: 14,
                    average: 95.00,
                    status: 'enrolled',
                    photo: '../../assets/student4.jpg'
                },
                {
                    id: 5,
                    lrn: '567890123456',
                    name: 'Martinez, Carlos Reyes',
                    type: 'Transferee',
                    gender: 'male',
                    age: 14,
                    average: 87.25,
                    status: 'enrolled',
                    photo: '../../assets/student5.jpg'
                },
                {
                    id: 6,
                    lrn: '678901234567',
                    name: 'Torres, Sofia Garcia',
                    type: 'New Student',
                    gender: 'female',
                    age: 13,
                    average: null,
                    status: 'pending',
                    photo: '../../assets/student6.jpg'
                },
                {
                    id: 7,
                    lrn: '789012345678',
                    name: 'Reyes, Miguel Santos',
                    type: 'Returnee',
                    gender: 'male',
                    age: 15,
                    average: 89.50,
                    status: 'enrolled',
                    photo: '../../assets/student7.jpg'
                },
                {
                    id: 8,
                    lrn: '890123456789',
                    name: 'Cruz, Elena Mendoza',
                    type: 'New Student',
                    gender: 'female',
                    age: 14,
                    average: 93.75,
                    status: 'enrolled',
                    photo: '../../assets/student8.jpg'
                }
            ];

            // Total mock students count
            window.totalStudents = 47;
            window.currentPage = 1;
            window.studentsPerPage = 8;
            window.totalPages = Math.ceil(window.totalStudents / window.studentsPerPage);
        }

        function setupEventListeners() {
            // Search functionality
            const searchInput = document.getElementById('studentSearch');
            if (searchInput) {
                searchInput.addEventListener('input', function () {
                    filterStudents(this.value);
                });
            }

            // Export button
            const exportBtn = document.querySelector('button[onclick="exportToExcel()"]');
            if (exportBtn) {
                exportBtn.addEventListener('click', exportToExcel);
            }

            // Print button
            const printBtn = document.querySelector('button[onclick="printMasterlist()"]');
            if (printBtn) {
                printBtn.addEventListener('click', printMasterlist);
            }
        }

        function setupPagination() {
            const prevBtn = document.getElementById('prevBtn');
            const nextBtn = document.getElementById('nextBtn');
            const currentPageSpan = document.getElementById('currentPage');
            const totalPagesSpan = document.getElementById('totalPages');
            const showingCountSpan = document.getElementById('showingCount');
            const totalCountSpan = document.getElementById('totalCount');

            // Update display
            totalPagesSpan.textContent = window.totalPages;
            totalCountSpan.textContent = window.totalStudents;
            updatePaginationDisplay();

            // Previous button
            prevBtn.addEventListener('click', function () {
                if (window.currentPage > 1) {
                    window.currentPage--;
                    updatePaginationDisplay();
                }
            });

            // Next button
            nextBtn.addEventListener('click', function () {
                if (window.currentPage < window.totalPages) {
                    window.currentPage++;
                    updatePaginationDisplay();
                }
            });

            function updatePaginationDisplay() {
                currentPageSpan.textContent = window.currentPage;
                showingCountSpan.textContent = Math.min(
                    window.studentsPerPage,
                    window.totalStudents - (window.currentPage - 1) * window.studentsPerPage
                );

                // Update button states
                prevBtn.disabled = window.currentPage === 1;
                nextBtn.disabled = window.currentPage === window.totalPages;
            }
        }

        function filterStudents(searchTerm) {
            const rows = document.querySelectorAll('#studentTableBody tr');
            let visibleCount = 0;
            const searchLower = searchTerm.toLowerCase();

            rows.forEach(row => {
                const rowText = row.textContent.toLowerCase();
                if (rowText.includes(searchLower)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });

            // Show/hide empty state
            const emptyState = document.getElementById('emptyState');
            if (visibleCount === 0 && searchTerm) {
                emptyState.classList.remove('hidden');
                document.querySelector('#studentTableBody').style.display = 'none';
                document.querySelector('.border-t').style.display = 'none';
            } else {
                emptyState.classList.add('hidden');
                document.querySelector('#studentTableBody').style.display = '';
                document.querySelector('.border-t').style.display = '';
            }

            // Update showing count
            document.getElementById('showingCount').textContent = visibleCount;
        }

        function clearSearch() {
            const searchInput = document.getElementById('studentSearch');
            searchInput.value = '';
            filterStudents('');
        }

        function exportToExcel() {
            // Show loading state
            const button = document.querySelector('button[onclick="exportToExcel()"]');
            const originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Exporting...';
            button.disabled = true;

            // Simulate export process
            setTimeout(() => {
                // Reset button
                button.innerHTML = originalText;
                button.disabled = false;

                // Show success notification
                showNotification('Masterlist exported successfully!', 'success');
            }, 1500);
        }

        function printMasterlist() {
            // Create print-friendly version
            const printWindow = window.open('', '_blank');
            const printContent = `
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Student Masterlist - Grade 7 - Section A</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; }
                        .header { text-align: center; margin-bottom: 30px; }
                        .header h1 { color: #991b1b; margin-bottom: 10px; }
                        .section-info { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
                        .info-item { border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
                        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                        th { background: #991b1b; color: white; padding: 10px; text-align: left; }
                        td { padding: 10px; border-bottom: 1px solid #ddd; }
                        .grade-badge { padding: 3px 8px; border-radius: 4px; font-size: 11px; }
                        .excellent { background: #10b981; color: white; }
                        .good { background: #3b82f6; color: white; }
                        .fair { background: #f59e0b; color: white; }
                        .footer { margin-top: 30px; text-align: right; font-size: 12px; color: #666; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Zamboanga National High School West</h1>
                        <h2>Grade 7 - Section A (St. Anne) - Student Masterlist</h2>
                        <p>Printed: ${new Date().toLocaleDateString()}</p>
                    </div>
                    
                    <div class="section-info">
                        <div class="info-item">
                            <strong>Program:</strong><br>STE
                        </div>
                        <div class="info-item">
                            <strong>Adviser:</strong><br>Mr. Kakashi Hatake
                        </div>
                        <div class="info-item">
                            <strong>Location:</strong><br>Room 201 - 2nd Floor
                        </div>
                        <div class="info-item">
                            <strong>Students:</strong><br>47 / 50
                        </div>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>LRN</th>
                                <th>Student Name</th>
                                <th>Gender</th>
                                <th>Age</th>
                                <th>Overall Average</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>1</td>
                                <td>123456789012</td>
                                <td>Dela Cruz, Juan Santos</td>
                                <td>Male</td>
                                <td>14</td>
                                <td><span class="grade-badge excellent">94.25</span></td>
                                <td>Enrolled</td>
                            </tr>
                            <tr>
                                <td>2</td>
                                <td>234567890123</td>
                                <td>Santos, Maria Reyes</td>
                                <td>Female</td>
                                <td>13</td>
                                <td><span class="grade-badge good">88.75</span></td>
                                <td>Enrolled</td>
                            </tr>
                            <tr>
                                <td>3</td>
                                <td>345678901234</td>
                                <td>Gonzales, Pedro Martinez</td>
                                <td>Male</td>
                                <td>15</td>
                                <td><span class="grade-badge fair">82.50</span></td>
                                <td>Enrolled</td>
                            </tr>
                            <tr>
                                <td>4</td>
                                <td>456789012345</td>
                                <td>Fernandez, Ana Lopez</td>
                                <td>Female</td>
                                <td>14</td>
                                <td><span class="grade-badge excellent">95.00</span></td>
                                <td>Enrolled</td>
                            </tr>
                            <tr>
                                <td>5</td>
                                <td>567890123456</td>
                                <td>Martinez, Carlos Reyes</td>
                                <td>Male</td>
                                <td>14</td>
                                <td><span class="grade-badge good">87.25</span></td>
                                <td>Enrolled</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div class="footer">
                        <p>Generated by ZNHS West Admin Portal</p>
                    </div>
                </body>
                </html>
            `;

            printWindow.document.write(printContent);
            printWindow.document.close();
            printWindow.print();
        }

        function showNotification(message, type = 'info') {
            const container = document.getElementById('notificationContainer');
            if (!container) return;

            const notification = document.createElement('div');
            notification.className = `bg-white border-l-4 ${type === 'success' ? 'border-green-500' : type === 'error' ? 'border-red-500' : type === 'warning' ? 'border-yellow-500' : 'border-blue-500'} rounded-lg shadow-lg p-4 max-w-sm animate-slide-in-right`;
            notification.innerHTML = `
                <div class="flex items-start gap-3">
                    <i class="fas fa-${type === 'success' ? 'check-circle text-green-500' : type === 'error' ? 'exclamation-circle text-red-500' : type === 'warning' ? 'exclamation-triangle text-yellow-500' : 'info-circle text-blue-500'} mt-1"></i>
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

        // Make functions globally available
        window.exportToExcel = exportToExcel;
        window.printMasterlist = printMasterlist;
        window.showNotification = showNotification;
        window.clearSearch = clearSearch;