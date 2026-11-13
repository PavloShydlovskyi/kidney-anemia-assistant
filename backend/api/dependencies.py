"""Залежності FastAPI: звідки маршрути беруть сервіс.

Сервіс створює main.create_app() і кладе в app.state; у тестах його можна
підмінити через app.dependency_overrides[get_service].
"""
from fastapi import Request

from services.assessment_service import AssessmentService


def get_service(request: Request) -> AssessmentService:
    return request.app.state.service
