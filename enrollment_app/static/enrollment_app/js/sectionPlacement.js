// Global variables
let rankedPrograms = [];
let selectedProgram = null;
let enrollmentContext = null;

// Program metadata
const programData = {
    STE: {
        key: 'STE',
        name: 'STE (Science, Technology, Engineering)',
        description: 'Advanced science and math track with research and lab focus.',
        icon: '🔬',
        color: 'blue'
    },
    SPFL: {
        key: 'SPFL',
        name: 'SPFL (Special Program in Foreign Language)',
        description: 'Language-focused program emphasizing communication and culture.',
        icon: '🗣️',
        color: 'purple'
    },
    SPTVE: {
        key: 'SPTVE',
        name: 'SPTVE (Special Program in Technical-Vocational Education)',
        description: 'Hands-on technical and vocational learning path.',
        icon: '🔧',
        color: 'orange'
    },
    SNED: {
        key: 'SNED',
        name: 'SNED (Special Needs Education)',
        description: 'Individualized support for learners requiring accommodations.',
        icon: '🤝',
        color: 'green'
    },
    OHSP: {
        key: 'OHSP',
        name: 'OHSP (Open High School Program)',
        description: 'Flexible, distance-friendly pathway for unique circumstances.',
        icon: '📚',
        color: 'teal'
    },
    TOP5: {
        key: 'TOP5',
        name: 'Top 5 Regular',
        description: 'Advanced regular section for high achievers.',
        icon: '🏅',
        color: 'amber'
    },
    REGULAR: {
        key: 'REGULAR',
        name: 'Regular',
        description: 'Standard curriculum with balanced workload.',
        icon: '📖',
        color: 'gray'
    }
};

function getContextPayload() {
    if (enrollmentContext) return enrollmentContext;
    const node = document.getElementById('recommendationPayload');
    if (!node) return {};
    try {
        enrollmentContext = JSON.parse(node.textContent);
    } catch (e) {
        console.error('Failed to parse recommendation payload', e);
        enrollmentContext = {};
    }
    return enrollmentContext;
}

const toBool = (value) => {
    if (value === undefined || value === null) return false;
    if (typeof value === 'boolean') return value;
    const str = String(value).toLowerCase();
    return ['yes', 'true', '1', 'y'].includes(str);
};

function getFormAcademicData() {
    const subjectInputs = document.querySelectorAll('.subject');
    const getVal = (name) => {
        const input = document.querySelector(`input[name="${name}"]`);
        return input ? parseFloat(input.value) || 0 : 0;
    };

    const grades = {
        mathematics: getVal('mathematics'),
        araling_panlipunan: getVal('araling_panlipunan'),
        english: getVal('english'),
        edukasyon_sa_pagpapakatao: getVal('edukasyon_sa_pagpapakatao'),
        science: getVal('science'),
        edukasyon_pangkabuhayan: getVal('edukasyon_pangkabuhayan'),
        filipino: getVal('filipino'),
        mapeh: getVal('mapeh'),
    };

    const validGrades = Object.values(grades).filter((g) => g > 0);
    const overallAverage = validGrades.length ? +(validGrades.reduce((a, b) => a + b, 0) / validGrades.length).toFixed(2) : 0;

    const dostSelect = document.querySelector('select[name="dost_exam_result"]');
    const dost_exam_result = dostSelect ? dostSelect.value : '';

    return { ...grades, overall_average: overallAverage, dost_exam_result };
}

function mergeContextData() {
    const payload = getContextPayload();
    const student = payload.student_data || {};
    const survey = payload.survey_data || {};
    const academic = { ...(payload.academic_data || {}), ...getFormAcademicData() };

    return { student, survey, academic };
}

function normalizeDost(value) {
    const v = (value || '').toLowerCase();
    if (v === 'passed') return 'passed';
    if (v === 'failed') return 'failed';
    return 'not_taken';
}

