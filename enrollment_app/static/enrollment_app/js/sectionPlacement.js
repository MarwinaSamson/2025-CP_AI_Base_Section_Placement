// Global variables
let rankedPrograms = [];
let selectedProgram = null;

// Program data with detailed information
const programData = {
    STE: {
        name: "STE (Science Technology and Engineering)",
        description: "Focuses on science, technology, engineering, and mathematics through hands-on learning and research-based activities.",
        icon: "🔬",
        color: "blue",
        requirements: {
            mathematics: 85,
            science: 85,
            english: 80,
            overall: 85
        }
    },
    SPFL: {
        name: "SPFL (Special Program in Foreign Language)",
        description: "Enhances communication skills through foreign language learning, particularly Chinese.",
        icon: "🗣️",
        color: "purple",
        requirements: {
            english: 85,
            filipino: 80,
            overall: 82
        }
    },
    SPTVL: {
        name: "SPTVL (Special Program in Technical Vocational Livelihood)",
        description: "Provides practical skills and knowledge in various technical and vocational fields.",
        icon: "🔧",
        color: "orange",
        requirements: {
            ep: 80,
            mapeh: 78,
            overall: 78
        }
    },
    SNED: {
        name: "SNED (Special Needs Education)",
        description: "Specialized program designed for students with special educational needs, providing tailored support and learning approaches.",
        icon: "🤝",
        color: "green",
        requirements: {
            overall: 75,
            specialNeeds: true
        }
    },
    OHSP: {
        name: "OHSP (Open High School Program)",
        description: "Flexible learning program for working students and those who need alternative schedules.",
        icon: "📚",
        color: "teal",
        requirements: {
            overall: 75,
            workingStudent: true
        }
    },
    REGULAR: {
        name: "Regular Heterogeneous Section",
        description: "Standard academic section providing comprehensive basic education curriculum.",
        icon: "📖",
        color: "gray",
        requirements: {
            overall: 70
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupRecommendationModal();
    setupProgramDetailsModal();
    setupSuccessModal();
});

function setupRecommendationModal() {
    const modal = document.getElementById('recommendationModal');
    const seeSectionBtn = document.getElementById('seeSectionBtn');
    const closeBtn = document.getElementById('closeRecommendationModal');
    
    if (!modal || !seeSectionBtn) return;
    
    // Open modal when clicking "See Recommended Program"
    seeSectionBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Collect student data and calculate rankings
        const studentData = collectStudentData();
        rankedPrograms = calculateProgramRankings(studentData);
        
        // Display ranked programs
        displayRankedPrograms(rankedPrograms, studentData);
        
        // Show modal
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

function collectStudentData() {
    const subjectInputs = document.querySelectorAll('.subject');
    const subjects = Array.from(subjectInputs);
    
    const data = {
        mathematics: parseFloat(subjects[0]?.value) || 0,
        aralingPanlipunan: parseFloat(subjects[1]?.value) || 0,
        english: parseFloat(subjects[2]?.value) || 0,
        edukasyonPagpapakatao: parseFloat(subjects[3]?.value) || 0,
        science: parseFloat(subjects[4]?.value) || 0,
        edukasyonPangkabuhayan: parseFloat(subjects[5]?.value) || 0,
        filipino: parseFloat(subjects[6]?.value) || 0,
        mapeh: parseFloat(subjects[7]?.value) || 0,
        overall: parseFloat(document.getElementById('overallAverage')?.value) || 0,
        dostExamResult: document.querySelector('select')?.value || 'failed',
        hasGrades: false
    };
    
    // Check if any grades were entered
    data.hasGrades = data.mathematics > 0 || data.english > 0 || data.science > 0 || data.overall > 0;
    
    return data;
}

function calculateProgramRankings(studentData) {
    const rankings = [];
    
    // Calculate score for each program
    for (const [programKey, program] of Object.entries(programData)) {
        let score = 0;
        let reasons = [];
        
        if (!studentData.hasGrades) {
            // Default ranking when no grades are entered
            const defaultRanks = { STE: 85, SPFL: 80, SPTVL: 75, SNED: 70, OHSP: 65, REGULAR: 90 };
            score = defaultRanks[programKey] || 70;
            reasons.push('Complete your academic data for personalized recommendations');
            reasons.push('This program is available for enrollment');
            reasons.push('Click to learn more about program requirements');
        } else {
            // Calculate based on actual grades
            if (programKey === 'STE') {
                const mathScore = (studentData.mathematics / 100) * 30;
                const scienceScore = (studentData.science / 100) * 30;
                const englishScore = (studentData.english / 100) * 15;
                const overallScore = (studentData.overall / 100) * 20;
                const dostBonus = studentData.dostExamResult === 'passed' ? 5 : 0;
                
                score = mathScore + scienceScore + englishScore + overallScore + dostBonus;
                
                if (studentData.mathematics >= 85) reasons.push(`Excellent Mathematics grade (${studentData.mathematics})`);
                else if (studentData.mathematics > 0) reasons.push(`Mathematics grade: ${studentData.mathematics}`);
                
                if (studentData.science >= 85) reasons.push(`Strong Science performance (${studentData.science})`);
                else if (studentData.science > 0) reasons.push(`Science grade: ${studentData.science}`);
                
                if (studentData.dostExamResult === 'passed') reasons.push('DOST exam passed');
                
                if (studentData.overall >= 85) reasons.push(`High overall average (${studentData.overall})`);
                else if (studentData.overall > 0) reasons.push(`Overall average: ${studentData.overall}`);
                
            } else if (programKey === 'SPFL') {
                const englishScore = (studentData.english / 100) * 35;
                const filipinoScore = (studentData.filipino / 100) * 30;
                const apScore = (studentData.aralingPanlipunan / 100) * 20;
                const overallScore = (studentData.overall / 100) * 15;
                
                score = englishScore + filipinoScore + apScore + overallScore;
                
                if (studentData.english >= 85) reasons.push(`Outstanding English skills (${studentData.english})`);
                else if (studentData.english > 0) reasons.push(`English grade: ${studentData.english}`);
                
                if (studentData.filipino >= 80) reasons.push(`Strong Filipino proficiency (${studentData.filipino})`);
                else if (studentData.filipino > 0) reasons.push(`Filipino grade: ${studentData.filipino}`);
                
                if (studentData.aralingPanlipunan >= 80) reasons.push(`Good Araling Panlipunan grade (${studentData.aralingPanlipunan})`);
                else if (studentData.aralingPanlipunan > 0) reasons.push(`Araling Panlipunan grade: ${studentData.aralingPanlipunan}`);
                
            } else if (programKey === 'SPTVL') {
                const epScore = (studentData.edukasyonPangkabuhayan / 100) * 35;
                const mapehScore = (studentData.mapeh / 100) * 30;
                const overallScore = (studentData.overall / 100) * 25;
                const practicalBonus = 10;
                
                score = epScore + mapehScore + overallScore + practicalBonus;
                
                if (studentData.edukasyonPangkabuhayan >= 80) reasons.push(`Strong EP performance (${studentData.edukasyonPangkabuhayan})`);
                else if (studentData.edukasyonPangkabuhayan > 0) reasons.push(`EP grade: ${studentData.edukasyonPangkabuhayan}`);
                
                if (studentData.mapeh >= 78) reasons.push(`Good MAPEH grade (${studentData.mapeh})`);
                else if (studentData.mapeh > 0) reasons.push(`MAPEH grade: ${studentData.mapeh}`);
                
                reasons.push('Well-suited for hands-on learning');
                
            } else if (programKey === 'SNED') {
                const overallScore = (studentData.overall / 100) * 40;
                const supportScore = 30;
                const adaptabilityScore = 30;
                
                score = overallScore + supportScore + adaptabilityScore;
                
                reasons.push('Provides specialized learning support');
                reasons.push('Tailored teaching approaches');
                reasons.push('Smaller class sizes for individual attention');
                
            } else if (programKey === 'OHSP') {
                const overallScore = (studentData.overall / 100) * 50;
                const flexibilityScore = 50;
                
                score = overallScore + flexibilityScore;
                
                reasons.push('Flexible learning schedule');
                reasons.push('Accommodates work commitments');
                reasons.push('Self-paced learning modules');
                
            } else if (programKey === 'REGULAR') {
                const overallScore = (studentData.overall / 100) * 60;
                const balanceScore = 40;
                
                score = overallScore + balanceScore;
                
                reasons.push('Comprehensive curriculum coverage');
                reasons.push('Balanced academic approach');
                if (studentData.overall >= 75) reasons.push(`Meets academic standards (${studentData.overall})`);
                else if (studentData.overall > 0) reasons.push(`Overall average: ${studentData.overall}`);
            }
        }
        
        // Ensure minimum reasons
        if (reasons.length === 0) {
            reasons.push('Eligible for this program');
            reasons.push('Meet with guidance counselor for more details');
        }
        
        rankings.push({
            program: programKey,
            name: program.name,
            description: program.description,
            icon: program.icon,
            color: program.color,
            score: Math.max(Math.round(score), 60), // Minimum score of 60
            reasons: reasons
        });
    }
    
    // Sort by score descending
    return rankings.sort((a, b) => b.score - a.score);
}

function displayRankedPrograms(programs, studentData) {
    const container = document.getElementById('rankedProgramsList');
    container.innerHTML = '';
    
    const rankLabels = ['Top Recommendation', '2nd Recommendation', '3rd Recommendation', '4th Recommendation', '5th Recommendation', '6th Recommendation'];
    
    programs.forEach((program, index) => {
        const rankLabel = rankLabels[index] || `${index + 1}th Recommendation`;
        const isTop = index === 0;
        
        // Color schemes based on rank
        let bgColor, borderColor, badgeColor, iconBg;
        
        if (index === 0) {
            bgColor = 'bg-red-50';
            borderColor = 'border-red-300';
            badgeColor = 'bg-red-100 text-red-800 border-red-200';
            iconBg = 'bg-red-100';
        } else if (index === 1) {
            bgColor = 'bg-yellow-50';
            borderColor = 'border-yellow-300';
            badgeColor = 'bg-yellow-100 text-yellow-800 border-yellow-200';
            iconBg = 'bg-yellow-100';
        } else if (index === 2) {
            bgColor = 'bg-blue-50';
            borderColor = 'border-blue-300';
            badgeColor = 'bg-blue-100 text-blue-800 border-blue-200';
            iconBg = 'bg-blue-100';
        } else {
            bgColor = 'bg-gray-50';
            borderColor = 'border-gray-300';
            badgeColor = 'bg-gray-100 text-gray-800 border-gray-200';
            iconBg = 'bg-gray-100';
        }
        
        const card = document.createElement('div');
        card.className = `${bgColor} border-2 ${borderColor} rounded-xl p-5 cursor-pointer hover:shadow-lg transition-all duration-300 transform hover:scale-[1.02]`;
        card.onclick = () => showProgramDetails(program, index, studentData);
        
        card.innerHTML = `
            <div class="flex items-start gap-4">
                <div class="flex-shrink-0">
                    <div class="w-16 h-16 ${iconBg} rounded-xl flex items-center justify-center border-2 ${borderColor}">
                        <span class="text-3xl">${program.icon}</span>
                    </div>
                </div>
                <div class="flex-1">
                    <div class="flex flex-wrap items-center gap-2 mb-2">
                        <span class="${badgeColor} text-xs font-bold px-3 py-1 rounded-full border">
                            ${isTop ? '⭐ ' : ''}${rankLabel}
                        </span>
                        <span class="bg-white text-gray-700 text-xs font-semibold px-3 py-1 rounded-full border border-gray-300">
                            ${program.score}% Match
                        </span>
                    </div>
                    <h5 class="text-lg font-bold text-gray-800 mb-1">${program.name}</h5>
                    <p class="text-sm text-gray-600 mb-3">${program.description}</p>
                    <div class="flex items-center justify-between">
                        <div class="text-xs text-gray-500">
                            <i class="fas fa-check-circle text-green-600 mr-1"></i>
                            ${program.reasons.length} matching factors
                        </div>
                        <div class="text-primary text-sm font-semibold hover:text-primary-dark flex items-center gap-1">
                            View Details
                            <i class="fas fa-arrow-right"></i>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(card);
    });
    
    // Add info message if no grades entered
    if (!studentData.hasGrades) {
        const infoBox = document.createElement('div');
        infoBox.className = 'bg-blue-50 border-l-4 border-blue-500 p-4 rounded mt-4';
        infoBox.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <i class="fas fa-lightbulb text-blue-500 mt-0.5"></i>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-blue-800">
                        <strong>Tip:</strong> Fill in your Grade 6 academic data to get personalized program recommendations based on your performance!
                    </p>
                </div>
            </div>
        `;
        container.appendChild(infoBox);
    }
}

function showProgramDetails(program, rank, studentData) {
    selectedProgram = program;
    
    const modal = document.getElementById('programDetailsModal');
    const rankLabels = ['Top Recommendation', '2nd Recommendation', '3rd Recommendation', '4th Recommendation', '5th Recommendation', '6th Recommendation'];
    const rankLabel = rankLabels[rank] || `${rank + 1}th Recommendation`;
    
    // Update modal content
    document.getElementById('detailProgramIcon').textContent = program.icon;
    document.getElementById('detailProgramName').textContent = program.name;
    document.getElementById('detailProgramRank').textContent = rankLabel;
    document.getElementById('detailProgramScore').textContent = `${program.score}% Match`;
    document.getElementById('detailProgramDescription').textContent = program.description;
    
    // Generate detailed explanation
    const explanation = generateDetailedExplanation(program, rank, studentData);
    document.getElementById('detailProgramExplanation').innerHTML = explanation;
    
    // Hide recommendation modal
    document.getElementById('recommendationModal').classList.add('hidden');
    
    // Show details modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function generateDetailedExplanation(program, rank, studentData) {
    let explanation = '';
    
    if (rank === 0) {
        explanation = `
            <div class="mb-4">
                <h6 class="font-bold text-gray-800 mb-2 flex items-center gap-2">
                    <i class="fas fa-trophy text-yellow-500"></i>
                    Why This is Your Top Match
                </h6>
                <p class="text-gray-700 mb-3">
                    ${studentData.hasGrades 
                        ? `Based on your academic performance, <strong>${program.name}</strong> is the best fit for your skills and abilities. Here's why:` 
                        : `<strong>${program.name}</strong> is highly recommended for incoming Grade 7 students. Here's what makes it a great choice:`}
                </p>
            </div>
        `;
    } else if (rank === 1) {
        explanation = `
            <div class="mb-4">
                <h6 class="font-bold text-gray-800 mb-2 flex items-center gap-2">
                    <i class="fas fa-medal text-gray-400"></i>
                    Why This is a Strong Alternative
                </h6>
                <p class="text-gray-700 mb-3">
                    ${studentData.hasGrades 
                        ? `<strong>${program.name}</strong> is an excellent second choice that aligns well with your profile:` 
                        : `<strong>${program.name}</strong> is another excellent option to consider:`}
                </p>
            </div>
        `;
    } else {
        explanation = `
            <div class="mb-4">
                <h6 class="font-bold text-gray-800 mb-2">
                    Why This Program Suits You
                </h6>
                <p class="text-gray-700 mb-3">
                    <strong>${program.name}</strong> ${studentData.hasGrades ? 'is recommended based on your qualifications:' : 'is available and offers unique benefits:'}
                </p>
            </div>
        `;
    }
    
    // Add specific reasons
    explanation += `
        <div class="space-y-3 mb-4">
            ${program.reasons.map(reason => `
                <div class="flex items-start gap-3 bg-white p-3 rounded-lg border border-gray-200">
                    <i class="fas fa-check-circle text-green-600 mt-1"></i>
                    <span class="text-gray-700">${reason}</span>
                </div>
            `).join('')}
        </div>
    `;
    
    // Add program-specific insights
    if (program.program === 'STE') {
        explanation += `
            <div class="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h6 class="font-semibold text-blue-900 mb-2">What to Expect in STE</h6>
                <ul class="text-sm text-blue-800 space-y-1">
                    <li>• Advanced Mathematics and Science subjects</li>
                    <li>• Hands-on laboratory experiments</li>
                    <li>• Research and innovation projects</li>
                    <li>• Preparation for STEM college programs</li>
                </ul>
            </div>
        `;
    } else if (program.program === 'SPFL') {
        explanation += `
            <div class="bg-purple-50 p-4 rounded-lg border border-purple-200">
                <h6 class="font-semibold text-purple-900 mb-2">What to Expect in SPFL</h6>
                <ul class="text-sm text-purple-800 space-y-1">
                    <li>• Intensive foreign language training</li>
                    <li>• Cultural immersion activities</li>
                    <li>• Communication and presentation skills</li>
                    <li>• International exchange opportunities</li>
                </ul>
            </div>
        `;
    } else if (program.program === 'SPTVL') {
        explanation += `
            <div class="bg-orange-50 p-4 rounded-lg border border-orange-200">
                <h6 class="font-semibold text-orange-900 mb-2">What to Expect in SPTVL</h6>
                <ul class="text-sm text-orange-800 space-y-1">
                    <li>• Hands-on technical training</li>
                    <li>• Vocational skill development</li>
                    <li>• Industry partnerships and internships</li>
                    <li>• Direct career pathway preparation</li>
                </ul>
            </div>
        `;
    } else if (program.program === 'SNED') {
        explanation += `
            <div class="bg-green-50 p-4 rounded-lg border border-green-200">
                <h6 class="font-semibold text-green-900 mb-2">What to Expect in SNED</h6>
                <ul class="text-sm text-green-800 space-y-1">
                    <li>• Individualized education plans</li>
                    <li>• Specialized teaching methods</li>
                    <li>• Additional support services</li>
                    <li>• Inclusive learning environment</li>
                </ul>
            </div>
        `;
    } else if (program.program === 'OHSP') {
        explanation += `
            <div class="bg-teal-50 p-4 rounded-lg border border-teal-200">
                <h6 class="font-semibold text-teal-900 mb-2">What to Expect in OHSP</h6>
                <ul class="text-sm text-teal-800 space-y-1">
                    <li>• Flexible class schedules</li>
                    <li>• Independent learning modules</li>
                    <li>• Weekend and evening classes available</li>
                    <li>• Work-study balance support</li>
                </ul>
            </div>
        `;
    } else if (program.program === 'REGULAR') {
        explanation += `
            <div class="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h6 class="font-semibold text-gray-900 mb-2">What to Expect in Regular Section</h6>
                <ul class="text-sm text-gray-800 space-y-1">
                    <li>• Comprehensive basic education curriculum</li>
                    <li>• Balanced academic subjects</li>
                    <li>• Solid foundation for senior high school</li>
                    <li>• Flexible track selection later</li>
                </ul>
            </div>
        `;
    }
    
    return explanation;
}

function setupProgramDetailsModal() {
    const modal = document.getElementById('programDetailsModal');
    const backBtn = document.getElementById('backToRecommendationsBtn');
    const confirmBtn = document.getElementById('confirmProgramBtn');
    const closeBtn = document.getElementById('closeProgramDetailsModal');
    
    if (!modal) return;
    
    // Back to recommendations
    if (backBtn) {
        backBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.getElementById('recommendationModal').classList.remove('hidden');
        });
    }
    
    // Close button
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.getElementById('recommendationModal').classList.remove('hidden');
        });
    }
    
    // Confirm selection
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            const originalText = confirmBtn.innerHTML;
            confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Submitting...';
            confirmBtn.disabled = true;
            
            setTimeout(() => {
                modal.classList.add('hidden');
                document.body.style.overflow = 'auto';
                confirmBtn.innerHTML = originalText;
                confirmBtn.disabled = false;
                showSuccessModal();
            }, 1500);
        });
    }
}

function setupSuccessModal() {
    const closeBtn = document.getElementById('closeSuccessModalBtn');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            const modal = document.getElementById('successSubmitModal');
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = 'auto';
            window.location.href = '/';
        });
    }
}

function showSuccessModal() {
    const modal = document.getElementById('successSubmitModal');
    const message = document.getElementById('successMessage');
    
    if (message && selectedProgram) {
        message.innerHTML = `
            Your selection of <strong class="text-primary">${selectedProgram.name}</strong> 
            with a <strong class="text-green-600">${selectedProgram.score}% match</strong> has been successfully submitted.
            <br><br>
            The school administration will review your placement and contact you for the next steps.
        `;
    }
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
    document.body.style.overflow = 'hidden';
}

// Make functions globally accessible
window.showProgramDetails = showProgramDetails;