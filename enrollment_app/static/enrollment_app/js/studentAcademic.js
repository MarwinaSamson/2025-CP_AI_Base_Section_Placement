// Handles autofill and extraction for student academic grades
// CARD-BASED DESIGN: Matching 3rd screenshot with colored cards

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

    // Session state for page-return restoration
    const _aData = window.academicData || {};

    // UI Elements
    const ocrStatusContainer = document.getElementById('ocrStatusContainer');
    const ocrVerifying = document.getElementById('ocrVerifying');
    const ocrVerified = document.getElementById('ocrVerified');
    const ocrError = document.getElementById('ocrError');
    const documentSection = document.getElementById('documentUploadSection');
    const agreementCheckbox = document.getElementById('agreementCheckbox');
    
    // Report card inputs
    const reportCardInput = document.getElementById('reportCardInput');
    const reportCardBackInput = document.getElementById('reportCardBackInput');
    const frontPreview = document.getElementById('frontPreview');
    const backPreview = document.getElementById('backPreview');

    // State tracking
    let nameVerified = false;
    let gradesAutofilled = false;
    let documentsUploaded = false;

    // =========================================================================
    // STEP 1: Report Card Upload → OCR Extraction
    // =========================================================================
    
    function triggerExtraction() {
        if (!reportCardInput.files.length) return;
        
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
            if (data.success && data.extracted_grades && data.name_verification) {
                // Check name verification
                if (data.name_verification.is_match) {
                    // SUCCESS: Name verified
                    nameVerified = true;
                    autofillGrades(data.extracted_grades);
                    showVerified();
                    showDocumentSection();
                } else {
                    // FAIL: Name mismatch - Show NEW separate modal
                    nameVerified = false;
                    showNameVerificationModal(data.name_verification);
                    showError();
                    hideDocumentSection();
                }
            } else {
                showError();
                hideDocumentSection();
            }
        })
        .catch(() => {
            showError();
            hideDocumentSection();
        });
    }
    
    if (reportCardInput) {
        reportCardInput.addEventListener('change', triggerExtraction);
    }
    if (reportCardBackInput) {
        reportCardBackInput.addEventListener('change', triggerExtraction);
    }

    // =========================================================================
    // STEP 2: Auto-fill Grades
    // =========================================================================
    
    function autofillGrades(grades) {
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
        
        let total = 0, count = 0;
        
        Object.keys(subjectMap).forEach(function (ocrKey) {
            if (grades[ocrKey] !== undefined) {
                const field = document.querySelector('input[name="' + subjectMap[ocrKey] + '"]');
                if (field) {
                    field.value = grades[ocrKey];
                    // Dispatch input event so auto-calculation and button state update
                    field.dispatchEvent(new Event('input', { bubbles: true }));
                    const val = parseFloat(grades[ocrKey]);
                    if (!isNaN(val) && val > 0) {
                        total += val;
                        count++;
                    }
                }
            }
        });
        
        // Fill overall average
        const overall = document.getElementById('overallAverage');
        if (overall) {
            const avg = count ? (total / count).toFixed(2) : '';
            overall.value = avg;
            
            // Create hidden field for backend
            let hiddenAvg = document.querySelector('input[name="overall_average"]');
            if (!hiddenAvg) {
                hiddenAvg = document.createElement('input');
                hiddenAvg.type = 'hidden';
                hiddenAvg.name = 'overall_average';
                overall.parentNode.appendChild(hiddenAvg);
            }
            hiddenAvg.value = avg;
        }

        gradesAutofilled = true;

        // Safety: recalculate after DOM settles to ensure average displays
        setTimeout(function() {
            var allSubjects = document.querySelectorAll('.subject');
            var overallField = document.getElementById('overallAverage');
            if (overallField && allSubjects.length > 0) {
                var t = 0, c = 0;
                allSubjects.forEach(function(s) {
                    var v = parseFloat(s.value);
                    if (!isNaN(v) && v > 0) { t += v; c++; }
                });
                overallField.value = c ? (t / c).toFixed(2) : '';
            }
        }, 100);
    }

    // =========================================================================
    // STEP 3: Show/Hide Document Section
    // =========================================================================
    
    function showDocumentSection() {
        if (documentSection) {
            documentSection.classList.remove('hidden');
        }
    }
    
    function hideDocumentSection() {
        if (documentSection) {
            documentSection.classList.add('hidden');
        }
    }

    // =========================================================================
    // PAGE LOAD RESTORATION
    // Restore state from previous visit using session data passed via window.academicData
    // =========================================================================

    // Restore dost_exam_result dropdown
    const dostSelect = document.querySelector('select[name="dost_exam_result"]');
    if (dostSelect && _aData.dostExamResult) {
        dostSelect.value = _aData.dostExamResult;
    }

    // If OCR was previously verified, show document section and verified badge
    if (_aData.ocrVerified) {
        nameVerified = true;
        gradesAutofilled = true;
        showDocumentSection();
        showVerified();
    }

    // Show "already uploaded" indicators for report card
    if (_aData.reportCardPath) {
        const frontIndicator = document.getElementById('frontUploadedIndicator');
        if (frontIndicator) frontIndicator.classList.remove('hidden');
        // Remove required so form can be submitted without re-uploading
        if (reportCardInput) reportCardInput.removeAttribute('required');
    }
    if (_aData.reportCardBack) {
        const backIndicator = document.getElementById('backUploadedIndicator');
        if (backIndicator) backIndicator.classList.remove('hidden');
    }

    // =========================================================================
    // STEP 4: NEW - Name Verification Modal (Separate, File 2 Style)
    // =========================================================================
    
    function showNameVerificationModal(nameVerification) {
        console.log('showNameVerificationModal called with:', nameVerification);

        const modal = document.getElementById('nameVerificationModal');
        if (!modal) {
            console.error('nameVerificationModal element not found!');
            return;
        }

        // Populate modal content
        const extractedNameEl = document.getElementById('extractedName');
        const registeredNameEl = document.getElementById('registeredName');
        const reasonEl = document.getElementById('verificationReason');
        const similarityEl = document.getElementById('similarityScore');

        if (extractedNameEl) {
            extractedNameEl.textContent = nameVerification.extracted || "Not found";
        }
        if (registeredNameEl) {
            registeredNameEl.textContent = nameVerification.registered || "N/A";
        }
        if (reasonEl) {
            reasonEl.textContent = nameVerification.reason || "Name verification failed";
        }
        if (similarityEl) {
            similarityEl.textContent = (nameVerification.similarity || 0).toFixed(1);
        }

        // Show modal
        modal.classList.remove('hidden');
        console.log('Name verification modal displayed');
    }

    // Close name verification modal
    const closeNameVerificationBtn = document.getElementById('closeNameVerificationModal');
    if (closeNameVerificationBtn) {
        closeNameVerificationBtn.addEventListener('click', function() {
            document.getElementById('nameVerificationModal').classList.add('hidden');
        });
    }

    // Reupload button - close modal and focus on file input
    const reuploadBtn = document.getElementById('reuploadReportCardBtn');
    if (reuploadBtn) {
        reuploadBtn.addEventListener('click', function() {
            document.getElementById('nameVerificationModal').classList.add('hidden');
            
            // Scroll to report card upload section
            const reportCardSection = document.getElementById('reportCardInput');
            if (reportCardSection) {
                reportCardSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
                // Focus the file input after scroll
                setTimeout(() => {
                    reportCardSection.focus();
                }, 500);
            }
        });
    }

    // =========================================================================
    // STEP 5: Grade Mismatch Modal (File 2 Style - Simpler)
    // =========================================================================
    
    function showMismatchModal(mismatches) {
        console.log('showMismatchModal called with:', mismatches);

        const mismatchList = document.getElementById('mismatchList');
        if (!mismatchList) {
            console.error('mismatchList element not found!');
            return;
        }

        mismatchList.innerHTML = "";

        if (mismatches && mismatches.length > 0) {
            console.log('Processing', mismatches.length, 'mismatches');

            mismatches.forEach((mismatch, index) => {
                console.log('Creating mismatch item', index, mismatch);

                const mismatchItem = document.createElement('div');
                mismatchItem.className = 'bg-white border border-red-300 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow';

                const difference = Math.abs(mismatch.manual - mismatch.extracted).toFixed(2);

                mismatchItem.innerHTML = `
                    <div class="flex items-start gap-3">
                        <div class="flex-shrink-0 w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                            <span class="text-red-600 font-bold text-sm">${index + 1}</span>
                        </div>
                        <div class="flex-1">
                            <p class="text-gray-800 font-semibold mb-2">${mismatch.subject}</p>
                            <div class="flex items-center gap-3 flex-wrap mb-2">
                                <div class="flex items-center gap-1">
                                    <span class="bg-red-100 text-red-800 px-3 py-1 rounded font-medium text-sm">
                                        Your input: <strong>${mismatch.manual}</strong>
                                    </span>
                                </div>
                                <i class="fas fa-arrow-right text-gray-400"></i>
                                <div class="flex items-center gap-1">
                                    <span class="bg-green-100 text-green-800 px-3 py-1 rounded font-medium text-sm">
                                        Report card: <strong>${mismatch.extracted}</strong>
                                    </span>
                                </div>
                            </div>
                            <p class="text-xs text-red-600 font-semibold">
                                <i class="fas fa-exclamation-circle"></i> Difference: ${difference} points
                            </p>
                        </div>
                    </div>
                `;
                mismatchList.appendChild(mismatchItem);
            });

            console.log('Mismatch list populated with', mismatchList.children.length, 'items');

            // Highlight mismatched fields in the form
            highlightMismatchedFields(mismatches);
        } else {
            console.warn('No mismatches to display');
            mismatchList.innerHTML = '<p class="text-gray-600 text-sm italic"><i class="fas fa-info-circle"></i> No mismatch data available.</p>';
        }

        // Show modal
        const modal = document.getElementById('mismatchModal');
        if (modal) {
            modal.classList.remove('hidden');
            console.log('Mismatch modal displayed');
        } else {
            console.error('mismatchModal element not found!');
        }
    }

    // Function to highlight mismatched fields in the form
    function highlightMismatchedFields(mismatches) {
        // First, remove all previous highlights
        document.querySelectorAll('.subject').forEach((input) => {
            input.classList.remove('border-red-500', 'bg-red-50', 'border-4');
            const label = input.previousElementSibling;
            if (label && label.tagName === 'LABEL') {
                const existingError = label.querySelector('.mismatch-indicator');
                if (existingError) {
                    existingError.remove();
                }
            }
        });

        // Highlight mismatched fields
        mismatches.forEach((mismatch) => {
            const fieldName = mismatch.subject_key;
            const input = document.querySelector(`input[name="${fieldName}"]`);
            if (input) {
                input.classList.add('border-red-500', 'bg-red-50', 'border-4');

                // Add indicator to label
                const label = input.previousElementSibling;
                if (label && label.tagName === 'LABEL') {
                    const errorSpan = document.createElement('span');
                    errorSpan.className = 'mismatch-indicator text-red-600 text-sm ml-2 font-semibold';
                    errorSpan.innerHTML = ` ⚠ Should be ${mismatch.extracted}`;
                    label.appendChild(errorSpan);
                }
            }
        });
    }

    // Close mismatch modal
    const closeMismatchBtn = document.getElementById('closeMismatchModal');
    if (closeMismatchBtn) {
        closeMismatchBtn.addEventListener('click', function() {
            document.getElementById('mismatchModal').classList.add('hidden');
        });
    }

    // Review grades button - close modal and scroll to form
    const reviewGradesBtn = document.getElementById('reviewGradesBtn');
    if (reviewGradesBtn) {
        reviewGradesBtn.addEventListener('click', function() {
            document.getElementById('mismatchModal').classList.add('hidden');

            // Scroll to the grade section
            const gradeSection = document.querySelector('.subject');
            if (gradeSection) {
                gradeSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                });

                // Find first mismatched field and focus
                const firstMismatch = document.querySelector('.subject.border-red-500');
                if (firstMismatch) {
                    setTimeout(() => {
                        firstMismatch.focus();
                        firstMismatch.select();
                    }, 500);
                }
            }
        });
    }

    // Clear highlights when user starts editing a field
    document.querySelectorAll('.subject').forEach((input) => {
        input.addEventListener('focus', function() {
            // Remove highlight from this specific field when user starts editing
            this.classList.remove('border-red-500', 'bg-red-50', 'border-4');

            // Remove the error indicator from label
            const label = this.previousElementSibling;
            if (label && label.tagName === 'LABEL') {
                const existingError = label.querySelector('.mismatch-indicator');
                if (existingError) {
                    existingError.remove();
                }
            }
        });
    });

    // =========================================================================
    // STEP 6: "See Recommended Program" Button Handler
    // =========================================================================

    const seeSectionBtn = document.getElementById('seeSectionBtn');

    // Enable/disable button based on form state
    function updateSeeSectionBtn() {
        if (!seeSectionBtn) return;
        const allGradesFilled = Array.from(document.querySelectorAll('.subject')).every(function(input) {
            const val = parseFloat(input.value);
            return !isNaN(val) && val >= 65 && val <= 100;
        });
        const agreed = agreementCheckbox && agreementCheckbox.checked;
        seeSectionBtn.disabled = !(allGradesFilled && agreed);
    }

    // Listen for changes to update button state
    if (agreementCheckbox) {
        agreementCheckbox.addEventListener('change', updateSeeSectionBtn);
    }
    document.querySelectorAll('.subject').forEach(function(input) {
        input.addEventListener('input', updateSeeSectionBtn);
    });

    function resetSeeSectionBtn() {
        if (seeSectionBtn) {
            seeSectionBtn.disabled = false;
            seeSectionBtn.innerHTML = '<i class="fas fa-graduation-cap"></i> See Recommended Program';
        }
    }

    // Button click: validate → submit grades via AJAX → then fetch recommendations
    if (seeSectionBtn) {
        seeSectionBtn.addEventListener('click', function() {
            const form = document.getElementById('academicForm2');
            if (!form) return;

            // Validate required fields
            if (!form.checkValidity()) {
                form.reportValidity();
                return;
            }

            // Build FormData from form (text fields only - files already uploaded via OCR)
            const formData = new FormData(form);
            formData.delete('report_card');
            formData.delete('report_card_back');
            for (const key of [...formData.keys()]) {
                if (key.startsWith('document_')) {
                    formData.delete(key);
                }
            }

            // Disable button and show loading
            seeSectionBtn.disabled = true;
            seeSectionBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

            // Step A: Submit grades to save in session + trigger OCR grade verification
            fetch(window.location.pathname, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken,
                },
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success) {
                    // Step B: Grades saved → now fetch recommendations (verify_grades_ajax)
                    fetchRecommendationAndShow();
                } else {
                    alert(data.error || 'Failed to save academic data');
                    resetSeeSectionBtn();
                }
            })
            .catch(function(error) {
                alert('Error saving grades: ' + error.message);
                resetSeeSectionBtn();
            });
        });
    }

    function fetchRecommendationAndShow() {
        const loadingDiv = document.getElementById('seeSectionLoading');
        if (loadingDiv) {
            loadingDiv.style.display = 'flex';
        }

        const verifyUrl = window.verifyGradesUrl || '/enroll/verify-grades/';

        fetch(verifyUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({}),
        })
        .then(function(response) {
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Server returned HTML instead of JSON. Check URL configuration.');
            }
            if (!response.ok) {
                return response.json().then(function(errorData) {
                    throw { errorData: errorData };
                });
            }
            return response.json();
        })
        .then(handleRecommendationResponse)
        .catch(handleRecommendationError)
        .finally(function() {
            if (loadingDiv) {
                loadingDiv.style.display = 'none';
            }
            resetSeeSectionBtn();
        });
    }

    function handleRecommendationResponse(data) {
        if (data.success && data.recommendations) {
            displayRecommendationModal(data.recommendations);
        } else if (data.name_verification && !data.name_verification.is_match) {
            showNameVerificationModal(data.name_verification);
        } else if (data.mismatches && data.mismatches.length > 0) {
            showMismatchModal(data.mismatches);
        } else {
            alert(data.message || 'Failed to generate recommendations');
        }
    }

    function handleRecommendationError(error) {
        if (error && error.errorData) {
            // Handle structured error from verify_grades_ajax
            var data = error.errorData;
            if (data.name_verification && !data.name_verification.is_match) {
                showNameVerificationModal(data.name_verification);
            } else if (data.mismatches && data.mismatches.length > 0) {
                showMismatchModal(data.mismatches);
            } else {
                alert(data.message || data.error || 'Verification failed');
            }
        } else {
            alert('Error generating recommendations: ' + (error.message || error));
        }
    }

    // =========================================================================
    // ORIGINAL RECOMMENDATION DISPLAY (from sectionPlacement.js)
    // =========================================================================

    // Program metadata for icons and descriptions
    var programMeta = {
        STE:     { icon: '🔬', name: 'STE (Science, Technology, Engineering)', description: 'Advanced science and math track with research and lab focus.' },
        SPFL:    { icon: '🗣️', name: 'SPFL (Special Program in Foreign Language)', description: 'Language-focused program emphasizing communication and culture.' },
        SPTVE:   { icon: '🔧', name: 'SPTVE (Special Program in Technical-Vocational Education)', description: 'Hands-on technical and vocational learning path.' },
        SNED:    { icon: '🤝', name: 'SNED (Special Needs Education)', description: 'Individualized support for learners requiring accommodations.' },
        OHSP:    { icon: '📚', name: 'OHSP (Open High School Program)', description: 'Flexible, distance-friendly pathway for unique circumstances.' },
        TOP5:    { icon: '🏅', name: 'Top 5 Regular', description: 'Advanced regular section for high achievers.' },
        REGULAR: { icon: '📖', name: 'Regular', description: 'Standard curriculum with balanced workload.' },
    };

    function getProgramIcon(code) {
        var meta = programMeta[(code || '').toUpperCase()];
        return meta ? meta.icon : '🎓';
    }

    function getProgramDescription(code) {
        var meta = programMeta[(code || '').toUpperCase()];
        return meta ? meta.description : 'Standard curriculum with balanced workload.';
    }

    function displayRecommendationModal(recommendations) {
        var modal = document.getElementById('recommendationModal');
        var container = document.getElementById('rankedProgramsList');
        if (!modal || !container) return;

        container.innerHTML = '';

        var rankLabels = ['Top Recommendation', '2nd Recommendation', '3rd Recommendation', '4th Recommendation', '5th Recommendation'];

        recommendations.forEach(function(rec, index) {
            var rankLabel = rankLabels[index] || (index + 1) + 'th Recommendation';
            var isTop = index === 0;
            // Count actual factors from breakdown, fallback to criteria_met length
            var matchingFactors = (rec.breakdown && rec.breakdown.top_factors && rec.breakdown.top_factors.length) || (rec.criteria_met && rec.criteria_met.length) || 1;
            var icon = getProgramIcon(rec.program_code);
            var description = getProgramDescription(rec.program_code);
            
            // Color schemes based on rank (original style)
            var bgColor, borderColor, badgeColor, iconBg;
            if (index === 0) {
                bgColor = 'bg-red-50'; borderColor = 'border-red-300';
                badgeColor = 'bg-red-100 text-red-800 border-red-200'; iconBg = 'bg-red-100';
            } else if (index === 1) {
                bgColor = 'bg-yellow-50'; borderColor = 'border-yellow-300';
                badgeColor = 'bg-yellow-100 text-yellow-800 border-yellow-200'; iconBg = 'bg-yellow-100';
            } else if (index === 2) {
                bgColor = 'bg-blue-50'; borderColor = 'border-blue-300';
                badgeColor = 'bg-blue-100 text-blue-800 border-blue-200'; iconBg = 'bg-blue-100';
            } else {
                bgColor = 'bg-gray-50'; borderColor = 'border-gray-300';
                badgeColor = 'bg-gray-100 text-gray-800 border-gray-200'; iconBg = 'bg-gray-100';
            }

            var card = document.createElement('div');
            card.className = bgColor + ' border-2 ' + borderColor + ' rounded-xl p-5 cursor-pointer hover:shadow-lg transition-all duration-300 transform hover:scale-[1.02]';

            card.innerHTML =
                '<div class="flex items-start gap-4">' +
                    '<div class="flex-shrink-0">' +
                        '<div class="w-16 h-16 ' + iconBg + ' rounded-xl flex items-center justify-center border-2 ' + borderColor + '">' +
                            '<span class="text-3xl">' + icon + '</span>' +
                        '</div>' +
                    '</div>' +
                    '<div class="flex-1">' +
                        '<div class="flex flex-wrap items-center gap-2 mb-2">' +
                            '<span class="' + badgeColor + ' text-xs font-bold px-3 py-1 rounded-full border">' +
                                (isTop ? '⭐ ' : '') + rankLabel +
                            '</span>' +
                            '<span class="bg-white text-gray-700 text-xs font-semibold px-3 py-1 rounded-full border border-gray-300">' +
                                rec.percentage_match + '% Match' +
                            '</span>' +
                        '</div>' +
                        '<h5 class="text-lg font-bold text-gray-800 mb-1">' + rec.program_name + '</h5>' +
                        '<p class="text-sm text-gray-600 mb-3">' + description + '</p>' +
                        '<div class="flex items-center justify-between">' +
                            '<div class="text-xs text-gray-500">' +
                                '<i class="fas fa-check-circle text-green-600 mr-1"></i>' +
                                matchingFactors + ' matching factor' + (matchingFactors !== 1 ? 's' : '') +
                            '</div>' +
                            '<div class="text-primary text-sm font-semibold hover:text-primary-dark flex items-center gap-1">' +
                                'View Details <i class="fas fa-arrow-right"></i>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                '</div>';

            card.addEventListener('click', (function(r, i) {
                return function() { showProgramDetails(r, i); };
            })(rec, index));

            container.appendChild(card);
        });

        modal.classList.remove('hidden');
    }

    function showProgramDetails(program, rankIndex) {
        // Hide recommendation modal
        document.getElementById('recommendationModal').classList.add('hidden');

        var detailsModal = document.getElementById('programDetailsModal');
        if (!detailsModal) return;

        var rankLabels = ['Top Recommendation', '2nd Recommendation', '3rd Recommendation', '4th Recommendation', '5th Recommendation'];
        var rankLabel = rankLabels[rankIndex] || (rankIndex + 1) + 'th Recommendation';
        var icon = getProgramIcon(program.program_code);
        var description = program.recommendation_level || getProgramDescription(program.program_code);

        // Populate details
        document.getElementById('detailProgramIcon').textContent = icon;
        document.getElementById('detailProgramRank').textContent = rankLabel;
        document.getElementById('detailProgramScore').textContent = program.percentage_match + '% Match';
        document.getElementById('detailProgramName').textContent = program.program_name;
        document.getElementById('detailProgramDescription').textContent = description;

        // Generate detailed explanation (original style)
        var explanationDiv = document.getElementById('detailProgramExplanation');
        if (explanationDiv) {
            var rankIcon, rankTitle;
            if (rankIndex === 0) {
                rankIcon = '<i class="fas fa-trophy text-yellow-500"></i>';
                rankTitle = 'Why This is Your Top Match';
            } else if (rankIndex === 1) {
                rankIcon = '<i class="fas fa-medal text-gray-400"></i>';
                rankTitle = 'A Strong Alternative';
            } else {
                rankIcon = '<i class="fas fa-star text-blue-400"></i>';
                rankTitle = 'Another Great Option';
            }

            var criteriaHtml = '';
            if (program.criteria_met && program.criteria_met.length > 0) {
                criteriaHtml = '<ul class="mt-3 space-y-2">';
                program.criteria_met.forEach(function(reason) {
                    criteriaHtml += '<li class="flex items-start gap-2 text-sm text-gray-700">' +
                        '<i class="fas fa-check-circle text-green-500 mt-0.5 flex-shrink-0"></i>' +
                        '<span>' + reason + '</span></li>';
                });
                criteriaHtml += '</ul>';
            }

            explanationDiv.innerHTML =
                '<div class="mb-4">' +
                    '<h6 class="font-bold text-gray-800 mb-2 flex items-center gap-2">' +
                        rankIcon + ' ' + rankTitle +
                    '</h6>' +
                    '<p class="text-gray-700 mb-3">' +
                        'Based on your academic performance, <strong>' + program.program_name + '</strong> ' +
                        'is recommended for your skills and abilities.' +
                    '</p>' +
                '</div>' +
                criteriaHtml;
        }

        // Show ML factors if present
        var factorsDiv = document.getElementById('detailProgramFactors');
        var factorsList = document.getElementById('detailProgramFactorsList');
        if (factorsDiv && factorsList) {
            if (Array.isArray(program.factors) && program.factors.length > 0) {
                factorsDiv.classList.remove('hidden');
                factorsList.innerHTML = program.factors.map(function(f) {
                    return '<li><span class="font-medium">' + f.feature + '</span>: <span class="text-gray-600">' + f.value + '</span></li>';
                }).join('');
            } else {
                factorsDiv.classList.add('hidden');
                factorsList.innerHTML = '';
            }
        }

        // Display breakdown if available
        var breakdownSection = document.getElementById('detailBreakdownSection');
        if (breakdownSection && program.breakdown) {
            breakdownSection.classList.remove('hidden');

            // Helper function to generate smart explanation from factors
            var generateSmartExplanation = function(factors, score, programName, scoreType) {
                if (!factors || factors.length === 0) {
                    return 'Based on your academic profile and background.';
                }
                
                var topFactors = factors.slice(0, 5);
                var academicFactors = [];
                var profileFactors = [];
                
                topFactors.forEach(function(f) {
                    var feature = f.feature.toLowerCase();
                    if (feature.includes('grade') || feature.includes('average')) {
                        academicFactors.push({
                            name: f.feature,
                            value: f.value
                        });
                    } else {
                        profileFactors.push({
                            name: f.feature,
                            value: f.value
                        });
                    }
                });
                
                var explanation = '';
                
                if (scoreType === 'academic') {
                    explanation = programName + ' predicted score of ' + score + ' is determined by: ';
                    var parts = [];
                    
                    if (academicFactors.length > 0) {
                        var academicParts = academicFactors.slice(0, 3).map(function(f) {
                            return 'your ' + f.name.toLowerCase() + ' (' + f.value + ')';
                        });
                        parts = parts.concat(academicParts);
                    }
                    
                    if (profileFactors.length > 0) {
                        var profileParts = profileFactors.slice(0, 2).map(function(f) {
                            var val = f.value === '1' ? 'strong interest' : (f.value === '0' ? 'limited interest' : f.value);
                            return f.name.toLowerCase() + ' (' + val + ')';
                        });
                        parts = parts.concat(profileParts);
                    }
                    
                    explanation += parts.join(', ') + '.';
                } else if (scoreType === 'confidence') {
                    explanation = programName + ' shows ' + score + '% confidence match based on: ';
                    var parts = [];
                    
                    if (academicFactors.length > 0) {
                        var academicStr = 'strong ' + academicFactors.slice(0, 2).map(function(f) {
                            return f.name.toLowerCase().replace('grade', '').trim() + ' (' + f.value + ')';
                        }).join(' and ');
                        parts.push(academicStr);
                    }
                    
                    if (profileFactors.length > 0) {
                        var profileStr = profileFactors.slice(0, 3).map(function(f) {
                            var val = f.value === '1' ? 'yes' : (f.value === '0' ? 'no' : f.value);
                            return f.name.toLowerCase() + ' (' + val + ')';
                        }).join(', ');
                        parts.push(profileStr);
                    }
                    
                    explanation += parts.join(' and ') + '.';
                }
                
                return explanation;
            };

            // Helper function to map program code to program name in breakdown
            var getSelectedFromBreakdown = function(breakdownArray, programCode) {
                if (!breakdownArray || breakdownArray.length === 0) return null;
                
                // Map program codes to search terms
                var searchMap = {
                    'STE': 'STE',
                    'SPFL': 'SPFL',
                    'SPTVE': 'SPTVE',
                    'REGULAR': ['Top-5 Regular', 'Hetero']  // Handle both TOP5 and HETERO
                };
                
                var searchTerms = searchMap[programCode];
                if (!searchTerms) return breakdownArray[0];
                
                if (Array.isArray(searchTerms)) {
                    // For REGULAR, match based on track
                    var track = program.regular_track;
                    var targetName = track === 'TOP5' ? 'Top-5 Regular' : 'Hetero';
                    return breakdownArray.find(function(p) { 
                        return p.program_name.includes(targetName); 
                    });
                } else {
                    return breakdownArray.find(function(p) { 
                        return p.program_name.includes(searchTerms); 
                    });
                }
            };

            // Stage 1: Show only selected program's Ridge Prediction
            var stage1Div = document.getElementById('detailStage1Breakdown');
            if (stage1Div && program.breakdown.stage1_all_programs) {
                stage1Div.classList.remove('hidden');
                
                var selectedProg = getSelectedFromBreakdown(program.breakdown.stage1_all_programs, program.program_code);
                
                if (selectedProg) {
                    document.getElementById('stage1ProgramName').textContent = selectedProg.program_name;
                    document.getElementById('stage1ProgramScore').textContent = selectedProg.predicted_average.toFixed(2);
                    
                    // Generate smart explanation using all factors
                    var smartExplanation = generateSmartExplanation(
                        program.breakdown.top_factors,
                        selectedProg.predicted_average.toFixed(2),
                        selectedProg.program_name,
                        'academic'
                    );
                    document.getElementById('stage1Explanation').textContent = smartExplanation;
                } else {
                    stage1Div.classList.add('hidden');
                }
            } else if (stage1Div) {
                stage1Div.classList.add('hidden');
            }

            // Stage 2: Show only selected program's Confidence Score
            var stage2Div = document.getElementById('detailStage2Breakdown');
            if (stage2Div && program.breakdown.stage2_all_programs) {
                stage2Div.classList.remove('hidden');
                
                var selectedProg2 = getSelectedFromBreakdown(program.breakdown.stage2_all_programs, program.program_code);
                
                if (selectedProg2) {
                    document.getElementById('stage2ProgramName').textContent = selectedProg2.program_name;
                    document.getElementById('stage2ProgramScore').textContent = selectedProg2.confidence_pct + '%';
                    document.getElementById('stage2ConfidenceBar').style.width = selectedProg2.confidence_pct + '%';
                    
                    // Generate smart explanation using all factors
                    var smartExplanation2 = generateSmartExplanation(
                        program.breakdown.top_factors,
                        selectedProg2.confidence_pct,
                        selectedProg2.program_name,
                        'confidence'
                    );
                    document.getElementById('stage2Explanation').textContent = smartExplanation2;
                } else {
                    stage2Div.classList.add('hidden');
                }
            } else if (stage2Div) {
                stage2Div.classList.add('hidden');
            }

            // Top Contributing Factors (top 10)
            var topFactorsDiv = document.getElementById('detailTopFactorsBreakdown');
            var topFactorsList = document.getElementById('topFactorsList');
            if (topFactorsDiv && topFactorsList && program.breakdown.top_factors && program.breakdown.top_factors.length > 0) {
                topFactorsDiv.classList.remove('hidden');
                var topFactorsHtml = '';
                program.breakdown.top_factors.forEach(function(factor, idx) {
                    topFactorsHtml += '<li class="text-gray-700"><strong>' + factor.feature + '</strong>: ' + factor.value + '</li>';
                });
                topFactorsList.innerHTML = topFactorsHtml;
            } else if (topFactorsDiv) {
                topFactorsDiv.classList.add('hidden');
            }
        } else if (breakdownSection) {
            breakdownSection.classList.add('hidden');
        }

        // Store current program for confirmation
        window.currentSelectedProgram = program;

        detailsModal.classList.remove('hidden');
    }

    // Close recommendation modal
    const closeRecommendationBtn = document.getElementById('closeRecommendationModal');
    if (closeRecommendationBtn) {
        closeRecommendationBtn.addEventListener('click', function() {
            document.getElementById('recommendationModal').classList.add('hidden');
        });
    }

    // Close program details modal
    const closeProgramDetailsBtn = document.getElementById('closeProgramDetailsModal');
    if (closeProgramDetailsBtn) {
        closeProgramDetailsBtn.addEventListener('click', function() {
            document.getElementById('programDetailsModal').classList.add('hidden');
        });
    }

    // Back to recommendations button
    const backToRecommendationsBtn = document.getElementById('backToRecommendationsBtn');
    if (backToRecommendationsBtn) {
        backToRecommendationsBtn.addEventListener('click', function() {
            document.getElementById('programDetailsModal').classList.add('hidden');
            document.getElementById('recommendationModal').classList.remove('hidden');
        });
    }

    // Confirm program button
    const confirmProgramBtn = document.getElementById('confirmProgramBtn');
    if (confirmProgramBtn) {
        confirmProgramBtn.addEventListener('click', function() {
            if (!window.currentSelectedProgram) return;
            
            const program = window.currentSelectedProgram;
            const studentLrn = document.querySelector('input[name="lrn"]')?.value;
            const confirmUrl = window.confirmProgramUrl || '/enroll/confirm-program/';
            
            fetch(confirmUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    program_code: program.program_code,
                    program_name: program.program_name,
                    regular_track: program.regular_track || null,
                    student_lrn: studentLrn,
                }),
            })
            .then(response => {
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    throw new Error('Server returned HTML instead of JSON');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Show success modal
                    document.getElementById('programDetailsModal').classList.add('hidden');
                    document.getElementById('successSubmitModal').classList.remove('hidden');
                    document.getElementById('successMessage').textContent = data.message;
                } else {
                    alert(data.error || 'Failed to confirm program selection');
                }
            })
            .catch(error => {
                console.error('Confirmation error:', error);
                alert('Error: ' + error.message);
            });
        });
    }

    // Close success modal and redirect
    const closeSuccessModalBtn = document.getElementById('closeSuccessModalBtn');
    if (closeSuccessModalBtn) {
        closeSuccessModalBtn.addEventListener('click', function() {
            window.location.href = '/';
        });
    }

    // =========================================================================
    // Download Application Form Function
    // =========================================================================
    window.downloadApplicationForm = function () {
        const downloadBtn = document.getElementById('downloadFormBtn');
        if (downloadBtn) {
            downloadBtn.disabled = true;
            downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        }

        // Read LRN from the readonly input at the top of the academic form
        const lrnInput = document.querySelector('input[name="lrn"]');
        const lrn = lrnInput ? lrnInput.value.trim() : '';

        const downloadUrl = '/download-application/' + (lrn ? '?lrn=' + encodeURIComponent(lrn) : '');

        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = '';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        setTimeout(function () {
            if (downloadBtn) {
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = '<i class="fas fa-download"></i> Download Form';
            }
        }, 2000);
    };

    // =========================================================================
    // UI Helper Functions
    // =========================================================================
    
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

    // =========================================================================
    // Grade Auto-calculation
    // =========================================================================
    
    const subjectInputs = document.querySelectorAll('.subject');
    const overall = document.getElementById('overallAverage');
    
    subjectInputs.forEach((input) => {
        input.addEventListener('input', () => {
            let total = 0, count = 0;
            subjectInputs.forEach((s) => {
                const val = parseFloat(s.value);
                if (!isNaN(val) && val > 0) {
                    total += val;
                    count++;
                }
            });
            overall.value = count ? (total / count).toFixed(2) : '';
        });
    });

    // =========================================================================
    // Preview Images
    // =========================================================================
    
    if (reportCardInput) {
        reportCardInput.addEventListener('change', function() {
            const hasFile = this.files && this.files.length;
            if (hasFile && this.files[0].type.startsWith('image')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    frontPreview.src = e.target.result;
                    frontPreview.classList.remove('hidden');
                };
                reader.readAsDataURL(this.files[0]);
            } else if (frontPreview) {
                frontPreview.classList.add('hidden');
                frontPreview.removeAttribute('src');
            }
        });
    }

    if (reportCardBackInput) {
        reportCardBackInput.addEventListener('change', function() {
            const hasFile = this.files && this.files.length;
            if (hasFile && this.files[0].type.startsWith('image')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    backPreview.src = e.target.result;
                    backPreview.classList.remove('hidden');
                };
                reader.readAsDataURL(this.files[0]);
            } else if (backPreview) {
                backPreview.classList.add('hidden');
                backPreview.removeAttribute('src');
            }
        });
    }

    // Make showMismatchModal and showNameVerificationModal globally accessible
    window.showMismatchModal = showMismatchModal;
    window.showNameVerificationModal = showNameVerificationModal;

    // Show saved recommendations from session (triggered by banner button)
    window.showSavedRecommendations = function() {
        const recPayloadEl = document.getElementById('recommendationPayload');
        if (!recPayloadEl) return;
        try {
            const recs = JSON.parse(recPayloadEl.textContent);
            if (recs && Array.isArray(recs) && recs.length > 0) {
                displayRecommendationModal(recs);
            }
        } catch(e) {
            console.error('Failed to parse saved recommendations:', e);
        }
    };
});

