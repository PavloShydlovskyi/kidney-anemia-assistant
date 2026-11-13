import { test } from "node:test";
import assert from "node:assert/strict";
import { submitAssessment } from "../src/controllers/assessmentForm.js";
import { ApiError } from "../src/api/httpClient.js";
const payload = {
  sex: "male",
  age: 45,
  creatinine: 90,
  creatinine_unit: "umol_l",
  hemoglobin: 130,
  hemoglobin_unit: "g_l",
  on_dialysis: false,
  pregnant: false,
};
function mockView() {
  const events = [];
  return {
    events,
    clearErrors: () => events.push("clear"),
    readAssessmentRequest: () => payload,
    getReference: () => null,
    showFieldError: (field) => events.push(`field:${field}`),
    showError: (message) => events.push(`error:${message}`),
    setLoading: (value) => events.push(`loading:${value}`),
    showResult: () => events.push("result"),
  };
}
test("successful submission shows result and releases button", async () => {
  const view = mockView();
  assert.equal(
    await submitAssessment(view, {
      createAssessment: async () => ({ egfr: 80 }),
    }),
    true,
  );
  assert.deepEqual(view.events, [
    "clear",
    "loading:true",
    "result",
    "loading:false",
  ]);
});
test("422 points to the server reported field", async () => {
  const view = mockView();
  await submitAssessment(view, {
    createAssessment: async () => {
      throw new ApiError("invalid", 422, [
        { field: "hemoglobin", message: "Too high" },
      ]);
    },
  });
  assert.ok(view.events.includes("field:hemoglobin"));
  assert.equal(view.events.at(-1), "loading:false");
});
test("network error releases button", async () => {
  const view = mockView();
  await submitAssessment(view, {
    createAssessment: async () => {
      throw new ApiError("Offline", 0);
    },
  });
  assert.ok(view.events.includes("error:Offline"));
  assert.equal(view.events.at(-1), "loading:false");
});
test("local validation stops request", async () => {
  const view = mockView();
  view.readAssessmentRequest = () => ({ ...payload, age: 10 });
  let called = false;
  assert.equal(
    await submitAssessment(view, {
      createAssessment: async () => {
        called = true;
      },
    }),
    false,
  );
  assert.equal(called, false);
  assert.ok(view.events.includes("field:age"));
});
