// Global variables
let selectedMethod = null;
let aiPredictions = [];

// Program data with weights for AI prediction
const programWeights = {
    STE: {
        name: "STE (Science Technology and Engineering)",
        description: "Focuses on science, technology, engineering, and mathematics.",
        weights: {
            mathematics: 0.25,
            science: 0.25,
            english: 0.15,
            overall: 0.20,
            dost: 0.15
        },
        minScore: 85
    },
    SPFL: {
        name: "SPFL (Special Program in Foreign Language)",
        description: "Focuses on foreign language proficiency.",
        weights: {
            english: 0.30,
            filipino: 0.25,
            overall: 0.25,
            communication: 0.20
        },
        minScore: 80
    },
    SPTVL: {
        name: "SPTVL (Special Program in Technical Vocational Livelihood)",
        description: "Practical skills in technical and vocational fields.",
        weights: {
            ep: 0.30,  // Edukasyon Pangkabuhayan
            mapeh: 0.25,
            overall: 0.25,
            practical: 0.20
        },
        minScore: 75
    },
    TOP5: {
        name: "Top 5 Sections",
        description: "For exceptional academic performance.",
        weights: {
            overall: 0.40,
            mathematics: 0.20,
            science: 0.20,
            english: 0.20
        },
        minScore: 85
    },
    HETERO: {
        name: "Hetero Regular",
        description: "Standard academic section.",
        weights: {
            overall: 0.50,
            balanced: 0.50
        },
        minScore: 70
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Setup prediction method modal events
    setupPredictionMethodModal();
    
    // Setup AI prediction modal events
    setupAiPredictionModal();
    
    // Setup AI confirmation modal events
    setupAiConfirmationModal();
});

function setupPredictionMethodModal() {
    const modal = document.getElementById('predictionMethodModal');
    const seeSectionBtn = document.getElementById('seeSectionBtn');
    const closeBtn = document.getElementById('closePredictionModal');
    const cancelBtn = document.getElementById('cancelPredictionBtn');
    const continueBtn = document.getElementById('continueBtn');
    
    if (!modal || !seeSectionBtn) return;
    
    // Open modal when clicking "See Section"
    seeSectionBtn.addEventListener('click', function(e) {
        e.preventDefault();
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    });
    
    // Close modal
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }
    
    // Close when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
    
    // Setup continue button
    if (continueBtn) {
        continueBtn.addEventListener('click', function() {
            if (selectedMethod === 'ai') {
                modal.classList.add('hidden');
                showAiPrediction();
            } else if (selectedMethod === 'manual') {
                window.location.href = 'sectionPlacement.html';
            }
        });
    }
    
    // Escape key to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
}

function selectMethod(method) {
    selectedMethod = method;
    const methodName = document.getElementById('methodName');
    const selectedMethodInfo = document.getElementById('selectedMethodInfo');
    const continueBtn = document.getElementById('continueBtn');
    
    if (method === 'ai') {
        methodName.textContent = 'AI-Powered Prediction';
        continueBtn.innerHTML = '<i class="fas fa-robot mr-2"></i> Get AI Prediction';
        continueBtn.className = 'px-6 py-2.5 bg-gradient-to-r from-primary to-primary-dark hover:from-primary-dark hover:to-primary text-white font-semibold rounded-lg transition-all hover:shadow-lg';
    } else {
        methodName.textContent = 'Manual Selection';
        continueBtn.innerHTML = '<i class="fas fa-hand-pointer mr-2"></i> Browse Sections';
        continueBtn.className = 'px-6 py-2.5 bg-gradient-to-r from-primary to-primary-dark hover:from-primary-dark hover:to-primary text-white font-semibold rounded-lg transition-all hover:shadow-lg';
    }
    
    selectedMethodInfo.classList.remove('hidden');
    continueBtn.disabled = false;
    continueBtn.classList.remove('cursor-not-allowed');
}

function clearSelection() {
    selectedMethod = null;
    document.getElementById('selectedMethodInfo').classList.add('hidden');
    document.getElementById('continueBtn').disabled = true;
    document.getElementById('continueBtn').className = 'px-6 py-2.5 bg-gray-300 text-gray-500 rounded-lg font-semibold transition-all cursor-not-allowed';
}