function calculateSurveyScores(survey) {
    const scores = {
        STE: 0,
        SPFL: 0,
        SPTVE: 0,
        OHSP: 0,
        SNED: 0,
        TOP5: 0,
        REGULAR: 0,
    };

    const interested = survey.interested_program;
    if (interested) {
        scores[interested] = (scores[interested] || 0) + 5;
    }

    if (survey.program_motivation === 'Very motivated' && interested) {
        scores[interested] += 2;
    } else if (survey.program_motivation === 'Slightly motivated' && interested) {
        scores[interested] += 1;
    }

    const enjoyedSubjects = survey.enjoyed_subjects || [];
    if (enjoyedSubjects.includes('Math') && enjoyedSubjects.includes('Science')) scores.STE += 3;
    if (enjoyedSubjects.includes('English') && enjoyedSubjects.includes('Filipino')) scores.SPFL += 2;
    if (enjoyedSubjects.includes('TLE')) scores.SPTVE += 2;

    const activities = survey.enjoyed_activities || [];
    if (activities.includes('Science experiments')) scores.STE += 2;
    if (activities.includes('Hands-on activities')) scores.SPTVE += 2;
    if (activities.includes('Reading') || activities.includes('Language-related activities')) scores.SPFL += 2;

    if (survey.study_hours === 'More than 3 hours') {
        scores.STE += 2;
        scores.TOP5 += 1;
    } else if (survey.study_hours === 'Less than 1 hour') {
        scores.OHSP += 1;
    }

    if (survey.assignments_on_time === 'Always') {
        scores.STE += 2;
        scores.TOP5 += 2;
    } else if (survey.assignments_on_time === 'Rarely') {
        scores.OHSP += 1;
    }

    if (survey.handle_difficult_lessons === 'Research') scores.STE += 2;
    if (survey.handle_difficult_lessons === 'Give up') {
        scores.SNED += 1;
        scores.OHSP += 1;
    }

    if (survey.device_availability === 'Not available' || survey.internet_access === 'No internet') scores.OHSP += 2;

    if (survey.absences === '0-3') {
        scores.STE += 2;
        scores.TOP5 += 2;
    } else if (survey.absences === 'More than 20') {
        scores.OHSP += 2;
    }

    const difficultyAreas = survey.difficulty_areas || [];
    if (difficultyAreas.includes('None')) {
        scores.STE += 2;
        scores.TOP5 += 2;
    }
    if (difficultyAreas.some((area) => ['Focusing', 'Social interaction'].includes(area))) {
        scores.SNED += 3;
    }

    if (survey.extra_support === 'Yes') scores.SNED += 3;

    if (survey.distance_from_school === 'More than 5 km' || survey.travel_difficulty === 'Yes') scores.OHSP += 2;

    return scores;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupRecommendationModalChrome();
    setupProgramDetailsModal();
    setupSuccessModal();
});

function setupRecommendationModalChrome() {
    const modal = document.getElementById('recommendationModal');
    const closeBtn = document.getElementById('closeRecommendationModal');
    if (!modal) return;

    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        });
    }

    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
            document.body.style.overflow = 'auto';
        }
    });
}

// Core recommendation renderer (invoked after grade verification)
window.renderProgramRecommendations = function renderProgramRecommendations() {
    const modal = document.getElementById('recommendationModal');
    const data = mergeContextData();
    rankedPrograms = runRecommendationRules(data);
    displayRankedPrograms(rankedPrograms, data);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
};

