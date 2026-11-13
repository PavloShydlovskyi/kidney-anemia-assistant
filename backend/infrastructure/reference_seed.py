"""Початкові дані довідника reference_thresholds з клінічних таблиць проєкту.

Відповідальний: Database Developer. Використовується міграцією 0001 і тестами.
Значення мають збігатися з domain/limits.py, domain/kidney.py, domain/anemia.py,
domain/blood.py — це перевіряє tests/test_repositories.py.
"""

CURRENT_VERSION = "KDIGO-2024/WHO-2024"
CURRENT_VERSION_TITLE = "KDIGO 2024 (ХХН), ВООЗ 2024 (анемія), KDIGO 2026 (ESA), AABB 2023"

# Формат одного рядка:
# {"guideline_version": CURRENT_VERSION, "kind": "input_limit", "parameter": "creatinine",
#  "sex": "male", "code": "", "lower_value": 40, "upper_value": 1000, "unit": "umol_l"}
#
# Очікувано 24 рядки:
#   input_limit   — egfr, creatinine, hemoglobin, rbc × male/female  (8)
#   gfr_category  — G1, G2, G3a, G3b, G4, G5, sex = 'any'            (6)
#   anemia_grade  — none, mild, moderate, severe × male/female      (8)
#   rbc_reference — normal × male/female                            (2)
# Коди одиниць: umol_l, g_l, 10e12_l, ml_min_1_73m2.


def guideline_version_row() -> dict:
    return {"version": CURRENT_VERSION, "title": CURRENT_VERSION_TITLE, "is_current": True}


def reference_rows() -> list[dict]:
    """TODO (Database Developer): повернути 24 рядки довідника."""
    raise NotImplementedError
