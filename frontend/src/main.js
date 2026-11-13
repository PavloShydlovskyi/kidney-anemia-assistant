import "../styles/main.css";
import "../styles/form.css";
import "../styles/results.css";
import "../styles/profile.css";
import {
  createAssessment,
  getPatientAssessments,
  previewAssessment,
} from "./api/assessmentApi.js";
import { getReference } from "./api/referenceApi.js";
import { createAssessmentFormView } from "./views/assessmentFormView.js";
import { showResult } from "./views/resultView.js";
import { createHistoryView } from "./views/historyView.js";
import { submitAssessment } from "./controllers/assessmentForm.js";
import { loadHistory } from "./controllers/historyPage.js";
import { initProfileView } from "./views/profileView.js";

const pages = ["assessment", "history", "profile"];
const guestNotice = document.querySelector("#guest-notice");
const profileView = initProfileView(document.querySelector("#profile-form"), {
  onChange: () => (guestNotice.hidden = true),
});
guestNotice.hidden = profileView.hasActiveAccount();
function navigate(page) {
  if (!pages.includes(page)) page = "assessment";
  for (const name of pages) {
    const section = document.querySelector(`#${name}-page`);
    section.hidden = name !== page;
    section.classList.toggle("visible", name === page);
  }
  document.querySelectorAll("[data-page]").forEach((button) => {
    const active = button.dataset.page === page;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  if (location.hash !== `#${page}`) history.replaceState(null, "", `#${page}`);
  window.scrollTo({ top: 0, behavior: "smooth" });
}
document
  .querySelectorAll("[data-page]")
  .forEach((button) =>
    button.addEventListener("click", () => navigate(button.dataset.page)),
  );
document.querySelectorAll('a[href="#assessment"]').forEach((link) =>
  link.addEventListener("click", (event) => {
    event.preventDefault();
    navigate("assessment");
  }),
);
window.addEventListener("hashchange", () => navigate(location.hash.slice(1)));
navigate(location.hash.slice(1));

const form = document.querySelector("#assessment-form");
const view = createAssessmentFormView(form, showResult);
getReference()
  .then((data) => view.setReference(data))
  .catch(() => {
    /* contract limits are available locally as a hint */
  });
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const signedIn = profileView.hasActiveAccount();
  const ok = await submitAssessment(view, {
    createAssessment: signedIn ? createAssessment : previewAssessment,
  });
  if (ok && signedIn) {
    const id = view.readAssessmentRequest().patient_id;
    if (id) document.querySelector("#history-patient-id").value = id;
  }
});
const historyForm = document.querySelector("#history-form");
const historyView = createHistoryView(
  document.querySelector("#history-region"),
);
historyForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const raw = document.querySelector("#history-patient-id").value;
  const error = document.querySelector("#history-error");
  const id = Number(raw);
  if (!Number.isInteger(id) || id < 1) {
    error.textContent = "Введіть цілий ID пацієнта від 1.";
    return;
  }
  error.textContent = "";
  loadHistory(id, historyView, { getPatientAssessments });
});
