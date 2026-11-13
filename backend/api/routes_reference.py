"""GET /api/reference — граничні значення вхідних показників для форми.

Frontend бере звідси підказки для полів, щоб форма показувала ті самі межі,
які перевіряє сервер. Межі беруться з ReferenceRepository через сервіс,
тому зміна довідника в БД одразу видна і формі, і перевірці.
"""
from fastapi import APIRouter, Depends

from domain.limits import Sex
from services.assessment_service import REQUEST_FIELD_BY_PARAMETER, AssessmentService

from .dependencies import get_service
from .schemas import LimitOut, ReferenceResponse

router = APIRouter(prefix="/api", tags=["reference"])

# Коди одиниць збігаються з колонкою reference_thresholds.unit у БД.
UNIT_BY_PARAMETER = {
    "egfr": "ml_min_1_73m2",
    "creatinine": "umol_l",
    "hemoglobin": "g_l",
    "rbc": "10e12_l",
}
PARAMETER_ORDER = ("egfr", "creatinine", "hemoglobin", "rbc")
SEX_ORDER = (Sex.MALE, Sex.FEMALE)


def load_reference_limits(service: AssessmentService = Depends(get_service)) -> list[LimitOut]:
    """Граничні значення чинної версії настанов у форматі API."""
    input_limits = service.reference().input_limits
    return [
        LimitOut(
            # Назви збігаються з полями запиту POST /api/assessments.
            indicator=REQUEST_FIELD_BY_PARAMETER[parameter],
            sex=sex,
            lower=input_limits[(parameter, sex)].lower,
            upper=input_limits[(parameter, sex)].upper,
            unit=UNIT_BY_PARAMETER[parameter],
        )
        for parameter in PARAMETER_ORDER
        for sex in SEX_ORDER
        if (parameter, sex) in input_limits
    ]


@router.get(
    "/reference",
    response_model=ReferenceResponse,
    summary="Граничні значення для форми",
    description=(
        "Межі включні; креатинін і гемоглобін — у базових одиницях "
        "(мкмоль/л, г/л). Для кожного показника — окремий рядок для кожної статі."
    ),
)
def get_reference(
    limits: list[LimitOut] = Depends(load_reference_limits),
) -> ReferenceResponse:
    return ReferenceResponse(limits=limits)
