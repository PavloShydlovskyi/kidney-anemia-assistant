"""Ступінь анемії за гемоглобіном з урахуванням статі (ВООЗ 2024).

Пороги — для дорослих 15–65 років і невагітних жінок. Межі передаються
ззовні (з довідника БД); тут — значення за замовчуванням.
"""
from dataclasses import dataclass
from typing import Mapping, Sequence

from .bands import band_code
from .limits import Sex

NO_ANEMIA = "none"
MILD = "mild"
MODERATE = "moderate"
SEVERE = "severe"


@dataclass(frozen=True)
class AnemiaGrade:
    code: str           # NO_ANEMIA, MILD, MODERATE, SEVERE
    lower_bound: float  # г/л


DEFAULT_ANEMIA_GRADES: Mapping[Sex, tuple[AnemiaGrade, ...]] = {
    Sex.MALE: (
        AnemiaGrade(NO_ANEMIA, 130),
        AnemiaGrade(MILD, 110),
        AnemiaGrade(MODERATE, 80),
        AnemiaGrade(SEVERE, 0),
    ),
    Sex.FEMALE: (
        AnemiaGrade(NO_ANEMIA, 120),
        AnemiaGrade(MILD, 110),
        AnemiaGrade(MODERATE, 80),
        AnemiaGrade(SEVERE, 0),
    ),
}

WHO_THRESHOLDS_MIN_AGE = 15
WHO_THRESHOLDS_MAX_AGE = 65


def classify_anemia(
    hemoglobin_g_l: float, sex: Sex,
    grades: Mapping[Sex, Sequence[AnemiaGrade]] = DEFAULT_ANEMIA_GRADES,
) -> str:
    """Повертає код ступеня анемії для гемоглобіну в г/л."""
    return band_code(hemoglobin_g_l, grades[sex])


def anemia_thresholds_apply(age: int, pregnant: bool) -> bool:
    """Чи підходять пороги ВООЗ 2024 цьому пацієнту."""
    return WHO_THRESHOLDS_MIN_AGE <= age <= WHO_THRESHOLDS_MAX_AGE and not pregnant
