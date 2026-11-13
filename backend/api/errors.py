"""Перетворення помилок на відповіді API в узгодженому форматі.

Будь-яка помилка повертається як {"detail": [{"field": ..., "message": ...}]},
щоб Frontend показував повідомлення біля відповідного поля форми.
"""
import logging
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.assessment_service import InputLimitError
from services.ports import DataIntegrityError, ReferenceDataError, UnknownPatientError

from .schemas import REQUEST_FIELD_BY_PARAMETER

logger = logging.getLogger(__name__)

PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "
REQUEST_BODY = "body"
PATIENT_ID_FIELD = "patient_id"
INTERNAL_ERROR_MESSAGE = "Внутрішня помилка сервера. Спробуйте ще раз або зверніться до адміністратора."
# Число, а не константа starlette: її назва відрізняється в різних версіях.
HTTP_422 = 422


def _error_response(status_code: int, details: list[dict]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": details})


def _single_error(status_code: int, field: Optional[str], message: str) -> JSONResponse:
    return _error_response(status_code, [{"field": field, "message": message}])


def _field_from_location(location: tuple) -> Optional[str]:
    """("body", "hemoglobin") -> "hemoglobin"; ("body",) -> None."""
    fields = [str(part) for part in location if part != REQUEST_BODY]
    return fields[0] if fields else None


async def handle_request_validation(request: Request, error: RequestValidationError) -> JSONResponse:
    details = [
        {
            "field": _field_from_location(detail["loc"]),
            "message": detail["msg"].removeprefix(PYDANTIC_VALUE_ERROR_PREFIX),
        }
        for detail in error.errors()
    ]
    return _error_response(HTTP_422, details)


async def handle_input_limits(request: Request, error: InputLimitError) -> JSONResponse:
    details = [
        {"field": REQUEST_FIELD_BY_PARAMETER[violation.parameter], "message": violation.message}
        for violation in error.violations
    ]
    return _error_response(HTTP_422, details)


async def handle_unknown_patient(request: Request, error: UnknownPatientError) -> JSONResponse:
    return _single_error(status.HTTP_404_NOT_FOUND, PATIENT_ID_FIELD, str(error))


async def handle_data_integrity(request: Request, error: DataIntegrityError) -> JSONResponse:
    return _single_error(status.HTTP_409_CONFLICT, None, str(error))


async def handle_reference_data(request: Request, error: ReferenceDataError) -> JSONResponse:
    return _single_error(status.HTTP_503_SERVICE_UNAVAILABLE, None, str(error))


async def handle_unexpected(request: Request, error: Exception) -> JSONResponse:
    logger.exception("Неочікувана помилка під час %s %s", request.method, request.url.path)
    return _single_error(status.HTTP_500_INTERNAL_SERVER_ERROR, None, INTERNAL_ERROR_MESSAGE)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, handle_request_validation)
    app.add_exception_handler(InputLimitError, handle_input_limits)
    app.add_exception_handler(UnknownPatientError, handle_unknown_patient)
    app.add_exception_handler(DataIntegrityError, handle_data_integrity)
    app.add_exception_handler(ReferenceDataError, handle_reference_data)
    app.add_exception_handler(Exception, handle_unexpected)
