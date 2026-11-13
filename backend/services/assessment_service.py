"""Сценарій оцінювання: перевірити → розрахувати ШКФ → класифікувати → заходи → зберегти.

Сервіс не знає про HTTP і SQL: отримує дані звичайними структурами,
межі — з ReferenceRepository, зберігає через AssessmentRepository.

evaluate() — запит: лише рахує і нічого не змінює.
assess()   — команда: рахує через evaluate() і зберігає результат пацієнта.
"""
from dataclasses import dataclass, replace
from datetime import date
from enum import Enum
from typing import Callable, Optional

from domain.anemia import anemia_thresholds_apply, classify_anemia
from domain.blood import classify_rbc
from domain.kidney import CATEGORIES_WITHOUT_REDUCED_GFR, calculate_egfr, classify_gfr
from domain.limits import LimitViolation, Parameter, Sex, find_limit_violations
from domain.measures import ClinicalFindings, suggest_measures

from .ports import (
    AssessmentRecord,
    AssessmentRepository,
    AssessmentResult,
    LabInput,
    ReferenceDataError,
    ReferenceRepository,
    ReferenceSet,
)

EGFR_DECIMALS = 1
EGFR_DISPLAY_LIMIT = 100

WARNING_CKD_NOT_CONFIRMED = ("Категорія G1–G2 сама не підтверджує ХХН: потрібні маркери "
                             "ураження нирок протягом ≥ 3 місяців.")
WARNING_HB_THRESHOLDS = ("Пороги гемоглобіну ВООЗ 2024 наведені для дорослих 15–65 років "
                         "і невагітних жінок; для цього пацієнта вони можуть не підходити.")
WARNING_RBC_INFORMATIONAL = ("Кількість еритроцитів лише інформаційна: вона не визначає ступінь "
                             "анемії і не впливає на заходи.")


class EgfrSource(str, Enum):
    LAB = "lab"
    CKD_EPI_2021 = "ckd_epi_2021"


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
    egfr_source: EgfrSource
    gfr_category: str
    hemoglobin_g_l: float
    anemia_grade: str
    rbc_status: Optional[str]
    measures: tuple[str, ...]
    warnings: tuple[str, ...]
    guideline_version: str


class InputLimitError(Exception):
    """Показники поза граничними значеннями (API: 422)."""

    def __init__(self, violations: list[LimitViolation]):
        super().__init__("; ".join(violation.message for violation in violations))
        self.violations = violations


class AssessmentService:
    def __init__(
        self,
        reference_repository: ReferenceRepository,
        assessment_repository: AssessmentRepository,
        today: Callable[[], date] = date.today,
    ):
        self._reference_repository = reference_repository
        self._assessment_repository = assessment_repository
        self._today = today

    def reference(self) -> ReferenceSet:
        return self._reference_repository.get_current()

    def history(self, patient_id: int) -> list[AssessmentRecord]:
        return self._assessment_repository.list_by_patient(patient_id)

    def assess(self, assessment_input: AssessmentInput) -> AssessmentOutcome:
        """Оцінює і, якщо вказано пацієнта, зберігає результат в історії."""
        outcome = self.evaluate(assessment_input)
        if assessment_input.patient_id is None:
            return outcome
        assessment_id = self._assessment_repository.save(
            _lab_input(assessment_input, outcome.taken_on), _assessment_result(outcome)
        )
        return replace(outcome, assessment_id=assessment_id)

    def evaluate(self, assessment_input: AssessmentInput) -> AssessmentOutcome:
        """Розраховує результат без збереження."""
        reference = self._complete_reference(assessment_input.sex)
        _check_limits(assessment_input, reference)

        egfr, source = _resolve_egfr(assessment_input)
        gfr_category = classify_gfr(egfr, reference.gfr_categories)
        anemia_grade = classify_anemia(
            assessment_input.hemoglobin_g_l, assessment_input.sex, reference.anemia_grades
        )
        measures = suggest_measures(ClinicalFindings(
            gfr_category=gfr_category,
            hemoglobin_g_l=assessment_input.hemoglobin_g_l,
            anemia_grade=anemia_grade,
            on_dialysis=assessment_input.on_dialysis,
        ))
        return AssessmentOutcome(
            assessment_id=None,
            patient_id=assessment_input.patient_id,
            taken_on=assessment_input.taken_on or self._today(),
            egfr=round(egfr, EGFR_DECIMALS),
            egfr_display=_egfr_display(round(egfr, EGFR_DECIMALS), source),
            egfr_source=source,
            gfr_category=gfr_category,
            hemoglobin_g_l=assessment_input.hemoglobin_g_l,
            anemia_grade=anemia_grade,
            rbc_status=_rbc_status(assessment_input, reference),
            measures=measures,
            warnings=_warnings(assessment_input, gfr_category),
            guideline_version=reference.guideline_version,
        )

    def _complete_reference(self, sex: Sex) -> ReferenceSet:
        """Довідник чинної версії; неповний -> ReferenceDataError (API: 503), а не KeyError."""
        reference = self._reference_repository.get_current()
        missing = _missing_reference_parts(reference, sex)
        if missing:
            raise ReferenceDataError(
                f"Довідник {reference.guideline_version} неповний: {', '.join(missing)}"
            )
        return reference


