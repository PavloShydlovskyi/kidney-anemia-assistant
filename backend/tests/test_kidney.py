import pytest
from domain.kidney import calculate_egfr, classify_gfr
from domain.limits import Parameter, Sex, find_limit_violations

@pytest.mark.parametrize("creatinine, sex", [(85, Sex.MALE), (67, Sex.FEMALE)])
def test_egfr_matches_reference_table_for_age_60(creatinine, sex):
    assert calculate_egfr(creatinine, 60, sex) == pytest.approx(90, abs=1)

@pytest.mark.parametrize("egfr, expected", [
    (90, "G1"), (89.9, "G2"), (60, "G2"), (59.6, "G3a"),
    (45, "G3a"), (30, "G3b"), (15, "G4"), (14.9, "G5"),
])
def test_gfr_category_boundaries(egfr, expected):
    assert classify_gfr(egfr) == expected

@pytest.mark.parametrize("creatinine, sex", [
    (39, Sex.MALE), (1001, Sex.MALE), (59, Sex.FEMALE), (1001, Sex.FEMALE),
])
def test_creatinine_outside_limits_is_reported(creatinine, sex):
    [violation] = find_limit_violations({Parameter.CREATININE: creatinine}, sex)
    assert violation.parameter is Parameter.CREATININE


@pytest.mark.parametrize("creatinine, sex", [
    (40, Sex.MALE), (1000, Sex.MALE), (60, Sex.FEMALE), (1000, Sex.FEMALE),
])
def test_creatinine_on_limits_is_accepted_and_calculated(creatinine, sex):
    assert find_limit_violations({Parameter.CREATININE: creatinine}, sex) == []
    assert calculate_egfr(creatinine, 60, sex) > 0


def test_rejects_non_positive_creatinine():
    with pytest.raises(ValueError):
        calculate_egfr(0, 60, Sex.MALE)


def test_rejects_child():
    with pytest.raises(ValueError):
        calculate_egfr(80, 16, Sex.FEMALE)
