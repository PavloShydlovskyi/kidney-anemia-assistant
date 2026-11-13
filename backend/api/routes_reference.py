"""GET /api/reference — граничні значення вхідних показників для форми.

Frontend бере звідси підказки для полів, щоб форма показувала ті самі межі,
які перевіряє сервер (schemas.AssessmentRequest). Клієнт порогів не зберігає.

Звідки беруться межі, вирішує залежність load_reference_limits. Зараз вона
читає значення за замовчуванням із domain/limits.py; коли з'явиться
ReferenceRepository (таблиця reference_thresholds), достатньо замінити лише її.
"""
from fastapi import APIRouter, Depends

from domain.limits import (
    CREATININE_LIMITS,
    EGFR_LIMITS,
    HEMOGLOBIN_LIMITS,
    RBC_LIMITS,
    Limits,
    Sex,
)

from .schemas import LimitOut, ReferenceResponse

router = APIRouter(prefix="/api", tags=["reference"])

# Назви показників збігаються з полями запиту POST /api/assessments,
# тому Frontend може прив'язати підказку прямо до поля форми.
# Коди одиниць збігаються з колонкою reference_thresholds.unit у БД.
EGFR_UNIT = "ml_min_1_73m2"
CREATININE_UNIT = "umol_l"
HEMOGLOBIN_UNIT = "g_l"
RBC_UNIT = "10e12_l"


def _by_sex(indicator: str, limits: dict[Sex, Limits], unit: str) -> list[LimitOut]:
    return [
        LimitOut(indicator=indicator, sex=sex, lower=value.lower, upper=value.upper, unit=unit)
        for sex, value in limits.items()
    ]


def load_reference_limits() -> list[LimitOut]:
    """Повертає граничні значення з клінічної таблиці."""
    # ШКФ має однакові межі для обох статей, але, як і в довіднику БД,
    # віддається окремим рядком для кожної статі — так формі простіше.
    egfr_by_sex = {Sex.MALE: EGFR_LIMITS, Sex.FEMALE: EGFR_LIMITS}
    return [
        *_by_sex("egfr_lab", egfr_by_sex, EGFR_UNIT),
        *_by_sex("creatinine", CREATININE_LIMITS, CREATININE_UNIT),
        *_by_sex("hemoglobin", HEMOGLOBIN_LIMITS, HEMOGLOBIN_UNIT),
        *_by_sex("rbc", RBC_LIMITS, RBC_UNIT),
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