def _missing_reference_parts(reference: ReferenceSet, sex: Sex) -> list[str]:
    return [
        *_missing_input_limits(reference, sex),
        *_missing_gfr_categories(reference),
        *_missing_anemia_grades(reference, sex),
        *_missing_rbc_reference(reference, sex),
    ]


def _missing_input_limits(reference: ReferenceSet, sex: Sex) -> list[str]:
    return [
        f"межі {parameter.value} ({sex.value})"
        for parameter in Parameter
        if (parameter, sex) not in reference.input_limits
    ]


def _missing_gfr_categories(reference: ReferenceSet) -> list[str]:
    return [] if _starts_at_zero(reference.gfr_categories) else ["категорії ШКФ від 0"]


def _missing_anemia_grades(reference: ReferenceSet, sex: Sex) -> list[str]:
    grades = reference.anemia_grades.get(sex, ())
    return [] if _starts_at_zero(grades) else [f"ступені анемії від 0 ({sex.value})"]


def _missing_rbc_reference(reference: ReferenceSet, sex: Sex) -> list[str]:
    return [] if sex in reference.rbc_reference else [f"референтні межі еритроцитів ({sex.value})"]


def _starts_at_zero(bands) -> bool:
    """Без категорії з нижньою межею 0 частина значень не потрапить у жодну."""
    return bool(bands) and min(band.lower_bound for band in bands) <= 0


def _check_limits(assessment_input: AssessmentInput, reference: ReferenceSet) -> None:
    measurements = {
        Parameter.EGFR: assessment_input.egfr_lab,
        Parameter.CREATININE: assessment_input.creatinine_umol_l,
        Parameter.HEMOGLOBIN: assessment_input.hemoglobin_g_l,
        Parameter.RBC: assessment_input.rbc_10e12_l,
    }
    violations = find_limit_violations(measurements, assessment_input.sex, reference.input_limits)
    if violations:
        raise InputLimitError(violations)


def _resolve_egfr(assessment_input: AssessmentInput) -> tuple[float, EgfrSource]:
    """ШКФ з лабораторії, якщо є; інакше — розрахунок за CKD-EPI 2021."""
    if assessment_input.egfr_lab is not None:
        return assessment_input.egfr_lab, EgfrSource.LAB
    egfr = calculate_egfr(assessment_input.creatinine_umol_l, assessment_input.age, assessment_input.sex)
    return egfr, EgfrSource.CKD_EPI_2021


def _rbc_status(assessment_input: AssessmentInput, reference: ReferenceSet) -> Optional[str]:
    if assessment_input.rbc_10e12_l is None:
        return None
    return classify_rbc(assessment_input.rbc_10e12_l, assessment_input.sex, reference.rbc_reference)


def _egfr_display(egfr: float, source: EgfrSource) -> str:
    if source is EgfrSource.CKD_EPI_2021 and egfr > EGFR_DISPLAY_LIMIT:
        return f"> {EGFR_DISPLAY_LIMIT}"
    return f"{egfr:.{EGFR_DECIMALS}f}"


def _warnings(assessment_input: AssessmentInput, gfr_category: str) -> tuple[str, ...]:
    warnings = []
    if gfr_category in CATEGORIES_WITHOUT_REDUCED_GFR:
        warnings.append(WARNING_CKD_NOT_CONFIRMED)
    if not anemia_thresholds_apply(assessment_input.age, assessment_input.pregnant):
        warnings.append(WARNING_HB_THRESHOLDS)
    if assessment_input.rbc_10e12_l is not None:
        warnings.append(WARNING_RBC_INFORMATIONAL)
    return tuple(warnings)


def _lab_input(assessment_input: AssessmentInput, taken_on: date) -> LabInput:
    return LabInput(
        patient_id=assessment_input.patient_id,
        taken_on=taken_on,
        age_years=assessment_input.age,
        creatinine_umol_l=assessment_input.creatinine_umol_l,
        hemoglobin_g_l=assessment_input.hemoglobin_g_l,
        rbc_10e12_l=assessment_input.rbc_10e12_l,
        on_dialysis=assessment_input.on_dialysis,
        egfr_lab=assessment_input.egfr_lab,
    )


def _assessment_result(outcome: AssessmentOutcome) -> AssessmentResult:
    return AssessmentResult(
        egfr=outcome.egfr,
        gfr_category=outcome.gfr_category,
        anemia_grade=outcome.anemia_grade,
        rbc_status=outcome.rbc_status,
        measures=outcome.measures,
        guideline_version=outcome.guideline_version,
    )
