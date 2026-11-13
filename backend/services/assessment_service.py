"""Сценарій оцінювання: перевірити → розрахувати ШКФ → класифікувати → заходи → зберегти.

Сервіс не знає про HTTP і SQL: отримує дані звичайними структурами,
межі — з ReferenceRepository, зберігає через AssessmentRepository.
"""
from dataclasses import dataclass
from datetime import date
from typing import Callable, Optional

from domain.anemia import anemia_thresholds_apply, classify_anemia
from domain.blood import classify_rbc
from domain.kidney import calculate_egfr, classify_gfr
from domain.limits import Sex, find_limit_violations
from domain.measures import suggest_measures

from .ports import (
    AssessmentRecord,
    AssessmentRepository,
    AssessmentResult,
    LabInput,
    ReferenceRepository,
    ReferenceSet,
)

EGFR_DISPLAY_LIMIT = 100

# Показник у довіднику -> поле запиту API (для повідомлень про помилки).
REQUEST_FIELD_BY_PARAMETER = {
    "egfr": "egfr_lab",
    "creatinine": "creatinine",
    "hemoglobin": "hemoglobin",
    "rbc": "rbc",
}


@dataclass(frozen=True)
class AssessmentInput:
    """Вхідні дані, вже переведені в системні одиниці."""
    sex: Sex
    age: int
    creatinine_umol_l: float
    hemoglobin_g_l: float
    rbc_10e12_l: Optional[float] = None
    egfr_lab: Optional[float] = None
    on_dialysis: bool = False
    pregnant: bool = False
    patient_id: Optional[int] = None
    taken_on: Optional[date] = None


@dataclass(frozen=True)
class AssessmentOutcome:
    assessment_id: Optional[int]
    patient_id: Optional[int]
    taken_on: date
    egfr: float
    egfr_display: str
    egfr_source: str
    gfr_category: str
    hemoglobin_g_l: float
    anemia_grade: str
    rbc_status: Optional[str]
    measures: tuple[str, ...]
    warnings: tuple[str, ...]
    guideline_version: str


@dataclass(frozen=True)
class FieldError:
    field: str
    message: str


class InputLimitError(Exception):
    """Показники поза граничними значеннями (API: 422)."""

    def __init__(self, errors: list[FieldError]):
        super().__init__("; ".join(e.message for e in errors))
        self.errors = errors


class AssessmentService:
    def __init__(
        self,
        references: ReferenceRepository,
        assessments: AssessmentRepository,
        today: Callable[[], date] = date.today,
    ):
        self._references = references
        self._assessments = assessments
        self._today = today

    def reference(self) -> ReferenceSet:
        return self._references.get_current()

    def history(self, patient_id: int) -> list[AssessmentRecord]:
        return self._assessments.list_by_patient(patient_id)

    def assess(self, data: AssessmentInput) -> AssessmentOutcome:
        reference = self._references.get_current()
        self._check_limits(data, reference)

        egfr, source = self._resolve_egfr(data, reference)
        gfr_category = classify_gfr(egfr, reference.gfr_categories)
        anemia_grade = classify_anemia(data.hemoglobin_g_l, data.sex, reference.anemia_grades)
        rbc_status = (
            classify_rbc(data.rbc_10e12_l, data.sex, reference.rbc_reference)
            if data.rbc_10e12_l is not None else None
        )
        measures = suggest_measures(gfr_category, data.hemoglobin_g_l, anemia_grade, data.on_dialysis)
        result = AssessmentResult(
            egfr=round(egfr, 1),
            gfr_category=gfr_category,
            anemia_grade=anemia_grade,
            rbc_status=rbc_status,
            measures=measures,
            guideline_version=reference.guideline_version,
        )

        taken_on = data.taken_on or self._today()
        assessment_id = self._save(data, taken_on, result)
        return AssessmentOutcome(
            assessment_id=assessment_id,
            patient_id=data.patient_id,
            taken_on=taken_on,
            egfr=result.egfr,
            egfr_display=_egfr_display(result.egfr, source),
            egfr_source=source,
            gfr_category=gfr_category,
            hemoglobin_g_l=data.hemoglobin_g_l,
            anemia_grade=anemia_grade,
            rbc_status=rbc_status,
            measures=measures,
            warnings=_warnings(data, gfr_category),
            guideline_version=reference.guideline_version,
        )

    @staticmethod
    def _check_limits(data: AssessmentInput, reference: ReferenceSet) -> None:
        values = {
            "egfr": data.egfr_lab,
            "creatinine": data.creatinine_umol_l,
            "hemoglobin": data.hemoglobin_g_l,
            "rbc": data.rbc_10e12_l,
        }
        violations = find_limit_violations(values, data.sex, reference.input_limits)
        if violations:
            raise InputLimitError([
                FieldError(REQUEST_FIELD_BY_PARAMETER[v.parameter], v.message)
                for v in violations
            ])

    @staticmethod
    def _resolve_egfr(data: AssessmentInput, reference: ReferenceSet) -> tuple[float, str]:
        """ШКФ з лабораторії, якщо є; інакше — розрахунок за CKD-EPI 2021."""
        if data.egfr_lab is not None:
            return data.egfr_lab, "lab"
        creatinine_limits = {
            sex: limits for (parameter, sex), limits in reference.input_limits.items()
            if parameter == "creatinine"
        }
        egfr = calculate_egfr(data.creatinine_umol_l, data.age, data.sex, creatinine_limits)
        return egfr, "ckd_epi_2021"

    def _save(self, data: AssessmentInput, taken_on: date, result: AssessmentResult) -> Optional[int]:
        """Зберігає лише оцінювання конкретного пацієнта."""
        if data.patient_id is None:
            return None
        lab = LabInput(
            patient_id=data.patient_id,
            taken_on=taken_on,
            age_years=data.age,
            creatinine_umol_l=data.creatinine_umol_l,
            hemoglobin_g_l=data.hemoglobin_g_l,
            rbc_10e12_l=data.rbc_10e12_l,
            on_dialysis=data.on_dialysis,
            egfr_lab=data.egfr_lab,
        )
        return self._assessments.save(lab, result)


def _egfr_display(egfr: float, source: str) -> str:
    if source == "ckd_epi_2021" and egfr > EGFR_DISPLAY_LIMIT:
        return f"> {EGFR_DISPLAY_LIMIT}"
    return f"{egfr:.1f}"


def _warnings(data: AssessmentInput, gfr_category: str) -> tuple[str, ...]:
    warnings = []
    if gfr_category in ("G1", "G2"):
        warnings.append("Категорія G1–G2 сама не підтверджує ХХН: потрібні маркери "
                        "ураження нирок протягом ≥ 3 місяців.")
    if not anemia_thresholds_apply(data.age, data.pregnant):
        warnings.append("Пороги гемоглобіну ВООЗ 2024 наведені для дорослих 15–65 років "
                        "і невагітних жінок; для цього пацієнта вони можуть не підходити.")
    if data.rbc_10e12_l is not None:
        warnings.append("Кількість еритроцитів лише інформаційна: вона не визначає ступінь "
                        "анемії і не впливає на заходи.")
    return tuple(warnings)
