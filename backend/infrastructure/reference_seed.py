"""Початкові дані довідника reference_thresholds з клінічних таблиць проєкту.

Відповідальний: Database Developer. Використовується міграцією 0001 і тестами.
Значення мають збігатися з domain/limits.py, domain/kidney.py, domain/anemia.py,
domain/blood.py — це перевіряє tests/test_repositories.py.
"""

CURRENT_VERSION = "KDIGO-2024/WHO-2024"
CURRENT_VERSION_TITLE = "KDIGO 2024 (ХХН), ВООЗ 2024 (анемія), KDIGO 2026 (ESA), AABB 2023"

# Коди одиниць: umol_l, g_l, 10e12_l, ml_min_1_73m2.
# Значення записані тут як дані (а не взяті з domain/), бо міграції мають
# відтворювати довідник саме таким, яким він був на момент міграції.

KIDNEY_KINDS = ("input_limit", "gfr_category")       # міграція 0001
ANEMIA_KINDS = ("anemia_grade", "rbc_reference")     # міграція 0002

_INPUT_LIMITS = [  # (показник, стать, нижня, верхня, одиниця) — обидві межі включні
    ("egfr", "male", 0, 100, "ml_min_1_73m2"),
    ("egfr", "female", 0, 100, "ml_min_1_73m2"),
    ("creatinine", "male", 40, 1000, "umol_l"),
    ("creatinine", "female", 60, 1000, "umol_l"),
    ("hemoglobin", "male", 40, 170, "g_l"),
    ("hemoglobin", "female", 30, 160, "g_l"),
    ("rbc", "male", 1, 6, "10e12_l"),
    ("rbc", "female", 1, 5, "10e12_l"),
]
_GFR_CATEGORIES = [("G1", 90), ("G2", 60), ("G3a", 45), ("G3b", 30), ("G4", 15), ("G5", 0)]
_ANEMIA_GRADES = {  # нижня межа ступеня, г/л (ВООЗ 2024, невагітні дорослі 15–65 років)
    "male": [("none", 130), ("mild", 110), ("moderate", 80), ("severe", 0)],
    "female": [("none", 120), ("mild", 110), ("moderate", 80), ("severe", 0)],
}
_RBC_REFERENCE = [("male", 4.3, 5.7), ("female", 3.8, 5.1)]   # ×10¹²/л


def guideline_version_row() -> dict:
    return {"version": CURRENT_VERSION, "title": CURRENT_VERSION_TITLE, "is_current": True}


def reference_rows() -> list[dict]:
    """24 рядки довідника версії CURRENT_VERSION."""
    rows = [_row("input_limit", parameter, sex, "", lower, upper, unit)
            for parameter, sex, lower, upper, unit in _INPUT_LIMITS]
    rows += [_row("gfr_category", "egfr", "any", code, lower, None, "ml_min_1_73m2")
             for code, lower in _GFR_CATEGORIES]
    rows += [_row("anemia_grade", "hemoglobin", sex, code, lower, None, "g_l")
             for sex, grades in _ANEMIA_GRADES.items() for code, lower in grades]
    rows += [_row("rbc_reference", "rbc", sex, "normal", lower, upper, "10e12_l")
             for sex, lower, upper in _RBC_REFERENCE]
    return rows


def _row(kind: str, parameter: str, sex: str, code: str,
         lower: float, upper: float | None, unit: str) -> dict:
    return {"guideline_version": CURRENT_VERSION, "kind": kind, "parameter": parameter,
            "sex": sex, "code": code, "lower_value": lower, "upper_value": upper, "unit": unit}
