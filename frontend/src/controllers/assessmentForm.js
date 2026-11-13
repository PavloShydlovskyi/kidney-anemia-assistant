import { validateAssessment } from "../validation/formValidation.js";
import { ApiError } from "../api/httpClient.js";
export async function submitAssessment(view, api) {
  view.clearErrors();
  const payload = view.readAssessmentRequest();
  const errors = validateAssessment(payload, view.getReference());
  if (Object.keys(errors).length) {
    for (const [field, message] of Object.entries(errors))
      view.showFieldError(field, message);
    return false;
  }
  view.setLoading(true);
  try {
    const result = await api.createAssessment(payload);
    view.showResult(result);
    return true;
  } catch (error) {
    if (
      error instanceof ApiError &&
      error.status === 422 &&
      error.details.length
    ) {
      let shown = false;
      for (const detail of error.details)
        if (
          typeof detail.field === "string" &&
          typeof detail.message === "string"
        ) {
          view.showFieldError(detail.field, detail.message);
          shown = true;
        }
      if (!shown) view.showError(error.message);
    } else
      view.showError(
        error instanceof ApiError
          ? error.message
          : "Не вдалося отримати результат. Спробуйте ще раз.",
      );
    return false;
  } finally {
    view.setLoading(false);
  }
}
