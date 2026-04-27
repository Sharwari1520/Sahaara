// =========================
// LOAD DASHBOARD HEADER
// =========================
const mainHeader = document.getElementById("mainHeader");

if (mainHeader) {
    fetch("/templates/header")
        .then(res => res.text())
        .then(data => {
            mainHeader.innerHTML = data;

            // GO HOME LOGIC
            const logo = mainHeader.querySelector("#dashboardLogo");
            if (logo) logo.addEventListener("click", () => window.location.href = "/dashboard");

            // ABOUT / CONTACT NAV
            const aboutBtn = mainHeader.querySelector("#dashboardAbout");
            const contactBtn = mainHeader.querySelector("#dashboardContact");

            const aboutSection = document.getElementById("aboutSection");
            const contactSection = document.getElementById("contactSection");

            function hideAllDashboardSections() {
                if (aboutSection) aboutSection.style.display = "none";
                if (contactSection) contactSection.style.display = "none";
            }

            if (aboutBtn) {
    aboutBtn.addEventListener("click", e => {
        e.preventDefault();
        hideAllDashboardSections();
        if (aboutSection) {
            aboutSection.style.display = "block";
            // scroll below the cards instead of scrollIntoView
            const cardsContainer = document.querySelector(".dashboard-box-container");
            const cardsBottom = cardsContainer.getBoundingClientRect().bottom + window.scrollY;
            window.scrollTo({ top: cardsBottom + 20, behavior: "smooth" });
        }
    });
}

if (contactBtn) {
    contactBtn.addEventListener("click", e => {
        e.preventDefault();
        hideAllDashboardSections();
        if (contactSection) {
            contactSection.style.display = "block";
            // scroll below the cards instead of scrollIntoView
            const cardsContainer = document.querySelector(".dashboard-box-container");
            const cardsBottom = cardsContainer.getBoundingClientRect().bottom + window.scrollY;
            window.scrollTo({ top: cardsBottom + 20, behavior: "smooth" });
        }
    });
}


            // PROFILE LOGIC
            const profileLogo = mainHeader.querySelector("#profileLogo");
            const userModal = document.getElementById("userModal");
            const logoutBtn = document.getElementById("logoutBtn");

            const displayName = document.getElementById("displayName");
            const displayAge = document.getElementById("displayAge");
            const displayGender = document.getElementById("displayGender");

            if (profileLogo && userModal) {
                profileLogo.addEventListener("click", () => {
                    const user = JSON.parse(localStorage.getItem("loggedInUser"));
                    if (!user) {
                        showPopup("popupInvalidLogin");
                        window.location.href = "/";
                        return;
                    }
                    displayName.textContent = `Name: ${user.username || 'N/A'}`;
                    displayAge.textContent = `Age: ${user.age || 'N/A'}`;
                    displayGender.textContent = `Gender: ${user.gender || 'N/A'}`;
                    userModal.style.display = "flex";
                });

                logoutBtn.addEventListener("click", () => {
                    localStorage.removeItem("loggedInUser");
                    window.location.href = "/";
                });

                userModal.addEventListener("click", e => {
                    if (e.target === userModal) userModal.style.display = "none";
                });
            }
        });
}

// =========================
// HERO IMAGE SLIDER
// =========================
const images = [
    "/static/images/hero.png",
    "/static/images/hero1.png",
    "/static/images/hero2.png",
    "/static/images/hero3.png"
];

let currentIndex = 0;
const heroImg = document.getElementById("heroImg");

if (heroImg) {
    setInterval(() => {
        currentIndex = (currentIndex + 1) % images.length;
        heroImg.src = images[currentIndex];
    }, 3000);
}

// =========================
// MODAL CONTROLS
// =========================
function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.style.display = "flex";
    if (id === "signupModal") generateCaptcha();
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = "none";
}

document.getElementById("openSignup")?.addEventListener("click", () => {
    openModal("signupModal");

    ["signupUsername","signupEmail","signupPassword","signupAge","captchaInput"].forEach(id => {
        const el = document.getElementById(id);
        if(el) el.value = "";
    });

    const genderSelect = document.getElementById("signupGender");
    if(genderSelect) genderSelect.selectedIndex = 0;

    localStorage.removeItem("loggedInUser");
    localStorage.removeItem("user_id");

    generateCaptcha();
});

document.getElementById("openLogin")?.addEventListener("click", () => openModal("loginModal"));

// =========================
// SHOW/HIDE PASSWORD
// =========================
document.getElementById("showSignupPassword")?.addEventListener("change", e => {
    const signupPassword = document.getElementById("signupPassword");
    if(signupPassword) signupPassword.type = e.target.checked ? "text" : "password";
});

document.getElementById("showLoginPassword")?.addEventListener("change", e => {
    const loginPassword = document.getElementById("loginPassword");
    if(loginPassword) loginPassword.type = e.target.checked ? "text" : "password";
});

