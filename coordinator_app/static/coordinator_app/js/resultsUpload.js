// Results Upload Module
const ResultsUploadModule = (() => {
    let uploadProgress = 0;

    // Notification system
    const Notification = {
        show(message, type = 'info', duration = 5000) {
            const container = document.getElementById('notificationContainer');
            const notification = document.createElement('div');
            notification.className = `notification-slide px-6 py-4 rounded-xl shadow-lg text-white font-medium flex items-center gap-3 ${
                type === 'success' ? 'bg-green-600' :
                type === 'error' ? 'bg-red-600' :
                type === 'warning' ? 'bg-yellow-600' :
                'bg-blue-600'
            }`;
            
            const icons = {
                success: 'fa-check-circle',
                error: 'fa-exclamation-circle',
                warning: 'fa-exclamation-triangle',
                info: 'fa-info-circle'
            };
            
            notification.innerHTML = `
                <i class="fas ${icons[type]}"></i>
                <span>${message}</span>
                <button onclick="this.parentElement.remove()" class="ml-auto hover:opacity-80">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            container.appendChild(notification);
            
            setTimeout(() => notification.remove(), duration);
        }
    };

    // Drag and drop handling
    const setupDragDrop = () => {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('bulkUpload');

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('border-primary', 'bg-red-50');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('border-primary', 'bg-red-50');
            });
        });

        dropZone.addEventListener('drop', handleDrop);
        fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
    };

    const handleDrop = (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    };

    const handleFiles = (files) => {
        if (files.length === 0) return;

        const file = files[0];

        // Validate file type
        const validTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                          'application/vnd.ms-excel', 
                          'text/csv'];
        if (!validTypes.includes(file.type) && !file.name.match(/\.(xlsx|xls|csv)$/i)) {
            Notification.show('Invalid file format. Please upload .xlsx, .xls, or .csv file', 'error');
            return;
        }

        // Validate file size (10MB)
        if (file.size > 10 * 1024 * 1024) {
            Notification.show('File size exceeds 10MB limit', 'error');
            return;
        }

        uploadBulkFile(file);
    };

    const uploadBulkFile = (file) => {
        const formData = new FormData();
        formData.append('file', file);

        const modal = document.getElementById('processingModal');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const recordCount = document.getElementById('recordCount');

        modal.classList.remove('hidden');
        uploadProgress = 0;

        // Simulate progress while uploading
        const progressInterval = setInterval(() => {
            if (uploadProgress < 90) {
                uploadProgress += Math.random() * 30;
                progressBar.style.width = uploadProgress + '%';
            }
        }, 500);

        const csrfToken = getCookie('csrftoken');
        
        fetch('/coordinator/api/results/bulk-upload/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            clearInterval(progressInterval);
            uploadProgress = 100;
            progressBar.style.width = '100%';

            if (data.success) {
                progressText.textContent = 'Processing Complete!';
                recordCount.textContent = `${data.data.success} records imported successfully, ${data.data.failed} failed`;
                
                setTimeout(() => {
                    modal.classList.add('hidden');
                    Notification.show(`${data.data.success} records imported successfully`, 'success');
                    
                    if (data.data.errors.length > 0) {
                        Notification.show(`${data.data.failed} records had errors. Check the details above.`, 'warning', 8000);
                    }
                    
                    // Reload the page to show new records
                    setTimeout(() => location.reload(), 1000);
                }, 2000);
            } else {
                modal.classList.add('hidden');
                Notification.show(data.message, 'error');
            }
        })
        .catch(error => {
            clearInterval(progressInterval);
            modal.classList.add('hidden');
            Notification.show('Error uploading file: ' + error.message, 'error');
        });
    };

    // Manual entry form handling
    const setupManualEntry = () => {
        const form = document.getElementById('manualEntryForm');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            e.preventDefault();

            const formData = new FormData(form);
            const csrfToken = getCookie('csrftoken');

            fetch('/coordinator/api/results/manual-entry/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Notification.show(data.message, 'success');
                    form.reset();
                    
                    // Reload page to show new record
                    setTimeout(() => location.reload(), 1500);
                } else {
                    Notification.show(data.message, 'error');
                }
            })
            .catch(error => {
                Notification.show('Error: ' + error.message, 'error');
            });
        });
    };

    // Download template
    window.downloadTemplate = () => {
        fetch('/coordinator/api/results/download-template/')
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'results_template_' + new Date().toISOString().split('T')[0] + '.xlsx';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                Notification.show('Template downloaded successfully', 'success');
            })
            .catch(error => {
                Notification.show('Error downloading template: ' + error.message, 'error');
            });
    };

    // Export results
    window.exportResults = () => {
        fetch('/coordinator/api/results/export/')
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T');
                a.download = 'all_results_' + timestamp[0] + '_' + timestamp[1].substring(0, 6) + '.xlsx';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                Notification.show('Results exported successfully', 'success');
            })
            .catch(error => {
                Notification.show('Error exporting results: ' + error.message, 'error');
            });
    };

    // View result details
    window.viewResult = (lrn) => {
        fetch(`/coordinator/api/results/${lrn}/view/`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const result = data.data;
                    const modal = createResultModal(result);
                    showModal(modal);
                } else {
                    Notification.show('Error loading result: ' + data.message, 'error');
                }
            })
            .catch(error => {
                Notification.show('Error: ' + error.message, 'error');
            });
    };

    // Create result modal
    const createResultModal = (result) => {
        const statusColors = {
            'qualified': { bg: 'bg-green-100', text: 'text-green-800' },
            'pending': { bg: 'bg-yellow-100', text: 'text-yellow-800' },
            'not_qualified': { bg: 'bg-red-100', text: 'text-red-800' },
            'waitlisted': { bg: 'bg-blue-100', text: 'text-blue-800' }
        };

        const colors = statusColors[result.status] || statusColors['pending'];

        return `
            <div class="fixed inset-0 z-50 overflow-y-auto hidden" id="resultModal">
                <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                    <div class="fixed inset-0 transition-opacity" aria-hidden="true">
                        <div class="absolute inset-0 bg-gray-900 bg-opacity-75"></div>
                    </div>

                    <span class="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

                    <div class="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-md sm:w-full animate-modal-fade-in">
                        <div class="bg-gradient-to-r from-red-600 to-red-800 px-6 py-4">
                            <h3 class="text-lg font-semibold text-white">Student Result Details</h3>
                        </div>

                        <div class="px-6 py-6 space-y-4">
                            <div>
                                <p class="text-sm text-gray-500 font-medium">Student Name</p>
                                <p class="text-lg font-semibold text-gray-800">${result.student_name}</p>
                            </div>

                            <div>
                                <p class="text-sm text-gray-500 font-medium">LRN</p>
                                <p class="text-lg font-mono text-gray-800">${result.lrn}</p>
                            </div>

                            <div class="grid grid-cols-3 gap-4">
                                <div class="bg-blue-50 rounded-lg p-3">
                                    <p class="text-xs text-blue-600 font-medium">Exam Score</p>
                                    <p class="text-2xl font-bold text-blue-800">${result.exam_score.toFixed(2)}</p>
                                </div>
                                <div class="bg-purple-50 rounded-lg p-3">
                                    <p class="text-xs text-purple-600 font-medium">Interview Score</p>
                                    <p class="text-2xl font-bold text-purple-800">${result.interview_score.toFixed(2)}</p>
                                </div>
                                <div class="bg-green-50 rounded-lg p-3">
                                    <p class="text-xs text-green-600 font-medium">Total</p>
                                    <p class="text-2xl font-bold text-green-800">${result.total_score.toFixed(2)}</p>
                                </div>
                            </div>

                            <div>
                                <p class="text-sm text-gray-500 font-medium">Average Score</p>
                                <p class="text-lg font-semibold text-gray-800">${result.average_score.toFixed(2)}</p>
                            </div>

                            <div>
                                <p class="text-sm text-gray-500 font-medium">Status</p>
                                <span class="inline-block px-3 py-1 ${colors.bg} ${colors.text} rounded-full text-sm font-semibold mt-1">
                                    ${result.status_display}
                                </span>
                            </div>

                            ${result.remarks ? `
                            <div>
                                <p class="text-sm text-gray-500 font-medium">Remarks</p>
                                <p class="text-gray-700">${result.remarks}</p>
                            </div>
                            ` : ''}

                            <div class="pt-4 border-t border-gray-200 text-xs text-gray-500">
                                <p>Updated by: ${result.updated_by}</p>
                                <p>Updated at: ${result.updated_at}</p>
                            </div>
                        </div>

                        <div class="bg-gray-50 px-6 py-4 flex justify-end gap-3">
                            <button onclick="window.closeResultModal()" class="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 font-medium">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    };

    // Show modal
    const showModal = (modalHTML) => {
        const container = document.createElement('div');
        container.innerHTML = modalHTML;
        document.body.appendChild(container);
        const modal = document.getElementById('resultModal');
        if (modal) modal.classList.remove('hidden');
    };

    // Delete result
    window.deleteResult = (lrn) => {
        if (!confirm('Are you sure you want to delete this record? This action cannot be undone.')) {
            return;
        }

        const csrfToken = getCookie('csrftoken');

        fetch(`/coordinator/api/results/${lrn}/delete/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Notification.show('Record deleted successfully', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                Notification.show('Error: ' + data.message, 'error');
            }
        })
        .catch(error => {
            Notification.show('Error: ' + error.message, 'error');
        });
    };

    // Close result modal
    window.closeResultModal = () => {
        const modal = document.getElementById('resultModal');
        if (modal) {
            modal.classList.add('hidden');
            setTimeout(() => {
                if (modal.parentElement) {
                    modal.parentElement.remove();
                }
            }, 300);
        }
    };

    // Utility function to get CSRF token
    const getCookie = (name) => {
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
    };

    // Initialize on page load
    const init = () => {
        setupDragDrop();
        setupManualEntry();
    };

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Public API
    return {
        Notification
    };
})();