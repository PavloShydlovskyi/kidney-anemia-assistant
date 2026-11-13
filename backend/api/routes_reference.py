"""GET /api/reference — граничні значення вхідних показників для форми.

Frontend бере звідси підказки для полів, щоб форма показувала ті самі межі,
які перевіряє сервер. Межі беруться з ReferenceRepository через сервіс,
тому зміна довідника в БД одразу видна і формі, і перевірці.
"""
from fastapi import APIRouter, Depends

from domain.limits import Limits, Parameter, Sex
from services.assessment_service import AssessmentService

from .dependencies import get_service
from .schemas import REQUEST_FIELD_BY_PARAMETER, LimitOut, ReferenceResponse

router = APIRouter(prefix="/api", tags=["reference"])

# Коди одиниць збігаються з колонкою reference_thresholds.unit у БД.
UNIT_BY_PARAMETER = {
    Parameter.EGFR: "ml_min_1_73m2",
    Parameter.CREATININE: "umol_l",
    Parameter.HEMOGLOBIN: "g_l",
    Parameter.RBC: "10e12_l",
}


def load_reference_limits(service: AssessmentService = Depends(get_service)) -> list[LimitOut]:
    """Граничні значення чинної версії настанов у форматі API."""
    input_limits = service.reference().input_limits
    return [
        _limit_out(parameter, sex, input_limits[(parameter, sex)])
        for parameter in Parameter
        for sex in Sex
        if (parameter, sex) in input_limits
    ]


def _limit_out(parameter: Parameter, sex: Sex, limits: Limits) -> LimitOut:
    return LimitOut(
        indicator=REQUEST_FIELD_BY_PARAMETER[parameter],
        sex=sex,
        lower=limits.lower,
        upper=limits.upper,
        unit=UNIT_BY_PARAMETER[parameter],
    )


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
