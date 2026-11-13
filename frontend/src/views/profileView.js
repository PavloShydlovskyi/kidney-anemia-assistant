import { getSession, login, logout, register } from "../api/authApi.js";
import { validateAuth } from "../profile/authValidation.js";

export function initProfileView(form, onChange = () => {}) {
  const $ = (selector) => document.querySelector(selector);
  const authCard = $("#account-auth");
  const currentCard = $("#account-current");
  const status = $("#profile-status");
  const submit = $("#auth-submit");
  let user = null;
  let registering = true;
  let changed = false;

  function showError(message) {
    status.textContent = message;
    status.hidden = !message;
  }

  function clearErrors() {
    showError("");
    form.querySelectorAll("[data-profile-error]").forEach((node) => {
      node.textContent = "";
    });
    form.querySelectorAll("[aria-invalid]").forEach((node) => {
      node.removeAttribute("aria-invalid");
    });
  }

  function render() {
    authCard.hidden = !!user;
    currentCard.hidden = !user;
    $("#profile-name-row").hidden = !registering;
    $("#auth-title").textContent = registering
      ? "Створити акаунт"
      : "Увійти в акаунт";
    submit.textContent = registering ? "Створити акаунт" : "Увійти";
    $("#auth-toggle").textContent = registering
      ? "У мене вже є акаунт"
      : "Створити акаунт";
    form.elements.password.autocomplete = registering
      ? "new-password"
      : "current-password";
    if (user) {
      $("#account-name").textContent = user.display_name;
      $("#account-email").textContent = user.email;
    }
  }

  $("#auth-toggle").addEventListener("click", () => {
    registering = !registering;
    form.elements.password.value = "";
    clearErrors();
    render();
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearErrors();
    const data = {
      display_name: form.elements.display_name.value.trim(),
      email: form.elements.email.value.trim(),
      password: form.elements.password.value,
    };
    const errors = validateAuth(data, registering);
    if (Object.keys(errors).length) {
      for (const [field, message] of Object.entries(errors)) {
        form.querySelector(`[data-profile-error="${field}"]`).textContent =
          message;
        form.elements[field].setAttribute("aria-invalid", "true");
      }
      return;
    }
    submit.disabled = true;
    try {
      const result = await (registering
        ? register(data)
        : login({
            email: data.email,
            password: data.password,
          }));
      if (!result.user) throw Error("Сервер не повернув дані користувача.");
      changed = true;
      user = result.user;
      form.reset();
      render();
      onChange();
    } catch (error) {
      for (const detail of error.details ?? []) {
        if (!["display_name", "email", "password"].includes(detail.field))
          continue;
        const field = form.elements.namedItem(detail.field);
        const label = form.querySelector(
          `[data-profile-error="${detail.field}"]`,
        );
        if (!field || !label) continue;
        label.textContent = detail.message;
        field.setAttribute("aria-invalid", "true");
      }
      if (form.querySelector('[aria-invalid="true"]')) return;
      showError(
        !registering && error.status === 401
          ? "Невірна електронна пошта або пароль."
          : error.message || "Не вдалося увійти. Спробуйте ще раз.",
      );
    } finally {
      submit.disabled = false;
    }
  });

  $("#account-signout").addEventListener("click", async () => {
    try {
      await logout();
      window.location.reload();
    } catch (error) {
      showError(error.message || "Не вдалося вийти з акаунта.");
    }
  });

  render();
  getSession()
    .then((result) => {
      if (changed) return;
      user = result.user ?? null;
      render();
      onChange();
    })
    .catch((error) => {
      if (!changed && error.status !== 401)
        showError("Не вдалося перевірити акаунт. Спробуйте пізніше.");
    });
  return { hasActiveAccount: () => !!user };
}