function runRecommendationRules({ student, survey, academic }) {
    const result = [];

    const acad = academic || {};
    const overall = parseFloat(acad.overall_average) || 0;
    const grades = {
        mathematics: parseFloat(acad.mathematics) || 0,
        science: parseFloat(acad.science) || 0,
        english: parseFloat(acad.english) || 0,
        filipino: parseFloat(acad.filipino) || 0,
        araling_panlipunan: parseFloat(acad.araling_panlipunan) || 0,
        edukasyon_sa_pagpapakatao: parseFloat(acad.edukasyon_sa_pagpapakatao) || 0,
        edukasyon_pangkabuhayan: parseFloat(acad.edukasyon_pangkabuhayan) || 0,
        mapeh: parseFloat(acad.mapeh) || 0,
    };

    const allAbove85 = Object.values(grades).every((g) => g >= 85 && g > 0);
    const stemCore = grades.mathematics >= 85 && grades.science >= 85 && grades.english >= 85;
    const dost = normalizeDost(acad.dost_exam_result);

    const isPwd = toBool(student.is_sped) || toBool(student.is_pwd);
    const working = toBool(student.is_working_student);

    // Tier 1: Mandatory overrides
    if (isPwd && (survey.extra_support === 'Yes' || (survey.difficulty_areas || []).some((d) => ['Focusing', 'Social interaction', 'Reading', 'Writing'].includes(d)))) {
        result.push(makeCard('SNED', 100, ['Special needs flagged', 'Support requested']));
        result.push(makeCard('OHSP', 85, ['Flexible learning option']));
        result.push(makeCard('REGULAR', 75, ['Standard curriculum with support']));
        return finalize(result);
    }

    if (working || survey.absences === 'More than 20' || (survey.distance_from_school === 'More than 5 km' && survey.travel_difficulty === 'Yes') || ((survey.device_availability === 'Not available') && (survey.internet_access === 'No internet')) || (student.family_responsibilities && survey.study_hours === 'Less than 1 hour')) {
        result.push(makeCard('OHSP', 98, ['Flexible learning needed']));
        result.push(makeCard('REGULAR', 82, ['Standard option with accommodations']));
        result.push(makeCard('SPTVE', 78, ['Practical skills program']));
        return finalize(result);
    }

    // Tier 2: Academic eligibility
    if (overall >= 90 && allAbove85 && stemCore && dost === 'passed') {
        result.push(makeCard('STE', 99, ['Overall >= 90', 'All subjects >= 85', 'Math/Science/English >= 85', 'DOST passed']));
        result.push(makeCard('SPFL', 88, ['Strong language skills complement your abilities']));
        result.push(makeCard('SPTVE', 87, ['Technical skills are another strong option']));
        return finalize(result);
    }

    if (overall >= 90 && allAbove85 && stemCore && (dost === 'failed' || dost === 'not_taken')) {
        const scores = calculateSurveyScores(survey);
        const highest = Object.entries(scores).sort((a, b) => b[1] - a[1])[0]?.[0];
        if (highest === 'STE') {
            result.push(makeCard('STE', 95, ['Excellent grades for STE', `DOST: ${dost}`]));
            result.push(makeCard('SPFL', 87, ['Strong alternative with your language abilities']));
            result.push(makeCard('SPTVE', 86, ['Technical-vocational option available']));
        } else if (highest === 'SPFL') {
            result.push(makeCard('SPFL', 93, ['Excellent grades + language inclination', `DOST: ${dost}`]));
            result.push(makeCard('STE', 90, ['STEM is still a strong option']));
            result.push(makeCard('TOP5', 88, ['Regular top section for high achievers']));
        } else if (highest === 'SPTVE') {
            result.push(makeCard('SPTVE', 93, ['Excellent grades + tech-voc interest', `DOST: ${dost}`]));
            result.push(makeCard('STE', 90, ['STEM is still a strong option']));
            result.push(makeCard('TOP5', 88, ['Regular top section for high achievers']));
        } else {
            result.push(makeCard('STE', 92, ['Excellent grades; consider DOST retake']));
            result.push(makeCard('TOP5', 89, ['Top regular section fits your performance']));
            result.push(makeCard('SPFL', 85, ['Language program is available']));
        }
        return finalize(result);
    }

    if (overall >= 90 && allAbove85) {
        result.push(makeCard('TOP5', 90, ['Overall >= 90', 'All subjects >= 85', 'High achiever']));
        result.push(makeCard('SPFL', 86, ['Language program suits high performers']));
        result.push(makeCard('SPTVE', 85, ['Technical-vocational option']));
        return finalize(result);
    }

    if (overall >= 85 && grades.english >= 85 && grades.filipino >= 85) {
        const scores = calculateSurveyScores(survey);
        if (scores.SPFL >= 10 || survey.interested_program === 'SPFL' || (survey.enjoyed_subjects || []).some((s) => ['English', 'Filipino'].includes(s))) {
            result.push(makeCard('SPFL', 88, ['Language strengths noted']));
            result.push(makeCard('TOP5', 84, ['High achiever option']));
            result.push(makeCard('REGULAR', 80, ['Standard curriculum available']));
            return finalize(result);
        }
    }

    if (overall >= 85 && (grades.edukasyon_pangkabuhayan >= 85 || grades.mapeh >= 85)) {
        const scores = calculateSurveyScores(survey);
        if (scores.SPTVE >= 10 || survey.interested_program === 'SPTVE' || ['Kinesthetic', 'Mixed'].includes(survey.learning_style)) {
            result.push(makeCard('SPTVE', 87, ['Practical skills + interest']));
            result.push(makeCard('TOP5', 84, ['High achiever option']));
            result.push(makeCard('REGULAR', 80, ['Standard curriculum available']));
            return finalize(result);
        }
    }

    // Tier 3: Survey-based ranking
    const surveyScores = calculateSurveyScores(survey);
    const ranked = Object.entries(surveyScores).sort((a, b) => b[1] - a[1]);
    if (ranked.length >= 3) {
        const topScore = ranked[0][1];
        const primary = ranked[0][0];
        const second = ranked[1][0];
        const third = ranked[2][0];
        result.push(makeCard(primary, Math.max(75, 60 + topScore), ['Based on your survey interests and habits']));
        result.push(makeCard(second, Math.max(70, 55 + ranked[1][1]), ['Strong secondary match from your profile']));
        result.push(makeCard(third, Math.max(65, 50 + ranked[2][1]), ['Another suitable option']));
        return finalize(result);
    } else if (ranked.length >= 2) {
        const topScore = ranked[0][1];
        const primary = ranked[0][0];
        const second = ranked[1][0];
        result.push(makeCard(primary, Math.max(75, 60 + topScore), ['Based on your survey interests and habits']));
        result.push(makeCard(second, Math.max(70, 55 + ranked[1][1]), ['Strong secondary match from your profile']));
        result.push(makeCard('REGULAR', 70, ['Standard curriculum available']));
        return finalize(result);
    } else if (ranked.length) {
        const topScore = ranked[0][1];
        const primary = ranked[0][0];
        result.push(makeCard(primary, Math.max(75, 60 + topScore), ['Based on your survey interests and habits']));
        result.push(makeCard('REGULAR', 72, ['Standard curriculum available']));
        result.push(makeCard('OHSP', 68, ['Flexible option available']));
        return finalize(result);
    }

    // Tier 4: Defaults
    if (overall >= 85) {
        result.push(makeCard('TOP5', 82, ['Good academic performance']));
        result.push(makeCard('REGULAR', 78, ['Standard curriculum available']));
        result.push(makeCard('SPFL', 75, ['Language program option']));
    } else if (overall >= 75) {
        result.push(makeCard('REGULAR', 78, ['Standard curriculum fit']));
        result.push(makeCard('OHSP', 72, ['Flexible option available']));
        result.push(makeCard('SPTVE', 70, ['Practical skills program']));
    } else {
        result.push(makeCard('REGULAR', 70, ['Support-focused placement']));
        result.push(makeCard('OHSP', 68, ['Flexible schedule option']));
        result.push(makeCard('SNED', 65, ['Additional support available if needed']));
    }

    return finalize(result);
}

