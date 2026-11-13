import pytest
from pydantic import ValidationError

from api.schemas import AssessmentRequest

BASE = {"sex": "female", "age": 60, "creatinine": 130, "hemoglobin": 95}


def make(**changes):
    return AssessmentRequest(**{**BASE, **changes})


def test_valid_request_uses_default_units():
    request = make()
    assert request.creatinine_umol_l == 130
    assert request.hemoglobin_g_l == 95


def test_converts_units():
    request = make(creatinine=1.5, creatinine_unit="mg_dl", hemoglobin=9.5, hemoglobin_unit="g_dl")
    assert request.creatinine_umol_l == pytest.approx(132.6)
    assert request.hemoglobin_g_l == pytest.approx(95)


def test_rejects_pregnant_male():
    with pytest.raises(ValidationError, match="Вагітність"):
        make(sex="male", pregnant=True)


@pytest.mark.parametrize("changes", [
    {"age": 16}, {"age": 121}, {"creatinine": 0}, {"hemoglobin": -1},
    {"rbc": 0}, {"sex": "other"}, {"creatinine_unit": "mmol_l"}, {"patient_id": 0},
])
def test_rejects_invalid_values(changes):
    with pytest.raises(ValidationError):
        make(**changes)


def test_rejects_missing_sex():
    with pytest.raises(ValidationError):
        AssessmentRequest(age=60, creatinine=80, hemoglobin=120)


def test_rejects_unknown_field():
    with pytest.raises(ValidationError):
        make(diagnosis="CKD")


def test_taken_on_is_optional_date():
    assert make().taken_on is None
    assert str(make(taken_on="2026-11-01").taken_on) == "2026-11-01"
