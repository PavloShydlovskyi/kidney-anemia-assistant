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


class Parameter(str, Enum):
    """Показник; значення збігаються з колонкою reference_thresholds.parameter."""
    EGFR = "egfr"
    CREATININE = "creatinine"
    HEMOGLOBIN = "hemoglobin"
    RBC = "rbc"


@dataclass(frozen=True)
class Limits:
    """Допустимий діапазон; обидві межі входять у нього."""
    lower: float
    upper: float

    def contains(self, value: float) -> bool:
        return self.lower <= value <= self.upper


InputLimits = Mapping[tuple[Parameter, Sex], Limits]

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

DEFAULT_INPUT_LIMITS: InputLimits = {
    **{(Parameter.EGFR, sex): EGFR_LIMITS for sex in Sex},
    **{(Parameter.CREATININE, sex): limits for sex, limits in CREATININE_LIMITS.items()},
    **{(Parameter.HEMOGLOBIN, sex): limits for sex, limits in HEMOGLOBIN_LIMITS.items()},
    **{(Parameter.RBC, sex): limits for sex, limits in RBC_LIMITS.items()},
}

PARAMETER_NAMES = {
    Parameter.EGFR: "ШКФ",
    Parameter.CREATININE: "Креатинін",
    Parameter.HEMOGLOBIN: "Гемоглобін",
    Parameter.RBC: "Еритроцити",
}
PARAMETER_UNITS = {
    Parameter.EGFR: "мл/хв/1,73 м²",
    Parameter.CREATININE: "мкмоль/л",
    Parameter.HEMOGLOBIN: "г/л",
    Parameter.RBC: "×10¹²/л",
}
SEX_NAMES = {Sex.MALE: "чоловіків", Sex.FEMALE: "жінок"}


@dataclass(frozen=True)
class LimitViolation:
    parameter: Parameter
    message: str


def find_limit_violations(
    measurements: Mapping[Parameter, Optional[float]],
    sex: Sex,
    input_limits: InputLimits = DEFAULT_INPUT_LIMITS,
) -> list[LimitViolation]:
    """Повертає всі виміряні показники поза граничними значеннями.

    Не виміряний показник (None) пропускається. Межі мають бути для кожного
    показника — повноту довідника перевіряє сервіс до виклику.
    """
    return [
        _violation(parameter, value, input_limits[(parameter, sex)], sex)
        for parameter, value in measurements.items()
        if value is not None and not input_limits[(parameter, sex)].contains(value)
    ]


def _violation(parameter: Parameter, value: float, limits: Limits, sex: Sex) -> LimitViolation:
    unit = PARAMETER_UNITS[parameter]
    return LimitViolation(
        parameter,
        f"{PARAMETER_NAMES[parameter]} {value:g} {unit} поза межами "
        f"{limits.lower:g}–{limits.upper:g} {unit} для {SEX_NAMES[sex]}",
    )
