"""Реалізації портів ReferenceRepository і AssessmentRepository на SQLAlchemy.

Відповідальний: Database Developer (звіт, п. 4.2).

Правила:
- лише параметризовані запити SQLAlchemy, явні колонки, без SELECT *;
- жодної клінічної логіки: категорії й межі — у domain/, тут лише читання й запис;
- винятки SQLAlchemy не виходять за межі модуля — перетворюються на винятки з ports;
- ключі ReferenceSet.input_limits — (parameter, Sex), parameter як у БД:
  egfr, creatinine, hemoglobin, rbc. Сервіс сам зіставляє їх з полями API.
"""
from dataclasses import asdict

from sqlalchemy import Connection, Engine, Row, exists, insert, select
from sqlalchemy.exc import IntegrityError, OperationalError

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
        """
        try:
            with self._engine.connect() as connection:
                version = connection.scalar(
                    select(guideline_versions.c.version).where(guideline_versions.c.is_current)
                )
                if version is None:
                    raise ReferenceDataError("У довіднику немає чинної версії настанов")
                rows = connection.execute(
                    select(reference_thresholds)
                    .where(reference_thresholds.c.guideline_version == version)
                ).all()
        except OperationalError as error:
            raise ReferenceDataError(
                "Довідник недоступний: БД не створена або зайнята "
                "(створити схему: alembic upgrade head)"
            ) from error
        return _to_reference_set(version, rows)


class SqlAlchemyAssessmentRepository:
    """Зберігає аналізи разом із результатами і повертає історію пацієнта."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, lab: LabInput, result: AssessmentResult) -> int:
        """Одна транзакція (engine.begin()): перевірка пацієнта, INSERT у lab_results,
        INSERT в assessments; повертає id оцінювання.

        Пацієнта немає -> UnknownPatientError; IntegrityError -> DataIntegrityError.
        """
        try:
            with self._engine.begin() as connection:
                _ensure_patient_exists(connection, lab.patient_id)
                lab_result_id = connection.execute(
                    insert(lab_results), asdict(lab)
                ).inserted_primary_key[0]
                assessment_row = {**asdict(result), "lab_result_id": lab_result_id}
                return connection.execute(
                    insert(assessments), assessment_row
                ).inserted_primary_key[0]
        except IntegrityError as error:
            raise DataIntegrityError(
                f"Аналіз пацієнта {lab.patient_id} не збережено: порушено обмеження БД"
            ) from error

    def list_by_patient(self, patient_id: int) -> list[AssessmentRecord]:
        """Один SELECT із JOIN lab_results і assessments, ORDER BY taken_on, id."""
        query = (
            select(assessments.c.id.label("assessment_id"), *_LAB_COLUMNS, *_RESULT_COLUMNS)
            .join_from(lab_results, assessments, assessments.c.lab_result_id == lab_results.c.id)
            .where(lab_results.c.patient_id == patient_id)
            .order_by(lab_results.c.taken_on, assessments.c.id)
        )
        with self._engine.connect() as connection:
            return [_to_record(row) for row in connection.execute(query)]


# ---------- Допоміжні функції ----------

_LAB_COLUMNS = (
    lab_results.c.patient_id, lab_results.c.taken_on, lab_results.c.age_years,
    lab_results.c.creatinine_umol_l, lab_results.c.hemoglobin_g_l,
    lab_results.c.rbc_10e12_l, lab_results.c.on_dialysis, lab_results.c.egfr_lab,
)
_RESULT_COLUMNS = (
    assessments.c.egfr, assessments.c.gfr_category, assessments.c.anemia_grade,
    assessments.c.rbc_status, assessments.c.measures, assessments.c.guideline_version,
)


def _ensure_patient_exists(connection: Connection, patient_id: int) -> None:
    """SELECT EXISTS(...) у patients; немає -> UnknownPatientError."""
    if not connection.scalar(select(exists().where(patients.c.id == patient_id))):
        raise UnknownPatientError(f"Пацієнта з id {patient_id} не знайдено")


def _to_record(row: Row) -> AssessmentRecord:
    """Рядок JOIN -> AssessmentRecord(assessment_id, LabInput, AssessmentResult)."""
    lab = LabInput(
        patient_id=row.patient_id, taken_on=row.taken_on, age_years=row.age_years,
        creatinine_umol_l=row.creatinine_umol_l, hemoglobin_g_l=row.hemoglobin_g_l,
        rbc_10e12_l=row.rbc_10e12_l, on_dialysis=row.on_dialysis, egfr_lab=row.egfr_lab,
    )
    result = AssessmentResult(
        egfr=row.egfr, gfr_category=row.gfr_category, anemia_grade=row.anemia_grade,
        rbc_status=row.rbc_status, measures=tuple(row.measures),
        guideline_version=row.guideline_version,
    )
    return AssessmentRecord(row.assessment_id, lab, result)


def _to_reference_set(version: str, rows: list[Row]) -> ReferenceSet:
    """Рядки reference_thresholds -> ReferenceSet.

    kind = input_limit   -> input_limits[(parameter, Sex)] = Limits(lower, upper)
    kind = gfr_category  -> GfrCategory(code, lower)
    kind = anemia_grade  -> anemia_grades[Sex] += AnemiaGrade(code, lower)
    kind = rbc_reference -> rbc_reference[Sex] = Limits(lower, upper)
    """
    input_limits, rbc_reference = {}, {}
    gfr_categories, anemia_grades = [], {Sex.MALE: [], Sex.FEMALE: []}
    for row in rows:
        if row.kind == "input_limit":
            input_limits[(row.parameter, Sex(row.sex))] = Limits(row.lower_value, row.upper_value)
        elif row.kind == "rbc_reference":
            rbc_reference[Sex(row.sex)] = Limits(row.lower_value, row.upper_value)
        elif row.kind == "gfr_category":
            gfr_categories.append(GfrCategory(row.code, row.lower_value))
        elif row.kind == "anemia_grade":
            anemia_grades[Sex(row.sex)].append(AnemiaGrade(row.code, row.lower_value))
    if not input_limits or not gfr_categories or not all(anemia_grades.values()):
        raise ReferenceDataError(f"Довідник версії {version} неповний")
    return ReferenceSet(
        guideline_version=version,
        input_limits=input_limits,
        gfr_categories=tuple(gfr_categories),
        anemia_grades={sex: tuple(grades) for sex, grades in anemia_grades.items()},
        rbc_reference=rbc_reference,
    )
