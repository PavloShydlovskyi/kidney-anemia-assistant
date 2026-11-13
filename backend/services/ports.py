"""Порти (інтерфейси) доступу до даних і структури для обміну з репозиторіями.

Узгоджено зі звітом Database Developer: назви полів структур збігаються
з назвами колонок БД. Реалізації — в infrastructure/.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Mapping, Optional, Protocol

from domain.anemia import AnemiaGrade
from domain.kidney import GfrCategory
from domain.limits import Limits, Sex


# ---------- Структури ----------

@dataclass(frozen=True)
class LabInput:
    """Один забір аналізів (рядок lab_results). Одиниці — системні."""
    patient_id: int
    taken_on: date
    age_years: int
    creatinine_umol_l: float
    hemoglobin_g_l: Optional[float]
    rbc_10e12_l: Optional[float]
    on_dialysis: bool
    egfr_lab: Optional[float]


@dataclass(frozen=True)
class AssessmentResult:
    """Результат оцінювання (рядок assessments без службових колонок)."""
    egfr: float
    gfr_category: str
    anemia_grade: Optional[str]
    rbc_status: Optional[str]
    measures: tuple[str, ...]
    guideline_version: str


@dataclass(frozen=True)
class AssessmentRecord:
    assessment_id: int
    lab: LabInput
    result: AssessmentResult


@dataclass(frozen=True)
class ReferenceSet:
    """Усі межі однієї версії настанов (рядки reference_thresholds)."""
    guideline_version: str
    input_limits: Mapping[tuple[str, Sex], Limits]
    gfr_categories: tuple[GfrCategory, ...]
    anemia_grades: Mapping[Sex, tuple[AnemiaGrade, ...]]
    rbc_reference: Mapping[Sex, Limits] = field(default_factory=dict)


# ---------- Інтерфейси ----------

class ReferenceRepository(Protocol):
    def get_current(self) -> ReferenceSet:
        """Межі чинної версії настанов."""


class AssessmentRepository(Protocol):
    def save(self, lab: LabInput, result: AssessmentResult) -> int:
        """Записує аналіз і результат в одній транзакції; повертає id оцінювання."""

    def list_by_patient(self, patient_id: int) -> list[AssessmentRecord]:
        """Історія пацієнта за датою аналізу."""


# ---------- Винятки ----------

class UnknownPatientError(Exception):
    """Пацієнта з таким id немає (API: 404)."""


class DataIntegrityError(Exception):
    """Порушено обмеження БД."""


class ReferenceDataError(Exception):
    """Немає чинної версії настанов або довідник неповний."""
