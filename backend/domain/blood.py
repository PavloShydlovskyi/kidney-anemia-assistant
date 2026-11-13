"""Оцінка еритроцитів відносно референтних меж.

Результат лише інформаційний: кількість еритроцитів не визначає ступінь
анемії і не впливає на заходи (клінічна таблиця).
"""
from typing import Mapping

from .limits import Limits, Sex

DEFAULT_RBC_REFERENCE: Mapping[Sex, Limits] = {   # ×10¹²/л, залежать від лабораторії
    Sex.MALE: Limits(4.3, 5.7),
    Sex.FEMALE: Limits(3.8, 5.1),
}


def classify_rbc(
    rbc_10e12_l: float, sex: Sex,
    reference: Mapping[Sex, Limits] = DEFAULT_RBC_REFERENCE,
) -> str:
    """Повертає low, normal або high."""
    limits = reference[sex]
    if rbc_10e12_l < limits.lower:
        return "low"
    if rbc_10e12_l > limits.upper:
        return "high"
    return "normal"
