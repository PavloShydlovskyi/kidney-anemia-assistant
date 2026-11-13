import {
  clearProfile,
  loadProfile,
  saveProfile,
} from "../profile/profileStore.js";

export function initProfileView(form, storage = window.localStorage) {
  const status = document.querySelector("#profile-status");
  const clearButton = document.querySelector("#profile-clear");
  const nameInput = form.elements.namedItem("display_name");
  const emailInput = form.elements.namedItem("email");
  const saved = loadProfile(storage);
  nameInput.value = saved.display_name;
  emailInput.value = saved.email;

  function clearMessages() {
    for (const field of ["display_name", "email"]) {
      const input = form.elements.namedItem(field);
      const message = form.querySelector(`[data-profile-error="${field}"]`);
      message.textContent = "";
      input.removeAttribute("aria-invalid");
      input.classList.remove("invalid");
    }
    status.hidden = true;
    status.textContent = "";
  }

  for (const input of [nameInput, emailInput]) {
    input.addEventListener("input", clearMessages);
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearMessages();
    const result = saveProfile(storage, {
      display_name: nameInput.value,
      email: emailInput.value,
    });
    if (result.errors) {
      for (const [field, message] of Object.entries(result.errors)) {
        const input = form.elements.namedItem(field);
        form.querySelector(`[data-profile-error="${field}"]`).textContent =
          message;
        input.setAttribute("aria-invalid", "true");
        input.classList.add("invalid");
      }
      return;
    }
    status.textContent = result.ok
      ? "Дані збережено на цьому пристрої."
      : result.message;
    status.hidden = false;
  });

  clearButton.addEventListener("click", () => {
    clearMessages();
    if (clearProfile(storage)) {
      form.reset();
      status.textContent = "Дані видалено з цього пристрою.";
    } else {
      status.textContent = "Не вдалося очистити дані в цьому браузері.";
    }
    status.hidden = false;
  });
}
