"""Реалізації портів ReferenceRepository і AssessmentRepository на SQLAlchemy.

Відповідальний: Database Developer (звіт, п. 4.2).

Правила:
- лише параметризовані запити SQLAlchemy, явні колонки, без SELECT *;
- жодної клінічної логіки: категорії й межі — у domain/, тут лише читання й запис;
- винятки SQLAlchemy не виходять за межі модуля — перетворюються на винятки з ports;
- ключі ReferenceSet.input_limits — (parameter, Sex), parameter як у БД:
  egfr, creatinine, hemoglobin, rbc. Сервіс сам зіставляє їх з полями API.
"""
from sqlalchemy import Connection, Engine, Row

from domain.anemia import AnemiaGrade
from domain.kidney import GfrCategory
from domain.limits import Limits, Sex
from infrastructure.db import (
    assessments,
    guideline_versions,
    lab_results,
    patients,
    reference_thresholds,
)
from services.ports import (
    AssessmentRecord,
    AssessmentResult,
    DataIntegrityError,
    LabInput,
    ReferenceDataError,
    ReferenceSet,
    UnknownPatientError,
)


class SqlAlchemyReferenceRepository:
    """Читає порогові та граничні значення чинної версії настанов."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_current(self) -> ReferenceSet:
        """SELECT чинної версії з guideline_versions, потім її рядків із reference_thresholds.

        Немає чинної версії або довідник неповний -> ReferenceDataError.
        TODO (Database Developer).
        """
        raise NotImplementedError


class SqlAlchemyAssessmentRepository:
    """Зберігає аналізи разом із результатами і повертає історію пацієнта."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, lab: LabInput, result: AssessmentResult) -> int:
        """Одна транзакція (engine.begin()): перевірка пацієнта, INSERT у lab_results,
        INSERT в assessments; повертає id оцінювання.

        Пацієнта немає -> UnknownPatientError; IntegrityError -> DataIntegrityError.
        TODO (Database Developer).
        """
        raise NotImplementedError

    def list_by_patient(self, patient_id: int) -> list[AssessmentRecord]:
        """Один SELECT із JOIN lab_results і assessments, ORDER BY taken_on, id.

        TODO (Database Developer).
        """
        raise NotImplementedError


# ---------- Допоміжні функції ----------

def _ensure_patient_exists(connection: Connection, patient_id: int) -> None:
    """SELECT EXISTS(...) у patients; немає -> UnknownPatientError. TODO."""
    raise NotImplementedError


def _to_record(row: Row) -> AssessmentRecord:
    """Рядок JOIN -> AssessmentRecord(assessment_id, LabInput, AssessmentResult). TODO."""
    raise NotImplementedError


def _to_reference_set(version: str, rows: list[Row]) -> ReferenceSet:
    """Рядки reference_thresholds -> ReferenceSet.

    kind = input_limit   -> input_limits[(parameter, Sex)] = Limits(lower, upper)
    kind = gfr_category  -> GfrCategory(code, lower)
    kind = anemia_grade  -> anemia_grades[Sex] += AnemiaGrade(code, lower)
    kind = rbc_reference -> rbc_reference[Sex] = Limits(lower, upper)
    TODO (Database Developer).
    """
    raise NotImplementedError
