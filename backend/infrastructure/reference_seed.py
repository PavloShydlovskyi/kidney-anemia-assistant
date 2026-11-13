"""Початкові дані довідника reference_thresholds з клінічних таблиць проєкту.

Версія KDIGO-2024/WHO-2024, 24 рядки:
    input_limit   — egfr, creatinine, hemoglobin, rbc × male/female  (8)
    gfr_category  — G1, G2, G3a, G3b, G4, G5, sex = 'any'            (6)
    anemia_grade  — none, mild, moderate, severe × male/female      (8)
    rbc_reference — normal × male/female                            (2)

Значення мають збігатися з domain/limits.py (перевіряє тест).
Використовується міграцією 0001 і тестами.

TODO: інкремент 1 (Database Developer).
"""
