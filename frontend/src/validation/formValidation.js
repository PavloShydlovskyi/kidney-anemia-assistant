export const DEFAULT_LIMITS = {
  male: {
    creatinine: [40, 1000],
    hemoglobin: [40, 170],
    rbc: [1, 6],
    egfr_lab: [0, 100],
  },
  female: {
    creatinine: [60, 1000],
    hemoglobin: [30, 160],
    rbc: [1, 5],
    egfr_lab: [0, 100],
  },
};

const units = {
  creatinine: { umol_l: 1, mg_dl: 88.4 },
  hemoglobin: { g_l: 1, g_dl: 10 },
};
export function convertForValidation(field, value, unit) {
  return value * (units[field]?.[unit] ?? 1);
}

export function getLimits(reference, sex, field) {
  const fallback = DEFAULT_LIMITS[sex]?.[field];
  if (!fallback) return null;
  const candidates = [
    reference?.[field]?.[sex],
    reference?.limits?.[field]?.[sex],
    reference?.[sex]?.[field],
  ];
  for (const candidate of candidates) {
    if (
      Array.isArray(candidate) &&
      candidate.length === 2 &&
      candidate.every(Number.isFinite)
    )
      return candidate;
    if (
      candidate &&
      Number.isFinite(candidate.min) &&
      Number.isFinite(candidate.max)
    )
      return [candidate.min, candidate.max];
  }
  return fallback;
}

export function validateAssessment(data, reference) {
  const errors = {};
  if (
    data.patient_id !== undefined &&
    (!Number.isInteger(data.patient_id) || data.patient_id < 1)
  )
    errors.patient_id = "Введіть цілий ID від 1.";
  if (!["male", "female"].includes(data.sex))
    errors.sex = "Оберіть стать пацієнта.";
  if (!Number.isInteger(data.age) || data.age < 18 || data.age > 120)
    errors.age = "Введіть вік від 18 до 120 років.";
  for (const field of ["creatinine", "hemoglobin"])
    if (!Number.isFinite(data[field]) || data[field] <= 0)
      errors[field] = "Введіть додатне числове значення.";
  for (const field of ["rbc", "egfr_lab"])
    if (
      data[field] !== undefined &&
      (!Number.isFinite(data[field]) ||
        data[field] < 0 ||
        (field === "rbc" && data[field] === 0))
    )
      errors[field] = "Введіть коректне додатне значення.";
  if (data.pregnant && data.sex !== "female")
    errors.pregnant = "Вагітність доступна лише для жінок.";
  if (!errors.sex)
    for (const field of ["creatinine", "hemoglobin", "rbc", "egfr_lab"]) {
      if (errors[field] || data[field] === undefined) continue;
      const [min, max] = getLimits(reference, data.sex, field);
      const normalized = convertForValidation(
        field,
        data[field],
        data[`${field}_unit`],
      );
      if (normalized < min || normalized > max)
        errors[field] =
          `Допустимий діапазон: ${min}–${max} ${field === "creatinine" ? "мкмоль/л" : field === "hemoglobin" ? "г/л" : field === "rbc" ? "×10¹²/л" : "мл/хв/1,73 м²"}.`;
    }
  return errors;
}
