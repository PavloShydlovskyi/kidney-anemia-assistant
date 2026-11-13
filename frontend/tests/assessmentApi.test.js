import { test } from "node:test";
import assert from "node:assert/strict";
import {
  createAssessment,
  getPatientAssessments,
  previewAssessment,
} from "../src/api/assessmentApi.js";
import { ApiError, request } from "../src/api/httpClient.js";
test("POST sends contract fields as JSON", async () => {
  let seen;
  const payload = { sex: "male", age: 43 };
  const result = await createAssessment(payload, async (url, options) => {
    seen = { url, options };
    return { ok: true, status: 201, json: async () => ({ id: 5 }) };
  });
  assert.equal(seen.url, "/api/assessments");
  assert.equal(seen.options.method, "POST");
  assert.deepEqual(JSON.parse(seen.options.body), payload);
  assert.equal(result.id, 5);
});
test("guest preview uses non-saving endpoint", async () => {
  let path;
  await previewAssessment({ age: 43 }, async (url) => {
    path = url;
    return { ok: true, status: 200, json: async () => ({ egfr: 80 }) };
  });
  assert.equal(path, "/api/assessments/preview");
});
test("history URL contains patient id", async () => {
  let path;
  await getPatientAssessments(19, async (url) => {
    path = url;
    return { ok: true, status: 200, json: async () => [] };
  });
  assert.equal(path, "/api/patients/19/assessments");
});
test("422 details are retained for field errors", async () => {
  await assert.rejects(
    request("/api/assessments", {}, async () => ({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [{ field: "hemoglobin", message: "Out of range" }],
      }),
    })),
    (error) =>
      error instanceof ApiError &&
      error.status === 422 &&
      error.details[0].field === "hemoglobin",
  );
});
test("network failure has a clear recoverable error", async () => {
  await assert.rejects(
    request("/api/reference", {}, async () => {
      throw Error("offline");
    }),
    (error) => error instanceof ApiError && error.status === 0,
  );
});
