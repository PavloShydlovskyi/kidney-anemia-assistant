"""Заходи для розгляду лікарем: гемодіаліз, ESA, переливання еритроцитів.

Це підказки за клінічною таблицею, а не призначення: рішення приймає лікар.
Джерела: KDIGO 2024 (діаліз), KDIGO 2026 (ESA), AABB 2023 (трансфузія).
"""
from dataclasses import dataclass
from typing import Optional

from .anemia import NO_ANEMIA

ESA_ON_DIALYSIS_MAX_HB_G_L = 100
TRANSFUSION_CONSIDER_BELOW_HB_G_L = 70
TRANSFUSION_NOT_AUTOMATIC_BELOW_HB_G_L = 80

DIALYSIS_BY_CATEGORY = {
    "G1": "Гемодіаліз не показаний лише на підставі стадії.",
    "G2": "Гемодіаліз не показаний лише на підставі стадії.",
    "G3a": "Гемодіаліз зазвичай не показаний; потрібне регулярне спостереження за прогресуванням ХХН.",
    "G3b": "Гемодіаліз зазвичай не показаний; потрібне регулярне спостереження за прогресуванням ХХН.",
    "G4": "Розглянути планування нирковозамісної терапії і підготовку діалізного доступу за показаннями.",
    "G5": "Оцінити показання до початку діалізу; не починати автоматично лише через ШКФ або креатинін.",
}
ESA_WITHOUT_DIALYSIS = ("ESA: без діалізу фіксованого порога немає — рішення індивідуальне "
                        "після оцінки причин анемії.")
ESA_ON_DIALYSIS = ("Розглянути початок ESA (діаліз, Hb ≤ 90–100 г/л); спершу оцінити й "
                   "усунути кориговані причини анемії. Цільовий Hb після початку — < 115 г/л.")
TRANSFUSION_CONSIDER = ("Розглянути переливання еритроцитів (Hb < 70 г/л) у гемодинамічно "
                        "стабільного пацієнта; рішення залежить від клінічного контексту.")
TRANSFUSION_NOT_AUTOMATIC = "Hb 70–79 г/л: автоматичного показання до переливання немає."


@dataclass(frozen=True)
class ClinicalFindings:
    """Те, що вже визначено для пацієнта і від чого залежать заходи."""
    gfr_category: str
    hemoglobin_g_l: float
    anemia_grade: str
    on_dialysis: bool


def suggest_measures(findings: ClinicalFindings) -> tuple[str, ...]:
    """Повертає заходи для розгляду в порядку: діаліз, ESA, трансфузія."""
    candidates = (
        None if findings.on_dialysis else DIALYSIS_BY_CATEGORY[findings.gfr_category],
        _esa(findings),
        _transfusion(findings.hemoglobin_g_l),
    )
    return tuple(measure for measure in candidates if measure)


def _esa(findings: ClinicalFindings) -> Optional[str]:
    if findings.anemia_grade == NO_ANEMIA:
        return None
    if not findings.on_dialysis:
        return ESA_WITHOUT_DIALYSIS
    if findings.hemoglobin_g_l <= ESA_ON_DIALYSIS_MAX_HB_G_L:
        return ESA_ON_DIALYSIS
    return None


def _transfusion(hemoglobin_g_l: float) -> Optional[str]:
    if hemoglobin_g_l < TRANSFUSION_CONSIDER_BELOW_HB_G_L:
        return TRANSFUSION_CONSIDER
    if hemoglobin_g_l < TRANSFUSION_NOT_AUTOMATIC_BELOW_HB_G_L:
        return TRANSFUSION_NOT_AUTOMATIC
    return None
