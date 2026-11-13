import { getLimits } from "../validation/formValidation.js";
export function createAssessmentFormView(form, resultView) {
  const errorBox = document.querySelector("#form-error");
  const submit = document.querySelector("#submit-button");
  let reference = null;
  function readAssessmentRequest() {
    const raw = new FormData(form);
    const result = {
      sex: raw.get("sex") || "",
      age: raw.get("age") === "" ? NaN : Number(raw.get("age")),
      creatinine:
        raw.get("creatinine") === "" ? NaN : Number(raw.get("creatinine")),
      creatinine_unit: raw.get("creatinine_unit"),
      hemoglobin:
        raw.get("hemoglobin") === "" ? NaN : Number(raw.get("hemoglobin")),
      hemoglobin_unit: raw.get("hemoglobin_unit"),
      on_dialysis: raw.has("on_dialysis"),
      pregnant: raw.has("pregnant"),
    };
    for (const key of ["patient_id", "rbc", "egfr_lab"])
      if (raw.get(key) !== "") result[key] = Number(raw.get(key));
    return result;
  }
  function clearErrors() {
    errorBox.hidden = true;
    errorBox.textContent = "";
    form.querySelectorAll("[data-error-for]").forEach((node) => {
      node.textContent = "";
    });
    form.querySelectorAll(".invalid").forEach((node) => {
      node.classList.remove("invalid");
      node.removeAttribute("aria-invalid");
    });
  }
  function showFieldError(field, message) {
    const label = form.querySelector(`[data-error-for="${field}"]`);
    const input = form.elements.namedItem(field);
    if (label) label.textContent = message;
    if (input instanceof HTMLElement) {
      input.classList.add("invalid");
      input.setAttribute("aria-invalid", "true");
    }
  }
  function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
  }
  function setLoading(loading) {
    submit.disabled = loading;
    submit.classList.toggle("loading", loading);
    submit.querySelector(".button-label").textContent = loading
      ? "Отримуємо результат…"
      : "Отримати результат";
    form.setAttribute("aria-busy", String(loading));
  }
  function updateHints() {
    const data = readAssessmentRequest();
    for (const field of ["creatinine", "hemoglobin", "rbc"]) {
      const hint = form.querySelector(`[data-hint-for="${field}"]`);
      if (!data.sex) {
        hint.textContent = "Оберіть стать, щоб побачити межі";
        continue;
      }
      const [min, max] = getLimits(reference, data.sex, field);
      hint.textContent = `Діапазон: ${min}–${max} ${field === "creatinine" ? "мкмоль/л" : field === "hemoglobin" ? "г/л" : "×10¹²/л"}`;
    }
  }
  form.querySelectorAll("input,select").forEach((input) =>
    input.addEventListener("input", () => {
      const field = input.name;
      const label = form.querySelector(`[data-error-for="${field}"]`);
      if (label) label.textContent = "";
      input.classList.remove("invalid");
      input.removeAttribute("aria-invalid");
      if (field === "sex") {
        const female =
          form.querySelector('input[name="sex"]:checked')?.value === "female";
        document.querySelector("#pregnant-row").hidden = !female;
        if (!female) form.elements.pregnant.checked = false;
      }
      if (["sex", "creatinine_unit", "hemoglobin_unit"].includes(field))
        updateHints();
    }),
  );
  updateHints();
  return {
    readAssessmentRequest,
    clearErrors,
    showFieldError,
    showError,
    setLoading,
    showResult: resultView,
    setReference(data) {
      reference = data;
      updateHints();
    },
    getReference() {
      return reference;
    },
  };
}