function showAiPrediction() {
    // Get student data from form
    const studentData = collectStudentData();
    
    // Calculate predictions
    aiPredictions = calculatePredictions(studentData);
    
    // Display results
    displayPredictionResults(aiPredictions);
    
    // Show modal
    const modal = document.getElementById('aiPredictionModal');
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function collectStudentData() {
    // Get all subject inputs
    const inputs = {
        mathematics: document.querySelector('input[placeholder*="Mathematics"]'),
        science: document.querySelector('input[placeholder*="Science"]'),
        english: document.querySelector('input[placeholder*="English"]'),
        filipino: document.querySelector('input[placeholder*="Filipino"]'),
        aralingPanlipunan: document.querySelector('input[placeholder*="Araling Panlipunan"]'),
        edukasyonPangkabuhayan: document.querySelector('input[placeholder*="Edukasyon Pangkabuhayan"]'),
        edukasyonPagpapakatao: document.querySelector('input[placeholder*="Edukasyon sa Pagpapakatao"]'),
        mapeh: document.querySelector('input[placeholder*="MAPEH"]')
    };
    
    const data = {
        mathematics: parseFloat(inputs.mathematics?.value) || 0,
        science: parseFloat(inputs.science?.value) || 0,
        english: parseFloat(inputs.english?.value) || 0,
        filipino: parseFloat(inputs.filipino?.value) || 0,
        aralingPanlipunan: parseFloat(inputs.aralingPanlipunan?.value) || 0,
        edukasyonPangkabuhayan: parseFloat(inputs.edukasyonPangkabuhayan?.value) || 0,
        edukasyonPagpapakatao: parseFloat(inputs.edukasyonPagpapakatao?.value) || 0,
        mapeh: parseFloat(inputs.mapeh?.value) || 0,
        overall: parseFloat(document.getElementById('overallAverage')?.value) || 0,
        dostExamResult: document.querySelector('select')?.value || 'not_taken'
    };
    
    return data;
}

function calculatePredictions(studentData) {
    const predictions = [];
    
    // Calculate score for each program
    for (const [programKey, program] of Object.entries(programWeights)) {
        let score = 0;
        
        if (programKey === 'STE') {
            score = (studentData.mathematics * 0.25) +
                   (studentData.science * 0.25) +
                   (studentData.english * 0.15) +
                   (studentData.overall * 0.20) +
                   (studentData.dostExamResult === 'passed' ? 15 : 0);
        } else if (programKey === 'SPFL') {
            score = (studentData.english * 0.30) +
                   (studentData.filipino * 0.25) +
                   (studentData.overall * 0.25) +
                   (studentData.aralingPanlipunan * 0.20);
        } else if (programKey === 'SPTVL') {
            score = (studentData.edukasyonPangkabuhayan * 0.30) +
                   (studentData.mapeh * 0.25) +
                   (studentData.overall * 0.25) +
                   20; // Practical skills bonus
        } else if (programKey === 'TOP5') {
            score = (studentData.overall * 0.40) +
                   (studentData.mathematics * 0.20) +
                   (studentData.science * 0.20) +
                   (studentData.english * 0.20);
        } else if (programKey === 'HETERO') {
            score = (studentData.overall * 0.50) + 50; // Base score
        }
        
        // Normalize to percentage
        score = Math.min(Math.max(score, 0), 100);
        
        // Check if meets minimum requirement
        if (score >= program.minScore) {
            predictions.push({
                program: programKey,
                name: program.name,
                description: program.description,
                score: Math.round(score),
                recommendation: getRecommendation(score)
            });
        }
    }
    
    // Sort by score descending
    return predictions.sort((a, b) => b.score - a.score);
}

function getRecommendation(score) {
    if (score >= 90) return 'Highly Recommended';
    if (score >= 80) return 'Strongly Recommended';
    if (score >= 70) return 'Recommended';
    return 'Eligible';
}

function displayPredictionResults(predictions) {
    const container = document.getElementById('predictionResults');
    container.innerHTML = '';
    
    if (predictions.length === 0) {
        container.innerHTML = `
            <div class="bg-red-50 border-l-4 border-red-500 p-4 rounded mb-4">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i class="fas fa-exclamation-circle text-red-500 mt-0.5"></i>
                    </div>
                    <div class="ml-3">
                        <h5 class="text-sm font-semibold text-red-800">No Strong Predictions Found</h5>
                        <p class="text-sm text-red-700 mt-1">
                            Based on your academic profile, we couldn't find a strong match for special programs.
                            Consider trying manual selection or consulting with school guidance.
                        </p>
                    </div>
                </div>
            </div>
        `;
        return;
    }
    
    predictions.forEach((pred, index) => {
        const isTop = index === 0;
        
        // Determine colors based on score
        let scoreColor, badgeColor, progressColor, borderColor;
        
        if (pred.score >= 90) {
            scoreColor = 'text-red-600';
            badgeColor = 'bg-red-100 text-red-800';
            progressColor = 'bg-red-600';
            borderColor = 'border-red-300';
        } else if (pred.score >= 80) {
            scoreColor = 'text-yellow-600';
            badgeColor = 'bg-yellow-100 text-yellow-800';
            progressColor = 'bg-yellow-500';
            borderColor = 'border-yellow-300';
        } else {
            scoreColor = 'text-gray-600';
            badgeColor = 'bg-gray-100 text-gray-800';
            progressColor = 'bg-gray-500';
            borderColor = 'border-gray-300';
        }
        
        const card = document.createElement('div');
        card.className = `border rounded-xl p-5 mb-4 ${isTop ? 'border-red-300 bg-red-50' : 'bg-white'} hover:shadow-md transition-shadow ${borderColor}`;
        
        card.innerHTML = `
            <div class="flex flex-col md:flex-row md:items-center gap-4">
                <div class="flex-shrink-0">
                    <div class="w-16 h-16 ${isTop ? 'bg-red-100 border-2 border-red-200' : 'bg-gray-100'} rounded-lg flex items-center justify-center">
                        <span class="text-2xl ${isTop ? 'text-red-600' : 'text-gray-600'}">
                            ${getProgramIcon(pred.program)}
                        </span>
                    </div>
                </div>
                <div class="flex-1">
                    <div class="flex flex-wrap items-center gap-2 mb-2">
                        <h5 class="text-lg font-semibold text-gray-800">${pred.name}</h5>
                        ${isTop ? '<span class="bg-red-100 text-red-700 text-xs font-bold px-2 py-1 rounded-full border border-red-200"><i class="fas fa-star mr-1"></i>Top Match</span>' : ''}
                        <span class="${badgeColor} text-xs font-semibold px-2 py-1 rounded-full border ${isTop ? 'border-red-200' : 'border-gray-200'}">
                            <i class="fas fa-${pred.recommendation === 'Highly Recommended' ? 'fire' : pred.recommendation === 'Strongly Recommended' ? 'bolt' : 'check'} mr-1"></i>
                            ${pred.recommendation}
                        </span>
                    </div>
                    <p class="text-gray-600 text-sm mb-3">${pred.description}</p>
                    
                    <div class="space-y-2">
                        <div class="flex justify-between items-center">
                            <span class="font-medium text-gray-700">Prediction Score</span>
                            <div class="flex items-center gap-2">
                                <span class="font-bold ${scoreColor}">
                                    ${pred.score}%
                                </span>
                                ${isTop ? '<span class="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Best Match</span>' : ''}
                            </div>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2.5">
                            <div class="${progressColor} h-2.5 rounded-full transition-all duration-500" style="width: ${pred.score}%"></div>
                        </div>
                        <div class="flex justify-between text-xs text-gray-500">
                            <span>Low</span>
                            <span>Medium</span>
                            <span>High</span>
                        </div>
                    </div>
                </div>
                ${isTop ? `
                <div class="flex-shrink-0">
                    <button onclick="confirmAiSelection('${pred.program}')"
                        class="px-4 py-2 bg-gradient-to-r from-primary to-primary-dark text-white rounded-lg font-semibold hover:from-primary-dark hover:to-primary transition-all flex items-center gap-2 shadow hover:shadow-md">
                        <i class="fas fa-check"></i>
                        Select This
                    </button>
                </div>
                ` : ''}
            </div>
        `;
        container.appendChild(card);
    });
    
    // Add summary section
    const summary = document.createElement('div');
    summary.className = 'bg-gray-50 rounded-xl p-4 mt-6 border border-gray-200';
    summary.innerHTML = `
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <i class="fas fa-chart-pie text-red-600"></i>
            </div>
            <div>
                <h6 class="font-semibold text-gray-800">Prediction Summary</h6>
                <p class="text-sm text-gray-600">
                    Based on ${predictions.length} program matches. Scores above 80% indicate strong alignment with program requirements.
                </p>
            </div>
        </div>
    `;
    container.appendChild(summary);
}

function getProgramIcon(program) {
    const icons = {
        STE: '🔬',
        SPFL: '🗣️',
        SPTVL: '🔧',
        TOP5: '🏆',
        HETERO: '📖'
    };
    return icons[program] || '📚';
}

function confirmAiSelection(program) {
    const prediction = aiPredictions.find(p => p.program === program);
    if (!prediction) return;
    
    const message = document.getElementById('aiConfirmationMessage');
    if (message) {
        message.innerHTML = `
            You are selecting <strong class="text-primary">${prediction.name}</strong> with a 
            <span class="font-bold ${prediction.score >= 90 ? 'text-red-600' : prediction.score >= 80 ? 'text-yellow-600' : 'text-gray-600'}">
                ${prediction.score}%
            </span> prediction score.
            <br><br>
            This will be submitted as your preferred section placement.
        `;
    }
    
    // Store the selected program
    const confirmationModal = document.getElementById('aiConfirmationModal');
    if (confirmationModal) {
        confirmationModal.setAttribute('data-selected-program', program);
    }
    
    // Close AI prediction modal
    const aiModal = document.getElementById('aiPredictionModal');
    if (aiModal) {
        aiModal.classList.add('hidden');
    }
    
    // Show confirmation modal
    if (confirmationModal) {
        confirmationModal.classList.remove('hidden');
    }
}

function setupAiPredictionModal() {
    const modal = document.getElementById('aiPredictionModal');
    const closeBtn = document.getElementById('closeAiModal');
    const tryManualBtn = document.getElementById('tryManualBtn');
    const confirmAiBtn = document.getElementById('confirmAiPredictionBtn');
    
    if (!modal) {
        console.error('AI Prediction Modal not found');
        return;
    }
    
    // Close modal
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }
    
    // Try manual instead
    if (tryManualBtn) {
        tryManualBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            window.location.href = 'sectionPlacement.html';
        });
    }
    
    // Confirm top prediction - FIX THIS PART
    if (confirmAiBtn) {
        confirmAiBtn.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Accept Top Recommendation clicked');
            
            if (aiPredictions && aiPredictions.length > 0) {
                confirmAiSelection(aiPredictions[0].program);
            } else {
                console.error('No predictions available');
                // If no predictions, calculate them first
                const studentData = collectStudentData();
                aiPredictions = calculatePredictions(studentData);
                if (aiPredictions.length > 0) {
                    confirmAiSelection(aiPredictions[0].program);
                }
            }
        });
    } else {
        console.error('Confirm AI button not found');
    }
    
    // Close when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
    
    // Escape key to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
}

