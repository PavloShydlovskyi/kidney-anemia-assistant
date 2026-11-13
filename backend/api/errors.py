"""Перетворення помилок на відповіді API в узгодженому форматі.

Будь-яка помилка повертається як {"detail": [{"field": ..., "message": ...}]},
щоб Frontend показував повідомлення біля відповідного поля форми.
"""
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.assessment_service import InputLimitError
from services.ports import DataIntegrityError, ReferenceDataError, UnknownPatientError

PYDANTIC_VALUE_ERROR_PREFIX = "Value error, "
# Число, а не константа starlette: її назва відрізняється в різних версіях.
HTTP_422 = 422


def _error_response(status_code: int, items: list[dict]) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": items})


def _field_from_location(location: tuple) -> str | None:
    """("body", "hemoglobin") -> "hemoglobin"; ("body",) -> None."""
    parts = [str(part) for part in location if part != "body"]
    return parts[0] if parts else None


async def handle_request_validation(request: Request, error: RequestValidationError) -> JSONResponse:
    items = [
        {
            "field": _field_from_location(e["loc"]),
            "message": e["msg"].removeprefix(PYDANTIC_VALUE_ERROR_PREFIX),
        }
        for e in error.errors()
    ]
    return _error_response(HTTP_422, items)


async def handle_input_limits(request: Request, error: InputLimitError) -> JSONResponse:
    items = [{"field": e.field, "message": e.message} for e in error.errors]
    return _error_response(HTTP_422, items)


async def handle_unknown_patient(request: Request, error: UnknownPatientError) -> JSONResponse:
    return _error_response(status.HTTP_404_NOT_FOUND, [{"field": "patient_id", "message": str(error)}])


async def handle_data_integrity(request: Request, error: DataIntegrityError) -> JSONResponse:
    return _error_response(status.HTTP_409_CONFLICT, [{"field": None, "message": str(error)}])


async def handle_reference_data(request: Request, error: ReferenceDataError) -> JSONResponse:
    return _error_response(status.HTTP_503_SERVICE_UNAVAILABLE, [{"field": None, "message": str(error)}])


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, handle_request_validation)
    app.add_exception_handler(InputLimitError, handle_input_limits)
    app.add_exception_handler(UnknownPatientError, handle_unknown_patient)
    app.add_exception_handler(DataIntegrityError, handle_data_integrity)
    app.add_exception_handler(ReferenceDataError, handle_reference_data)
