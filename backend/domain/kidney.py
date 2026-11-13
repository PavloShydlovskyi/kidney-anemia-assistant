"""Оцінювання функції нирок: ШКФ за CKD-EPI 2021 і категорія ШКФ G1–G5 (KDIGO 2024)."""
from dataclasses import dataclass
from typing import Mapping, Sequence

from .limits import CREATININE_LIMITS, Limits, Sex

UMOL_L_PER_MG_DL = 88.4
MIN_ADULT_AGE = 18


@dataclass(frozen=True)
class CkdEpiCoefficients:
    kappa: float       # мг/дл
    alpha: float
    sex_factor: float


CKD_EPI_2021 = {
    Sex.MALE: CkdEpiCoefficients(kappa=0.9, alpha=-0.302, sex_factor=1.0),
    Sex.FEMALE: CkdEpiCoefficients(kappa=0.7, alpha=-0.241, sex_factor=1.012),
}
CKD_EPI_BASE = 142
CKD_EPI_UPPER_EXPONENT = -1.200
CKD_EPI_AGE_FACTOR = 0.9938


@dataclass(frozen=True)
class GfrCategory:
    code: str
    lower_bound: float  # мл/хв/1,73 м², межа входить у категорію


DEFAULT_GFR_CATEGORIES = (
    GfrCategory("G1", 90),
    GfrCategory("G2", 60),
    GfrCategory("G3a", 45),
    GfrCategory("G3b", 30),
    GfrCategory("G4", 15),
    GfrCategory("G5", 0),
)


def check_creatinine(
    creatinine_umol_l: float, sex: Sex,
    limits: Mapping[Sex, Limits] = CREATININE_LIMITS,
) -> None:
    """Перевіряє, що креатинін у граничних значеннях для статі."""
    allowed = limits[sex]
    if not allowed.contains(creatinine_umol_l):
        raise ValueError(
            f"Креатинін {creatinine_umol_l} мкмоль/л поза межами "
            f"{allowed.lower}–{allowed.upper} для статі {sex.value}"
        )


def calculate_egfr(
    creatinine_umol_l: float, age: int, sex: Sex,
    creatinine_limits: Mapping[Sex, Limits] = CREATININE_LIMITS,
) -> float:
    """Повертає ШКФ, мл/хв/1,73 м², за креатиніном у мкмоль/л."""
    check_creatinine(creatinine_umol_l, sex, creatinine_limits)
    if age < MIN_ADULT_AGE:
        raise ValueError("CKD-EPI 2021 застосовують лише для дорослих")

    k = CKD_EPI_2021[sex]
    ratio = creatinine_umol_l / UMOL_L_PER_MG_DL / k.kappa
    return (
        CKD_EPI_BASE
        * min(ratio, 1) ** k.alpha
        * max(ratio, 1) ** CKD_EPI_UPPER_EXPONENT
        * CKD_EPI_AGE_FACTOR ** age
        * k.sex_factor
    )


def classify_gfr(
    egfr: float, categories: Sequence[GfrCategory] = DEFAULT_GFR_CATEGORIES
) -> str:
    """Повертає код категорії ШКФ; межі передаються ззовні (з довідника БД)."""
    for category in sorted(categories, key=lambda c: c.lower_bound, reverse=True):
        if egfr >= category.lower_bound:
            return category.code
    raise ValueError("ШКФ не потрапляє в жодну категорію")
