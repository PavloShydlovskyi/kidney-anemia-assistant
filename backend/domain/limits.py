"""Граничні значення вхідних показників за клінічною таблицею.

Тут лежать значення за замовчуванням. У робочому застосунку їх читають
з таблиці reference_thresholds (ReferenceRepository), а цей модуль
задає структуру і служить запасним варіантом для тестів.
"""
from dataclasses import dataclass
from enum import Enum


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
