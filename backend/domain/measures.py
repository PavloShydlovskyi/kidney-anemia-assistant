"""Заходи для розгляду лікарем: гемодіаліз, ESA, переливання еритроцитів.

Це підказки за клінічною таблицею, а не призначення: рішення приймає лікар.
Джерела: KDIGO 2024 (діаліз), KDIGO 2026 (ESA), AABB 2023 (трансфузія).
"""

ESA_ON_DIALYSIS_MAX_HB = 100        # г/л: на діалізі розглядати ESA при Hb ≤ 90–100
TRANSFUSION_BELOW_HB = 70           # г/л: розглядати трансфузію при Hb < 70
NO_AUTOMATIC_TRANSFUSION_BELOW = 80 # г/л: при 70–79 автоматичного показання немає

DIALYSIS_BY_CATEGORY = {
    "G1": "Гемодіаліз не показаний лише на підставі стадії.",
    "G2": "Гемодіаліз не показаний лише на підставі стадії.",
    "G3a": "Гемодіаліз зазвичай не показаний; потрібне регулярне спостереження за прогресуванням ХХН.",
    "G3b": "Гемодіаліз зазвичай не показаний; потрібне регулярне спостереження за прогресуванням ХХН.",
    "G4": "Розглянути планування нирковозамісної терапії і підготовку діалізного доступу за показаннями.",
    "G5": "Оцінити показання до початку діалізу; не починати автоматично лише через ШКФ або креатинін.",
}


def suggest_measures(
    gfr_category: str, hemoglobin_g_l: float, anemia_grade: str, on_dialysis: bool,
) -> tuple[str, ...]:
    """Повертає заходи для розгляду в порядку: діаліз, ESA, трансфузія."""
    measures = [
        _dialysis(gfr_category, on_dialysis),
        _esa(hemoglobin_g_l, anemia_grade, on_dialysis),
        _transfusion(hemoglobin_g_l),
    ]
    return tuple(m for m in measures if m)


def _dialysis(gfr_category: str, on_dialysis: bool) -> str | None:
    if on_dialysis:
        return None
    return DIALYSIS_BY_CATEGORY[gfr_category]


def _esa(hemoglobin_g_l: float, anemia_grade: str, on_dialysis: bool) -> str | None:
    if anemia_grade == "none":
        return None
    if not on_dialysis:
        return ("ESA: без діалізу фіксованого порога немає — рішення індивідуальне "
                "після оцінки причин анемії.")
    if hemoglobin_g_l <= ESA_ON_DIALYSIS_MAX_HB:
        return ("Розглянути початок ESA (діаліз, Hb ≤ 90–100 г/л); спершу оцінити й "
                "усунути кориговані причини анемії. Цільовий Hb після початку — < 115 г/л.")
    return None


def _transfusion(hemoglobin_g_l: float) -> str | None:
    if hemoglobin_g_l < TRANSFUSION_BELOW_HB:
        return ("Розглянути переливання еритроцитів (Hb < 70 г/л) у гемодинамічно "
                "стабільного пацієнта; рішення залежить від клінічного контексту.")
    if hemoglobin_g_l < NO_AUTOMATIC_TRANSFUSION_BELOW:
        return "Hb 70–79 г/л: автоматичного показання до переливання немає."
    return None