function setupAiConfirmationModal() {
    const modal = document.getElementById('aiConfirmationModal');
    const cancelBtn = document.getElementById('cancelAiConfirmationBtn');
    const confirmBtn = document.getElementById('finalConfirmAiBtn');
    
    if (!modal) return;
    
    // Cancel button
    if (cancelBtn) {
        cancelBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            // Go back to AI prediction modal
            const aiModal = document.getElementById('aiPredictionModal');
            if (aiModal) {
                aiModal.classList.remove('hidden');
            }
        });
    }
    
    // Final confirmation
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            const selectedProgram = modal.getAttribute('data-selected-program');
            
            // Show loading
            const originalText = confirmBtn.innerHTML;
            confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Submitting...';
            confirmBtn.disabled = true;
            
            // Simulate submission
            setTimeout(() => {
                // Close confirmation modal
                modal.classList.add('hidden');
                document.body.style.overflow = 'auto';
                
                // Reset button
                confirmBtn.innerHTML = originalText;
                confirmBtn.disabled = false;
                
                // Show success modal
                showAiSuccessModal(selectedProgram);
            }, 1500);
        });
    }
    
    // Close when clicking outside
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            const aiModal = document.getElementById('aiPredictionModal');
            if (aiModal) {
                aiModal.classList.remove('hidden');
            }
        }
    });
}

function showAiSuccessModal(program) {
    const prediction = aiPredictions.find(p => p.program === program);
    const modal = document.getElementById('aiSuccessSubmitModal');
    const message = document.getElementById('aiSuccessMessage');
    
    if (!modal) return;
    
    if (message && prediction) {
        message.innerHTML = `
            Your AI-predicted section (<strong>${program}</strong>) with a 
            <span class="font-bold ${prediction.score >= 90 ? 'text-red-600' : prediction.score >= 80 ? 'text-yellow-600' : 'text-gray-600'}">
                ${prediction.score}%
            </span> match has been successfully submitted.
            <br><br>
            The school will review your placement shortly.
        `;
    }
    
    // Show the modal
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
}

function closeAiSuccessModal() {
    const modal = document.getElementById('aiSuccessSubmitModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        document.body.style.overflow = 'auto';
        // Redirect to home or dashboard
        window.location.href = 'landing.html';
    }
}

// Make functions available globally
window.selectMethod = selectMethod;
window.clearSelection = clearSelection;
window.confirmAiSelection = confirmAiSelection;
window.closeAiSuccessModal = closeAiSuccessModal;