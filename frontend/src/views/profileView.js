import {
  getActiveAccount,
  loadAccountState,
  registerAccount,
  signOut,
  switchAccount,
} from "../profile/profileStore.js";

function browserStorage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function initProfileView(form, storage = browserStorage()) {
  const title = document.querySelector("#profile-title");
  const intro = document.querySelector("#profile-intro");
  const setupCard = document.querySelector("#account-setup");
  const currentCard = document.querySelector("#account-current");
  const switchCard = document.querySelector("#account-switch");
  const list = document.querySelector("#account-list");
  const status = document.querySelector("#profile-status");
  const nameInput = form.elements.namedItem("display_name");
  const emailInput = form.elements.namedItem("email");
  let mode = "auto";

  function showStatus(message) {
    status.textContent = message;
    status.hidden = false;
  }

  function clearMessages() {
    for (const field of ["display_name", "email"]) {
      const input = form.elements.namedItem(field);
      form.querySelector(`[data-profile-error="${field}"]`).textContent = "";
      input.removeAttribute("aria-invalid");
      input.classList.remove("invalid");
    }
    status.hidden = true;
    status.textContent = "";
  }

  function render() {
    const state = loadAccountState(storage);
    const active = state.accounts.find((item) => item.id === state.activeId);
    const setupVisible =
      !active && (state.accounts.length === 0 || mode === "register");
    setupCard.hidden = !setupVisible;
    currentCard.hidden = !active;
    switchCard.hidden = !!active || setupVisible;
    title.textContent = active
      ? "Акаунт"
      : setupVisible
        ? "Створіть профіль"
        : "Оберіть профіль";
    intro.textContent = active
      ? "Ваші дані на цьому пристрої."
      : setupVisible
        ? "Вкажіть ім’я та електронну пошту, щоб почати роботу."
        : "Увійдіть у збережений профіль або створіть інший.";
    if (active) {
      document.querySelector("#account-name").textContent = active.display_name;
      document.querySelector("#account-email").textContent = active.email;
    }
    if (!switchCard.hidden) {
      list.replaceChildren();
      for (const account of state.accounts) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "account-choice";
        button.setAttribute("aria-label", `Увійти як ${account.display_name}`);
        const details = document.createElement("span");
        const name = document.createElement("strong");
        const email = document.createElement("small");
        name.textContent = account.display_name;
        email.textContent = account.email;
        details.append(name, email);
        const action = document.createElement("span");
        action.textContent = "Увійти";
        button.append(details, action);
        button.addEventListener("click", () => {
          clearMessages();
          if (switchAccount(storage, account.id)) {
            window.location.reload();
          } else {
            showStatus("Не вдалося відкрити профіль у цьому браузері.");
          }
        });
        list.append(button);
      }
    }
  }

  for (const input of [nameInput, emailInput]) {
    input.addEventListener("input", clearMessages);
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    clearMessages();
    const result = registerAccount(storage, {
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
    if (!result.ok) {
      showStatus(result.message);
      return;
    }
    form.reset();
    mode = "auto";
    render();
  });

  document.querySelector("#account-signout").addEventListener("click", () => {
    clearMessages();
    if (signOut(storage)) {
      window.location.reload();
    } else {
      showStatus("Не вдалося вийти з профілю в цьому браузері.");
    }
  });

  document.querySelector("#account-add").addEventListener("click", () => {
    clearMessages();
    mode = "register";
    render();
  });

  render();
  return { hasActiveAccount: () => !!getActiveAccount(storage) };
}
