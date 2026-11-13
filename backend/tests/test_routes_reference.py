import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes_reference import load_reference_limits, router
from api.schemas import LimitOut


@pytest.fixture
def app():
    application = FastAPI()
    application.include_router(router)
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


def find(limits, indicator, sex):
    return next(l for l in limits if l["indicator"] == indicator and l["sex"] == sex)


def test_returns_200_and_all_limits(client):
    response = client.get("/api/reference")
    assert response.status_code == 200
    limits = response.json()["limits"]
    # ШКФ — один запис, решта по одному для кожної статі
    assert len(limits) == 1 + 2 * 3


@pytest.mark.parametrize("indicator, sex, lower, upper, unit", [
    ("egfr_lab", None, 0, 100, "ml/min/1.73m2"),
    ("creatinine", "male", 40, 1000, "umol_l"),
    ("creatinine", "female", 60, 1000, "umol_l"),
    ("hemoglobin", "male", 40, 170, "g_l"),
    ("hemoglobin", "female", 30, 160, "g_l"),
    ("rbc", "male", 1, 6, "10^12/l"),
    ("rbc", "female", 1, 5, "10^12/l"),
])
def test_limits_match_clinical_table(client, indicator, sex, lower, upper, unit):
    limit = find(client.get("/api/reference").json()["limits"], indicator, sex)
    assert (limit["lower"], limit["upper"], limit["unit"]) == (lower, upper, unit)


def test_indicators_match_request_fields(client):
    from api.schemas import AssessmentRequest

    indicators = {l["indicator"] for l in client.get("/api/reference").json()["limits"]}
    assert indicators <= set(AssessmentRequest.model_fields)


def test_limits_source_can_be_replaced(app, client):
    # Так пізніше підключиться ReferenceRepository: замінюється лише залежність.
    app.dependency_overrides[load_reference_limits] = lambda: [
        LimitOut(indicator="hemoglobin", sex="female", lower=1, upper=2, unit="g_l")
    ]
    assert client.get("/api/reference").json() == {
        "limits": [{"indicator": "hemoglobin", "sex": "female", "lower": 1, "upper": 2, "unit": "g_l"}]
    }
