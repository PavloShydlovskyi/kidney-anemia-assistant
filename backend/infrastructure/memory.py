"""Тимчасові репозиторії в пам'яті.

Потрібні, щоб застосунок і тести працювали до появи SQLAlchemy-репозиторіїв
від Database Developer (infrastructure/repositories.py). Дані зникають
після перезапуску сервера.
"""
from itertools import count
from threading import Lock
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
    """Без known_patients приймає будь-який id пацієнта (таблиці patients ще немає)."""

    def __init__(self, known_patients: Optional[Iterable[int]] = None):
        self._known_patients = set(known_patients) if known_patients is not None else None
        self._records: list[AssessmentRecord] = []
        self._next_id = count(1)
        # FastAPI виконує синхронні маршрути в пулі потоків: без блокування
        # два одночасні запити могли отримати однаковий id.
        self._lock = Lock()

    def save(self, lab: LabInput, result: AssessmentResult) -> int:
        if not self._is_known(lab.patient_id):
            raise UnknownPatientError(f"Пацієнта з id {lab.patient_id} не знайдено")
        with self._lock:
            assessment_id = next(self._next_id)
            self._records.append(AssessmentRecord(assessment_id, lab, result))
        return assessment_id

    def list_by_patient(self, patient_id: int) -> list[AssessmentRecord]:
        with self._lock:
            records = [record for record in self._records if record.lab.patient_id == patient_id]
        return sorted(records, key=lambda record: (record.lab.taken_on, record.assessment_id))

    def _is_known(self, patient_id: int) -> bool:
        return self._known_patients is None or patient_id in self._known_patients
