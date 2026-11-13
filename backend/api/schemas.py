"""Схеми запитів і відповідей API (Pydantic v2).

Схема запиту:
1. перевіряє типи і обов'язкові поля;
2. переводить одиниці до спільних (креатинін — мкмоль/л, гемоглобін — г/л);
3. перевіряє логічні умови (вагітність лише для жінок).

Граничні значення з клінічної таблиці перевіряє сервіс, бо вони беруться
з довідника БД (reference_thresholds), а не записані в схемі.
Клінічні розрахунки тут не виконуються — вони в domain/.
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.limits import Sex

UMOL_L_PER_MG_DL = 88.4
G_L_PER_G_DL = 10


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

    patient_id: Optional[int] = Field(
        default=None, ge=1, description="Якщо вказано, результат зберігається в історії пацієнта"
    )
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
    taken_on: Optional[date] = Field(
        default=None, description="Дата аналізу; якщо не вказано — сьогодні"
    )

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
    def check_pregnancy(self) -> "AssessmentRequest":
        if self.pregnant and self.sex is Sex.MALE:
            raise ValueError("Вагітність може бути вказана лише для жінок")
        return self


# ---------- Відповіді ----------

class AssessmentResponse(BaseModel):
    """Результат оцінювання. Не є діагнозом: заходи — лише для розгляду лікарем."""

    id: Optional[int] = Field(default=None, description="Немає, якщо patient_id не вказано")
    patient_id: Optional[int] = None
    taken_on: Optional[date] = None
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


class HistoryItem(BaseModel):
    """Один запис історії пацієнта (GET /api/patients/{id}/assessments)."""

    id: int
    taken_on: date
    age: int
    creatinine_umol_l: float
    hemoglobin_g_l: Optional[float] = None
    rbc: Optional[float] = None
    egfr_lab: Optional[float] = None
    on_dialysis: bool
    egfr: float
    gfr_category: str
    anemia_grade: Optional[AnemiaGrade] = None
    rbc_status: Optional[RbcStatus] = None
    measures: list[str] = Field(default_factory=list)
    guideline_version: str


class LimitOut(BaseModel):
    """Одне граничне значення для GET /api/reference."""

    indicator: str
    sex: Optional[Sex] = None
    lower: float
    upper: float
    unit: str


class ReferenceResponse(BaseModel):
    limits: list[LimitOut]


class ErrorItem(BaseModel):
    field: Optional[str] = Field(description="Поле запиту; null — помилка не прив'язана до поля")
    message: str


class ErrorResponse(BaseModel):
    """Узгоджений формат помилок 422 / 404 / 409 / 503."""

    detail: list[ErrorItem]
