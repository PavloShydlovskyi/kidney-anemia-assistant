import { test } from "node:test";
import assert from "node:assert/strict";
import {
  validateAssessment,
  convertForValidation,
} from "../src/validation/formValidation.js";
const valid = {
  sex: "female",
  age: 35,
  creatinine: 90,
  creatinine_unit: "umol_l",
  hemoglobin: 120,
  hemoglobin_unit: "g_l",
  on_dialysis: false,
  pregnant: false,
};
test("valid input passes local checks", () =>
  assert.deepEqual(validateAssessment(valid), {}));
test("missing age, sex and measurements show separate errors", () => {
  const errors = validateAssessment({
    age: NaN,
    creatinine: NaN,
    hemoglobin: NaN,
  });
  for (const key of ["sex", "age", "creatinine", "hemoglobin"])
    assert.ok(errors[key]);
});
test("sex specific boundaries are inclusive", () => {
  assert.deepEqual(
    validateAssessment({ ...valid, creatinine: 60, hemoglobin: 160 }),
    {},
  );
  assert.ok(validateAssessment({ ...valid, creatinine: 59 }).creatinine);
});
test("units are normalized for local range hints", () => {
  assert.equal(convertForValidation("creatinine", 1, "mg_dl"), 88.4);
  assert.deepEqual(
    validateAssessment({
      ...valid,
      creatinine: 1,
      creatinine_unit: "mg_dl",
      hemoglobin: 12,
      hemoglobin_unit: "g_dl",
    }),
    {},
  );
});
test("invalid optional values are rejected", () => {
  assert.ok(validateAssessment({ ...valid, patient_id: 0 }).patient_id);
  assert.ok(validateAssessment({ ...valid, rbc: 0 }).rbc);
  assert.ok(validateAssessment({ ...valid, egfr_lab: 101 }).egfr_lab);
});
