(function () {
  const loginForm = document.getElementById("login-form");
  const logoutBtn = document.getElementById("logout-btn");

  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const username = document.getElementById("username").value;
      const password = document.getElementById("password").value;
      const error = document.getElementById("login-error");
      error.textContent = "";
      try {
        const result = await API.json("/auth/login", {
          method: "POST",
          body: JSON.stringify({ username, password }),
        });
        localStorage.setItem("token", result.access_token);
        window.location.href = "/dashboard";
      } catch (err) {
        error.textContent = err.message;
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("token");
      window.location.href = "/";
    });
  }
})();

