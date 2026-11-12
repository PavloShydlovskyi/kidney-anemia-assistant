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


@pytest.mark.parametrize("sex, hemoglobin", [("male", 40), ("male", 170), ("female", 30), ("female", 160)])
def test_accepts_hemoglobin_on_limits(sex, hemoglobin):
    creatinine = 80
    assert make(sex=sex, hemoglobin=hemoglobin, creatinine=creatinine)


@pytest.mark.parametrize("sex, hemoglobin", [("male", 39), ("male", 171), ("female", 29), ("female", 161)])
def test_rejects_hemoglobin_outside_limits(sex, hemoglobin):
    with pytest.raises(ValidationError, match="Гемоглобін"):
        make(sex=sex, hemoglobin=hemoglobin, creatinine=80)


def test_hemoglobin_limits_checked_after_unit_conversion():
    with pytest.raises(ValidationError, match="Гемоглобін 170 г/л"):
        make(hemoglobin=17, hemoglobin_unit="g_dl")


@pytest.mark.parametrize("sex, creatinine", [("male", 39), ("female", 59), ("female", 1001)])
def test_rejects_creatinine_outside_limits(sex, creatinine):
    with pytest.raises(ValidationError, match="Креатинін"):
        make(sex=sex, creatinine=creatinine)


@pytest.mark.parametrize("sex, rbc, ok", [("male", 6, True), ("male", 6.1, False), ("female", 5, True), ("female", 5.1, False)])
def test_rbc_limits_depend_on_sex(sex, rbc, ok):
    if ok:
        assert make(sex=sex, rbc=rbc, creatinine=80)
    else:
        with pytest.raises(ValidationError, match="Еритроцити"):
            make(sex=sex, rbc=rbc, creatinine=80)


@pytest.mark.parametrize("egfr, ok", [(0, True), (100, True), (100.5, False), (-1, False)])
def test_lab_egfr_limits(egfr, ok):
    if ok:
        assert make(egfr_lab=egfr)
    else:
        with pytest.raises(ValidationError, match="ШКФ"):
            make(egfr_lab=egfr)


def test_reports_all_limit_errors_at_once():
    with pytest.raises(ValidationError) as error:
        make(creatinine=20, hemoglobin=200)
    message = str(error.value)
    assert "Креатинін" in message and "Гемоглобін" in message


def test_rejects_pregnant_male():
    with pytest.raises(ValidationError, match="Вагітність"):
        make(sex="male", pregnant=True, creatinine=80)


def test_rejects_minor_and_missing_sex():
    with pytest.raises(ValidationError):
        make(age=16)
    with pytest.raises(ValidationError):
        AssessmentRequest(age=60, creatinine=80, hemoglobin=120)


def test_rejects_unknown_field():
    with pytest.raises(ValidationError):
        make(diagnosis="CKD")
