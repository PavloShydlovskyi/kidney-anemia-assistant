"""Граничні значення вхідних показників за клінічною таблицею.

Тут лежать значення за замовчуванням. У робочому застосунку їх читають
з таблиці reference_thresholds (ReferenceRepository), а цей модуль
задає структуру і служить запасним варіантом для тестів.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Optional


class Sex(str, Enum):
    MALE = "male"
    FEMALE = "female"


@dataclass(frozen=True)
class Limits:
    lower: float
    upper: float  # обидві межі входять у допустимий діапазон

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper


EGFR_LIMITS = Limits(0, 100)                     # мл/хв/1,73 м², для ШКФ із лабораторії

CREATININE_LIMITS = {                            # мкмоль/л
    Sex.MALE: Limits(40, 1000),
    Sex.FEMALE: Limits(60, 1000),
}

HEMOGLOBIN_LIMITS = {                            # г/л
    Sex.MALE: Limits(40, 170),
    Sex.FEMALE: Limits(30, 160),
}

RBC_LIMITS = {                                   # ×10¹²/л
    Sex.MALE: Limits(1, 6),
    Sex.FEMALE: Limits(1, 5),
}


# Показник у довіднику -> межі для статі. Ключі як у reference_thresholds:
# parameter (egfr, creatinine, hemoglobin, rbc) і стать.
DEFAULT_INPUT_LIMITS = {
    **{("egfr", sex): EGFR_LIMITS for sex in Sex},
    **{("creatinine", sex): limits for sex, limits in CREATININE_LIMITS.items()},
    **{("hemoglobin", sex): limits for sex, limits in HEMOGLOBIN_LIMITS.items()},
    **{("rbc", sex): limits for sex, limits in RBC_LIMITS.items()},
}

PARAMETER_NAMES = {
    "egfr": "ШКФ",
    "creatinine": "Креатинін",
    "hemoglobin": "Гемоглобін",
    "rbc": "Еритроцити",
}
PARAMETER_UNITS = {
    "egfr": "мл/хв/1,73 м²",
    "creatinine": "мкмоль/л",
    "hemoglobin": "г/л",
    "rbc": "×10¹²/л",
}
SEX_NAMES = {Sex.MALE: "чоловіків", Sex.FEMALE: "жінок"}


@dataclass(frozen=True)
class LimitViolation:
    parameter: str
    message: str


def find_limit_violations(
    values: Mapping[str, Optional[float]],
    sex: Sex,
    input_limits: Mapping[tuple[str, Sex], Limits] = DEFAULT_INPUT_LIMITS,
) -> list[LimitViolation]:
    """Повертає всі показники поза граничними значеннями (порожні — пропускає)."""
    violations = []
    for parameter, value in values.items():
        limits = input_limits.get((parameter, sex))
        if value is None or limits is None or limits.contains(value):
            continue
        unit = PARAMETER_UNITS[parameter]
        violations.append(LimitViolation(
            parameter,
            f"{PARAMETER_NAMES[parameter]} {value:g} {unit} поза межами "
            f"{limits.lower:g}–{limits.upper:g} {unit} для {SEX_NAMES[sex]}",
        ))
    return violations
