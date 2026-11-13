"""Інтеграційні тести рівня даних на справжній SQLite у тимчасовому файлі.

Тести вже написані за звітом Database Developer (п. 4.4), а реалізації ще немає,
тому модуль пропускається. Щоб почати, приберіть рядок pytestmark нижче
і пишіть код, доки тести не стануть зеленими.
"""
from datetime import date

import pytest

from domain.anemia import DEFAULT_ANEMIA_GRADES
from domain.kidney import classify_gfr
from domain.limits import DEFAULT_INPUT_LIMITS, Sex
from infrastructure.db import create_db_engine, create_schema
from infrastructure.reference_seed import reference_rows
from infrastructure.repositories import SqlAlchemyAssessmentRepository, SqlAlchemyReferenceRepository
from services.ports import AssessmentResult, DataIntegrityError, LabInput, UnknownPatientError

pytestmark = pytest.mark.skip(reason="TODO: Database Developer — прибрати, коли репозиторії готові")


# ---------- Фікстури ----------

@pytest.fixture
def engine(tmp_path):
    engine = create_db_engine(f"sqlite:///{tmp_path / 'test.db'}")
    create_schema(engine)
    # TODO: вставити guideline_version_row(), reference_rows() і пацієнтів з id 1 і 2
    return engine


@pytest.fixture
def repo(engine):
    return SqlAlchemyAssessmentRepository(engine)


@pytest.fixture
def reference(engine):
    return SqlAlchemyReferenceRepository(engine)


def make_lab(patient_id=2, taken_on=date(2026, 11, 13), creatinine=130.0):
    return LabInput(patient_id=patient_id, taken_on=taken_on, age_years=60,
                    creatinine_umol_l=creatinine, hemoglobin_g_l=95.0, rbc_10e12_l=3.6,
                    on_dialysis=False, egfr_lab=None)


def make_result(egfr=40.6, category="G3b"):
    return AssessmentResult(egfr=egfr, gfr_category=category, anemia_grade="moderate",
                            rbc_status="low", measures=("…",), guideline_version="KDIGO-2024/WHO-2024")


# ---------- Тести ----------

def test_seed_has_24_rows():
    assert len(reference_rows()) == 24


def test_seed_matches_domain_defaults(reference):
    current = reference.get_current()
    assert dict(current.input_limits) == dict(DEFAULT_INPUT_LIMITS)
    assert {sex: set(grades) for sex, grades in current.anemia_grades.items()} == \
           {sex: set(grades) for sex, grades in DEFAULT_ANEMIA_GRADES.items()}


def test_saved_result_is_returned_unchanged(repo):
    assessment_id = repo.save(make_lab(), make_result())
    [record] = repo.list_by_patient(2)
    assert record.assessment_id == assessment_id
    assert record.lab == make_lab() and record.result == make_result()


def test_history_is_chronological_and_per_patient(repo):
    repo.save(make_lab(taken_on=date(2026, 11, 1)), make_result(egfr=38.0))
    repo.save(make_lab(taken_on=date(2026, 9, 1)), make_result(egfr=44.0))
    repo.save(make_lab(patient_id=1), make_result())
    dates = [record.lab.taken_on for record in repo.list_by_patient(2)]
    assert dates == [date(2026, 9, 1), date(2026, 11, 1)]
    assert repo.list_by_patient(999) == []


def test_unknown_patient(repo):
    with pytest.raises(UnknownPatientError):
        repo.save(make_lab(patient_id=999), make_result())


def test_save_is_atomic(repo):
    with pytest.raises(DataIntegrityError):
        repo.save(make_lab(), make_result(category="G7"))
    assert repo.list_by_patient(2) == []


def test_calculated_egfr_above_100_is_stored(repo):
    repo.save(make_lab(patient_id=1, creatinine=40.0), make_result(egfr=120.3, category="G1"))
    [record] = repo.list_by_patient(1)
    assert record.result.egfr == pytest.approx(120.3)


@pytest.mark.parametrize("egfr, expected", [(90, "G1"), (89.9, "G2"), (45, "G3a"), (14.9, "G5")])
def test_db_categories_work_with_domain(reference, egfr, expected):
    assert classify_gfr(egfr, reference.get_current().gfr_categories) == expected
