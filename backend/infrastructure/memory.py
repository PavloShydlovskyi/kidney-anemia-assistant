"""Тимчасові репозиторії в пам'яті.

Потрібні, щоб застосунок і тести працювали до появи SQLAlchemy-репозиторіїв
від Database Developer (infrastructure/repositories.py). Дані зникають
після перезапуску сервера.
"""
from dataclasses import replace
from typing import Iterable, Optional

from domain.anemia import DEFAULT_ANEMIA_GRADES
from domain.blood import DEFAULT_RBC_REFERENCE
from domain.kidney import DEFAULT_GFR_CATEGORIES
from domain.limits import DEFAULT_INPUT_LIMITS
from services.ports import (
    AssessmentRecord,
    AssessmentResult,
    LabInput,
    ReferenceSet,
    UnknownPatientError,
)

CURRENT_GUIDELINE_VERSION = "KDIGO-2024/WHO-2024"


def default_reference_set() -> ReferenceSet:
    """Межі з клінічної таблиці (ті самі, що в reference_seed.py для БД)."""
    return ReferenceSet(
        guideline_version=CURRENT_GUIDELINE_VERSION,
        input_limits=dict(DEFAULT_INPUT_LIMITS),
        gfr_categories=DEFAULT_GFR_CATEGORIES,
        anemia_grades=dict(DEFAULT_ANEMIA_GRADES),
        rbc_reference=dict(DEFAULT_RBC_REFERENCE),
    )


class InMemoryReferenceRepository:
    def __init__(self, reference: Optional[ReferenceSet] = None):
        self._reference = reference or default_reference_set()

    def get_current(self) -> ReferenceSet:
        return self._reference


class InMemoryAssessmentRepository:
    """known_patients=None — приймати будь-який id пацієнта."""

    def __init__(self, known_patients: Optional[Iterable[int]] = None):
        self._known = set(known_patients) if known_patients is not None else None
        self._records: list[AssessmentRecord] = []

    def save(self, lab: LabInput, result: AssessmentResult) -> int:
        if self._known is not None and lab.patient_id not in self._known:
            raise UnknownPatientError(f"Пацієнта з id {lab.patient_id} не знайдено")
        assessment_id = len(self._records) + 1
        self._records.append(AssessmentRecord(assessment_id, lab, replace(result)))
        return assessment_id

    def list_by_patient(self, patient_id: int) -> list[AssessmentRecord]:
        records = [r for r in self._records if r.lab.patient_id == patient_id]
        return sorted(records, key=lambda r: (r.lab.taken_on, r.assessment_id))
