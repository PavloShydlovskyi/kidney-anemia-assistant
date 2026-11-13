import pytest

from domain.anemia import anemia_thresholds_apply, classify_anemia
from domain.blood import classify_rbc
from domain.bands import band_code
from domain.kidney import GfrCategory
from domain.limits import Parameter, Sex, find_limit_violations
from domain.units import creatinine_mg_dl_to_umol_l, creatinine_umol_l_to_mg_dl, hemoglobin_g_dl_to_g_l
from domain.measures import ClinicalFindings, suggest_measures

M, F = Sex.MALE, Sex.FEMALE


@pytest.mark.parametrize("sex, hb, expected", [
    (M, 130, "none"), (M, 129, "mild"), (M, 110, "mild"), (M, 109, "moderate"),
    (M, 80, "moderate"), (M, 79, "severe"),
    (F, 120, "none"), (F, 119, "mild"), (F, 110, "mild"), (F, 109, "moderate"), (F, 79, "severe"),
])
def test_anemia_grade_by_who_2024(sex, hb, expected):
    assert classify_anemia(hb, sex) == expected


@pytest.mark.parametrize("age, pregnant, applies", [(15, False, True), (65, False, True), (66, False, False), (30, True, False)])
def test_anemia_thresholds_apply(age, pregnant, applies):
    assert anemia_thresholds_apply(age, pregnant) is applies


@pytest.mark.parametrize("sex, rbc, expected", [
    (M, 4.2, "low"), (M, 4.3, "normal"), (M, 5.7, "normal"), (M, 5.8, "high"),
    (F, 3.7, "low"), (F, 3.8, "normal"), (F, 5.1, "normal"), (F, 5.2, "high"),
])
def test_rbc_status(sex, rbc, expected):
    assert classify_rbc(rbc, sex) == expected


def test_limit_violations_collects_all_and_skips_missing():
    violations = find_limit_violations(
        {Parameter.CREATININE: 20, Parameter.HEMOGLOBIN: 170, Parameter.RBC: None, Parameter.EGFR: None}, F)
    assert [v.parameter for v in violations] == [Parameter.CREATININE, Parameter.HEMOGLOBIN]
    assert violations[1].message == "Гемоглобін 170 г/л поза межами 30–160 г/л для жінок"


def test_limits_are_inclusive():
    assert find_limit_violations({Parameter.CREATININE: 40, Parameter.HEMOGLOBIN: 170, Parameter.EGFR: 100}, M) == []


def measures(category, hb, grade, on_dialysis):
    return suggest_measures(ClinicalFindings(category, hb, grade, on_dialysis))


def has(found, text):
    return any(text in measure for measure in found)


@pytest.mark.parametrize("category, text", [
    ("G2", "не показаний лише на підставі стадії"),
    ("G3b", "зазвичай не показаний"),
    ("G4", "планування нирковозамісної терапії"),
    ("G5", "Оцінити показання до початку діалізу"),
])
def test_dialysis_by_category(category, text):
    assert has(measures(category, 130, "none", on_dialysis=False), text)


def test_no_dialysis_advice_when_already_on_dialysis():
    assert not has(measures("G5", 130, "none", on_dialysis=True), "діаліз")


def test_esa_on_dialysis_only_up_to_100():
    assert has(measures("G5", 100, "moderate", True), "Розглянути початок ESA")
    assert not has(measures("G5", 101, "moderate", True), "ESA")


def test_esa_without_dialysis_is_individual():
    assert has(measures("G3b", 95, "moderate", False), "рішення індивідуальне")
    assert not has(measures("G3b", 125, "none", False), "ESA")


@pytest.mark.parametrize("hb, text", [
    (69, "Розглянути переливання"),
    (70, "автоматичного показання до переливання немає"),
    (79, "автоматичного показання до переливання немає"),
])
def test_transfusion_thresholds(hb, text):
    assert has(measures("G3a", hb, "severe", False), text)


def test_no_transfusion_advice_from_80():
    assert not has(measures("G3a", 80, "moderate", False), "переливання")


def test_band_code_picks_highest_lower_bound_and_ignores_order():
    bands = [GfrCategory("low", 0), GfrCategory("high", 50), GfrCategory("mid", 20)]
    assert [band_code(v, bands) for v in (0, 19.9, 20, 50, 80)] == ["low", "low", "mid", "high", "high"]


def test_band_code_rejects_value_below_all_bands():
    with pytest.raises(ValueError):
        band_code(-1, [GfrCategory("low", 0)])


def test_units():
    assert creatinine_mg_dl_to_umol_l(1.0) == pytest.approx(88.4)
    assert creatinine_umol_l_to_mg_dl(88.4) == pytest.approx(1.0)
    assert hemoglobin_g_dl_to_g_l(9.5) == pytest.approx(95)
