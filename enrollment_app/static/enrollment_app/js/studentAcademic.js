// Handles autofill and extraction icon for student academic grades

document.addEventListener('DOMContentLoaded', function () {
    // CSRF token helper
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
    const csrftoken = getCookie('csrftoken');
    // Extraction status
    let extracting = false;
    const ocrStatusContainer = document.getElementById('ocrStatusContainer');
    const ocrVerifying = document.getElementById('ocrVerifying');
    const ocrVerified = document.getElementById('ocrVerified');
    const ocrError = document.getElementById('ocrError');

    // Listen for file input change (front and back)
    const reportCardInput = document.getElementById('reportCardInput');
    const reportCardBackInput = document.getElementById('reportCardBackInput');
    function triggerExtraction() {
        if (!reportCardInput.files.length) return;
        extracting = true;
        showExtracting();
        const formData = new FormData();
        formData.append('report_card', reportCardInput.files[0]);
        if (reportCardBackInput && reportCardBackInput.files.length) {
            formData.append('report_card_back', reportCardBackInput.files[0]);
        }
        formData.append('ajax_extract', '1');
        fetch(window.location.pathname, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrftoken,
            },
        })
            .then((response) => response.json())
            .then((data) => {
                extracting = false;
                if (data.success && data.extracted_grades) {
                    autofillGrades(data.extracted_grades);
                    showVerified();
                } else {
                    showError();
                }
            })
            .catch(() => {
                extracting = false;
                showError();
            });
    }
    if (reportCardInput) {
        reportCardInput.addEventListener('change', triggerExtraction);
    }
    if (reportCardBackInput) {
        reportCardBackInput.addEventListener('change', triggerExtraction);
    }

    function autofillGrades(grades) {
        // Map OCR subjects to form fields
        const subjectMap = {
            'Mathematics': 'mathematics',
            'ArPan': 'araling_panlipunan',
            'English': 'english',
            'EsP': 'edukasyon_sa_pagpapakatao',
            'Science': 'science',
            'EPP/TLE': 'edukasyon_pangkabuhayan',
            'Filipino': 'filipino',
            'MAPEH': 'mapeh',
        };
        Object.keys(subjectMap).forEach(function (ocrKey) {
            if (grades[ocrKey] !== undefined) {
                const field = document.querySelector('input[name="' + subjectMap[ocrKey] + '"]');
                if (field) {
                    field.value = grades[ocrKey];
                }
            }
        });
    }

    function showExtracting() {
        if (ocrStatusContainer) ocrStatusContainer.classList.remove('hidden');
        if (ocrVerifying) ocrVerifying.classList.remove('hidden');
        if (ocrVerified) ocrVerified.classList.add('hidden');
        if (ocrError) ocrError.classList.add('hidden');
    }
    function showVerified() {
        if (ocrStatusContainer) ocrStatusContainer.classList.remove('hidden');
        if (ocrVerifying) ocrVerifying.classList.add('hidden');
        if (ocrVerified) ocrVerified.classList.remove('hidden');
        if (ocrError) ocrError.classList.add('hidden');
    }
    function showError() {
        if (ocrStatusContainer) ocrStatusContainer.classList.remove('hidden');
        if (ocrVerifying) ocrVerifying.classList.add('hidden');
        if (ocrVerified) ocrVerified.classList.add('hidden');
        if (ocrError) ocrError.classList.remove('hidden');
    }
});
