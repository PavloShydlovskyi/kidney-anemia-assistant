"""Оцінювання функції нирок: ШКФ за CKD-EPI 2021 і категорія ШКФ G1–G5 (KDIGO 2024).

Граничні значення креатиніну тут не перевіряються: це робить сервіс один раз
для всіх показників (domain.limits.find_limit_violations).
"""
from dataclasses import dataclass
from typing import Sequence

from .bands import band_code
from .limits import Sex
from .units import creatinine_umol_l_to_mg_dl

MIN_ADULT_AGE = 18


@dataclass(frozen=True)
class CkdEpiCoefficients:
    kappa_mg_dl: float
    alpha: float
    sex_factor: float


CKD_EPI_2021 = {
    Sex.MALE: CkdEpiCoefficients(kappa_mg_dl=0.9, alpha=-0.302, sex_factor=1.0),
    Sex.FEMALE: CkdEpiCoefficients(kappa_mg_dl=0.7, alpha=-0.241, sex_factor=1.012),
}
CKD_EPI_BASE = 142
CKD_EPI_UPPER_EXPONENT = -1.200
CKD_EPI_AGE_FACTOR = 0.9938


@dataclass(frozen=True)
class GfrCategory:
    code: str
    lower_bound: float  # мл/хв/1,73 м²


DEFAULT_GFR_CATEGORIES = (
    GfrCategory("G1", 90),
    GfrCategory("G2", 60),
    GfrCategory("G3a", 45),
    GfrCategory("G3b", 30),
    GfrCategory("G4", 15),
    GfrCategory("G5", 0),
)

# Без маркерів ураження нирок ≥ 3 місяців ці категорії не підтверджують ХХН.
CATEGORIES_WITHOUT_REDUCED_GFR = frozenset({"G1", "G2"})


def calculate_egfr(creatinine_umol_l: float, age: int, sex: Sex) -> float:
    """Повертає ШКФ, мл/хв/1,73 м², за креатиніном у мкмоль/л."""
    if creatinine_umol_l <= 0:
        raise ValueError("Креатинін має бути більшим за нуль")
    if age < MIN_ADULT_AGE:
        raise ValueError("CKD-EPI 2021 застосовують лише для дорослих")

    coefficients = CKD_EPI_2021[sex]
    ratio = creatinine_umol_l_to_mg_dl(creatinine_umol_l) / coefficients.kappa_mg_dl
    return (
        CKD_EPI_BASE
        * min(ratio, 1) ** coefficients.alpha
        * max(ratio, 1) ** CKD_EPI_UPPER_EXPONENT
        * CKD_EPI_AGE_FACTOR ** age
        * coefficients.sex_factor
    )


def classify_gfr(egfr: float, categories: Sequence[GfrCategory] = DEFAULT_GFR_CATEGORIES) -> str:
    """Повертає код категорії ШКФ; межі передаються ззовні (з довідника БД)."""
    return band_code(egfr, categories)
