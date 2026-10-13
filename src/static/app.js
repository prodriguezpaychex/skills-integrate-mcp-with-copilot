document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const teacherRequired = document.getElementById("teacher-required");
  const messageDiv = document.getElementById("message");
  const accountButton = document.getElementById("account-button");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginMessage = document.getElementById("login-message");
  const cancelLogin = document.getElementById("cancel-login");
  let isTeacher = false;

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => {
      const entities = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      };
      return entities[character];
    });
  }

  function showMessage(element, text, type) {
    element.textContent = text;
    element.className = `message ${type}`;
    setTimeout(() => element.classList.add("hidden"), 5000);
  }

  function updateAccountControls() {
    accountButton.textContent = isTeacher ? "👤 Sign out" : "👤 Teacher login";
    accountButton.setAttribute(
      "aria-label",
      isTeacher ? "Sign out of teacher account" : "Teacher login"
    );
    signupForm.hidden = !isTeacher;
    teacherRequired.hidden = isTeacher;
  }

  async function readResponse(response) {
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || "An error occurred");
    }
    return result;
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await readResponse(response);
      activitiesList.replaceChildren();

      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "-- Select an activity --";
      activitySelect.replaceChildren(placeholder);

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";
        const spotsLeft = details.max_participants - details.participants.length;
        const participantsHTML = details.participants.length
          ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) => `<li>
                      <span class="participant-email">${escapeHtml(email)}</span>
                      ${
                        isTeacher
                          ? `<button class="delete-btn" type="button"
                              data-activity="${escapeHtml(name)}"
                              data-email="${escapeHtml(email)}"
                              aria-label="Unregister ${escapeHtml(email)} from ${escapeHtml(name)}">❌</button>`
                          : ""
                      }
                    </li>`
                  )
                  .join("")}
              </ul>
            </div>`
          : "<p><em>No participants yet</em></p>";

        activityCard.innerHTML = `
          <h4>${escapeHtml(name)}</h4>
          <p>${escapeHtml(details.description)}</p>
          <p><strong>Schedule:</strong> ${escapeHtml(details.schedule)}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">${participantsHTML}</div>
        `;
        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.textContent = "";
      const errorMessage = document.createElement("p");
      errorMessage.textContent = "Failed to load activities. Please try again later.";
      activitiesList.appendChild(errorMessage);
      console.error("Error fetching activities:", error);
    }
  }

  async function refreshTeacherStatus() {
    try {
      const response = await fetch("/auth/me");
      const result = await readResponse(response);
      isTeacher = result.authenticated;
      updateAccountControls();
    } catch (error) {
      console.error("Error checking teacher login:", error);
    }
  }

  accountButton.addEventListener("click", async () => {
    if (!isTeacher) {
      loginMessage.className = "message hidden";
      loginDialog.showModal();
      document.getElementById("username").focus();
      return;
    }

    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      const result = await readResponse(response);
      isTeacher = false;
      updateAccountControls();
      await fetchActivities();
      showMessage(messageDiv, result.message, "success");
    } catch (error) {
      showMessage(messageDiv, error.message, "error");
    }
  });

  cancelLogin.addEventListener("click", () => loginDialog.close());

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(loginForm);
    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: formData.get("username"),
          password: formData.get("password"),
        }),
      });
      await readResponse(response);
      isTeacher = true;
      loginDialog.close();
      loginForm.reset();
      updateAccountControls();
      await fetchActivities();
      showMessage(messageDiv, "Signed in as teacher", "success");
    } catch (error) {
      showMessage(loginMessage, error.message, "error");
    }
  });

  activitiesList.addEventListener("click", async (event) => {
    const button = event.target.closest(".delete-btn");
    if (!button || !isTeacher) return;

    const activity = button.dataset.activity;
    const email = button.dataset.email;
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      const result = await readResponse(response);
      await fetchActivities();
      showMessage(messageDiv, result.message, "success");
    } catch (error) {
      showMessage(messageDiv, error.message, "error");
    }
  });

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = document.getElementById("email").value;
    const activity = activitySelect.value;
    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        { method: "POST" }
      );
      const result = await readResponse(response);
      signupForm.reset();
      await fetchActivities();
      showMessage(messageDiv, result.message, "success");
    } catch (error) {
      showMessage(messageDiv, error.message, "error");
    }
  });

  updateAccountControls();
  refreshTeacherStatus().then(fetchActivities);
});
