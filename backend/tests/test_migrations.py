"""Міграції Alembic і робота застосунку на SQLite.

Перевіряють: міграції дають ту саму схему, що й infrastructure/db.py; дані
інкремента 1 не губляться після наступних міграцій; CHECK переживають
перебудову таблиць; відкат працює; API зберігає й повертає історію з БД.
"""
import sqlite3

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert

from conftest import alembic_config
from infrastructure.db import create_db_engine, metadata, patients
from main import create_app


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = tmp_path / "migrated.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    return path


def query(db_path, sql):
    with sqlite3.connect(db_path) as connection:
        return connection.execute(sql).fetchall()


def test_head_matches_schema_in_db_py(db_path):
    command.upgrade(alembic_config(), "head")

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        assert compare_metadata(MigrationContext.configure(connection), metadata) == []
    engine.dispose()
    assert query(db_path, "SELECT COUNT(*) FROM reference_thresholds") == [(24,)]
    assert query(db_path, "PRAGMA foreign_key_check") == []


def test_increment_1_data_survives_later_migrations(db_path):
    command.upgrade(alembic_config(), "0001_kidney")
    assert query(db_path, "SELECT COUNT(*) FROM reference_thresholds") == [(14,)]
    with sqlite3.connect(db_path) as connection:
        connection.executescript("""
            INSERT INTO patients (id, record_code, sex) VALUES (1, 'P-0001', 'male');
            INSERT INTO lab_results (id, patient_id, taken_on, age_years, creatinine_umol_l)
                VALUES (1, 1, '2026-01-15', 60, 85);
            INSERT INTO assessments (lab_result_id, guideline_version, egfr, gfr_category, measures)
                VALUES (1, 'KDIGO-2024/WHO-2024', 90.4, 'G1', '[]');
        """)

    command.upgrade(alembic_config(), "head")

    assert query(db_path, "SELECT creatinine_umol_l, hemoglobin_g_l FROM lab_results") == [(85.0, None)]
    assert query(db_path, "SELECT gfr_category, anemia_grade FROM assessments") == [("G1", None)]


def test_checks_survive_table_rebuild(db_path):
    command.upgrade(alembic_config(), "head")
    with pytest.raises(sqlite3.IntegrityError), sqlite3.connect(db_path) as connection:
        connection.execute("INSERT INTO patients (record_code, sex) VALUES ('P', 'male')")
        connection.execute(
            "INSERT INTO lab_results (patient_id, taken_on, age_years, creatinine_umol_l, hemoglobin_g_l) "
            "VALUES (1, '2026-01-15', 60, 85, -5)")


def test_downgrade_to_base_and_upgrade_again(db_path):
    command.upgrade(alembic_config(), "head")
    command.downgrade(alembic_config(), "base")
    tables = {name for (name,) in query(db_path, "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert tables == {"alembic_version"}

    command.upgrade(alembic_config(), "head")
    assert query(db_path, "SELECT COUNT(*) FROM reference_thresholds") == [(24,)]


def test_api_saves_and_returns_history_from_sqlite(db_path):
    command.upgrade(alembic_config(), "head")
    with create_db_engine(f"sqlite:///{db_path}").begin() as connection:
        connection.execute(insert(patients), {"id": 17, "record_code": "P-0017", "sex": "female"})
    client = TestClient(create_app())   # build_service() бере DATABASE_URL

    created = client.post("/api/assessments", json={
        "patient_id": 17, "sex": "female", "age": 60, "creatinine": 130,
        "hemoglobin": 95, "rbc": 3.6, "taken_on": "2026-11-13"})
    assert created.status_code == 201
    assert (created.json()["gfr_category"], created.json()["anemia_grade"]) == ("G3b", "moderate")

    history = client.get("/api/patients/17/assessments")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert client.post("/api/assessments", json={
        "patient_id": 99, "sex": "female", "age": 60, "creatinine": 130,
        "hemoglobin": 95}).status_code == 404
