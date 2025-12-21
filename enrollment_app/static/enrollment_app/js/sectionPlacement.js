// Program data with descriptions
const programData = {
  STE: {
    name: "STE (Science Technology and Engineering)",
    description:
      "The Science Technology and Engineering (STE) program focuses on developing students' skills in science, technology, engineering, and mathematics through hands-on learning and research-based activities.",
  },
  SPFL: {
    name: "SPFL (Special Program in Foreign Language)",
    description:
      "The Special Program in Foreign Language (SPFL) focuses on enhancing communication skills by learning foreign language such as Chinese.",
  },
  SPTVL: {
    name: "SPTVL (Special Program in Technical Vocational Livelihood)",
    description:
      "The Special Program in Technical Vocational Livelihood (SPTVL) provides students with practical skills and knowledge in various technical and vocational fields to prepare them for the workforce.",
  },
  TOP5: {
    name: "Top 5 Sections",
    description:
      "Reserved for students with exceptional academic performance (85-90 average). These sections provide advanced learning opportunities and enhanced academic support.",
  },
}

let selectedProgram = null

// Add click event listeners to available program cards
document.addEventListener("DOMContentLoaded", () => {
  const availableCards = document.querySelectorAll(".program-card.available")

  availableCards.forEach((card) => {
    card.addEventListener("click", function () {
      const program = this.getAttribute("data-program")
      showConfirmationModal(program)
    })
  })
})

function showConfirmationModal(program) {
  selectedProgram = program;

  const modal = document.getElementById("confirmationModal");
  const programNameElement = document.getElementById("selectedProgramName");
  const programDescriptionElement = document.getElementById("selectedProgramDescription");

  if (programData[program]) {
    programNameElement.textContent = programData[program].name;
    programDescriptionElement.textContent = programData[program].description;
  }

  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function closeConfirmationModal() {
  const modal = document.getElementById("confirmationModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

function closeSuccessModal() {
  const modal = document.getElementById("successModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}


// function confirmSelection() {
//   if (selectedProgram) {
//     // Close confirmation modal
//     closeConfirmationModal()

//     // Show success modal
//     setTimeout(() => {
//       const successModal = document.getElementById("successModal")
//       successModal.style.display = "block"
//     }, 300)
//   }
// }

function confirmSelection() {
    if (!selectedProgram) return;

    // Close confirmation modal
    closeConfirmationModal();

    // Show success modal after a short delay (optional smoothness)
    setTimeout(() => {
        const modal = document.getElementById("successSubmitModal");
        modal.classList.remove("hidden");
        modal.classList.add("flex");
    }, 200);
}


function closeSuccessSubmitModal() {
    const modal = document.getElementById("successSubmitModal");
    modal.classList.add("hidden");
    window.location.href = "landing.html";
}




function goBack() {
    // Redirect back to the enrollment form using the defined redirect URL
    window.location.href = redirectUrl;
}

// Close modal when clicking outside of it
window.onclick = (event) => {
  const confirmationModal = document.getElementById("confirmationModal")
  const successModal = document.getElementById("successModal")

  if (event.target === confirmationModal) {
    closeConfirmationModal()
  }

  if (event.target === successModal) {
    closeSuccessModal()
  }
}

// Simulate qualification logic based on student data
// This would normally be populated from the previous form data
function determineQualifications() {
  // This is where you would implement the logic based on:
  // - Working student status
  // - Disability status
  // - DOST exam results
  // - Grade average


  const qualifications = {
    isWorkingStudent: false,
    hasDisability: false,
    dostExamResult: "passed",
    gradeAverage: 92,
  }


  updateProgramAvailability(qualifications)
}

function updateProgramAvailability(qualifications) {
  // This function would enable/disable programs based on student qualifications
  // Example logic:
  // if (qualifications.gradeAverage < 85) {
  //     // Only regular section available
  //     enableProgram('REGULAR');
  //     disableProgram('TOP5');
  //     disableProgram('STE');
  //     disableProgram('SPFL');
  //     disableProgram('SPTVL');
  // }
}

function enableProgram(programId) {
  const card = document.querySelector(`[data-program="${programId}"]`)
  if (card) {
    card.classList.remove("disabled")
    card.classList.add("available")
  }
}

function disableProgram(programId) {
  const card = document.querySelector(`[data-program="${programId}"]`)
  if (card) {
    card.classList.remove("available")
    card.classList.add("disabled")
  }
}
