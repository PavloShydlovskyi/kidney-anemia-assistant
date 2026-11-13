"""POST /api/assessments — нове оцінювання; GET /api/patients/{id}/assessments — історія.

Маршрути лише перетворюють схеми API на структури сервісу й назад.
Помилки (422, 404) формує api/errors.py.
"""
from fastapi import APIRouter, Depends, Path, status

from services.assessment_service import AssessmentInput, AssessmentOutcome, AssessmentService
from services.ports import AssessmentRecord

from .dependencies import get_service
from .schemas import AssessmentRequest, AssessmentResponse, ErrorResponse, HistoryItem

router = APIRouter(prefix="/api", tags=["assessments"])


@router.post(
    "/assessments",
    response_model=AssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Нове оцінювання",
    responses={
        422: {"model": ErrorResponse, "description": "Некоректні дані або вихід за граничні значення"},
        404: {"model": ErrorResponse, "description": "Пацієнта не знайдено"},
    },
)
def create_assessment(
    request: AssessmentRequest,
    service: AssessmentService = Depends(get_service),
) -> AssessmentResponse:
    outcome = service.assess(_to_input(request))
    return _to_response(outcome)


@router.get(
    "/patients/{patient_id}/assessments",
    response_model=list[HistoryItem],
    summary="Історія оцінювань пацієнта",
    description="Записи впорядковані за датою аналізу, старіші спочатку (для графіка).",
)
def list_patient_assessments(
    patient_id: int = Path(ge=1),
    service: AssessmentService = Depends(get_service),
) -> list[HistoryItem]:
    return [_to_history_item(record) for record in service.history(patient_id)]


def _to_input(request: AssessmentRequest) -> AssessmentInput:
    return AssessmentInput(
        sex=request.sex,
        age=request.age,
        creatinine_umol_l=request.creatinine_umol_l,
        hemoglobin_g_l=request.hemoglobin_g_l,
        rbc_10e12_l=request.rbc,
        egfr_lab=request.egfr_lab,
        on_dialysis=request.on_dialysis,
        pregnant=request.pregnant,
        patient_id=request.patient_id,
        taken_on=request.taken_on,
    )


def _to_response(outcome: AssessmentOutcome) -> AssessmentResponse:
    return AssessmentResponse(
        id=outcome.assessment_id,
        patient_id=outcome.patient_id,
        taken_on=outcome.taken_on,
        egfr=outcome.egfr,
        egfr_display=outcome.egfr_display,
        egfr_source=outcome.egfr_source.value,
        gfr_category=outcome.gfr_category,
        hemoglobin_g_l=outcome.hemoglobin_g_l,
        anemia_grade=outcome.anemia_grade,
        rbc_status=outcome.rbc_status,
        measures=list(outcome.measures),
        warnings=list(outcome.warnings),
        guideline_version=outcome.guideline_version,
    )


def _to_history_item(record: AssessmentRecord) -> HistoryItem:
    lab, result = record.lab, record.result
    return HistoryItem(
        id=record.assessment_id,
        taken_on=lab.taken_on,
        age=lab.age_years,
        creatinine_umol_l=lab.creatinine_umol_l,
        hemoglobin_g_l=lab.hemoglobin_g_l,
        rbc=lab.rbc_10e12_l,
        egfr_lab=lab.egfr_lab,
        on_dialysis=lab.on_dialysis,
        egfr=result.egfr,
        gfr_category=result.gfr_category,
        anemia_grade=result.anemia_grade,
        rbc_status=result.rbc_status,
        measures=list(result.measures),
        guideline_version=result.guideline_version,
    )