function makeCard(key, score, reasons) {
    const meta = programData[key] || { name: key, description: '', icon: '🎓', color: 'gray' };
    return {
        program: key,
        name: meta.name,
        description: meta.description,
        icon: meta.icon,
        color: meta.color,
        score: Math.min(100, Math.max(Math.round(score), 60)),
        reasons: reasons && reasons.length ? reasons : ['Eligible based on provided data']
    };
}

function finalize(cards) {
    return cards.sort((a, b) => b.score - a.score);
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
            if (!selectedProgram) {
                alert('No program selected');
                return;
            }
            
            const originalText = confirmBtn.innerHTML;
            confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Submitting...';
            confirmBtn.disabled = true;
            
            // Get student LRN from context
            const data = mergeContextData();
            const studentLrn = data.student?.lrn || '';
            
            // Call backend to save enrollment data
            fetch('/confirm-program/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({
                    program_code: selectedProgram.program,
                    student_lrn: studentLrn,
                })
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    modal.classList.add('hidden');
                    document.body.style.overflow = 'auto';
                    showSuccessModal();
                } else {
                    alert(result.error || 'Failed to confirm program selection');
                    confirmBtn.innerHTML = originalText;
                    confirmBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error confirming program:', error);
                alert('An error occurred while submitting your selection. Please try again.');
                confirmBtn.innerHTML = originalText;
                confirmBtn.disabled = false;
            });
        });
    }
}

// Helper function to get CSRF token
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
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