// =========================================================================
// Document Upload Handler
// =========================================================================

function handleRequirementUpload(event) {
    const input = event.target;
    const file = input.files[0];
    if (!file) return;
    
    const reqId = input.dataset.reqId;
    const reqName = input.dataset.reqName;
    const maxFileSizeMB = parseInt(input.dataset.maxSize) || 50;
    const maxFileSize = maxFileSizeMB * 1024 * 1024;
    const statusDiv = document.getElementById(`status-${reqId}`);
    const reqContainer = document.getElementById(`req-${reqId}`);
    
    statusDiv.classList.remove('hidden');
    statusDiv.innerHTML = '';
    
    if (file.size > maxFileSize) {
        statusDiv.innerHTML = `
            <div class="flex items-center gap-2 text-red-600 bg-red-50 px-3 py-2 rounded">
                <i class="fas fa-exclamation-circle"></i>
                <span class="text-sm">File too large. Maximum size is ${maxFileSizeMB}MB.</span>
            </div>
        `;
        input.value = '';
        return;
    }
    
    statusDiv.innerHTML = `
        <div class="flex items-center gap-2 text-blue-600 bg-blue-50 px-3 py-2 rounded">
            <i class="fas fa-check-circle"></i>
            <span class="text-sm font-medium">${file.name} ready to upload (${(file.size / 1024).toFixed(2)}KB)</span>
        </div>
    `;
    
    reqContainer.classList.add('border-blue-500', 'bg-blue-50');
    reqContainer.classList.remove('border-primary', 'border-dashed');
}