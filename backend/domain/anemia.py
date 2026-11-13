"""Ступінь анемії за гемоглобіном з урахуванням статі (ВООЗ 2024).

Пороги — для дорослих 15–65 років і невагітних жінок. Межі передаються
ззовні (з довідника БД); тут — значення за замовчуванням.
"""
from dataclasses import dataclass
from typing import Mapping, Sequence

from .limits import Sex


@dataclass(frozen=True)
class AnemiaGrade:
    code: str           # none, mild, moderate, severe
    lower_bound: float  # г/л, межа входить у ступінь


DEFAULT_ANEMIA_GRADES: Mapping[Sex, tuple[AnemiaGrade, ...]] = {
    Sex.MALE: (
        AnemiaGrade("none", 130),
        AnemiaGrade("mild", 110),
        AnemiaGrade("moderate", 80),
        AnemiaGrade("severe", 0),
    ),
    Sex.FEMALE: (
        AnemiaGrade("none", 120),
        AnemiaGrade("mild", 110),
        AnemiaGrade("moderate", 80),
        AnemiaGrade("severe", 0),
    ),
}

WHO_THRESHOLDS_MIN_AGE = 15
WHO_THRESHOLDS_MAX_AGE = 65


def classify_anemia(
    hemoglobin_g_l: float, sex: Sex,
    grades: Mapping[Sex, Sequence[AnemiaGrade]] = DEFAULT_ANEMIA_GRADES,
) -> str:
    """Повертає код ступеня анемії для гемоглобіну в г/л."""
    for grade in sorted(grades[sex], key=lambda g: g.lower_bound, reverse=True):
        if hemoglobin_g_l >= grade.lower_bound:
            return grade.code
    raise ValueError("Гемоглобін не потрапляє в жоден ступінь")


def anemia_thresholds_apply(age: int, pregnant: bool) -> bool:
    """Чи підходять пороги ВООЗ 2024 цьому пацієнту."""
    return WHO_THRESHOLDS_MIN_AGE <= age <= WHO_THRESHOLDS_MAX_AGE and not pregnant
