"""Наскрізні тести API: запит -> сервіс -> домен -> репозиторій у пам'яті."""
import pytest
from fastapi.testclient import TestClient

from infrastructure.memory import InMemoryAssessmentRepository, InMemoryReferenceRepository
from main import create_app
from services.assessment_service import AssessmentService

EXAMPLE = {
    "patient_id": 17, "sex": "female", "age": 60,
    "creatinine": 130, "creatinine_unit": "umol_l",
    "hemoglobin": 9.5, "hemoglobin_unit": "g_dl",
    "rbc": 3.6, "on_dialysis": False,
}


@pytest.fixture
def client():
    service = AssessmentService(InMemoryReferenceRepository(), InMemoryAssessmentRepository(known_patients=[17]))
    return TestClient(create_app(service))


def test_create_assessment_matches_contract_example(client):
    response = client.post("/api/assessments", json=EXAMPLE)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert (body["egfr"], body["gfr_category"], body["anemia_grade"]) == (40.6, "G3b", "moderate")
    assert (body["hemoglobin_g_l"], body["rbc_status"]) == (95, "low")
    assert body["guideline_version"] == "KDIGO-2024/WHO-2024"
    assert body["measures"] and isinstance(body["warnings"], list)


def test_limit_errors_use_agreed_422_format(client):
    response = client.post("/api/assessments", json={**EXAMPLE, "creatinine": 20, "hemoglobin": 17})
    assert response.status_code == 422
    assert response.json() == {"detail": [
        {"field": "creatinine", "message": "Креатинін 20 мкмоль/л поза межами 60–1000 мкмоль/л для жінок"},
        {"field": "hemoglobin", "message": "Гемоглобін 170 г/л поза межами 30–160 г/л для жінок"},
    ]}


def test_schema_errors_use_agreed_422_format(client):
    response = client.post("/api/assessments", json={**EXAMPLE, "age": 16, "sex": "male", "pregnant": True})
    assert response.status_code == 422
    fields = [item["field"] for item in response.json()["detail"]]
    assert "age" in fields


def test_model_level_error_has_no_field_and_clean_message(client):
    response = client.post("/api/assessments", json={**EXAMPLE, "sex": "male", "pregnant": True, "creatinine": 80})
    assert response.json() == {"detail": [{"field": None, "message": "Вагітність може бути вказана лише для жінок"}]}


def test_unknown_patient_returns_404(client):
    response = client.post("/api/assessments", json={**EXAMPLE, "patient_id": 99})
    assert response.status_code == 404
    assert response.json()["detail"][0]["field"] == "patient_id"


def test_history_in_date_order(client):
    client.post("/api/assessments", json={**EXAMPLE, "taken_on": "2026-11-01"})
    client.post("/api/assessments", json={**EXAMPLE, "taken_on": "2026-09-01", "creatinine": 110})
    history = client.get("/api/patients/17/assessments").json()
    assert [h["taken_on"] for h in history] == ["2026-09-01", "2026-11-01"]
    assert history[0]["hemoglobin_g_l"] == 95
    assert client.get("/api/patients/5/assessments").json() == []


def test_cors_allows_live_server(client):
    response = client.options("/api/reference", headers={
        "Origin": "http://127.0.0.1:5500", "Access-Control-Request-Method": "GET"})
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5500"


def test_openapi_docs_available(client):
    assert client.get("/docs").status_code == 200
