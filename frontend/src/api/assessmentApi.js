import { request } from "./httpClient.js";
export const createAssessment = (payload, fetcher) =>
  request(
    "/api/assessments",
    { method: "POST", body: JSON.stringify(payload) },
    fetcher,
  );
export const getPatientAssessments = (patientId, fetcher) =>
  request(
    `/api/patients/${encodeURIComponent(patientId)}/assessments`,
    {},
    fetcher,
  );
