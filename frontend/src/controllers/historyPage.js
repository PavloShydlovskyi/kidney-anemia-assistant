import { ApiError } from "../api/httpClient.js";
export async function loadHistory(patientId, view, api) {
  view.showLoading();
  try {
    const data = await api.getPatientAssessments(patientId);
    view.showHistory(
      Array.isArray(data) ? data : (data.assessments ?? data.items ?? []),
    );
  } catch (error) {
    view.showError(
      error instanceof ApiError
        ? error.message
        : "Не вдалося завантажити історію. Спробуйте ще раз.",
    );
  }
}
