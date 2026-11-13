"""Збирання застосунку FastAPI і підключення залежностей.

Запуск (з папки backend):
    uvicorn main:app --reload
Документація API: http://127.0.0.1:8000/docs

Зараз використовуються репозиторії в пам'яті (infrastructure/memory.py).
Коли Database Developer завершить infrastructure/repositories.py, змінюється
лише функція build_service — маршрути, сервіс і домен залишаються як є.
"""
import os
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.errors import register_error_handlers
from api.routes_assessments import router as assessments_router
from api.routes_reference import router as reference_router
from infrastructure.memory import InMemoryAssessmentRepository, InMemoryReferenceRepository
from services.assessment_service import AssessmentService

# Адреси Frontend під час розробки (VS Code Live Server); змінюються через змінну середовища.
DEFAULT_CORS_ORIGINS = "http://localhost:5500,http://127.0.0.1:5500"


def build_service() -> AssessmentService:
    return AssessmentService(
        reference_repository=InMemoryReferenceRepository(),
        assessment_repository=InMemoryAssessmentRepository(),
    )


def cors_origins_from_env() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def create_app(
    service: Optional[AssessmentService] = None,
    cors_origins: Optional[list[str]] = None,
) -> FastAPI:
    app = FastAPI(
        title="Система підтримки лікаря: функція нирок та анемія",
        description="ШКФ за CKD-EPI 2021, категорії G1–G5, ступінь анемії. "
                    "Результати не є діагнозом; рішення приймає лікар.",
        version="0.1.0",
    )
    app.state.service = service or build_service()
    app.include_router(reference_router)
    app.include_router(assessments_router)
    register_error_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins if cors_origins is not None else cors_origins_from_env(),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    return app


app = create_app()
