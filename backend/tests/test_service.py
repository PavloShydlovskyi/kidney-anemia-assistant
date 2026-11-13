from dataclasses import replace
from datetime import date

import pytest

from domain.limits import Limits, Parameter, Sex
from infrastructure.memory import (
    InMemoryAssessmentRepository,
    InMemoryReferenceRepository,
    default_reference_set,
)
from services.assessment_service import AssessmentInput, AssessmentService, InputLimitError
from services.ports import ReferenceDataError, UnknownPatientError

TODAY = date(2026, 11, 13)


def make_service(reference=None, known_patients=None):
    return AssessmentService(
        InMemoryReferenceRepository(reference),
        InMemoryAssessmentRepository(known_patients),
        today=lambda: TODAY,
    )


def make_input(**changes):
    data = AssessmentInput(sex=Sex.FEMALE, age=60, creatinine_umol_l=130, hemoglobin_g_l=95, rbc_10e12_l=3.6)
    return replace(data, **changes)


def test_example_from_api_contract():
    outcome = make_service().assess(make_input())
    assert (outcome.egfr, outcome.gfr_category, outcome.anemia_grade, outcome.rbc_status) == (40.6, "G3b", "moderate", "low")
    assert outcome.egfr_source == "ckd_epi_2021" and outcome.egfr_display == "40.6"
    assert outcome.guideline_version == "KDIGO-2024/WHO-2024"
    assert outcome.taken_on == TODAY


def test_lab_egfr_is_used_instead_of_calculation():
    outcome = make_service().assess(make_input(egfr_lab=25))
    assert (outcome.egfr, outcome.egfr_source, outcome.gfr_category) == (25, "lab", "G4")


def test_calculated_egfr_above_100_is_displayed_as_limit():
    outcome = make_service().assess(make_input(sex=Sex.MALE, creatinine_umol_l=40, hemoglobin_g_l=140, rbc_10e12_l=None))
    assert outcome.egfr > 100
    assert outcome.egfr_display == "> 100" and outcome.gfr_category == "G1"


def test_all_limit_violations_are_reported():
    with pytest.raises(InputLimitError) as error:
        make_service().assess(make_input(creatinine_umol_l=20, hemoglobin_g_l=170, egfr_lab=101))
    assert [v.parameter for v in error.value.violations] == [Parameter.EGFR, Parameter.CREATININE, Parameter.HEMOGLOBIN]


def test_limits_come_from_reference_repository():
    reference = default_reference_set()
    limits = dict(reference.input_limits)
    limits[(Parameter.HEMOGLOBIN, Sex.FEMALE)] = Limits(100, 160)
    service = make_service(replace(reference, input_limits=limits))
    with pytest.raises(InputLimitError):
        service.assess(make_input(hemoglobin_g_l=95))


def test_saves_only_with_patient_and_returns_history_in_date_order():
    service = make_service()
    assert service.assess(make_input()).assessment_id is None
    service.assess(make_input(patient_id=5, taken_on=date(2026, 11, 1)))
    service.assess(make_input(patient_id=5, taken_on=date(2026, 9, 1)))
    service.assess(make_input(patient_id=6))
    history = service.history(5)
    assert [r.lab.taken_on for r in history] == [date(2026, 9, 1), date(2026, 11, 1)]
    assert history[0].result.gfr_category == "G3b"


def test_unknown_patient():
    with pytest.raises(UnknownPatientError):
        make_service(known_patients=[1]).assess(make_input(patient_id=2))


def test_warnings():
    old = make_service().assess(make_input(age=70, sex=Sex.MALE, creatinine_umol_l=80, hemoglobin_g_l=140, rbc_10e12_l=None))
    assert any("15–65" in w for w in old.warnings)
    assert any("G1–G2" in w for w in old.warnings)
    assert not any("еритроцитів" in w for w in old.warnings)


def test_evaluate_does_not_save():
    repository = InMemoryAssessmentRepository()
    service = AssessmentService(InMemoryReferenceRepository(), repository, today=lambda: TODAY)
    outcome = service.evaluate(make_input(patient_id=5))
    assert outcome.assessment_id is None
    assert repository.list_by_patient(5) == []


@pytest.mark.parametrize("break_reference", [
    lambda r: replace(r, input_limits={k: v for k, v in r.input_limits.items() if k != (Parameter.CREATININE, Sex.FEMALE)}),
    lambda r: replace(r, rbc_reference={}),
    lambda r: replace(r, anemia_grades={Sex.MALE: r.anemia_grades[Sex.MALE]}),
    lambda r: replace(r, gfr_categories=()),
    lambda r: replace(r, gfr_categories=tuple(c for c in r.gfr_categories if c.code != "G5")),
])
def test_incomplete_reference_is_reported_not_crashed(break_reference):
    service = make_service(break_reference(default_reference_set()))
    with pytest.raises(ReferenceDataError, match="неповний"):
        service.assess(make_input())
