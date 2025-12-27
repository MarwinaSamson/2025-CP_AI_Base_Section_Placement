document.addEventListener('DOMContentLoaded', function () {
            // File upload handling
            const bulkUpload = document.getElementById('bulkUpload');
            const dropZone = document.getElementById('dropZone');

            bulkUpload.addEventListener('change', function (e) {
                if (e.target.files.length > 0) {
                    processFile(e.target.files[0]);
                }
            });

            // Drag and drop
            dropZone.addEventListener('dragover', function (e) {
                e.preventDefault();
                dropZone.classList.add('border-primary', 'bg-red-50');
            });

            dropZone.addEventListener('dragleave', function () {
                dropZone.classList.remove('border-primary', 'bg-red-50');
            });

            dropZone.addEventListener('drop', function (e) {
                e.preventDefault();
                dropZone.classList.remove('border-primary', 'bg-red-50');

                if (e.dataTransfer.files.length > 0) {
                    const file = e.dataTransfer.files[0];
                    if (file.type.includes('excel') || file.type.includes('spreadsheet') ||
                        file.name.endsWith('.csv') || file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
                        processFile(file);
                    } else {
                        showNotification('Please upload only Excel or CSV files', 'error');
                    }
                }
            });

            // Manual form submission
            document.getElementById('manualEntryForm').addEventListener('submit', function (e) {
                e.preventDefault();
                showNotification('Manual entry saved successfully', 'success');
                this.reset();
            });
        });

        function processFile(file) {
            if (file.size > 10 * 1024 * 1024) {
                showNotification('File size exceeds 10MB limit', 'error');
                return;
            }

            // Show processing modal
            const modal = document.getElementById('processingModal');
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');
            const recordCount = document.getElementById('recordCount');

            modal.classList.remove('hidden');

            // Simulate processing
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                progressBar.style.width = progress + '%';

                if (progress <= 30) {
                    progressText.textContent = 'Reading file contents...';
                } else if (progress <= 60) {
                    progressText.textContent = 'Validating data...';
                } else if (progress <= 90) {
                    progressText.textContent = 'Processing records...';
                } else {
                    progressText.textContent = 'Finalizing...';
                }

                if (progress >= 100) {
                    clearInterval(interval);
                    setTimeout(() => {
                        modal.classList.add('hidden');
                        showNotification(`${file.name} processed successfully. 45 records imported.`, 'success');
                        progressBar.style.width = '0%';
                    }, 500);
                }
            }, 200);
        }

        function downloadTemplate() {
            // In a real app, this would download an actual template file
            showNotification('Template download started', 'info');
            // Simulate download
            const link = document.createElement('a');
            link.href = '#';
            link.download = 'stem_results_template.xlsx';
            link.click();
        }

        function exportResults() {
            showNotification('Exporting all results to Excel...', 'info');
            // Simulate export
            setTimeout(() => {
                showNotification('Results exported successfully', 'success');
            }, 1500);
        }

        function showNotification(message, type = 'info') {
            const container = document.getElementById('notificationContainer');
            const notification = document.createElement('div');

            const bgColor = type === 'success' ? 'bg-green-500' :
                type === 'error' ? 'bg-red-500' :
                    type === 'warning' ? 'bg-yellow-500' : 'bg-primary';

            notification.className = `${bgColor} text-white px-4 py-3 rounded-lg shadow-lg notification-slide`;
            notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
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