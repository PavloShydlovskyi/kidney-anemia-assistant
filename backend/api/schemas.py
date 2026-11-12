"""Схеми запитів і відповідей API (Pydantic v2).

Схема запиту:
1. перевіряє типи і обов'язкові поля;
2. переводить одиниці до спільних (креатинін — мкмоль/л, гемоглобін — г/л);
3. перевіряє граничні значення з клінічної таблиці окремо для статі.

Якщо щось не так, FastAPI автоматично повертає 422 з поясненням.
Клінічні розрахунки тут не виконуються — вони в domain/.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.limits import (
    CREATININE_LIMITS,
    EGFR_LIMITS,
    HEMOGLOBIN_LIMITS,
    RBC_LIMITS,
    Limits,
    Sex,
)

UMOL_L_PER_MG_DL = 88.4
G_L_PER_G_DL = 10
SEX_NAMES = {Sex.MALE: "чоловіків", Sex.FEMALE: "жінок"}


class CreatinineUnit(str, Enum):
    UMOL_L = "umol_l"
    MG_DL = "mg_dl"


class HemoglobinUnit(str, Enum):
    G_L = "g_l"
    G_DL = "g_dl"


class AnemiaGrade(str, Enum):
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class RbcStatus(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


# ---------- Запит ----------

class AssessmentRequest(BaseModel):
    """Дані для POST /api/assessments."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "patient_id": 17,
                "sex": "female",
                "age": 60,
                "creatinine": 130,
                "creatinine_unit": "umol_l",
                "hemoglobin": 9.5,
                "hemoglobin_unit": "g_dl",
                "rbc": 3.6,
                "on_dialysis": False,
            }
        },
    )

    patient_id: Optional[int] = Field(default=None, ge=1)
    sex: Sex
    age: int = Field(ge=18, le=120, description="Вік, роки; CKD-EPI 2021 — лише для дорослих")
    creatinine: float = Field(gt=0)
    creatinine_unit: CreatinineUnit = CreatinineUnit.UMOL_L
    hemoglobin: float = Field(gt=0)
    hemoglobin_unit: HemoglobinUnit = HemoglobinUnit.G_L
    rbc: Optional[float] = Field(default=None, gt=0, description="Еритроцити, ×10¹²/л")
    egfr_lab: Optional[float] = Field(
        default=None, description="ШКФ, якщо її розрахувала лабораторія, мл/хв/1,73 м²"
    )
    on_dialysis: bool = False
    pregnant: bool = False

    @property
    def creatinine_umol_l(self) -> float:
        if self.creatinine_unit is CreatinineUnit.MG_DL:
            return self.creatinine * UMOL_L_PER_MG_DL
        return self.creatinine

    @property
    def hemoglobin_g_l(self) -> float:
        if self.hemoglobin_unit is HemoglobinUnit.G_DL:
            return self.hemoglobin * G_L_PER_G_DL
        return self.hemoglobin

    @model_validator(mode="after")
    def check_limits(self) -> "AssessmentRequest":
        if self.pregnant and self.sex is Sex.MALE:
            raise ValueError("Вагітність може бути вказана лише для жінок")

        errors = [
            _outside("Креатинін", self.creatinine_umol_l, CREATININE_LIMITS[self.sex], "мкмоль/л", self.sex),
            _outside("Гемоглобін", self.hemoglobin_g_l, HEMOGLOBIN_LIMITS[self.sex], "г/л", self.sex),
        ]
        if self.rbc is not None:
            errors.append(_outside("Еритроцити", self.rbc, RBC_LIMITS[self.sex], "×10¹²/л", self.sex))
        if self.egfr_lab is not None:
            errors.append(_outside("ШКФ", self.egfr_lab, EGFR_LIMITS, "мл/хв/1,73 м²"))

        errors = [e for e in errors if e]
        if errors:
            raise ValueError("; ".join(errors))
        return self


def _outside(
    name: str, value: float, limits: Limits, unit: str, sex: Optional[Sex] = None
) -> Optional[str]:
    """Повертає текст помилки, якщо значення поза граничними, інакше None."""
    if limits.contains(value):
        return None
    who = f" для {SEX_NAMES[sex]}" if sex else ""
    return f"{name} {value:g} {unit} поза межами {limits.lower:g}–{limits.upper:g} {unit}{who}"


# ---------- Відповіді ----------

class AssessmentResponse(BaseModel):
    """Результат оцінювання. Не є діагнозом: заходи — лише для розгляду лікарем."""

    id: Optional[int] = None
    patient_id: Optional[int] = None
    egfr: float = Field(description="ШКФ, мл/хв/1,73 м²")
    egfr_display: str = Field(description="Для показу: «> 100», якщо розрахована ШКФ вища за 100")
    egfr_source: str = Field(description="lab — з лабораторії, ckd_epi_2021 — розрахована")
    gfr_category: str = Field(description="G1, G2, G3a, G3b, G4 або G5")
    hemoglobin_g_l: float
    anemia_grade: AnemiaGrade
    rbc_status: Optional[RbcStatus] = None
    measures: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    guideline_version: str
    created_at: Optional[datetime] = None


class LimitOut(BaseModel):
    """Одне граничне значення для GET /api/reference."""

    indicator: str
    sex: Optional[Sex] = None
    lower: float
    upper: float
    unit: str


class ReferenceResponse(BaseModel):
    limits: list[LimitOut]
