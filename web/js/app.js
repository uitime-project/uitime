document.addEventListener("DOMContentLoaded", () => {
  // --- THEME TOGGLE LOGIC ---
  const themeToggle = document.getElementById("theme-toggle");
  const sunIcon = document.getElementById("sun-icon");
  const moonIcon = document.getElementById("moon-icon");
  const mainLogo = document.getElementById("main-logo");

  const currentTheme = localStorage.getItem("uitime-theme") || "light";
  document.body.setAttribute("data-theme", currentTheme);
  updateThemeIcons(currentTheme);

  themeToggle.addEventListener("click", () => {
    let theme = document.body.getAttribute("data-theme");
    let newTheme = theme === "light" ? "dark" : "light";

    document.body.setAttribute("data-theme", newTheme);
    localStorage.setItem("uitime-theme", newTheme);
    updateThemeIcons(newTheme);
  });

  function updateThemeIcons(theme) {
    if (theme === "dark") {
      sunIcon.classList.add("hidden");
      moonIcon.classList.remove("hidden");
      mainLogo.src = "assets/logo-main-dark.png";
    } else {
      sunIcon.classList.remove("hidden");
      moonIcon.classList.add("hidden");
      mainLogo.src = "assets/logo-main-light.png";
    }
  }

  // --- API & GENERATOR LOGIC ---
  const API_URL = "https://uitime.onrender.com/api/Auth/generate-invite";

  const consentCheckbox = document.getElementById("consent-checkbox");
  const generateBtn = document.getElementById("generate-btn");
  const generateSection = document.getElementById("generate-section");
  const resultSection = document.getElementById("result-section");
  const inviteCodeValue = document.getElementById("invite-code-value");
  const copyBtn = document.getElementById("copy-btn");
  const errorMsg = document.getElementById("error-msg");

  consentCheckbox.addEventListener("change", (e) => {
    generateBtn.disabled = !e.target.checked;
  });

  generateBtn.addEventListener("click", async () => {
    const originalText = generateBtn.innerText;
    generateBtn.innerText = "generating...";
    generateBtn.disabled = true;
    errorMsg.classList.add("hidden");

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("network error");
      }

      const data = await response.json();

      inviteCodeValue.innerText = data.inviteCode;

      generateSection.classList.add("hidden");
      resultSection.classList.remove("hidden");
      resultSection.classList.add("fade-in");
    } catch (error) {
      console.error("fetch error:", error);
      errorMsg.classList.remove("hidden");
      generateBtn.innerText = originalText;
      generateBtn.disabled = false;
    }
  });

  copyBtn.addEventListener("click", async () => {
    const code = inviteCodeValue.innerText;
    try {
      await navigator.clipboard.writeText(code);

      const originalIcon = copyBtn.innerHTML;
      copyBtn.innerHTML =
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#27ae60" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';

      setTimeout(() => {
        copyBtn.innerHTML = originalIcon;
      }, 2000);
    } catch (err) {
      console.error("failed to copy: ", err);
    }
  });
});
