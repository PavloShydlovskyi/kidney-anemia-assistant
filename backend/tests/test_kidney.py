import pytest
from domain.kidney import Sex, calculate_egfr, classify_gfr

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
def test_rejects_creatinine_outside_limits(creatinine, sex):
    with pytest.raises(ValueError):
        calculate_egfr(creatinine, 60, sex)

@pytest.mark.parametrize("creatinine, sex", [
    (40, Sex.MALE), (1000, Sex.MALE), (60, Sex.FEMALE), (1000, Sex.FEMALE),
])
def test_accepts_creatinine_on_limits(creatinine, sex):
    assert calculate_egfr(creatinine, 60, sex) > 0

def test_rejects_child():
    with pytest.raises(ValueError):
        calculate_egfr(80, 16, Sex.FEMALE)