// =========================
// CAPTCHA GENERATION
// =========================
let captchaValue = "";
function generateCaptcha() {
    captchaValue = Math.random().toString(36).substring(2, 7);
    const captchaText = document.getElementById("captchaText");
    if (captchaText) captchaText.innerText = captchaValue;
}

// =========================
// POPUP FUNCTION
// =========================
function showPopup(popupId) {
    const popup = document.getElementById(popupId);
    if (!popup) return;
    popup.classList.add('show');
    setTimeout(() => popup.classList.remove('show'), 2500);
}

// =========================
// SIGNUP LOGIC
// =========================
document.getElementById("signupBtn")?.addEventListener("click", () => {
    const username = document.getElementById("signupUsername")?.value.trim();
    const email = document.getElementById("signupEmail")?.value.trim();
    const password = document.getElementById("signupPassword")?.value.trim();
    const age = document.getElementById("signupAge")?.value.trim();
    const gender = document.getElementById("signupGender")?.value;
    const captchaInput = document.getElementById("captchaInput")?.value.trim();

    if(!username || !email || !password || !age || !gender || !captchaInput) {
        showPopup("popupInvalidSignup");
        return;
    }

    if(isNaN(age) || age < 1 || age > 120) {
        showPopup("popupInvalidSignup");
        return;
    }

    if(captchaInput.toLowerCase() !== captchaValue.toLowerCase()) {
        showPopup("popupInvalidCaptcha");
        generateCaptcha();
        return;
    }

    fetch("/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username,email,password,age,gender,captcha:captchaInput,captchaActual:captchaValue })
    })
    .then(res => res.json())
    .then(data => {
        if(data.message) {
            localStorage.setItem("loggedInUser", JSON.stringify({ username, age, gender, id: data.userId || "" }));
            showPopup("popupSignupSuccess");
            closeModal("signupModal");
            setTimeout(() => openModal("loginModal"), 1000);
        } else {
            showPopup("popupInvalidSignup");
        }
        generateCaptcha();
    })
    .catch(() => generateCaptcha());
});

// =========================
// LOGIN LOGIC
// =========================
document.getElementById("loginBtn")?.addEventListener("click", () => {
    const username = document.getElementById("loginUsername")?.value.trim();
    const password = document.getElementById("loginPassword")?.value.trim();

    if(!username || !password) {
        showPopup("popupInvalidLogin");
        return;
    }

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username,password })
    })
    .then(res => res.json())
    .then(data => {
        if(data.message) {
            localStorage.setItem("loggedInUser", JSON.stringify({
                username:data.user.username,
                age:data.user.age,
                gender:data.user.gender,
                id:data.user.id
            }));
            localStorage.setItem("user_id", data.user.id);
            showPopup("popupLoginSuccess");
            setTimeout(() => window.location.href = "/dashboard", 1000);
        } else {
            showPopup("popupInvalidLogin");
        }
    })
    .catch(() => showPopup("popupInvalidLogin"));
});

// =========================
// OPEN DAILY HEALTH
// =========================
function openDailyHealth() {
    window.location.href = "/daily-health";
}

// =========================
// AUTO-HIDE ABOUT / CONTACT SECTIONS
// =========================
document.addEventListener("click", e => {
    const aboutSection = document.getElementById("aboutSection");
    const contactSection = document.getElementById("contactSection");
    const aboutBtn = document.getElementById("dashboardAbout");
    const contactBtn = document.getElementById("dashboardContact");

    if((aboutSection?.style.display === "block") || (contactSection?.style.display === "block")) {
        const clickedInsideAbout = aboutSection?.contains(e.target);
        const clickedInsideContact = contactSection?.contains(e.target);
        const clickedOnAboutBtn = aboutBtn?.contains(e.target);
        const clickedOnContactBtn = contactBtn?.contains(e.target);

        if(!clickedInsideAbout && !clickedInsideContact && !clickedOnAboutBtn && !clickedOnContactBtn) {
            if(aboutSection) aboutSection.style.display = "none";
            if(contactSection) contactSection.style.display = "none";
        }
    }
});

// =========================
// PAGE SECTION LOGIC
// =========================
document.addEventListener("DOMContentLoaded", () => {
    if(!document.body.classList.contains("dashboard-page")) {
        const featureSections = document.querySelectorAll(".feature-section");
        document.querySelectorAll(".nav-links a").forEach(link => {
            link.addEventListener("click", e => {
                e.preventDefault();
                const targetId = link.getAttribute("href")?.substring(1);
                const target = document.getElementById(targetId);
                if(!target) return;
                featureSections.forEach(s => s.style.display = "none");
                target.style.display = "block";
                target.scrollIntoView({ behavior:"smooth" });
            });
        });
        if(localStorage.getItem("formUserData")) openModal("loginModal");
    }
});
